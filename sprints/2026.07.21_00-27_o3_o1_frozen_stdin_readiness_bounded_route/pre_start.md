# O3/O1 Frozen Stdin Readiness + Bounded Route - Pre Start

## Sprint metadata

- `sprint_type: epic`
- 启动时间：`2026-07-21 00:27 CST`
- 状态：`planning_complete_pending_engineer_dispatch`
- Product owner：`product-okr-owner`
- 唯一 live owner / 主责集成：`robot-software-engineer`
- 条件只读复核：`robot-algorithm-engineer`、`robot-hardware-engineer`
- Full-stack：`not_dispatched`
- SSH target：`root@192.168.1.11:37878`
- planning target HEAD：`af08e6545819758b1b3e6127903d55d5664fa93a`
- authorization：`ceo_20260721_0025_operator_watch_route_clear_physical_limit_v4`
- run：`run_o3_o1_frozen_stdin_readiness_route_20260721_0025_01`
- action：`action_o3_o1_bounded_nav_20260721_0025_01`
- planning proof boundary：`planning_only_no_ssh_no_live_no_control_no_okr_credit`

## 用户价值与产品北极星

北极星仍是普通用户把垃圾交给机器人后，机器人可验证地沿固定路线送达，并在任何异常时可靠停止。本轮不是再做一层 readiness 包装，而是把上一轮已确认的 client transport 缺口替换为唯一可审计入口：先冻结 request，用本地 `jq -c` 提取并完成 parse、hash、对象数量断言，再经 stdin pipe 原样送给远端 `curl --data-binary @-`；严禁 inline JSON。

唯一有价值的链路是：`fresh authorization -> frozen request -> local jq/assert/hash -> stdin transport -> exactly-once Phase A -> current final READINESS_GO decision -> conditional pre-stop -> exactly-one bounded NavigateToPose -> terminal -> post-stop -> T=1001/HIL/operator evidence -> clean owned cleanup`。任一 gate 失败都必须 NO-GO、安全停止并封存，不能靠重试、旧材料或 HTTP `200` 制造成功。

## Fresh authorization 与独立窗口

CEO 在 `2026-07-21 00:25 CST` 给出新的独立授权 `ceo_20260721_0025_operator_watch_route_clear_physical_limit_v4`：operator 看护、路线清空、物理位置受限、受控运动已授权，目标为 `root@192.168.1.11:37878`。它不得与任何旧授权、旧 request、旧 raw、旧 terminal 或旧 nested success 混用。

本 planning 不消费授权。授权消费点严格定义为 Engineer 对 remote `/api/nav2/start` 发出唯一 transport attempt；即使 HTTP 非 `2xx`、JSON parse 失败、remote handler invocation=`0` 或 transport 在 handler 前损坏，也视为已消费。本窗口 `no_retry=true`。

冻结 identity 至少包含 authorization、run/action、目标 host、目标 commit、固定 route request identity、operator/route/physical-limit 条件、`no_retry=true` 和所有 endpoint 预期计数。默认沿用已接受的 fixed goal `map (0.8, 0.25, yaw=0)`、task `task_o3_28_pose_fixed_route_consumer_20260713_0402` 与 route intent `route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path`；Engineer 必须把它们写进同一冻结 request，禁止现场临时改 goal 或 identity。

## 最近两轮 blocker 核对与方向去重

1. `sprints/2026.07.20_20-25_o3_o1_current_readiness_bounded_route/` 的 `parent_helper_monotonic_clock_origin_mismatch` 造成 parent 在约 `80395ms` 截断 helper，只形成 partial；该轮消费完旧授权，Phase B=`0`。随后离线实现 absolute deadline 合同，但当时尚未 live 验证。
2. `sprints/2026.07.20_21-26_o3_o1_live_deadline_fix_validation_bounded_route/` 已在真实板自然形成 `artifact_kind=final`、`last_phase=final`、`current_command=null`，`DEADLINE_LIVE_VALIDATED=true`，因此 deadline blocker 已 live 关闭，不得再次消费。
3. 上一轮唯一 start 因多层 shell quoting 损坏 JSON，形成新 blocker `phase_a_start_json_transport_corrupted_before_remote_handler`，只消费 `1/2`；remote command invocation=`0`，却因 endpoint attempt 已发生而禁止重试。本轮用冻结 request + 本地 `jq -c` + stdin transport 直接验证该根因，不再使用 inline JSON。
4. O5 约 `85%` 为最低 Objective，但 provider/runtime blocker 已消费 `2/2`，本轮必须暂停 O5，不得第三次打开 tunnel/provider/preflight/wrapper/readback。O6/O7 各约 `93%`，O1 约 `94%`；fresh motion authorization 与独立 transport 修复入口使本轮合法切换到 O3 readiness supporting + O1/O6/O7 bounded route evidence。

## 本轮核心抓手

由一个 `robot-software-engineer` 单线集成，因为冻结文件、Upper API、O10 helper、live endpoint、raw transport、stop/cleanup 与计数强耦合：

1. Phase 0 冻结 identity/request，运行本地 parse/hash/count 与离线回归；复核 target HEAD/content SHA，远端 SHA、py_compile、service/health、initial stopped/no-motion 全 clean 后才可继续。
2. Phase A 只允许 start/proof/latest 各一次；start/proof body 均从同一 `frozen_requests.json` 由 `jq -c` 取出，本地断言后经 stdin pipe 送往远端 curl。所有 request/response raw 与 transport metadata 先原样持久化，再 parse/判定。
3. 只有同一 current final artifact 对 map/amcl/planner/controller、current pose/persisted pose、dynamic TF、planner-only path 与 obstacle clear 全部明确给出 `READINESS_GO=true`，才进入 Phase B。
4. Phase A artifact 冻结后，`robot-algorithm-engineer` 才做 frozen read-only readiness review；不得 SSH、live、retry 或发控制命令。
5. Phase B 由同一个 Robot Software owner 串行执行 pre-base-stop exactly once、exactly-one bounded `NavigateToPose`、terminal readback、post-base-stop at most once、owned cleanup exactly once；任何失败/timeout/unknown 都不 retry。
6. 只有 Phase B execute=`1` 且 artifact 已冻结，才顺序派 `robot-hardware-engineer` 做 `T=1001`/HIL/operator 只读复核。Full-stack 不派。

## 硬停止与 no-retry 合同

- Phase 0 任一 SHA/compile/service/health/initial-safety gate 失败：Phase A start/proof/latest=`0/0/0`，不消费授权。
- frozen request parse、hash、数量或 identity 断言失败：禁止 transport，Phase A=`0`；允许本地修复冻结文件后重新断言，因为尚未触发授权消费点。
- Phase A start attempt 发出后授权立即消费。start semantic、proof natural final、current identity 或任一 readiness field missing/unknown/stale/conflict/false：`READINESS_GO=false`，执行 owned stop exactly once，封存且 no retry。
- Phase A NO-GO 时 Phase B pre-stop/execute/post-stop=`0/0/0`；不得创建 route-success、HIL-success 或 delivery-success artifact。
- Phase B pre-base-stop 失败：execute=`0`、post-base-stop=`0`，owned cleanup 后封存。
- execute 一旦发出，不论 success/fail/timeout/unknown，count=`1` 且永不重试；随后最多一次 post-base-stop、只读 terminal/status/feedback、一次 owned Nav2 cleanup。
- 只清理由本轮 owner 创建并由 PID/process-group/manifest 归属证明的资源；禁止 broad kill、禁止碰既有非 owned runtime。cleanup residual 非零时按安全事件 blocked 收口。
- 禁止 `/initialpose`、manual、free-roam、direct `/cmd_vel`、UART 直控、inline JSON、第二 goal、第二 route、旧授权/旧 nested success 混用。

## 预期证据、信用边界与 KR

- Phase 0 与 stdin transport clean 只证明部署/传输，不等于 readiness。
- Phase A NO-GO 只形成 current diagnostic artifact；route execution、user action、HIL、delivery、safe-to-control 均为 false。
- `READINESS_GO=true` 只允许进入 Phase B，不等于 route success。
- clean pre-stop + execute handler 接受形成 mission attempt candidate；same-lineage terminal success 才形成 route success candidate。
- route success + same-window pre/post stop + valid `T=1001` motion/post-stop + operator outcome 才形成 HIL/operator candidate。
- `delivery_success=false` 与 `safe_to_control=false` 默认保持；Engineer 不得自行抬分或归档 KR。
- O5/O6/O7/O1 百分比在 planning 阶段全部 flat；KR `不归档`，历史完成区无新增。

## Sprint 留档顺序

本 Epic 当前仅按顺序创建 `pre_start.md -> prd.md -> tech-plan.md`。Engineer 实际执行后才创建 `tech-done.md`；Product acceptance 后再创建 `side2side_check.md`、`final.md`，并基于冻结证据更新 `OKR.md`、`docs/process/okr_progress_log.md` 与必要产品/导航/硬件文档。本 planning 禁止预建后续 closeout 文档、commit 或 push。
