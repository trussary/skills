// Evidence capture for /qa: screenshots, no assertions. Run once the live pass in the browser pane is clean.
//
//   cd <checkout> && QA_SHOTS=<dir> BASE_URL=<url> [QA_WIDTHS=390,860,1280] [QA_SIGN_IN=<module>] node <this file> <shots.json>
//
// Run it from the checkout root: @playwright/test is resolved from the checkout's node_modules, not from this file's directory.
//
// <shots.json> is a list of shots:
//   [{ "name": "623-preview-home", "url": "/home", "as": "member", "click": ["Start"] },
//    { "name": "623-preview-draft", "url": "file:///…/prototype/material.html", "side": "prototype" }]
// - `url`: a path on the app (BASE_URL, default http://localhost:3000) or a full URL (a saved prototype page).
// - `as`: a role the sign-in module knows, or omitted (signed out).
// - `click`: accessible names clicked in order after load (button, link, tab or text), to reach a state.
// - `side`: "build" (default) or "prototype"; part of the file name.
// - `widths`: per shot; default QA_WIDTHS, else [390, 860, 1280].
// QA_SIGN_IN is a path to an ES module whose default export is `async (request, as, base) => void`: it signs the
// Playwright APIRequestContext `request` in as role `as` (cookies land in the context). Required when any shot has `as`.
// Writes <name>-<width>-<side>.png into $QA_SHOTS (required). Prints each file; exits 1 if any shot failed.
import { readFileSync, mkdirSync } from "node:fs";
import { createRequire } from "node:module";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const { chromium } = createRequire(join(process.cwd(), "package.json"))("@playwright/test");

const base = process.env.BASE_URL ?? "http://localhost:3000";
const out = process.env.QA_SHOTS;
const defaultWidths = process.env.QA_WIDTHS ? process.env.QA_WIDTHS.split(",").map(Number) : [390, 860, 1280];
if (!out || !process.argv[2]) {
  console.error("usage: QA_SHOTS=<dir> node capture.mjs <shots.json>");
  process.exit(2);
}
mkdirSync(out, { recursive: true });
const shots = JSON.parse(readFileSync(process.argv[2], "utf8"));
const signIn = process.env.QA_SIGN_IN ? (await import(pathToFileURL(resolve(process.env.QA_SIGN_IN)).href)).default : null;

const browser = await chromium.launch();
const sessions = {};

// One signed-in storage state per role.
async function session(as) {
  if (!as) return { cookies: [], origins: [] };
  if (sessions[as]) return sessions[as];
  if (!signIn) throw new Error(`shot signs in as ${as} but QA_SIGN_IN is not set`);
  const ctx = await browser.newContext({ baseURL: base });
  await signIn(ctx.request, as, base);
  sessions[as] = await ctx.storageState();
  await ctx.close();
  return sessions[as];
}

let failed = 0;
for (const shot of shots) {
  for (const width of shot.widths ?? defaultWidths) {
    const file = join(out, `${shot.name}-${width}-${shot.side ?? "build"}.png`);
    const ctx = await browser.newContext({ baseURL: base, viewport: { width, height: 900 }, storageState: await session(shot.as) });
    const page = await ctx.newPage();
    try {
      await page.goto(shot.url, { waitUntil: "networkidle" });
      for (const name of shot.click ?? []) {
        const target = page.getByRole("button", { name }).or(page.getByRole("link", { name })).or(page.getByRole("tab", { name })).or(page.getByText(name, { exact: true }));
        await target.first().click();
        await page.waitForLoadState("networkidle");
      }
      await page.waitForTimeout(800); // let client queries that start after networkidle settle
      await page.screenshot({ path: file, fullPage: true });
      console.log(file);
    } catch (error) {
      failed++;
      console.error(`${file}: ${error.message.split("\n")[0]}`);
    }
    await ctx.close();
  }
}
await browser.close();
process.exit(failed ? 1 : 0);
