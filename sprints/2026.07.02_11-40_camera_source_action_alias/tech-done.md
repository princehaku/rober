# Camera Source Action Alias Micro Sprint

sprint_type: micro

## 实际改动

- PC `GET /api/robot-control/summary` 顶层新增 `camera_source_diagnosis_next_action_plain`。
- 当底层 `live_wysiwyg_camera_source_diagnosis_next_action_plain` 为 `not_loaded` 时，该顶层字段 fallback 到 `camera_recovery_next_action_plain`，避免现场 `curl | jq` 读到 `null`。
- USB full-speed 场景现在顶层直接给出“换高速 USB 口/线或带供电 USB Hub 后复测；共享预览不是页面独占”。
- 更新 shared contract、summary 构造、robotControlSummary 测试、`docs/product/pc_tools_workstation.md` 和 `pc-tools/README.md`。

## 验证结果

- `git diff --check`：通过。
- `cd pc-tools/workstation && npm test -- --run catalog.test.ts App.test.ts robotControlSummary.test.ts`：3 个测试文件通过，427 个测试通过。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过；仅保留 Vite chunk size warning。
- PC Node 已重启到 `0.0.0.0:7001`，监听 PID `10750`。
- 真实 summary smoke 显示：

```json
{
  "status": "needs_wheel_rerun",
  "objective_missing_ids": ["motion", "wysiwyg", "mapping"],
  "camera_source_diagnosis_status": "uvc_full_speed_usb_not_exclusive",
  "camera_source_diagnosis_next_action_plain": "摄像头现在挂在 USB 12M full-speed，换高速 USB 口/线或带供电 USB Hub，减少转接并确认供电后复测；共享预览不是页面独占。",
  "camera_usb_speed": "12M",
  "camera_usb_full_speed_detected": true,
  "camera_hardware_action_required": true,
  "camera_blocks_mapping_start": true,
  "camera_blocks_free_move": false,
  "mapping_start_missing_evidence": ["camera_first_frame"]
}
```

- 重启后发现雷达贴图短暂过期，已按固定 no-motion 链路刷新雷达 scan proof 和 map preview；最终 summary 收敛为：

```json
{
  "live_wysiwyg_missing_reasons": ["camera"],
  "radar_overlay_wysiwyg_complete": true,
  "radar_overlay_needs_refresh": false,
  "mapping_start_missing_evidence": ["camera_first_frame"]
}
```

## 剩余风险

- 相机仍未 WYSIWYG，根因仍是 USB 12M full-speed / 首帧读不到；需要现场换高速 USB 口/线或带供电 Hub 后再复测。
- 建图仍缺 `camera_first_frame`；自由移动不被相机阻塞。
- Motion 仍缺同窗口 wheel raw L/R 非零、delivery success、键盘连续手控和自由移动运行读回；本轮没有安全确认，未执行任何运动控制。
