# O7 Full-stack live route 用户动作回执 - Final

## Sprint metadata

- `sprint_type: epic`
- Sprint：`sprints/2026.07.20_11-20_o7_full_stack_live_route_user_action_receipt/`
- Product owner：`product-okr-owner`
- Implementation owner：`full-stack-software-engineer`
- Final status：`accepted_software_contract_blocked_live_acceptance_no_okr_credit`
- Contract Proof boundary：`software_proof_o7_route_user_action_receipt_contract_only`
- Live Proof boundary：`blocked_live_attempt_no_receipt_no_remote_action`
- Blocker：`local_loopback_interceptor_header_only_http_400`

## Product acceptance decision

Product 接受 receipt contract、hostile/fail-closed matrix、全量测试/build/lint/diff、中文注释比例和产品文档同步；
拒绝把本轮 local execute curl 计为有效 live 用户动作，也拒绝 route execution、delivery、HIL、safe-to-control、
robot control、Mission Objective 0 或 OKR credit。

用户价值增量只发生在软件层：既有 workstation Nav2 execute endpoint 现在可以安全绑定 same-task identity，并在真正进入
handler 后为 forwarded/rejected/failed/timeout/unsafe 生成统一 receipt。计划中的真实用户旅程未完成，因为当前 exec
loopback isolation 在 handler 前返回 header-only HTTP 400，六个 live response 全为空。

## 实际交付

Full-stack 已完成：

- `pc-tools/workstation/src/shared/contracts.ts`：五项 audit identity 和
  `trashbot.pc_tools_workstation.o7_route_user_action_receipt.v1`。
- `pc-tools/workstation/src/server/index.ts`：identity/summary 脱敏、统一 receipt builder、remote schema fail-closed、
  exactly-one/no implicit retry contract。
- `pc-tools/workstation/test/catalog.test.ts`：success lineage、hostile identity、preflight reject、remote 500、schema drift、
  timeout/no retry/no manual 与 dangerous true 覆盖。
- `docs/product/pc_tools_workstation.md`：identity、receipt、stop rule 与 Proof boundary 同步。
- 本 sprint request、invocation manifest、六个原始空 response artifact 与 `tech-done.md`。

Product closeout 新增本 `side2side_check.md`、`final.md`，并在 `OKR.md` O7 段和
`docs/process/okr_progress_log.md` 追加 flat note。未修改百分比，未归档 KR。

## 验证证据

Engineer 已记录：

- targeted 最终：`Test Files 1 passed (1)`、`Tests 5 passed | 254 skipped (259)`；exit `0`。
- 全量：`Test Files 4 passed (4)`、`Tests 532 passed (532)`；exit `0`。
- build：`34 modules transformed`、`built in 1.88s`；exit `0`，仅既有 large chunk warning。
- lint：首轮两处 `no-control-regex` exit `1`；修复为 code-point filter 后 exit `0`。
- scoped `git diff --check`：exit `0`。
- 新增中文注释比例：contracts `23.26%`、server `20.28%`、test `20.20%`，均严格 `>20%`。

Product artifacts 核对：manifest 可由 `python3 -m json.tool` 解析；本地 execute/stop curl 各 `1`，remote execute/stop
均 `0`，no retry true，7072 PID cleanup clean。六个 response artifact 均为 `0 bytes`，所以 action receipt/stop receipt
JSON 断言真实失败；未以 mock/synthetic 覆盖。

## 失败定位

Live acceptance 精确阻塞在 `local_loopback_interceptor_header_only_http_400`，Engineer 记录的 runtime failure class 为
`localhost_exec_network_interception_before_workstation_handler`。health、summary、execute、stop、latest、feedback 均收到
`HTTP 400`、`Content-Length: 0`，而 Express handler invocation=`0`。

这不是此前 Algorithm/Hardware worker 在业务文件/命令前 stall 的同一 blocker：本轮 Full-stack 代码与验证均已完成。
它也不是已证明的 upper computer、Nav2、定位、controller、WAVE ROVER 或路线 blocker，因为远端调用数为 `0`。

## OKR、Mission 与 KR 收口

- O5：约 `85%`，继续暂停 provider/runtime blocker `2/2`，本轮未触达。
- O6：约 `93%`，没有新的同 task live receipt/readback，保持 flat。
- O7：约 `93%`，接受 contract 工程增量，但缺真实 receipt/user action，保持 flat。
- O1：约 `94%`，无 remote control、feedback、HIL 或 stop receipt，保持 flat。
- `current_run_artifact_delta=true` 仅限工程合同/manifest，不是 mission-grade delta。
- `external_artifact_delta=false`
- `live_control_delta=false`
- `user_action_delta=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `safe_to_control=false`
- `mission_objective_0_satisfied=false`
- `okr_credit=false`
- 主百分比：不调整
- KR：`不归档`
- 历史区：无新增完成 KR；本 sprint 的 software contract 与 blocked live 事实只留在本 final、OKR flat note 和进度日志。

## 剩余风险与下一轮唯一入口

本 sprint 的 exactly-once execute 和 stop curl 已消费，禁止在本 sprint 内再次执行 live POST、换端口补跑、开启
wrapper/canary 或生成 mock receipt。

下一轮只在以下信号出现后重开新的 action window：runtime owner 提供可复核的 loopback/network 修复证据，证明同进程
`127.0.0.1:7072` 的只读 `/api/health` 已进入 Express 并返回 workstation JSON；或 CEO/Product 批准一个不经过当前
loopback interceptor 的执行环境并先完成只读 health/summary。两种入口都还需要新的 fresh bounded-motion authorization。

即使未来 receipt forwarded 或 terminal succeeded，仍须分别补 route terminal、同窗口 wheel/HIL、stop、
delivery/operator acceptance；receipt 不替代这些证据。
