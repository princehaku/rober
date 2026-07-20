# O3/O1 Live Deadline Fix Validation + Bounded Route - Pre Start

## Sprint metadata

- `sprint_type: epic`
- 状态：`planning_complete_pending_engineer_dispatch`
- Product owner：`product-okr-owner`
- 唯一 live owner / 主责集成：`robot-software-engineer`
- 条件专业验收：`robot-algorithm-engineer`、`robot-hardware-engineer`
- Full-stack：默认不派；仅在产生 current route terminal 且既有 receipt contract 暴露真实 bug 时条件派发
- 上位机：`root@192.168.1.11:37878`
- 部署目标 HEAD：`85ba7308785aa3c4033180a097e3d388358a97de`
- 目标：真实板 exactly-once 验证 absolute monotonic deadline fix；仅 `READINESS_GO=true` 后执行一次受限路线
- planning proof boundary：`planning_only_no_live_no_control_no_okr_credit`

## 用户价值与产品北极星

用户需要的不是第三份 readiness 包装，而是把已离线通过的 parent/helper absolute monotonic deadline 修复部署到真实上位机，在 fresh operator 授权下只开一个 current strict-no-motion 窗口，得到自然 final。只有定位、TF、planner/controller、path、障碍和 stop gate 同时全绿，才执行一次可停止、不可重试、可归因的 bounded `NavigateToPose`。

本轮北极星是单一 lineage：`target HEAD -> remote SHA hard gate -> exactly-once Phase A natural final -> READINESS_GO decision -> conditional pre-stop -> exactly-one bounded route -> post-stop -> owned cleanup -> conditional T=1001/HIL review`。任何 NO-GO 或失败也必须封存为 current artifact，不能用重跑制造成功。

## Fresh authorization gate change

CEO 在 2026-07-20 21:24 再次明确：上位机为 `ssh root@192.168.1.11 -p 37878`，小车运动已授权，有 operator 看护、路线清空和物理位置限制。该消息相对旧 `ceo_20260720_2025_operator_watch_route_clear_physical_limit_v1` 是新的 fresh authorization，不复用上一 sprint 已消费窗口。

本轮冻结新 identity：

- `authorization_ref=ceo_20260720_2124_operator_watch_route_clear_physical_limit_v2`
- `run_id=run_o3_o1_current_readiness_route_20260720_2124_01`
- `task_id=task_o3_28_pose_fixed_route_consumer_20260713_0402`
- `route_intent_id=route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path`
- `action_id=action_o3_o1_bounded_nav_20260720_2124_01`
- fixed goal：`map (0.8, 0.25, yaw=0)`

Fresh authorization 只改变“允许在硬门后进行一次受限动作”的准入，不证明 current pose、persisted pose、dynamic TF、planner/controller、path、obstacle clear、pre-stop、route success、`T=1001`、HIL、delivery 或 `safe_to_control`。

## 上轮事实与 blocker 去重

- `sprints/2026.07.20_20-25_o3_o1_current_readiness_bounded_route/` 的唯一 Phase A 在 parent `80395ms` 被截断，只得到 partial/interrupted，`READINESS_GO=false`；Phase B pre-stop/goal/post-stop=`0/0/0`，owned cleanup residual=`0`，无物理运动。
- 精确根因已定位为 `parent_helper_monotonic_clock_origin_mismatch`：parent 与 helper 起点相差约 `3631ms`，旧 4 秒 final reserve 实际只剩约 `0.764s`。
- HEAD `85ba7308785aa3c4033180a097e3d388358a97de` 已实现 parent 在 argv/Popen 前生产 absolute deadline、helper 消费同一 monotonic deadline、`communicate()` 只使用 remaining，并通过离线 Upper `119`、O10 `170`、集成 `289` 测试；它仍缺真实板 natural-final 验证。
- O5 约 `85%` 最低，但 provider/runtime 同根因 blocker 已消费 `2/2`，本轮继续暂停，不得第三次打开 tunnel/provider/preflight/wrapper/readback。
- O1 约 `94%`、O6/O7 各约 `93%` 均保持 flat；O3 仅作为 current readiness supporting。planning、部署、NO-GO 或单独 path success 都不自动获得 OKR credit。

## 本轮核心抓手

由同一个 `robot-software-engineer` 严格串行完成：

1. Phase 0 冻结新 identity/request，确认本地 HEAD 与目标 commit，运行离线回归，将目标 commit 的两份脚本部署到上位机，重启 Upper API；远端 commit/部署 manifest、脚本 SHA、py_compile、service health、初始 stopped/no-existing-motion 全部通过后才允许 Phase A。
2. Phase A exactly once 执行 strict-no-motion start/proof/latest，要求在绝对 deadline 内自然形成 current final，并计算 `READINESS_GO`。
3. Phase A frozen 后才派 `robot-algorithm-engineer` 做只读 readiness/algorithm review；它不得自行 SSH、live、start/proof/stop/goal 或 retry。
4. `READINESS_GO=true` 时仍由原 `robot-software-engineer` 继续一次 pre-base-stop。pre-stop fail 立即封存、owned cleanup，goal invocation=`0`，不得重试。
5. 只有 pre-stop clean 才 exactly once 执行 fixed goal，随后最多一次 post-stop、只读 terminal/feedback/status、一次 owned Nav2 cleanup。无论 terminal success/fail/timeout/unknown 均不得第二次 goal。
6. Phase B artifacts 完全 frozen 后才派 `robot-hardware-engineer` 做同窗 `T=1001`/HIL 只读验收。Full-stack 默认不派。

## 硬停止与 no-retry 合同

- Phase 0 的目标 commit、remote SHA、remote py_compile、service restart/health 任一不 clean：Phase A invocation=`0`，先修复部署或健康问题；未恢复硬门不得继续。
- Phase A start/proof/latest、natural final、current pose/persisted pose、dynamic TF、planner/controller/path、obstacle、existing motion 或 artifact parse 任一 missing/unknown/stale/conflict/timeout：`READINESS_GO=false`，执行一次 owned cleanup 后封存；不得同窗修复后重跑。
- `READINESS_GO=true` 但 pre-base-stop semantic/readback 任一失败：goal=`0`，owned cleanup 后封存；不得第二次 pre-stop 或 retry。
- execute 一旦调用，不论 success/fail/timeout/unknown，exactly once；最多一次 post-base-stop，再做只读 readback 和 owned cleanup。
- 禁止 `/initialpose`、manual、free-roam、direct `/cmd_vel`、UART 直控、第二 goal、第二路线、28-pose 扩展执行、unattended motion 或用另一 owner 接管 live。
- 任何现场 bug 先由对应 Engineer 在自己的文件范围修复并完成离线验证；本授权窗口不因修复重开，下一次 live 必须重新取得 fresh authorization。

## Owner 与交接顺序

- `robot-software-engineer`：唯一 live owner；Phase 0/A/B、raw/manifest、stop/cleanup、范围内最小修复和 `tech-done.md` 汇总。
- `robot-algorithm-engineer`：仅 Phase A frozen 后只读审核 absolute deadline、current/final、pose/TF、planner/controller/path 与 `READINESS_GO`；不同意时直接 NO-GO，不自行重跑。
- `robot-hardware-engineer`：仅 Phase B frozen 且 execute=`1` 后，按 vendor source 只读验收 same-window pre/post stop 与 `T=1001` 的 `L/R/r/p/y/v`；不发任何硬件或控制命令。
- `full-stack-software-engineer`：默认 `not_dispatched`；只有 current route terminal 已冻结且既有 receipt contract 出现可复现真实 bug 才最小修复，不允许补造 receipt/mock success。

## 预期证据与信用边界

- Phase 0 通过：只证明部署一致性，不证明 readiness。
- Phase A NO-GO：只接受 current safe diagnostic delta；route/user-action/HIL/delivery/safe 仍 false。
- Phase A GO + pre-stop clean + execute accepted：只形成 mission attempt / user-action candidate，不等于 route success。
- current terminal success + 同 lineage latest：形成 route success candidate。
- route success + same-window pre/post stop + valid `T=1001` motion/post-stop + operator outcome：形成 current HIL/operator acceptance candidate。
- `delivery_success=false` 本轮固定；`safe_to_control` 不因单次成功自动变 true。所有百分比与 KR 归档只在 Product closeout 基于冻结证据决定。

## Sprint 留档顺序

本 Epic 只先创建 `pre_start.md -> prd.md -> tech-plan.md`。Engineer 实际执行后才能创建 `tech-done.md`；Product acceptance 后才能创建 `side2side_check.md`、`final.md` 并决定是否更新 `OKR.md` 与 `docs/process/okr_progress_log.md`。本 planning 阶段不得预生成 closeout 文档。
