# O3 AMCL Lifecycle Path Generation Repair PRD

## 用户价值和产品北极星

用户北极星不变：普通手机用户把垃圾交给机器人后，机器人能够沿固定路线安全完成送达。当前 mission 缺的不是新的 UI 包装，而是让真实板 no-motion 定位链真正进入 planner-only path generation attempt。本 sprint 的产品价值是把定位、TF 和 path gate 从“requested 但未 attempted”推进到“可尝试且可复核”，为后续真实 route execution 和 delivery evidence 铺路。

## OKR 对齐

- O5 当前约 `85%`，仍是最低 Objective，但缺口是明确的真实 production/external evidence：公网 HTTPS/TLS、4G/SIM、production DB/queue、worker/cutover、OSS/CDN live traffic、真实手机/browser。最近 O5 已固定 `okr_credit_allowed=false`，没有新 external material 不应继续消费。
- O1/O6/O7 当前约 `93%`，本轮不是去追表面百分比，而是补 mission chain 的 no-motion 前置条件。
- 方向判断：`继续` O3/O1 supporting no-motion localization/path readiness；`暂停` O5 support-only；`不调整` O5/O1/O6/O7 百分比；`不归档` KR。

## 问题定义

截至 `20-46` final，真实板链路已经证明：

- 旧 source/CLI blocker 已清掉：`board_source_preflight_ready`、`ros2_cli_ok=true`、`rclpy_import_ok=true`
- 但 localization/path gate 仍 blocked：
  - `/amcl` lifecycle inactive
  - `/amcl_pose` stale
  - `/scan` dual-QoS timeout
  - `/map_once_not_observed`
  - `cli_initialpose_publish_failed`
  - dynamic `map->odom` missing
  - `path_generation_requested=true` 但 `path_generation_attempted=false`

因此本 sprint 的问题不是“能不能再读回一点状态”，而是“能不能把 localization/TF gate 修到允许 planner-only path attempt 的门槛”。

## 范围内

- 明确本轮只处理 O3 no-motion localization/path readiness
- 只派 `robot-algorithm-engineer` 单线闭环
- 只允许 AMCL lifecycle、`/scan`、`/map`、`/amcl_pose`、dynamic TF、initialpose publish、planner-only path generation gate 相关实现和验证
- 只接受 strict no-motion 证据

## 范围外

- O5 production external evidence
- O6/O7 archive/readback/consumer/UI
- 真实 route execution
- delivery/operator acceptance
- HIL pass
- 发布 `/cmd_vel`
- `/api/base/manual`
- NavigateToPose
- WAVE ROVER UART

## 成功标准

计划阶段成功标准：

- 三份文档完整建立 epic 计划链：`pre_start.md`、`prd.md`、`tech-plan.md`
- `tech-plan.md` 包含 `## OKR 最低优先级核对`
- owner、文件范围、接口边界、验收命令和 no-motion 约束可直接给 Algorithm worker 执行

implementation 阶段目标成功标准：

- 至少把 localization/TF gate 向前推进一层，且证据能明确说明：
  - `/amcl` lifecycle 是否 clean active
  - `/scan`、`/map`、`/amcl_pose` 是否 fresh enough
  - dynamic `map->odom` 是否出现
  - 若这些 gate ready，则 `path_generation_attempted=true`
  - 若仍 blocked，必须给出比 `20-46` 更窄的 root cause

## 不加分边界

以下结果都不能算 OKR 新进展：

- 继续重复 O5 support-only packet/readback
- 只有 `path_generation_requested=true`
- 只有 planner ready、topic type 可见或 sample 曾出现
- 只有 partial artifact、wrapper、总结性 readback，没有更窄 root cause 或新的 attempted/generated 事实
- 任何突破 no-motion 边界的“假成功”

## 验收口径

- 文档必须让后续 worker 能直接复制命令执行
- 必须显式保留所有 safety/control/HIL/delivery false 字段
- 必须写明：只有 localization/TF gate ready，才允许 planner-only `ComputePathToPose` attempt
- 最终 closeout 若没有 `path_generation_attempted=true`，也必须证明 blocker 已从 `20-46` 进一步缩窄，不能原样复述
