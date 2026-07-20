# O3/O1 Current Readiness + Bounded Route - Side-to-Side Check

## Sprint metadata

- `sprint_type: epic`
- Product owner：`product-okr-owner`
- Product decision：`accept_current_no_go_cleanup_and_offline_absolute_deadline_contract_reject_mission_credit`
- `READINESS_GO=false`
- proof boundary：`software_proof_plus_current_no_go_not_live_fix_validation`
- `PRODUCT_ACCEPTANCE_COMPLETE=yes`
- KR：`不归档`

## Product 对照验收

| 检查项 | 计划口径 | 实际证据 | Product 判定 |
| --- | --- | --- | --- |
| Fresh authorization | operator 看护、路线清空、物理位置受限下只允许一次 Phase A；GO 后才允许单次 bounded route | CEO 本轮 fresh 授权成立；唯一 Phase A 已消费 | 接受授权门禁，不得重跑 |
| Phase A 调用 | start/proof/latest/owned-stop 各最多一次 | `1/1/1/1` | 通过调用次数 gate |
| Strict no-motion | base/lidar `false/false`，new-open=`0/0`，禁止 `/initialpose`、manual、direct `/cmd_vel`、UART 与 goal | effective argv 与 artifact 均为 `false/false`、`0/0`；forbidden 与 goal 全为 `0`，`physical_motion=false` | 通过安全边界 |
| Readiness final | 80 秒预算内自然 final，current pose/TF/persisted pose、planner/controller、path 与 obstacle 全绿 | parent `80395ms` 撞 80 秒 timeout；仅 partial/interrupted，path 未尝试、count=`0`，obstacle clear 未证明 | `READINESS_GO=false`，拒绝 readiness |
| Phase B | 仅 GO 后 pre-base-stop/goal/post-base-stop | `0/0/0`，Phase B manifest absent | 正确 fail closed；拒绝 route/user action/HIL |
| Cleanup | NO-GO 后 owned stop，PID 与 process group residual=`0` | lifecycle stopped，PID file absent，final residual=`0` | 接受 cleanup |
| 根因 | 解释上一轮 80 秒合同为何仍被 parent 截断 | parent/helper monotonic 起点相差约 `3631ms`，实际 reserve 约剩 `0.764s` | 接受 `parent_helper_monotonic_clock_origin_mismatch` |
| 离线修复 | parent 在 Popen 前生产 absolute deadline，helper 消费同一 deadline，wait 只用 remaining | producer/consumer、pre/post-Popen fail-closed 与 legacy compatibility 已实现 | 接受软件合同，不接受 live fix validation |
| 工程验证 | owner 运行测试、修复失败并复验 | Upper `119` OK(skip1)、O10 `170` OK、集成 `289` OK(skip1)，py_compile/JSON/rg/diff 通过 | 接受 Engineer 证据；Product 不重跑 |
| 中文注释 | 新增技术注释全部中文且比例 `>20%` | Robot `75/317=23.66%`；Algorithm integration audit `36/163=22.09%`，Algorithm 自身 final audit `38/168=22.619%` | 通过 |

## 当前现场事实

Phase A start semantic success，但 proof 在 `80395ms` 被 Upper API 80 秒 parent timeout 截断。Canonical current evidence 是 partial/interrupted，而不是 final：`artifact_kind=partial`、`natural_completion=false`、`last_phase=interrupted`、`initialpose_publish_attempts=0`、path requested/attempted/succeeded/generated=`true/false/false/false`、point count=`0`。Current AMCL pose、persisted pose audit、planner/controller readiness 与 obstacle clear 均未达到 GO 门槛。

NO-GO 后只执行一次 `/api/nav2/stop`，最终 lifecycle stopped、owned PID file absent、lifecycle PID 与 helper process group 均 absent、`residual_count=0`。第一版 residual scan 的自匹配 `1` 已由只读匹配修正；最终事实以 `phase_a_owned_cleanup_residual_final.json` 为准，没有第二次 stop 或第二个 live window。

Phase B pre-base-stop/goal/post-base-stop=`0/0/0`，`T=1001` invocation=`0`，所以旧 operator report 或历史 route success 不得覆盖本轮 current NO-GO。

## Root cause 与离线 absolute deadline 合同

Algorithm review 对齐 parent `80395ms` 与 helper start-to-SIGINT `76764ms`，定位未计入 helper-relative deadline 的 startup gap 约 `3631ms`。旧 4 秒 final reserve 因 clock origin 不同，现场只剩约 `0.764s`，所以后移 package probe 仍不足以保证自然 final。

Product 接受以下离线修复事实：Algorithm helper 新增可选 absolute monotonic deadline consumer，取 absolute/relative 更早值；Robot Software 在 argv/Popen 前创建同机 absolute deadline，并让 `communicate()` 只等待 remaining。Deadline 在 Popen 前耗尽时不创建子进程，Popen 后耗尽时仅清理 parent-owned process group；旧调用保持兼容且不扩窗。

验证 artifact 记录 `119 + 170 = 289` 项集成通过，hostile fixture 模拟 `3.6s` startup 后 parent wait=`76.4s`，仍自然形成 blocked final，不读取 partial fallback、不写 timeout fallback、不发 timeout signal。该结果是 offline end-to-end software contract，不是板端 live fix validation。

## Mission / OKR 对照

- `current_run_artifact_delta=true`：仅表示本轮 current safe NO-GO、单窗口调用与 clean cleanup 证据。
- `external_artifact_delta=false`
- `live_control_delta=false`
- `user_action_delta=false`
- `route_execution_success=false`
- `hil_pass=false`
- `delivery_success=false`
- `safe_to_control=false`
- `okr_credit=false`
- Mission Objective 0：`blocked_before_attempt_on_current_localization_readiness`

O5 约 `85%` 且 provider/runtime blocker `2/2`，继续暂停；O6/O7 各约 `93%`，O1 约 `94%`，全部 flat。O3 只接受 supporting current NO-GO 与软件修复，不单独计主分；KR `不归档`，历史完成区无新增。

## Agent 调度与边界

本 sprint planning 阶段的 Product worker 曾两次在业务文件前零落盘 stall；该事实不是 mission result。主节点随后按白名单补齐 planning 三文档。真实 business worker 已恢复：Robot Software 与 Robot Algorithm Engineer 实际修改业务代码、测试和 navigation 文档，写入结构 artifact 并运行验收；这只证明工程执行通道恢复，不改变本轮 NO-GO 与零 OKR credit。

Product 本阶段只读核对 planning、`tech-done.md`、全部 Robot/Algorithm JSON、工程 diff、docs/tests 变更；没有重跑工程测试、SSH、ROS、Nav2、控制 endpoint 或 live。

## 下一轮唯一入口

本授权窗口已由唯一 Phase A 消费，**不得重跑**。下一步只能在重新确认新的 current operator、route、obstacle、readiness 条件并取得**新的 fresh 授权**后，将已修复版本部署并执行 exactly-one Phase A。未重新 live 验证前，proof boundary 保持 `software_proof_plus_current_no_go_not_live_fix_validation`；Phase A 仍为 NO-GO 时，Phase B invocation 必须保持 `0`。
