# Safety Action Aliases Micro Sprint

sprint_type: micro

## 实际改动

- PC `GET /api/robot-control/summary` 顶层补齐安全确认后动作清单 alias：
  - `field_acceptance_safety_confirm_ready_action_ids`
  - `field_acceptance_safety_confirm_ready_action_endpoints`
- `*_action_ids` 与 `field_acceptance_packet.safety_confirm_ready_step_ids` 同源；`*_action_endpoints` 与 `*_action_start_endpoints` 同源，作为现场 `curl | jq` 脚本的直觉别名。
- 普通首屏 `plain-field-acceptance-packet` 和 `plain-field-acceptance-remaining-actions` 同步暴露：
  - `data-safety-confirm-ready-action-ids`
  - `data-safety-confirm-ready-action-endpoints`
- 更新 `docs/product/pc_tools_workstation.md` 和 `pc-tools/README.md`，明确这些字段只描述勾安全确认后的 Nav2/键盘/free-roam 执行入口，不自动勾确认、不发车、不提交送达、不 stop。

## 验证结果

- `git diff --check`：通过。
- `cd pc-tools/workstation && npm test -- --run catalog.test.ts App.test.ts robotControlSummary.test.ts`：3 个测试文件通过，427 个测试通过。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过；仅保留 Vite chunk size warning。
- PC Node 已重启到 `0.0.0.0:7001`，监听 PID `75115`。
- 真实只读 smoke：

```json
{
  "status": "needs_wheel_rerun",
  "objective_missing_ids": ["motion", "wysiwyg", "mapping"],
  "field_acceptance_safety_confirm_ready_action_ids": [
    "run_nav2_route",
    "hold_keyboard",
    "start_free_move"
  ],
  "field_acceptance_safety_confirm_ready_action_labels": [
    "完整行程执行",
    "键盘连续手控",
    "自由自助移动"
  ],
  "field_acceptance_safety_confirm_ready_action_endpoints": [
    "/api/robot-control/nav2/goal/execute",
    "/api/robot-control/base/manual",
    "/api/robot-control/free-roam/autonomy/start"
  ],
  "field_acceptance_safety_confirm_ready_action_stop_endpoints": [
    "/api/robot-control/base/stop",
    "/api/robot-control/base/stop",
    "/api/robot-control/free-roam/autonomy/stop"
  ],
  "field_acceptance_primary_safety_confirm_ready_action_id": "run_nav2_route",
  "map_display_operator_default_surface": "pc_big_map_direct_view",
  "map_display_companion_replaces_pc_ui": false
}
```

## 剩余风险

- 本轮只做只读 API/DOM 合同增强，没有现场安全确认，因此没有执行真实 Nav2 路线、键盘连续手控或自由移动。
- 当前目标仍缺 `motion/wysiwyg/mapping`：motion 还需要安全确认后的同窗口 wheel raw L/R 非零、delivery success、键盘连续手控和自由移动读回；WYSIWYG/建图仍受相机首帧与当前雷达贴图状态影响。
- 本轮未调用任何运动控制 POST，未启动 ROS2/RViz2/Foxglove/Nav2/建图 runtime，未发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
