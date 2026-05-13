# Sprint 2026.05.13_16-17 Mobile Web Browser Proof Gate - Side2Side Check

## 验收结论

本轮达到 PRD 的真实本地 Chromium-family browser proof / Docker-local browser software proof 验收口径，可以作为 Objective 4 的保守进度增量；不能作为真实 iPhone/Android device behavior、production app、真实 PWA install prompt、真实云/4G、OSS/CDN live traffic、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达证据。

## PRD 对照

| 验收项 | 结果 | 证据 |
| --- | --- | --- |
| Browser gate 指向当前 `mobile/web/`，不验证旧入口 | 通过 | Task A summary 写明 `served_root=/Users/m4/apps/rober/mobile/web`，fixture 为 `mobile/fixtures/mobile_web_status.fixture.json`。 |
| Evidence 写入本 sprint `evidence/` 目录 | 通过 | `mobile_web_browser_390x844.json/png`、`mobile_web_browser_768x900.json/png`、`mobile_web_browser_acceptance_summary.json` 已落盘。 |
| 390x844 viewport 通过 phone-safe browser 验收 | 通过 | hit area、overlap、horizontal overflow、ACK visible/not delivery success、Diagnostics、Support Handoff、bundle visible/copyable、primary actions disabled 均 passed。 |
| 768x900 viewport 通过 phone-safe browser 验收 | 通过 | 同上，summary `checks[1].passed=true`。 |
| Start/Confirm/Cancel 在缺真实条件时 fail closed | 通过 | 两个 viewport 均 `primary_actions_disabled=true`，PRD 的 blocked-by-design 口径保持。 |
| ACK 只作为 accepted/processing evidence | 通过 | 两个 viewport 均 `ack_copy_visible=true` 且 `ack_not_delivery_success=true`。 |
| Browser proof 和 summary 不触发 robot backend action/ACK/cursor | 通过 | Task B targeted tests `Ran 94 tests in 47.671s OK`，覆盖 metadata-only response、valid command mixed metadata 和 protocol normalization。 |
| Closeout 保留证据边界 | 通过 | Task C 更新 `OKR.md`、`docs/process/okr_progress_log.md`、`tech-done.md`、`final.md`。 |

## OKR 最低优先级回顾

启动时 `OKR.md` 4.1 的最低完成度 Objective 是 Objective 5 约 67%，Objective 4 约 68% 为次低。本 sprint 选择 Objective 4 的理由仍成立：Objective 5 下一步需要真实 OSS/CDN、4G/SIM、云账号或 production DB/queue 外部证据；最近 DB/queue external probe 与 OSS/CDN live probe 已完成 blocked-by-design software proof，当前主机没有可用外部条件，继续 O5 会重复消费同一类 blocker。

Task A/B 完成后，Objective 4 可保守上调到约 70%，原因是当前 `mobile/web/` PWA 已从 local/static fixture string smoke 推进到真实本地 Chromium-family browser proof，并有 robot metadata-only compatibility fence。上调后 Objective 5 约 67% 仍为最低完成度 Objective。

## 非声明边界

本轮不声明：

- 真实 iPhone/Android device behavior。
- production app 可用。
- 真实 PWA install prompt 出现或通过。
- 真实云/4G 可用。
- OSS/CDN live traffic 通过。
- production DB/queue 可用。
- Nav2/fixed-route 运行通过。
- WAVE ROVER 运动、UART feedback、HIL 或 `hil_pass`。
- 真实投放、真实取消完成或真实送达。

ACK 仍只是 accepted/processing evidence，不是 delivery success、dropoff success、cancel completed、Nav2/fixed-route success、WAVE ROVER motion、HIL 或真实任务完成。

## 剩余证据链

- 需要真实 iPhone/Android 主流浏览器验收截图或录屏。
- 需要 production app 或可分发 PWA install prompt 证据。
- Objective 5 下一步需要真实云/4G、OSS/CDN live traffic 或 production DB/queue 外部环境证据；若这些条件仍不可用，下一步应继续 Objective 4 的真实手机设备/production app/PWA prompt 验收缺口。
- 需要 Nav2/fixed-route、WAVE ROVER、HIL 和真实送达证据才能继续提升机器人闭环目标。
