# O3 AMCL Map TF Recovery Probe Pre Start

## sprint_type

sprint_type: epic

## 启动时间

2026-07-11 06:37 CST

## 上轮未完成项

- `sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/` 已在真实上位机 no-motion 场景下确认 `/scan observed=true`。
- 同一窗口仍然没有观察到 `/amcl_pose`、`map->odom`、`map->base_link`，`/api/nav2/proof/refresh` 仍落到 `blocked_refresh_readback_failed` / `refresh_command_failed`。
- O5 仍是最低主 Objective，约 `~85%`，但最近 O5 external evidence lane 已明确缺真实公网 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic 和真实 phone/browser evidence；继续 O5 support-only/readback 会重复消费同一 blocker。

## 本轮目标

本轮继续临时激活 O3 现场验证 lane，在不发运动命令、不触发 NavigateToPose、不调用 `/cmd_vel` 或 `/api/base/manual` 的前提下，把 `/amcl_pose`、`map` frame 和 TF 链路从现象级 blocked 下钻到可复核根因。

最低可接受结果是新增同轮真实板 root-cause artifact：能说明 AMCL/map/TF 卡在 map server、map topic、map yaml、lifecycle state、AMCL 参数、TF tree 或 refresh endpoint 其中哪一层。

更高价值结果是在安全 no-motion 前提下修复可确认的配置或脚本缺口，重跑 `/api/nav2/proof/refresh`，产出同轮 `path_generated=true` 或新的 route/material artifact。若没有 path 成功，本轮必须明确 OKR 百分比不变。

## Owner

- 主责：`robot-algorithm-engineer`
- 协作：主节点只做任务拆解、派单、验收和 sprint 汇总。

## 风险边界

- 禁止发送 `/cmd_vel`、`/api/base/manual`、NavigateToPose 或任何真实运动命令。
- 若涉及 lifecycle start/restart，只能在已有代码或文档确认其为 no-motion proof 链路时使用，并且 artifact 必须固定 `safe_to_control=false`、`delivery_success=false`、`robot_control_executed=false`、`route_execution_success=false`、`hil_pass=false`。
- 本轮可以改 preflight 诊断脚本、测试和导航文档；不得碰 O5/O6/O7 已有 support packet/readback 文件。
