# PRD - O3 Map Server On-Configure IO Order Repair

## 背景

自动化 `rober-okr` 每小时推进最低进度 OKR。O5 约 `85%` 仍最低，但当前缺真实 production external evidence；继续 support-only 不计分。可执行 lane 是 O3/O1 strict no-motion 现场链路，当前 true-board root cause 已收敛到：

- `map_server_configure_return_failure_before_deferred_map_read_completed`
- `lifecycle_manager_changestate_response_failure_during_configure_before_deferred_map_read_completed`

13:54 sprint 已证明 FastDDS SHM 噪声不是 primary root cause，bond 在 configure failure 前未创建，且 `/map_server` 仍未 lifecycle clean/active。本轮产品需求是继续向可执行修复推进，而不是重复同一句 blocker。

## 用户价值和产品北极星

用户价值：恢复真实上位机 `/map_server` lifecycle，让 fixed-route/nav 现场链路能继续进入 `/map`、AMCL、TF 和 planner-only path proof，最终服务普通手机用户一键送垃圾的主闭环。

产品北极星：普通用户无需理解 ROS2、SSH、地图文件或硬件调试，只需要手机发起送垃圾任务；机器人应能沿固定路线可靠送达。本 sprint 是该北极星的前置 technical unblock，不直接交付用户可见功能。

## OKR 映射和方向判断

- O5：方向 `暂停 support-only`。没有真实 HTTPS/TLS、公网入口、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser 或 external production evidence，本轮不应继续做 O5 readiness 包装。
- O3/O1：方向 `继续`。本轮处理 current same-run path generation 与 Nav2 route execution 的 `/map_server` lifecycle 前置 blocker。
- O6/O7：方向 `暂停等待材料`。没有 live route execution、delivery/operator 或 production readback 时，不新增 read-only surface。
- KR 历史归档：本轮计划阶段不归档 KR；预计实施阶段也只有在出现 mission-grade evidence 时才考虑归档或调百分比。

## 本轮需求

`robot-software-engineer` 后续必须做一个 true-board strict no-motion repair/proof：

1. 优先修复 `/map_server` lifecycle clean/active。
2. 若不能修复，必须输出比 13:54 artifact 更窄、可执行的 root cause。
3. 更窄 root cause 必须落在以下至少一类：
   - map_server `on_configure` return path
   - map IO completion ordering
   - lifecycle manager ChangeState response handling
   - executor timing / starvation
   - bond prerequisites / creation timing
   - map_server parameter exception
   - map_server source-level exception
   - ChangeState RPC error / timeout / response body
4. 若 artifact 仍只重复 `map_server_configure_return_failure_before_deferred_map_read_completed`，且没有新增细节，本轮必须标记 `needs retry`；连续无法推进时 `升级 CEO` 或切换 Objective。

## 范围

In scope：

- strict no-motion helper / lifecycle script / launch 参数级修复。
- true-board artifact 采集和回拉。
- additive proof schema 字段，描述 `on_configure`、map IO ordering、ChangeState、executor、bond 和参数/异常证据。
- navigation docs 同步新的 proof boundary。
- sprint `tech-done.md` 和 `artifacts/` 留档。

Out of scope：

- NavigateToPose。
- `/cmd_vel`。
- `/api/base/manual`。
- WAVE ROVER UART。
- 硬件配置、串口、波特率、接线。
- O5/O6/O7 API/UI/archive surface。
- OKR.md 或 `docs/process/okr_progress_log.md` 更新，除非后续 Product 验收阶段另行授权。

## Strict No-Motion 安全要求

本轮所有 true-board 和 local 命令必须带 strict no-motion 意图，并保持以下字段 false：

- `path_generation_attempted=false`，除非 `/map_server` clean 后只进入 planner-only gate 且 Product/Engineer 在 tech-done 中明确说明边界。
- `path_generated=false`，除非明确进入 no-motion planner-only proof 且未触发 route execution。
- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `uses_base_uart=false`

不得因 `/map_server` lifecycle clean/active 就声称 safe-to-control、HIL、route execution 或 delivery success。

## 验收口径

Accept：

- `/map_server` lifecycle clean/active；或
- 比 13:54 更窄的 root cause，且 root cause 可指导下一条修复命令或源码/参数检查。

Needs retry：

- 只重复 `map_server_configure_return_failure_before_deferred_map_read_completed`。
- 没有记录 map_server `on_configure` return path、map IO completion ordering、lifecycle manager ChangeState response handling、executor timing、bond prerequisites、参数/异常/源码级原因中的任何一个。
- 没有 true-board artifact。
- 没有 strict no-motion false 字段。

Reject：

- 任何 NavigateToPose、`/cmd_vel`、`/api/base/manual`、WAVE ROVER UART 或硬件配置改动。
- 把 cleanup/LiDAR/AMCL/TF 噪声当 primary blocker 而没有证明它覆盖 `/map_server` configure。

## 优先级

P0：

- `/map_server` lifecycle clean/active。
- 或 narrow root cause 到 `on_configure` / map IO ordering / ChangeState / executor / bond / parameter / exception。

P1：

- 若 `/map_server` clean，读取 `/map` sample 和 lifecycle readback，但仍保持 no-motion。

P2：

- 等 Product 验收后再决定是否交给 Algorithm 恢复 AMCL/TF/path gate。

## 风险和证据缺口

- 即使 `/map_server` clean，仍不证明 `/map` sample、AMCL pose、dynamic `map->odom`、planner path、route execution、delivery、HIL 或 production external evidence。
- 如果 true-board SSH 不可达，本轮只能记录环境 blocker，不能用 local artifact 代替 true-board proof。
- 如果第三轮仍无法比同一 root cause 更窄，Product 必须要求 `升级 CEO` 或切换 Objective，避免连续消费同一 blocker。
