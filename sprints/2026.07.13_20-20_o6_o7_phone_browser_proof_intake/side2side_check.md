# Side2Side Check - O6/O7 Phone Browser Proof Intake

## Sprint Metadata

- sprint_type: epic
- run_time: 2026-07-13 21:03:10 CST
- Sprint: `sprints/2026.07.13_20-20_o6_o7_phone_browser_proof_intake/`
- Product owner: `product-okr-owner`
- Primary implementation owner: `full-stack-software-engineer`
- Supporting implementation owner: `robot-software-engineer`
- Product verdict: accepted as support-only distinct evidence path

## Inputs Checked

- `pre_start.md`
- `prd.md`
- `tech-plan.md`
- `tech-done.md`
- `OKR.md` O5/O6/O7/O1 current state

## User Value And Product North Star

普通手机用户最终需要的不是更多内部 wrapper，而是同一 `task_id` 下可追溯的任务、路线、手机/浏览器验收材料、安全边界和缺口说明。产品北极星仍是普通用户通过手机触发固定路线送达，并能在失败或未完成时看到可信证据链。

本轮抓手把 `phone_browser_terminal_material` 接进 O6/O7 selected-task 证据链：运营人员可以从 O7 主路径发起 `phone-browser-proof/intake`，只写入安全摘要，再回读同一任务的材料状态。该抓手能减少未来真实 phone/browser 材料到位后的接线成本，但当前仍只是 local/mock software proof。

## Side By Side Acceptance

| 项目 | PRD / Tech Plan 口径 | Tech Done 证据 | Product 判断 |
| --- | --- | --- | --- |
| O6 archive/readback | 新增 `phone_browser_terminal_material`，白名单材料和 safe refs，只回读安全摘要 | `remote_cloud_relay.py` 新增 schema `trashbot.o6.phone_browser_terminal_material.v1`，proof boundary 固定 `software_proof_o6_o7_phone_browser_terminal_material_intake_only`；field evidence、artifact bundle、`field_motion_evidence_packet` 或轻量顶层字段可 intake 并回读 | 接受 |
| O7 selected-task action | 新增 `POST /api/o7/consumer-read/tasks/:taskId/phone-browser-proof/intake?baseUrl=<local-loopback-url>` | O7 adapter、server route、client API、shared contract、Vue UI 和 tests 已实现；receipt schema 为 `trashbot.pc_tools_workstation.o7_phone_browser_proof_intake_result.v1` | 接受 |
| 同一任务身份 | path/body task id 一致，写入后同一 task readback | O7 receipt 包含 `same_task_id_consumed=true`、`phone_browser_terminal_material_written=true`、`phone_browser_terminal_material_readback=true`；O6/O7 均要求同 task | 接受 |
| fail-closed | 非回环 URL、task mismatch、dangerous true、raw URL/token/local path/raw body 均失败 | O6 hostile 测试覆盖 raw URL、cookie、Authorization、token、本地路径、screenshot body、DOM dump、traceback、`/cmd_vel`、serial/UART、WAVE ROVER 和 dangerous true field；O7 覆盖非回环 URL、task mismatch、dangerous true、raw URL/token/local path/raw body、控制词和坏 O6 receipt | 接受 |
| fixed false fields | 必须固定 `safe_to_control=false`、`delivery_success=false`、`route_execution_success=false`、`hil_pass=false`、`connects_cloud_production=false` | O6/O7 tech-done 均记录固定 false fields；O7 还保留 `robot_control_executed=false` | 接受 |
| 文档同步 | 更新 O6/O7 interface 和 product docs | O6 docs: `docs/interfaces/o6_cloud_archive_api.md`、`docs/product/cloud_4g_infrastructure.md`、`docs/product/remote_4g_mvp.md`；O7 docs: `docs/interfaces/o7_realtime_operator_console.md`、`docs/product/pc_tools_workstation.md` | 接受 |

## Verification Evidence Reviewed

Robot Software Engineer:

- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`：exit 0。
- `python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay`：`Ran 193 tests in 84.730s`，`OK`。
- Anchor `rg`：exit 0，命中 O6 code、tests、docs 和 sprint docs。
- Scoped `git diff --check`：exit 0。
- 首轮失败定位：artifact bundle consumer alias 未暴露 `phone_browser_terminal_material`，已补齐 alias 后通过。

Full-Stack Software Engineer:

- `cd pc-tools/workstation && npm run test`：`Test Files 3 passed (3)`，`Tests 507 passed (507)`。
- `cd pc-tools/workstation && npm run build`：通过，`built in 1.98s`，仅保留既有 Vite large chunk warning。
- `cd pc-tools/workstation && npm run lint`：exit 0。
- Anchor `rg`：exit 0，命中 O7 adapter、server route、client API、shared contract、Vue UI、tests、docs 和 sprint docs。
- Scoped `git diff --check`：exit 0。
- 首轮失败定位：response-side unsafe scanner 把允许的固定 false key `reads_local_path=false` 误判为 raw local path；已改为 response 只扫描字符串值，request body 仍对 raw key fail closed。

## Product Acceptance Conclusion

接受本 sprint 为 O6/O7 selected-task phone/browser terminal-material local/mock intake/readback software proof only。它比重复 bundle export 或 readback wrapper 更具体，因为它增加了一个 distinct write/readback path，并能消费同一 `task_id` 的 phone/browser terminal material 安全摘要。

不接受为 real phone/browser proof、production cloud proof、production DB/queue、OSS/CDN live traffic、4G/SIM、route execution、delivery/operator acceptance、真实 delivery success、HIL、safe-to-control 或 O5 external evidence。

## OKR / KR Decision

- Direction judgment: continue O6/O7 evidence-chain support path, but keep mission scoring gate unchanged.
- O5: flat at about `85%`; this sprint did not touch CDN/TLS probe, readiness packet, production cloud or external evidence.
- O1: flat at about `94%`; no explicit operator-approved live HIL, stop HIL capture, route execution or safe-to-control evidence.
- O6/O7: flat at about `93%`; accepted only as support-only local/mock software proof.
- KR history: 不归档。没有完成、取消、替换或过期的 KR 可移动到历史区。

## Explicit Non-Touch Boundary

本轮 Product 验收确认：没有触碰硬件/vendor、WAVE ROVER、ESP32、Orange Pi、UART、串口、ROS2 launch、motion/control、`/cmd_vel`、`/api/base/manual`、NavigateToPose、WAVE ROVER UART、O5 CDN/TLS probe 或 O5 readiness packet consumption。

## Remaining Risks And Needed Evidence

- 仍缺真实手机/browser 操作链、真实公网入口、生产 DB/queue、OSS/CDN live traffic、4G/SIM 和真实设备验收材料。
- 仍缺 live route execution、delivery/operator acceptance、真实 delivery success、current live HIL 和 safe-to-control。
- 下一轮若继续 O6/O7，必须消费更强材料：真实 phone/browser acceptance、live route execution、delivery record、operator acceptance 或 production readback；否则不应继续靠 support-only wrapper 提升 OKR。
