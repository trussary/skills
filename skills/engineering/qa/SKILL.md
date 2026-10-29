---
name: qa
description: "QA a UI ticket against its approved prototype: use the running app in the browser pane like a manual tester at phone, tablet and desktop widths, compare with the prototype and the project's design system, fix as you go, publish a QA Evidence artifact with the screenshots, and report on the PR. Needs the Claude desktop app (its built-in browser pane and the Artifact tool). Use for any ticket with UI before it is merged, or when the user asks to QA a screen."
---

Needs the Claude desktop app: the built-in browser pane (`mcp__Claude_Browser__*` tools) and the Artifact tool. Without them, stop and tell the user.

QA one UI ticket against the prototype it was built from. This is acceptance, not regression: regression protection comes from the unit and integration tests (see /tdd). The work is a **live loop**: use the app, see a mismatch, fix the code, let HMR reload, look again. Evidence is captured once, at the end.

Project facts come from `docs/agents/project.md`: `## Dev stack` (start, port, parallel checkouts, stop) and `## UI and QA` (design system, widths, users to act as, copy checks, e2e flows, evidence language). A missing section falls back to the default given at each step; say which defaults you used in the report.

## Inputs

- The ticket (issue number), and the PR if one exists.
- Every prototype linked in the ticket's `## Prototype` section. Read each with the Artifact tool (`action: "read"`).
- The design system: the one the ticket or its map names, else the one in `## UI and QA`, else the tokens and components already in the codebase. Read its tokens, components and any UI terms its README lists.

## Steps

1. Read the ticket's acceptance criteria and the prototypes. List the screens and flows to check, and in each prototype screen every section and visual element (illustration, mascot, animation, image): each one is either on the list or named in the ticket as left out. A check that compares copy only ships screens with a missing hero illustration, intro animation or whole section.
2. Start the app in the background with the `## Dev stack` start command (default: the dev script in the README or `package.json`), with that section's port overrides when another checkout holds the ports, or point at staging if the change is deployed there. A stack this run started is stopped afterwards with the section's stop command; a stack that was already up keeps running.
3. Open the app in the built-in browser with `preview_start {url}`. The web port is the one the dev server prints (`## Dev stack` says where); checkouts differ, so read it rather than assume 3000. Sign in as each user in `## UI and QA` "Users to act as" (default: ask the user for test accounts, or read them from the project's seed files). To switch role in one flow, sign in again as the other account; set up a role whose screens are not under test through the API instead.
4. Run the **live loop** on each screen and state, at each width in `## UI and QA` (`resize_window`; default 390, 860 and 1280 px, phone first):
   - use it the way each user role would: click, type, submit, go back, reload;
   - compare with the prototype: layout and hierarchy, states (empty, loading, error, done);
   - UI copy and glossary terms (`GLOSSARY.md`, the design system README, the copy checks in `## UI and QA`);
   - design-system tokens and components, not one-off colors or spacing; overflow, wrapping and clipping at the narrowest width;
   - the acceptance criteria;
   - `read_console_messages` and `read_network_requests` show no errors.
   Look with text first: `read_page` or `get_page_text` for content, copy, states and overflow; `javascript_tool` for computed sizes. Take a screenshot only to judge layout against the prototype, one per screen and width, at `scale: 0.5`, and `zoom` into a region for detail. Each screenshot stays in context for the rest of the run; the evidence images come from step 5, outside it.
   A mismatch that is clearly an implementation bug is fixed on the spot and looked at again; the screen is done when it matches at every width. Keep a list of each screen and state checked: step 5 captures exactly those.
5. Capture the evidence with `${CLAUDE_SKILL_DIR}/capture.mjs`: write the step 4 list as a shot list (its header has the format; one entry per screen and state, `side: "prototype"` entries for the same states from the prototype page saved locally with `Artifact` `action: "read"` and `path`, opened by `file://` URL), then from the checkout root run `QA_SHOTS=<scratchpad>/qa-<issue#>/shots BASE_URL=http://localhost:<port> node ${CLAUDE_SKILL_DIR}/capture.mjs <list>`. Add `QA_WIDTHS` when `## UI and QA` lists other widths, and `QA_SIGN_IN=<module>` (the sign-in module `## UI and QA` names) for shots with `as`. Images stay out of the repo. A prototype that does not render offline gets a link in the figcaption and no image. The step 4 look already judged each screen, so check the capture by the files capture.mjs lists, not by reading the images back.
6. Write a Playwright spec at `e2e/<issue#>-<slug>.spec.ts` only for a flow worth running again: the e2e flows `## UI and QA` lists (default: sign-in, submitting work, and flows that broke before). Role- and text-based locators, run until it passes against the built app. If an older spec in `e2e/` is broken by this change, fix it or delete it.
7. Build the QA Evidence artifact from `${CLAUDE_SKILL_DIR}/EVIDENCE-TEMPLATE.html`. Copy it, fill every `{{placeholder}}`, repeat the REPEAT blocks, delete unused blocks, and publish with the Artifact tool, passing `$QA_SHOTS` images as `files` under `shots/`. Headings stay English; prose is in the evidence language `## UI and QA` names (default English); UI copy under test is quoted verbatim.
   - One artifact per ticket. QA again after a fix → find its URL in the earlier PR comment and publish to that `url`, bumping the Round field.
   - The artifact is private. Tell the user the link and that sharing it is the user's call.
   - Screenshots come from fixture data only.
8. Report on the PR (`gh api repos/<owner>/<repo>/issues/<pr>/comments -F body=@<file>`, repo from `docs/agents/issue-tracker.md`), or to the user if there is no PR:
   - The artifact link and the verdict line: **Pass**, or a numbered list of mismatches (screen, expected, actual) in text.
   - The decisions for human, in text.
   - The e2e spec path and how to run it (`npx playwright test e2e/<file>`), when step 6 wrote one.
   - No images in the comment and none committed to git: the artifact holds them, and no `toHaveScreenshot` baselines either.

A mismatch where the prototype itself looks wrong is a question for the human: report it, don't change the design.
