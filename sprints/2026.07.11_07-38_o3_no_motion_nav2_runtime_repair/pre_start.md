# O3 No-Motion Nav2 Runtime Repair Pre Start

## sprint_type

sprint_type: epic

## 上轮未完成项和阻塞

- O5 仍是当前最低主 Objective，约 `~85%`，但 `cloud_production_cutover_readiness_packet` 已明确 `okr_credit_allowed=false`，当前环境没有真实公网 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic 或真实手机/browser external evidence。继续 O5 readiness / wrapper / local probe 会重复消费 `no_real_production_external_evidence` blocker。
- 最近两轮现场 O3 lane 已把 blocker 从 `/scan` 未确认推进到 no-motion Nav2/map/AMCL runtime 未 ready：
  - `2026.07.11_05-55_o3_live_localization_sensor_smoke`：`/scan observed=true`，但 `/amcl_pose`、`map->odom`、`map->base_link` 和 refresh readback 仍 blocked。
  - `2026.07.11_06-37_o3_amcl_map_tf_recovery_probe`：`/map` topic type 缺失、`/amcl_pose` topic type 缺失、`/map_server` / `/amcl` / `/planner_server` lifecycle unavailable、`map` frame 未建立；configured managed map basename `trashbot_map.yaml` 可读。
- 同一 blocker 已连续两轮以诊断方式消费；本轮必须进入 no-motion runtime repair，不能再只扩探针。

## 本轮目标

在不发送 `/cmd_vel`、不调用 `/api/base/manual`、不执行 NavigateToPose goal、不中断真实硬件安全边界的前提下，修复或恢复受管 Nav2/map/AMCL runtime 启动链路，使真实上位机 no-motion refresh 至少进入新的状态层级。

最低可接受结果：

- 本地测试证明 `/api/nav2/start` / `/api/nav2/proof/refresh` 的 managed runtime 路径不会触发运动命令。
- 真实板 artifact 证明本轮已尝试受管 runtime repair，并输出新的 start/status/refresh 根因。

高价值结果：

- `/map_server`、`/amcl`、`/planner_server` lifecycle 从 unavailable 变为 active 或明确的更深层失败；
- `/map` topic、`/amcl_pose`、`map->odom` / `map->base_link` 出现；
- `/api/nav2/proof/refresh` 产出 same-run `path_generated=true` 或 path/root-cause artifact。

## Owner

- 主责 owner：`robot-software-engineer`
- 主节点：只负责本 sprint 拆解、派单、验收、`side2side_check.md` / `final.md` 汇总和自动化记忆更新。

## 风险边界

- `starts_nav2=true` 只表示 no-motion 服务栈恢复，不代表 route execution、HIL pass、safe-to-control 或 delivery success。
- 本轮不允许新增任何默认运动入口，不允许默认发布 `/cmd_vel`，不允许默认执行 goal。
- 若真实板不可达或 runtime 仍失败，必须保留 fail-closed artifact 和下一轮可执行修复点；OKR 百分比保持不变。
