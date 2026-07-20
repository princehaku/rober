# O3/O1 Nav2 Readiness Repair + Bounded Mission - Pre Start

## Sprint metadata

- `sprint_type: epic`
- 启动时间：`2026-07-21 01:28 CST`
- 状态：`planning_complete_pending_engineer_dispatch`
- Product owner：`product-okr-owner`
- 主责与最终集成：`robot-software-engineer`
- 独立实现：`robot-algorithm-engineer`（仅限不重叠的 O10 pose/TF/path gate 文件）
- 条件式复核：`rober-hardware-engineer`（仅 Phase B execute=`1` 后）
- Full-stack：`not_dispatched`
- SSH target：`root@192.168.1.11:37878`
- fresh authorization：`ceo_20260721_0128_operator_watch_route_clear_physical_limit_v5`
- run：`run_o3_o1_nav2_readiness_repair_bounded_mission_20260721_0128_01`
- action：`action_o3_o1_bounded_mission_20260721_0128_01`
- planning proof boundary：`planning_only_no_ssh_no_live_no_control_no_okr_credit`

## 用户价值与产品北极星

北极星仍是普通用户把垃圾交给机器人后，机器人能沿固定路线完成可验证、可停止的送达。本轮直接修复发车前所需的真实传感器、定位和 Nav2 lifecycle 能力，而不是继续制造 wrapper、transport 或 readiness-only 证明。

唯一有效链路为：`sensor-enabled/base-disabled lifecycle -> current /scan + canonical map -> current/persisted pose + dynamic TF -> planner/controller active -> planner-only path + same-current obstacle-clear -> exactly-once Phase A -> 九门全绿 -> exactly-once Phase B bounded mission -> current T=1001/HIL/operator evidence -> owned cleanup`。九门未全绿就必须 NO-GO，不能用 HTTP `200`、旧 nested success、历史 scan/pose 或本地 Mock 替代。

## 事实基线与方向去重

- O5 约 `85%`，provider/runtime blocker 已消费 `2/2`，继续暂停；不得再开 provider、preflight、tunnel、readback 或 support-only wrapper。
- O6/O7 各约 `93%`，O1 约 `94%`；O3 作为当前 mission supporting lane。本 planning 不调百分比，KR `不归档`，历史区无新增。
- 上一 Epic 已关闭 absolute deadline 与 frozen stdin transport；Phase A start/proof/latest/owned-stop=`1/1/1/1`、retry=`0`，但 `READINESS_GO=false`、Phase B=`0/0/0`、current `T=1001=0`。
- 上一请求同时设置 `base_enabled=false`、`lidar_enabled=false`、`reuse_existing_scan=true`、`managed_runtime_opt_in=false`、`initialpose_opt_in=false`，却要求 current `/scan`、persisted pose、dynamic TF、planner/controller、planner-only path 和 obstacle-clear 全绿；该输入合同自身不可满足，禁止原样复用。
- 本轮必须实现并部署 `sensor-enabled/base-disabled` 安全 lifecycle：Phase A 允许 O11 独占 LiDAR `/scan`，底盘始终禁用且 base UART new-open=`0`；Phase B 前不发送 goal、`/cmd_vel`、manual 或 WAVE ROVER motion command。

## Fresh authorization 与消费点

CEO 本轮提供独立 fresh authorization `ceo_20260721_0128_operator_watch_route_clear_physical_limit_v5`，条件为 operator 看护、路线清空、物理限制，目标 `root@192.168.1.11:37878`。本 planning 不消费授权。

授权只在修复、离线回归、Docker build、部署 SHA、远端 py_compile/service/health、初始 stopped/no-owned-residual 全部通过后，由 Robot Software 发出唯一 Phase A `/api/nav2/start` attempt 时消费。该 attempt 无论 transport、HTTP、parse 或 semantic 成败都不可 retry。不得混用 v4 或更早授权、raw、terminal、pose、scan、TF 或 path。

## 本轮核心抓手与责任边界

1. `robot-software-engineer` 主责 Upper API 与 O11：把 strict no-motion start 合同扩展为明确的 `lidar_enabled=true`、`reuse_existing_scan=false`、`base_enabled=false` sensor-owned 模式；启动 canonical map + LiDAR + Nav2，证明 base UART 未打开；完成集成测试、部署与唯一 live orchestration。
2. `robot-algorithm-engineer` 在不重叠文件中主责 O10：按 timestamp/freshness 审计 current `/scan`、canonical map、current/persisted pose、dynamic `map->odom` 与可解析 `map->base_link`、planner/controller lifecycle、fixed-goal planner-only path 和 same-current obstacle-clear。不得把 static/fake TF、stale scan 或历史 pose 判绿。
3. Robot 与 Algorithm 的源码、测试、文档、artifact 目录必须互不重叠；`tech-done.md` 只由 Robot 集成 owner 汇总。若实施发现共享文件不可避免，立即改为 Robot 单主责，Algorithm 只读 frozen review，不并行写共享文件。
4. `rober-hardware-engineer` 仅在 Phase B `execute_attempt_count=1` 后启动；必须依次阅读 `docs/vendor/VENDOR_INDEX.md`、`json_cmd.h`、`uart_ctrl.h`、`ugv_advance.h`、`ugv_rpi/base_ctrl.py`，再对本 run 的 `T=1001`、轮速/停止和 HIL 证据做复核。不得借历史反馈，也不得补发 goal 或运动命令。
5. Full-stack 不派发；本轮不新增手机、Web、云或用户触点 surface。

## exactly-once、no-retry 与 Phase B 准入

- Phase A 固定为 start/proof/latest/owned-stop=`1/1/1/1`、retry=`0`；proof 内 `/initialpose` 如启用也必须 canonical、最多一次、no retry，并保持 no-motion。
- 九门为 map、AMCL、planner、controller、current pose、persisted pose、dynamic TF、planner-only path、obstacle-clear；每门必须来自同一 current natural-final，字段 missing/unknown/stale/conflict/false 任一即 `READINESS_GO=false`。
- Phase A start 后必须出现 current `/scan` publisher 与新鲜 LaserScan；canonical map 必须绑定本轮 YAML/image hash 与 current `/map` 内容，不能只看 map_server active。
- Phase B 只有 `READINESS_GO=true` 才允许 pre-base-stop -> exactly-one bounded goal -> post-base-stop；goal attempt 一旦发出，不论 success/fail/timeout/unknown 都不得 retry。
- Phase A 和 Phase B 都只清理由本轮 O11 PID/process-group/manifest 明确 owned 的资源；禁止 broad kill。NO-GO 必须 owned cleanup 后达到 stopped、PID null、residual=`0`。
- Phase B 前 physical motion=false；任何意外 `/cmd_vel`、manual、free-roam、direct UART、base UART new-open 或非 owned 进程都立即停止并按安全事件收口。

## 证据、OKR 与历史归档边界

- 能力修复、离线测试和部署只证明 readiness prerequisites，不等于 mission attempt。
- Phase A 九门全绿只解锁 Phase B，不等于 route、HIL、delivery 或 safe-to-control 成功。
- Phase B goal handler 的同 lineage attempt 才是 mission attempt candidate；同 run terminal、current `T=1001`、post-stop、operator 结果必须分别核证。
- `delivery_success=false`、`hil_pass=false`、`safe_to_control=false` 默认保持，只有本轮直接证据逐项满足才允许 Product 在收口阶段重新判断。
- 当前没有完成、取消、替换或过期 KR；历史记录位置暂无新增。证据源为上一 sprint `tech-done.md`、`side2side_check.md`、`final.md`、Robot `readiness_decision.json` 与 Algorithm `readiness_review.json`；剩余风险是 sensor/定位/Nav2 九门及 Phase B/HIL 均未闭合。

## Sprint 留档顺序

本 Epic 当前只创建 `pre_start.md -> prd.md -> tech-plan.md`。Engineer 实际完成后才创建 `tech-done.md`，Product 验收后再创建 `side2side_check.md`、`final.md`，并更新 `OKR.md`、`docs/process/okr_progress_log.md` 与受影响的 `docs/`。本 planning 不预建收口文档、不 SSH、不执行 live/control、不改 `OKR.md`。
