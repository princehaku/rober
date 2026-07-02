# Free Move Action UI Binding

## sprint_type

micro

## 实际改动

- 普通 PC 页面 `plain-free-move-acceptance-proof` 验收卡改为优先消费 summary 顶层 `current_free_move_action_*`。
- 验收卡 DOM 新增 `data-current-action-id`、`data-current-action-ready`、`data-latest-endpoint`、`data-readback-endpoints`、`data-required-success-markers`、`data-without-camera-allowed`、`data-without-radar-allowed` 和 `data-current-action-sends-motion`。
- 页面继续明确自由移动发车前只需现场安全确认，相机和雷达 WYSIWYG 不阻塞先低速自由移动；验收卡本身仍是只读 proof，点击卡片不会发车。
- 同步更新 `docs/product/pc_tools_workstation.md`。

## 验证结果

- `npm test -- --run App.test.ts`：1 个测试文件、237 个用例通过。
- `npm test -- --run robotControlSummary.test.ts App.test.ts catalog.test.ts`：3 个测试文件、428 个用例通过。
- `npm run lint`：通过。
- `npm run build`：通过，Vite 仅保留既有大 chunk warning。
- `git diff --check`：通过。
- PC Node 已重启到 `0.0.0.0:7001`，监听 PID `94694`。
- `GET http://127.0.0.1:7001/` 返回 HTTP 200。
- `GET http://127.0.0.1:7001/map` 返回 HTTP 200。
- 真实 summary smoke：
  - `current_free_move_action_id=start_free_move`
  - `current_free_move_action_ready=true`
  - `current_free_move_action_start_endpoint=/api/robot-control/free-roam/autonomy/start`
  - `current_free_move_action_stop_endpoint=/api/robot-control/free-roam/autonomy/stop`
  - `current_free_move_action_latest_endpoint=/api/robot-control/free-roam/autonomy/latest`
  - `current_free_move_action_readback_endpoints=[free-roam latest, map preview, summary]`
  - `current_free_move_action_required_success_markers=[free_roam_latest_motion_ready]`
  - `current_free_move_action_without_camera_allowed=true`
  - `current_free_move_action_without_radar_allowed=true`
  - `current_free_move_action_sends_motion=true`
  - `free_move_start_ready=true`
  - `mapping_start_ready=false`
  - `camera_current_visible=false`
  - `radar_overlay_wysiwyg_complete=true`

## 剩余风险

- 本轮只接 UI 消费和 DOM 验收字段，不执行任何 motion/control POST。
- 完整 Nav2 路线的同窗口 wheel L/R 非零、送达确认、PC 键盘连续手控和自由移动真实运动仍需要现场安全确认后验收。
- 相机 WYSIWYG 仍受 USB 12M full-speed / 首帧不可见影响；需要现场换高速 USB/线/供电 Hub 后复测。
