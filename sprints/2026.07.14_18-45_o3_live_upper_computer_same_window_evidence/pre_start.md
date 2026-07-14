# Pre Start - O3 Live Upper-Computer Same-Window Evidence

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_18-45_o3_live_upper_computer_same_window_evidence/`
- Start window: 2026-07-14 18:45 Asia/Shanghai
- Product owner: `product-okr-owner`
- Implementation and integration owner: `robot-algorithm-engineer`
- Planning status: ready for implementation dispatch
- Execution boundary: strict `no-motion`

## 必读事实和上轮未完成项

本轮计划已核对 `AGENTS.md`、`OKR.md`、自动化记忆、以下三轮 closeout，以及现有
`onboard/scripts/o10_amcl_nav2_runtime_proof.py`、targeted tests 和导航文档：

- `2026.07.14_13-38_o3_same_window_route_readiness_precheck`：只形成
  `blocked_missing_same_window_live_evidence` readiness checklist，缺 fresh 同窗口 `/scan`、
  `/amcl_pose`、dynamic `map_to_odom` 和 planner result。
- `2026.07.14_15-38_o7_live_relay_browser_smoke_artifact`：只证明本机 live loopback HTTP。
- `2026.07.14_16-40_o7_live_relay_headless_browser_smoke`：已推进到真实 headless Chrome，
  但仍是 support-only，O5/O7 百分比保持 flat。
- `2026.07.13_03-00_o3_live_full_structured_path_capture` 和
  `2026.07.12_21-57_o3_radar_status_baudrate_readback_repair`：证明现有 helper 曾在同一真实板
  完成 strict no-motion `ComputePathToPose`；本轮必须重采 fresh current-window artifact，不能把
  旧 21/28 pose artifact 当成当前证据。

硬件参数来源边界：已查 `docs/vendor/VENDOR_INDEX.md`。Vendor 资料只给出 WAVE ROVER UART
事实，不给出本项目 LiDAR 的 `150000` baudrate；因此本轮不会把 `150000` 当 vendor 默认值。
只有当前板只读 `GET /api/radar/status` 再次返回 `baudrate=150000` 且指向 current lifecycle/
diagnostics 时，才按项目导航文档复用现有 `/dev/ttyACM0` LiDAR lifecycle。任何不一致都作为
current-run exact root cause 落盘，不改硬件参数、不抢占串口。

## 用户价值和产品北极星

北极星仍是让普通用户能发起一条可验证、可复盘、最终可送达的垃圾收集任务。本轮核心价值
不是再做 readiness、handoff 或状态面板，而是利用 CEO 新提供的真实上位机入口
`ssh root@192.168.1.11 -p 37878`，把导航证据推进到当前窗口的真实传感器、定位、TF、
Nav2 lifecycle 和 planner-only path artifact。它直接回答“当前板此刻能否在不运动的前提下
生成路径；若不能，最窄现场根因是什么”。

## OKR 映射和方向判断

- 当前推进区最低 Objective：O5，约 `85%`。
- O1 当前约 `94%`；本轮走 O3 导航能力 lane，为 O1 的 live localization/planner 缺口补
  fresh same-window evidence。
- O6/O7 当前约 `93%`。
- 方向判断：`调整`。暂停 O5 cloud/relay/browser/CLI support-only 小切片，切换到 O3 live
  upper-computer no-motion evidence。
- 切换理由：最近 O5/O7 已连续消费 CLI export、live relay HTTP、headless browser 等同一类
  production/cloud blocker，仍没有 success-class external evidence；继续同类 surface 已触发
  “同一 blocker 最多消费 2 轮”和 WIP 红线。CEO 本轮新增可达真实上位机入口，O3 fresh live
  artifact 已成为当前环境可推进的更强证据类。
- KR 决策：计划阶段不归档、不调整百分比。只有实现阶段形成 fresh true-board artifact 后，
  Product closeout 才能按证据判断是否有计分增量；planner-only 成功本身仍不等于 route
  execution、delivery、HIL 或 safe-to-control。
- 已完成 KR 历史位置不移动：继续保留在 `OKR.md` 历史区和
  `docs/process/okr_progress_log.md`；本轮没有已完成、取消、替换或过期 KR 可归档。

## 本轮核心抓手

由 `robot-algorithm-engineer` 单 owner 复用 `o10_amcl_nav2_runtime_proof.py` 和现有 live
capture 流程，在 `192.168.1.11:37878` 生成 fresh raw JSON，并把目标 host、remote hostname、
开始/结束时间、SSH/helper exit code 和 helper SHA 一并留档。主验收链为：

`/scan -> /amcl_pose -> map/amcl lifecycle -> dynamic map_to_odom -> ComputePathToPose -> path artifact`

任一环节失败都必须进入同一 current-window raw evidence，给出 exact root cause；不得退化为
`readiness_ready`、`material_ready`、`handoff_ready` 或仅消费历史 artifact 的 wrapper。

## Owner 和协作边界

- `robot-algorithm-engineer`：单线负责 SSH 采集、artifact 落盘、必要的明确 helper bug 修复、
  targeted tests、失败定位、复验和 `tech-done.md`。
- `product-okr-owner`：结果返回后做 evidence acceptance 和阶段收口。
- 不并行派 Hardware owner。本轮不改接线、串口、波特率、固件或底盘配置；如果只读 radar
  status 与既有 evidence 冲突，先记录为 blocker，后续再单独派硬件事实咨询。

## Strict No-Motion 红线

本轮禁止真实运动，禁止发布 `/cmd_vel`，禁止调用 `/api/base/manual`，禁止
`NavigateToPose`，禁止 controller/BT route execution，禁止打开 WAVE ROVER UART，禁止任何
非零底盘命令。允许只读 topic/lifecycle/TF/AMCL/地图检查、no-motion localization 初始化，
以及显式 opt-in 的 planner-only `ComputePathToPose`。

所有 artifact 必须固定：

- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`

## Epic 留档顺序和风险

本计划阶段只创建 `pre_start.md -> prd.md -> tech-plan.md`。进入实现后由 Algorithm owner
更新 `tech-done.md`；Product 验收后再按顺序生成 `side2side_check.md -> final.md`。不得预生成
后续 closeout 文档。

主要风险：SSH/Auth 不可达、板端 helper 与本地版本漂移、current radar lifecycle/baudrate 与
历史不一致、ROS graph/lifecycle timeout、`/scan` 或 `/amcl_pose` 无 fresh sample、dynamic
`map_to_odom` 缺失、planner action 不可用。每项都有 current-run exact-root-cause 接受路径，
但只有 fresh board attempt，不接受历史复用或 support-only wrapper 作为替代。
