# trussary-skills

[English](./README.md)

Quy trình làm việc với agent của Brio (công cụ dạy IELTS của Trussary), đóng gói thành plugin cho Claude Code. Plugin gồm skill, subagent và hook, đưa một phần việc đi từ issue roadmap tới PR đã merge với CI xanh. Ở mỗi cổng, người quyết định; phần còn lại agent làm.

Đây là bản fork của [mattpocock/skills](https://github.com/mattpocock/skills). Phần lõi là các skill của Matt: grilling, domain modeling, TDD, code review, wayfinder, spec và ticket. Bản fork bổ sung những phần giúp nhiều agent cùng build một spec song song mà kết quả vẫn review được:

- subagent implementer, merger, QA và reviewer;
- tách model executor và advisor, mỗi PR kết thúc bằng một bản ghi `## Run`;
- read budget cho từng ticket;
- hook chặn ghi file qua shell và chặn đọc file quá lớn;
- `/retro` để chỉnh lại toàn bộ dựa trên số liệu trong các bản ghi.

## Vòng lặp

```
issue roadmap
  └─ /wayfinder        mỗi slice một map: các ticket quyết định, giải bằng grilling, research, prototype
       └─ /to-spec     đích đến của map, viết thành một issue spec
            └─ /to-tickets   ticket tracer-bullet có quan hệ chặn, mỗi ticket ghi executor và read budget
                 └─ /implement-spec   implementer chạy trên các ticket sẵn sàng, merge vào một nhánh tích hợp,
                                      /code-review mỗi đợt, /qa cho ticket có UI, PR mở tới khi CI xanh
                      └─ người merge → dọn nhánh và worktree → /retro
```

`/implement` là bản một ticket của `/implement-spec`. `/grill-with-docs`, `/tdd`, `/diagnosing-bugs`, `/research` và `/prototype` dùng trong vòng lặp hoặc dùng riêng.

## Cài đặt

Plugin chỉ chạy trên Claude Code, vì subagent, hook và đường dẫn `${CLAUDE_PLUGIN_ROOT}` là tính năng của Claude Code.

```bash
claude plugin marketplace add trussary/skills
claude plugin install trussary-skills@trussary
```

Sau đó chạy một lần trong mỗi repo:

```
/setup-trussary-skills
```

Skill này tạo `docs/agents/` gồm issue tracker, triage label, domain docs, thông tin project và model. Nó cũng thêm khối `## Workflow` và `## Agent skills` vào `CLAUDE.md`. Cuối cùng nó đề xuất các guardrail, mỗi mục bạn tự chọn bật:

- luật chặn push vào `main` và force push;
- tự dọn nhánh đã merge khi mở phiên;
- model advisor.

Bộ mẫu đã điền đầy đủ của một project thật nằm ở [examples/brio](./examples/brio/docs/agents/).

Không cài chung với `mattpocock-skills` vì trùng tên skill. Chỉ chọn một trong hai.

### Yêu cầu

- `gh` để làm việc với issue và PR trên GitHub. Các skill lập kế hoạch cũng chạy được với GitLab và tracker markdown cục bộ.
- `python3` cho hook và tool.
- `/qa` và `/prototype` cần trình duyệt tích hợp và Artifact của app Claude desktop.
- Có MCP server codegraph thì agent dùng nó, không có thì agent dùng Grep và Read.

## Có gì bên trong

Danh sách đầy đủ ở [README tiếng Anh](./README.md#whats-in-it). Tóm tắt:

- **Lập kế hoạch:** `/wayfinder`, `/grill-with-docs`, `/to-spec`, `/to-tickets`, `/triage`.
- **Build:** `/implement-spec`, `/implement`, `/tdd`, `/diagnosing-bugs`, `/prototype`.
- **Kiểm tra:** `/code-review`, `/qa`, `/security-audit` (của [Cloudflare](https://github.com/cloudflare/security-audit-skill), MIT).
- **Cải tiến:** `/retro`, `/improve-codebase-architecture`, `/writing-for-agents`.
- **Subagent:** `trussary-skills:implementer`, `trussary-skills:merger`, `trussary-skills:qa`, `trussary-skills:reviewer`.

## Đóng góp

Xem [CONTRIBUTING.md](./CONTRIBUTING.md). Khi upstream mattpocock/skills ra bản mới, thay đổi được merge về bằng tay.

## Giấy phép

MIT, xem [LICENSE](./LICENSE). Dựa trên [mattpocock/skills](https://github.com/mattpocock/skills) của Matt Pocock.
