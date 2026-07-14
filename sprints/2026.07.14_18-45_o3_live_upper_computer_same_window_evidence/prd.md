# PRD - O3 Live Upper-Computer Same-Window Evidence

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_18-45_o3_live_upper_computer_same_window_evidence/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-algorithm-engineer`
- Target: `root@192.168.1.11:37878`
- Product mode: fresh live evidence, strict `no-motion`

## 问题定义

项目已经有 13:38 same-window readiness precheck、15:38 live relay HTTP smoke 和 16:40
headless browser smoke，但这些产物都没有回答当前真实上位机是否同时具备 fresh `/scan`、
fresh `/amcl_pose`、active map/AMCL lifecycle、dynamic `map_to_odom` 与 planner-only path。
继续增加 wrapper、browser panel 或 CLI export 不能缩短现场导航闭环。

CEO 已给出当前真实上位机 SSH 入口。本轮产品需求是生成一份带当前窗口 provenance 的 raw
JSON evidence，成功时记录真实 no-motion path；失败时把 blocker 收敛到 SSH、ROS source、
radar lifecycle、map/AMCL lifecycle、sensor sample、localization TF 或 planner action 中的精确
一层。无论成功或失败，都必须能被下一位 owner 直接复验。

## 用户故事

作为现场 autonomous/navigation owner，我希望执行一次有界、不可运动的真实板采集，获得：

1. 这次证据来自 `192.168.1.11:37878`、哪台 remote hostname、何时开始和结束、运行了哪个
   helper SHA、SSH/helper 的 exit code；
2. `/scan` 和 `/amcl_pose` 是否在本窗口观察到 fresh sample；
3. `/map_server` 和 `/amcl` 是否 active，地图 YAML/OccupancyGrid 是否可读；
4. `map_to_odom` 是否由 dynamic `/tf` source 观察到，而不是只凭 static 或历史 readback；
5. `ComputePathToPose` 是否实际 attempted，是否生成非空 path，以及 `path_point_count`；
6. 如果任一步失败，得到当前 run 的 exact root cause 和下一条最小复验命令；
7. 全程确认没有机器人运动、底盘 UART 或 route execution 副作用。

## 用户价值和北极星映射

该证据把“路线材料已准备”推进成“真实板当前 localization/planner 是否工作”的可验证事实，
为后续受控 route execution、delivery result 和 operator acceptance 去除一层不确定性。它映射
O3 autonomous capability lane，并支撑 O1 当前约 `94%` 的定位/Nav2 缺口；不把 planner-only
成功误记为 delivery 或 HIL。

## 范围内

- 有界 SSH identity/time/source preflight。
- 只读 `GET /api/radar/status`，确认是否可复用 existing LiDAR lifecycle；`150000` 必须来自
  current readback，不得凭历史或 vendor 默认猜测。
- 复用 `onboard/scripts/o10_amcl_nav2_runtime_proof.py`。
- 只读 topic、endpoint、map、lifecycle、TF、AMCL 检查。
- 严格 no-motion localization 初始化和 planner-only `ComputePathToPose`。
- fresh remote raw JSON、local capture envelope、stdout/stderr/exit metadata 和 `tech-done.md`。
- 仅当 fresh live attempt 证明 helper 有明确 bug 时，允许修 helper、targeted tests 和相关导航
  文档，然后在同一 owner 下复验。

## 范围外

- `/cmd_vel`、`/api/base/manual`、`NavigateToPose`、controller/BT、fixed-route movement。
- WAVE ROVER UART、`/dev/ttyS5`、任何非零底盘命令或硬件配置修改。
- current live HIL、safe-to-control、delivery/operator acceptance、production cloud claim。
- O5/O6/O7 relay、browser、CLI export、readback、handoff、intake 或 readiness wrapper。
- 为了让结果变绿而修改地图、AMCL 参数、LiDAR baudrate/port 或 lifecycle holder。

## Artifact Contract

主产物至少包括：

- `artifacts/algorithm/live_upper_computer_same_window_evidence.remote.raw.json`
  - 从真实板拉回的 helper 原始输出；不得用历史 artifact 覆盖。
- `artifacts/algorithm/live_upper_computer_same_window_evidence.raw.json`
  - current-window capture envelope，记录 target host/port、remote hostname、开始/结束 UTC 与板端
    时间、local/remote helper SHA、SSH/helper exit code、remote raw path 和嵌入/引用的 proof。
- `artifacts/algorithm/live_upper_computer_same_window_evidence.stdout.log`
- `artifacts/algorithm/live_upper_computer_same_window_evidence.stderr.log`
- `tech-done.md`

Capture envelope 必须明确：

- `schema=trashbot.o3.live_upper_computer_same_window_evidence.v1`
- `target_host=192.168.1.11`
- `target_port=37878`
- `fresh_live_attempted=true`
- `historic_artifact_used_as_current_live_proof=false`
- `proof_boundary=robot_runtime_o3_strict_no_motion_localization_planner_evidence_only`
- current timestamps、remote hostname、helper SHA 和 exit codes
- `/scan`、`/amcl_pose`、dynamic `map_to_odom`、map/AMCL lifecycle、path generation 的 observed
  值，或对应 current-run exact root cause
- 全部固定 false safety fields

## 优先级

P0：保持 no-motion 红线和 current-run provenance，不产生任何控制副作用。

P1：在同一 fresh raw evidence 中拿到 `/scan`、`/amcl_pose`、dynamic `map_to_odom`、map/AMCL
lifecycle 和 `ComputePathToPose` 结果。

P2：若失败，保留 partial/final raw artifact、exit code、stderr 和最窄 root cause；不得只返回
“超时”或“未准备”。

P3：只有确认 helper bug 后才修 helper/tests/docs；ROS runtime、地图、传感器或 SSH 环境问题
不得伪装成 helper bug。

## Product Acceptance

### 成功路径

以下字段必须来自同一次 current-window board run：

- `/scan` observed 且 sample/freshness 可判断；
- `/amcl_pose` observed 且 frame/timestamp 可判断；
- `map_server_active=true`、`amcl_active=true`；
- dynamic `map_to_odom` source observed；
- `path_generation_attempted=true`、`path_generated=true`、`path_point_count>0`；
- boundary 明确是 planner-only `ComputePathToPose`；
- 所有 control/delivery/HIL safety fields 为 false。

### Fail-closed 路径

允许 SSH/helper exit `2`、`124` 或 `255`，但必须仍生成 fresh capture envelope，并满足：

- target、timestamp、attempted command boundary 和原始 exit/stderr 已记录；
- 如果 remote raw JSON 已产生，必须拉回且 JSON 可解析；
- root cause 指向精确层，例如 `ssh_connect_timeout`、`radar_status_current_readback_mismatch`、
  `map_server_lifecycle_not_active`、`amcl_pose_sample_not_observed`、
  `map_to_odom_dynamic_source_missing` 或 `compute_path_to_pose_result_not_received`；
- 给出下一条最小 no-motion 复验命令；
- 不接受只写 `blocked_missing_same_window_live_evidence` 或只消费 13:38 readiness artifact。

### 拒绝条件

- 任何真实运动、`/cmd_vel`、`/api/base/manual`、`NavigateToPose`、WAVE ROVER UART 或非零
  底盘命令痕迹；
- 把 static/history `map_to_odom` 当作 current dynamic source；
- 把旧 21/28 pose artifact 当本轮 fresh raw JSON；
- 没有 target host/port、timestamp、exit code 或 helper SHA；
- 把 planner-only path 宣称为 route execution、delivery、HIL 或 safe-to-control；
- 只新增 readiness/readback/handoff/browser/CLI wrapper，没有真实 SSH attempt。

## OKR 和 KR 收口规则

- fresh planner-only 成功可作为 O3/O1 current live evidence，由 Product 在 closeout 时判断是否
  仅更新证据描述或产生保守增量；不得自动上调百分比。
- exact current-run blocker 只允许证明本轮有效诊断，不得为已有 support-only blocker重复计分。
- 没有 route execution、delivery/operator acceptance、current live HIL、safe-to-control 或 O5
  success-class production evidence，不归档 KR。
