# Camera First Frame Top Aliases

## sprint_type

micro

## 实际改动

- `GET /api/robot-control/summary` 顶层新增并固定透出相机首帧读回短字段：
  - `camera_first_frame_probe_status`
  - `camera_first_frame_failure_reason`
- 两个字段与 `live_closure_summary.camera_first_frame_*` 同源，现场 `curl | jq` 不需要再翻嵌套对象，也不会读到缺字段。
- 同步 TypeScript contract、`robotControlSummary.test.ts` 和 `docs/product/pc_tools_workstation.md`。
- 该改动只解释画面为什么没显示，不启动独占相机、建图 runtime、Nav2/manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。

## 验证结果

- `npm test -- --run robotControlSummary.test.ts`：1 个测试文件、10 个用例通过。
- `npm test -- --run App.test.ts catalog.test.ts robotControlSummary.test.ts`：3 个测试文件、429 个用例通过。
- `npm run build`：通过，Vite 仅保留既有大 chunk warning。
- `npm run lint`：通过。
- `git diff --check`：通过。
- PC Node 已重启到 `0.0.0.0:7001`，监听 PID `73793`。
- live smoke `GET http://127.0.0.1:7001/api/robot-control/summary` 读回：
  - 顶层 `camera_first_frame_probe_status=source_first_frame_failed`
  - 顶层 `camera_first_frame_failure_reason=first_frame_total_timeout`
  - `live_closure_summary.camera_first_frame_probe_status=source_first_frame_failed`
  - `live_closure_summary.camera_first_frame_failure_reason=first_frame_total_timeout`
  - `camera_source_diagnosis_status=uvc_full_speed_usb_not_exclusive`
  - `camera_hardware_action_required=true`
  - `live_wysiwyg_missing_surface_ids=["camera"]`
  - `radar_map_points_visible=true`
  - `map_current_visible=true`
  - `mapping_start_missing_reasons=["camera_first_frame"]`

## 剩余风险

- 本轮没有执行任何 motion/control POST，没有复验 Nav2 wheel raw L/R 非零、delivery success、PC 键盘连续手控或自由移动真实运动；这些仍需现场安全确认后验收。
- 当前 WYSIWYG / 建图仍剩相机首帧缺口；live 诊断显示不是页面独占，当前硬件动作仍是处理 USB 12M full-speed 后复测。
