# Sprint 2026.05.13_07-08 Mobile Operation Log Gate - Side By Side Check

## Sprint Type

- `sprint_type: epic`
- evidence_boundary：`software_proof_docker_mobile_operation_log_gate`
- 验收时间：2026-05-13 07:14 Asia/Shanghai

## 对照结论

本轮满足 PRD 和 tech-plan 的 P0 验收口径：手机端已新增只读 operation log 面板，能展示最近事件、恢复提示和支持交接入口；robot compatibility fence 已证明 operation-log metadata 不触发 action、不 POST ACK、不推进或持久化 cursor，并且不改变 `trashbot.remote.v1` command/status/ACK 语义。

本轮只进入 Objective 4 的 local/Docker software proof，不进入真实手机、真实云、真实机器人或真实送达证据链。

## PRD/Tech Plan 对照

| 验收项 | 结果 | 证据 |
| --- | --- | --- |
| operation log 面板在 fixture/static smoke 中可见 | 通过 | Task A `mobile.test_mobile_web_entrypoint` 输出 `Ran 7 tests in 0.002s OK`。 |
| 异常/blocked/pending ACK/offline/manual takeover 有可读恢复提示 | 通过 | Task A 从 phone-safe status/readiness/support 字段派生事件并展示恢复提示。 |
| 支持交接入口可见且不触发控制动作 | 通过 | Task A 面板只读；Task B metadata-only fence 不触发 backend action。 |
| Start/Confirm/Cancel 不因 operation log metadata 绕过 command safety | 通过 | Task A 保持 primary actions fail-closed；Task B 确认 metadata 不污染 robot command envelope。 |
| Robot compatibility fence 通过 | 通过 | Task B targeted unittest 输出 `Ran 69 tests in 34.102s OK`，`py_compile` 与 scoped diff check 通过。 |
| docs 同步 | 通过 | `mobile/README.md`、`docs/product/mobile_user_flow.md`、`docs/interfaces/ros_contracts.md`、`docs/product/remote_4g_mvp.md` 已由 worker 同步；本 closeout 更新 sprint、`OKR.md`、`docs/process/okr_progress_log.md`。 |

## 文档路径核对

已确认以下引用路径存在：

- `docs/product/mobile_user_flow.md`
- `docs/product/remote_4g_mvp.md`
- `docs/interfaces/ros_contracts.md`
- `docs/process/okr_progress_log.md`

## 不声明范围

本轮明确不声明：

- 真实手机设备/browser 验收。
- production app。
- 真实 PWA install prompt。
- 真实云/4G。
- OSS/CDN live traffic。
- production DB/queue。
- Nav2/fixed-route。
- WAVE ROVER。
- HIL。
- 真实送达。

ACK 仍只是 accepted/processing evidence，不是 delivery success。

## 阻塞与风险

- 真实手机浏览器、设备尺寸、触控和 PWA install prompt 仍需后续补证。
- 真实云/4G、OSS/CDN live traffic、production DB/queue 仍属于 Objective 5 后续证据。
- 真实机器人状态、Nav2/fixed-route、WAVE ROVER、HIL 和真实送达仍依赖 O1/O2/O3 后续证据。
- closed test socket `ResourceWarning` exit 0，当前不阻塞本 sprint，但后续若重复出现可由 robot worker 单独清理测试资源释放。

## OKR 回顾

tech-plan 中"最低 Objective 是 Objective 4"的理由仍成立。本轮直接推进 O4 的手机用户体验与低成本量产边界，证据足以支持 Objective 4 从约 58% 保守上调到约 60%。Objective 1/2/3/5 未获得新实证，不调整。
