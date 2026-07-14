# O3 Scan Probe QoS Repair PRD

## 背景

最新现场 O3 no-motion artifact 已把 blocker 从泛化 `map_to_odom_not_observed` 下钻到 `/scan_probe_timeout`、`/amcl_pose_probe_timeout` 和 `map_to_odom_dynamic_source_missing`。其中 `/scan` topic type 可见但 once probe timeout，说明下一步应先确认 LiDAR scan 的持续发布、QoS/CLI echo 兼容性和 managed runtime 保活窗口，而不是继续包装 O6/O7 readback。

## 用户价值

固定路线和送垃圾闭环的下一跳是 current same-run path generation。`/scan` 是 AMCL 产生 `/amcl_pose` 和 dynamic `map->odom` 的前置输入；如果只知道 topic 存在但无法读到一帧，就无法可靠判断问题在 LiDAR driver、DDS QoS、managed runtime 窗口、AMCL 参数还是 TF 链。

## 范围

本轮只做 no-motion scan probe / QoS / freshness repair：

- 改进 O10 helper 的 `/scan` 采样方式和 artifact 字段。
- 增加测试覆盖，证明 timeout、multi-attempt、QoS fallback、publisher endpoint 信息能 fail-closed。
- 更新 `docs/navigation/` 中 no-motion proof 与 fixed-route workflow 说明。
- 在真实板上复验 helper 并保存 live artifact。

## 非目标

- 不执行 `NavigateToPose` 或真实运动。
- 不打开底盘控制，不触发 WAVE ROVER command，不声明 safe-to-control。
- 不调整 O5 production readiness 或 O6/O7 readback schema。
- 不消费旧 historical material 作为新 OKR 增量。

## 验收标准

- 本地单测覆盖新增 `/scan` probe 行为。
- 本地 Mac 无 ROS 时仍 fail-closed，不假装 live proof。
- 真实板 artifact 至少证明 `/scan` 当前是否可通过 sensor-data QoS 或 fallback CLI 读取；若不可读取，root cause 必须比 `/scan_probe_timeout` 更可操作。
- 安全字段保持 `safe_to_control=false`、`robot_control_executed=false`、`delivery_success=false`、`hil_pass=false`。
