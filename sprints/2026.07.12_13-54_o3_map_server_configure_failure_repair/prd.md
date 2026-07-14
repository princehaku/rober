# PRD - O3 Map Server Configure Failure Repair

## 用户价值和北极星

北极星仍是普通手机用户一键发车送垃圾。当前阻塞在真实上位机 fixed-route/nav 前置链路：`/map_server` 不能完成 lifecycle configure/active，导致 `/map`、AMCL pose、dynamic `map->odom` 和 planner-only path generation 不能进入有效验证。本轮用户价值是把这个前置 blocker 修掉或下钻到工程可执行的下一层。

## 目标

Robot Software 在 strict no-motion 前提下修复或收窄 `/map_server` configure failure：

1. 优先修复 launch、参数、map IO、lifecycle manager timing 或 executor ordering，使 `/map_server` lifecycle clean/active。
2. 若无法修复，artifact 必须明确更窄 root cause，例如 parameter invalid、map IO deferred ordering、configure callback exception、ChangeState response detail、executor starvation、service/RPC timing 或 bond prerequisite。
3. 所有安全字段继续 fail-closed，不进入 motion/control/delivery/HIL 断言。

## 非目标

- 不推进 O5 support-only readiness。
- 不做 O6/O7 UI、archive、readback surface。
- 不做 NavigateToPose、route execution、`/cmd_vel`、`/api/base/manual` 或 WAVE ROVER UART。
- 不修改硬件配置、串口、波特率、接线或 vendor 事实。
- 不把 no-motion diagnostic 计为 OKR 百分比提升，除非出现 same-run path generation、route execution、current HIL 或 production external evidence。

## 成功指标

- true-board artifact 中 `/map_server` lifecycle clean/active；或 root cause 比 `map_server_configure_callback_return_failure` 更窄。
- artifact 明确记录 configure callback、map yaml/PGM read、ChangeState response、process/log window、executor/bond/service timing。
- `path_generation_attempted=false` 或仅在 lifecycle clean 后进入 planner-only gate；无 motion/control。
- `safe_to_control=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false` 保持。
- `tech-done.md` 写明实际改动、验证命令、返回码、artifact 字段、失败定位和剩余风险。

## 用户验收口径

Product 验收只接受以下两类结果：

- `lifecycle_clean_or_active`: `/map_server` clean/active，后续可交给 Algorithm 恢复 `/map`、AMCL、TF 和 planner-only path gate。
- `narrower_root_cause`: 比上一轮 configure failure 更窄，并足以指导下一轮明确修复或升级。

若结果仍是同一句 `map_server_configure_callback_return_failure`，且没有更窄证据，本轮不接受为进展。

## 风险

- true-board SSH 或 ROS runtime 不可达时，只能记录 blocked，不能用 macOS local artifact 替代 live proof。
- 如果 root cause 落到 Nav2 upstream 或 system timing，需要在 final 中明确下一轮是修复、参数调整、还是 CEO 决策。
- LiDAR serial cleanup 噪声必须隔离为非主因，除非新证据证明它阻断 map_server configure；若变成硬件事实，转 Hardware。
