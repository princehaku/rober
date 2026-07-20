# PRD

## 元数据与产品决定

- `sprint_type: epic`
- 状态：`planning_complete_pending_engineer_dispatch`
- 用户价值：让机器人在真正拥有当前 scan、地图、定位、TF、planner/controller、路径与净空证据后，才尝试一次受控路线任务。
- 产品北极星：普通用户可获得可验证、可靠、异常时可停止的垃圾送达。
- 方向判断：O5 `暂停`；O3/O1 当前 mission lane `继续并调整抓手`，从 readiness 复述切到 sensor/localization/Nav2 能力修复与一次有界任务。

## OKR 映射、KR 与历史区

- O5 约 `85%` 且 provider/runtime blocker=`2/2`，继续暂停，不得第三轮消费同一根因。
- O6/O7 各约 `93%`，本轮只在真实 route/terminal/operator 材料形成后才可能获得 supporting evidence。
- O1 约 `94%`，本轮直接补 current live base stop、`T=1001`、HIL 与 route execution 缺口，但 planning 阶段 flat。
- O3 作为 mission supporting lane，直接补 current map/localization/TF/path/readiness 与 bounded route；未形成 Phase B terminal 前不计 mission success。
- KR 当前 `不归档`。历史区无新增；上一 sprint 的 transport closeout 继续留在其 `final.md`，不得搬成 route/HIL 完成记录。

## 问题定义

上一请求把 `base_enabled=false`、`lidar_enabled=false`、`reuse_existing_scan=true`、`managed_runtime_opt_in=false`、`initialpose_opt_in=false` 同时冻结，却要求依赖当前传感器与受管 Nav2 的九门全绿。现场结果如实显示 `/scan_no_publisher`、canonical map 不 clean、pose 不新鲜、persisted pose 未消费、dynamic TF 缺失、planner/controller inactive、path 未尝试、obstacle-clear 未证明。

Transport 与 deadline 已关闭，因此本轮禁止再做 wrapper/transport/readiness-only proof。产品需要的是可部署的 `sensor-enabled/base-disabled` lifecycle 和定位/readiness 修复，然后在新授权下只开一个 live window。

## 功能需求

### R1：安全 sensor lifecycle

- `/api/nav2/start` 必须接受并严格校验 `strict_no_motion=true`、`base_enabled=false`、`lidar_enabled=true`、`reuse_existing_scan=false`、有限 `timeout_s`。
- O11 必须独占启动本轮 LiDAR publisher、canonical map 与 Nav2 stack；已有非 owned `/scan` publisher、LiDAR holder、Nav2 owner 或 PID 冲突时 fail closed，不抢占、不 broad kill。
- lifecycle readback 必须证明 `base_enabled=false`、`lidar_enabled=true`、base UART new-open=`0`、LiDAR serial owned new-open=`1`、`physical_motion=false`。
- start 只建 runtime，不发送 goal、manual、free-roam、direct `/cmd_vel`、`T=1/T=11/T=13` 或其他底盘运动命令。

### R2：current `/scan` 与 canonical map

- `/scan` 必须有本轮 owned publisher，LaserScan header timestamp 可解析且在规定 freshness window 内；topic type、frame、range 数组和有效有限采样数必须通过。
- canonical map 固定为 `/root/rober/onboard/runtime/maps/trashbot_map.yaml`；记录 YAML 与 image SHA-256、resolution/origin/width/height，并将 current `/map` OccupancyGrid 与 canonical 内容核对。
- 仅 `map_server active`、历史 map、旧 hash 或 `/map` topic 可见都不足以判绿。

### R3：current/persisted pose 与 dynamic TF

- O10 必须记录 current `/amcl_pose` 的 ROS stamp、receipt time、age、frame 与 covariance，并按同一 monotonic/wall-clock 基准给出 freshness。
- persisted pose 必须有明确 source、timestamp、canonical map identity，并在本次 runtime 中被 live consume；pre-publish sample、post-publish sample与最终判定不得互相冲突。
- 如需要 `/initialpose`，只能使用 canonical map 可复算的 free-cell pose，Phase A 内最多一次、no retry，并记录 attempt/receipt；不得人工临时改坐标。
- `map->odom` 必须来自 current dynamic TF、timestamp fresh 且唯一归因 AMCL；`map->base_link` 必须在同一时点可解析。static/fake `map->odom`、历史 TF 或不同 run 的 chain 不得判绿。

### R4：planner/controller 与 planner-only path

- `map_server`、`amcl`、`planner_server`、`controller_server` 四个 lifecycle 都必须 active；planner/controller 的 service/action readiness 必须可调用。
- fixed goal 沿用 `map (0.8, 0.25, yaw=0)`、task `task_o3_28_pose_fixed_route_consumer_20260713_0402` 与既有 route intent；禁止现场改 goal。
- Phase A 只能请求 planner-only path，不发送 `NavigateToPose` 或 FollowPath；必须记录 requested/attempted/succeeded/generated、point_count、frame、start/goal 与 path freshness。

### R5：same-current obstacle-clear

- obstacle-clear 必须使用生成该 natural-final 的同一 current scan，记录 scan stamp、receipt age、有效点数、最小距离、阈值与结论。
- stale scan、历史 `lidar_min_distance_m=0.035...`、空数组、NaN/Inf 全部 fail closed。
- 路线清空/operator 口头条件是授权上下文，不替代当前传感器净空门。

### R6：exactly-once Phase A 与 Phase B

- fresh authorization 固定为 `ceo_20260721_0128_operator_watch_route_clear_physical_limit_v5`；start attempt 发出即消费。
- Phase A start/proof/latest/owned-stop=`1/1/1/1`，所有 retry=`0`，只接受 same-current natural-final。
- 九门 map/AMCL/planner/controller/current pose/persisted pose/dynamic TF/planner-only path/obstacle-clear 全绿才写 `READINESS_GO=true`。
- Phase B 仅在 GO 后执行 pre-base-stop -> exactly-once bounded goal -> post-base-stop；Phase B 前无运动，goal 不论结果均 no retry。
- Robot Software 负责 live orchestration。Hardware 仅 execute=`1` 后从本 run artifact 复核 current `T=1001`、轮速、停止和 HIL，不补发控制。

### R7：owned cleanup 与证据边界

- Phase A 不论 GO/NO-GO 都执行一次 O11 owned stop；Phase B 结束后清理本轮 owned runtime。
- cleanup 必须证明 lifecycle stopped、PID null、PID file=`0`、owned residual=`0`、broad kill=false；否则状态为安全事件，不得写 clean。
- `route_execution_success`、`hil_pass`、`delivery_success`、`safe_to_control` 默认 false；只有同 authorization/run/action/task/route 的直接证据逐项满足才可改变。

## 非目标

- 不修 O5 provider/runtime，不新增手机、Web、云或 O6/O7 surface。
- 不做第二个 readiness 窗口、第二 goal、retry、free-roam、manual、direct UART 或 unattended motion。
- 不修改 WAVE ROVER firmware、串口默认值、电气或机械配置。
- 不把 software proof、部署成功、九门 GO 或 goal accepted 单独称为 delivery success。

## 优先级与验收口径

| 优先级 | 验收项 | 必须满足 |
|---|---|---|
| P0 | 安全合同 | base disabled、sensor enabled、Phase B 前无运动、owned cleanup 可证 |
| P0 | current readiness | 九门同一 natural-final 全绿，任一 missing/stale/conflict 即 NO-GO |
| P0 | exactly-once | Phase A=`1/1/1/1`、retry=0；Phase B GO 才 `1/1/1`，goal retry=0 |
| P1 | bounded mission | 同 lineage terminal 与 operator evidence；失败也必须 post-stop/cleanup |
| P1 | T=1001/HIL | execute=1 后顺序读取 vendor，再核对 current L/R/姿态/电压与停止证据 |
| P1 | 工程质量 | targeted/full/Docker 通过；技术注释全中文且比例严格 `>20%`；相关 docs 同步 |

## 风险与待补证据

- base disabled 时现场可能缺少可信 `odom->base_link`；不得用 fake/static 结果冒充 current localization，必须由 Algorithm 证明 chain 来源，不能证明则 NO-GO。
- LiDAR serial 可能已有 holder 或 `/scan` 可能多 publisher；必须 fail closed，禁止抢占。
- canonical map 与现场环境可能漂移；hash 相同也不等于障碍清空，仍需 same-current scan。
- `/initialpose` 即使 no-motion 也可能造成定位跳变；必须 canonical、至多一次且 operator 看护。
- Phase B 开启底盘后，Phase A 的传感器/TF freshness 可能漂移；goal 前必须做 same-current admission readback，不能重跑整套 Phase A。
- 没有真实 terminal、current `T=1001`、post-stop 与 operator acceptance 前，route/HIL/delivery/safe 均未完成。

## 后续 Sprint 文档

当前完成 `pre_start.md`、`prd.md`、`tech-plan.md`。Engineer 完成后创建 `tech-done.md`；Product 再创建 `side2side_check.md`、`final.md`，并依据实证更新 `OKR.md`、`docs/process/okr_progress_log.md`。若无实证，百分比保持 flat、KR 不归档。
