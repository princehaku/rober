# O3 Scan Endpoint Timing Inventory PRD

## 背景

上一轮 O3 live no-motion sprint 已消除旧 `/scan` 主进程 `rclpy` ImportError，把 blocker 收敛为 `/scan_rclpy_child_timeout_after_import`：

- `/scan.topic_type=sensor_msgs/msg/LaserScan` 可见。
- `import_check.ok=true`。
- ROS-sourced child Python 可以 import `rclpy`，但 `/scan.probe.observed=false`。
- CLI fallback 仍 timeout。
- `/amcl_pose=false`、`map_to_odom=false`、`path_generated=false`。

产品上，这已经不是"能否加载 rclpy"的问题，而是"当前现场是否真的有 LiDAR publisher 持续发布 LaserScan，helper 是否能在正确 QoS 和窗口内拿到样本"的问题。本轮 PRD 要把下一步验收从修旧 ImportError 切到 publisher、endpoint、QoS、sample timing 的事实清单。

## 用户价值

固定路线送垃圾的用户价值是当前现场能定位、生成路线并最终送达。`/scan` 是 AMCL 定位和 same-run path generation 的第一层输入：

1. LiDAR runtime 启动并发布 `/scan`。
2. helper 能用正确 QoS 在 bounded window 内读到 LaserScan sample。
3. AMCL 输出 `/amcl_pose`。
4. dynamic `map->odom` 出现。
5. `path_generated=true`。
6. 后续才有 route execution、delivery record、operator confirmation 和 O6/O7 current-run material。

本轮只推进第 1-2 步的可观测证据，不把诊断产物包装成送达结果。

## 产品北极星

北极星：普通手机用户把垃圾交给小车后，小车可沿固定路线安全送达，并且每次执行都有可复盘证据。

本轮贡献：把现场路线生成 blocker 从"读不到 `/scan`"细化为可执行的 publisher/runtime/QoS/timing 分类，让下一条现场命令能直接修 publisher、调 QoS/window 或复验 localization/path。

## OKR 映射和方向判断

- O5：方向判断为暂停 support-only 追分。O5 仍是最低主 Objective，约 `~85%`，但当前缺口是真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、production worker/cutover、OSS/CDN live traffic 和真实手机/browser evidence；继续 readiness/probe/checklist 不计分。
- O1：方向判断为继续相邻支持。`/scan` publisher/sample timing inventory 直接服务于 O1 的 current same-run path generation success 缺口。
- O3：归档 Objective 的现场验证临时 lane，不单独计分；本轮使用 O3 lane 产出 O1 localization/path 前置证据。
- O6/O7：方向判断为等待 current-run material。只有 O3/O1 产出 current scan/localization/path、route 或 delivery/operator material，O6/O7 才有新的同任务证据可消费。

本轮不更新 `OKR.md`，不归档 KR，不调整百分比。没有 `path_generated=true` 时，Product closeout 也不得上调主 OKR。

## KR 拆解、更新或历史归档

- O1 current same-run path generation：本轮只推进 `/scan` publisher/sample readiness；成功条件是 scan sample 或更窄 blocker，不等于 path generation success。
- O6/O7 current-run material：本轮只产出上游 artifact 字段；不直接新增 archive/readback/UI schema。
- O5 production evidence：本轮不推进；等待真实 external production evidence。
- 已完成 KR：无。
- 历史归档：无。本 planning sprint 不把任何 KR 移入历史区。

## 本轮核心抓手

核心抓手是 LiDAR publisher/sample timing/endpoint inventory，而不是再修旧 ImportError：

- 捕获 `/scan` publisher count、publisher node/name、topic type、endpoint QoS、subscriber/requested QoS。
- 记录 managed runtime 是否启动 LiDAR 相关 launch/process/lifecycle，以及 probe 开始和结束时间。
- 记录 child probe import、subscription 创建、first sample latency、sample count、last sample stamp/receive time。
- 输出稳定分类，至少覆盖 no publisher、LiDAR runtime not started、publisher visible but no sample、QoS/window timeout、child probe timeout after import、sample observed。

## 范围

本 planning 阶段只创建：

- `sprints/2026.07.11_15-44_o3_scan_endpoint_timing_inventory/pre_start.md`
- `sprints/2026.07.11_15-44_o3_scan_endpoint_timing_inventory/prd.md`
- `sprints/2026.07.11_15-44_o3_scan_endpoint_timing_inventory/tech-plan.md`

后续 implementation 阶段建议允许 `robot-algorithm-engineer` 修改：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.11_15-44_o3_scan_endpoint_timing_inventory/tech-done.md`
- `sprints/2026.07.11_15-44_o3_scan_endpoint_timing_inventory/artifacts/*`

## 非目标

- 不修改 `OKR.md`、`docs/`、产品代码或测试代码。
- 不执行机器人运动，不发底盘控制，不触发 WAVE ROVER UART。
- 不把 `/scan.topic_type` 可见当成 sample observed。
- 不把 child import 成功当成 localization ready。
- 不新增 O5 readiness/support-only packet、O6 archive schema、O7 UI surface 或 cloud relay probe。
- 不宣称 safe-to-control、HIL、delivery success 或 route execution success。

## 需要做什么

1. `robot-algorithm-engineer` 读取上一轮 live artifact，确认当前 blocker 是 `/scan_rclpy_child_timeout_after_import`，不是旧 ImportError。
2. 在 helper 中新增 `/scan` endpoint inventory，优先使用 ROS2 topic info / endpoint info / bounded sample probe 的组合。
3. 在 child probe 中记录 import ok、subscriber created、sample wait window、first sample latency、sample count 和 timeout boundary。
4. 增加 root cause 分类函数，确保 no publisher、runtime not started、visible no sample、QoS/window timeout、child timeout after import 不互相覆盖。
5. 本地无 ROS 或真实板不可达时 fail-closed，artifact 明确标注 local-only / not live proof。
6. 真实板可达时运行 live no-motion helper并拉回 artifact；若 scan observed，再复验 `/amcl_pose`、`map_to_odom` 和 `path_generated`。

## 优先级和验收口径

- 优先级：P0。它是 O1 current same-run path generation 与 O6/O7 current-run material 的前置 live blocker。
- Product 验收：接受新的可执行 root cause 或 scan sample observed；不接受只复述上一轮 `/scan_rclpy_child_timeout_after_import`，也不接受只新增静态文档。
- Safety 验收：`safe_to_control=false`、`robot_control_executed=false`、`delivery_success=false`、`route_execution_success=false`、`hil_pass=false` 必须保留。
- OKR 验收：没有 `path_generated=true`，不调整 O1/O5/O6/O7 百分比。

## 对应责任 Engineer

- 主责：`robot-algorithm-engineer`
- Product closeout：`product-okr-owner`
- 只读咨询：`robot-software-engineer`，仅限 ROS runtime / launch endpoint 事实。
- 不参与：`rober-hardware-engineer`、`full-stack-software-engineer`。

## 风险、阻塞和需要补齐的证据链

- 风险：publisher endpoint 可见但 sample timeout，可能需要 QoS/window、DDS discovery 或 LiDAR lifecycle 进一步修正。
- 风险：scan observed 后仍可能卡在 AMCL initial pose、map quality、TF source 或 planner readiness。
- 阻塞：真实板 SSH / ROS runtime 不可达时只能产出 local fail-closed。
- 待补证据链：`scan_publisher_visible=true` -> `scan_sample_observed=true` -> `/amcl_pose_observed=true` -> `map_to_odom=true` -> `path_generated=true` -> current-run route material -> O6/O7 archive/readback -> delivery/operator material。

## 需要创建或更新的 sprint 文档

本轮 planning 阶段创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

后续 implementation / acceptance 阶段才允许创建：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
