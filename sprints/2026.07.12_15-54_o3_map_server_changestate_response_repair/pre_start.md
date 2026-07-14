# Pre Start - O3 Map Server ChangeState Response Repair

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_15-54_o3_map_server_changestate_response_repair/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Start time: `2026-07-12 15:54 CST`
- Target Objective: O3/O1 strict no-motion field lane, because O5 is lowest but blocked on real production external evidence
- Proof boundary: `software_proof_o3_o1_strict_no_motion_map_server_changestate_response_repair_only`

## 上轮输入

上一轮 accepted sprint 是 `sprints/2026.07.12_14-54_o3_map_server_on_configure_io_order_repair/`。

关键事实：

- True-board artifact `live_o10_map_server_on_configure_io_order_repair.raw.json` 为 `status=blocked_with_root_cause`。
- Primary root cause 是 `map_server_changestate_response_failure_after_image_load_before_map_read_completed`。
- lifecycle manager 已请求 configure，`/map_server` configure callback 已进入，YAML/image load 已开始。
- ChangeState failure 发生在 image load started 之后、map read completed 之前。
- `path_generation_attempted=false`、`path_generated=false`、`safe_to_control=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`。

## 同一 Blocker 红线

最近两轮不是完全相同 blocker：

- 13:54：`map_server_configure_return_failure_before_deferred_map_read_completed`
- 14:54：`map_server_changestate_response_failure_after_image_load_before_map_read_completed`

本轮允许继续，但必须推进到以下两类之一：

1. `/map_server` lifecycle clean/active，并继续 strict no-motion 读取 `/map`、AMCL、TF、planner-only path gate。
2. 比 `map_server_changestate_response_failure_after_image_load_before_map_read_completed` 更窄的 callback exception、map IO、ChangeState RPC、executor、process exit、parameter 或 AMCL configure root cause。

如果本轮只重复上一句 root cause，必须在验收中标记为未达成，需要重试；重试后仍重复时，下一轮应升级 CEO 或切换 Objective。

## Owner 和边界

本轮单 owner：`robot-software-engineer`。

选择理由：当前 blocker 位于 ROS2/Nav2 lifecycle manager、map_server configure callback、runtime log parsing 和 helper proof contract，仍是机器人软件主链路问题。Algorithm 只有在 `/map_server` lifecycle clean 后再接 `/map`、AMCL、dynamic `map->odom` 和 planner-only path。Hardware 只有在 LiDAR serial/runtime/接线事实成为 primary root cause 后才介入，并必须先读 `docs/vendor/VENDOR_INDEX.md`。

## 验收口径

- 保持 strict no-motion：不发布 `/cmd_vel`，不调用 `/api/base/manual`，不发 NavigateToPose，不打开 WAVE ROVER UART。
- 输出 true-board artifact，并在 `tech-done.md` 记录命令、返回码、核心字段、失败定位和剩余风险。
- 若修复成功，artifact 必须至少证明 `/map_server active` 或 lifecycle clean readback。
- 若未修复成功，artifact 必须给出比上轮更窄的 root cause，不接受重复 wrapper。
