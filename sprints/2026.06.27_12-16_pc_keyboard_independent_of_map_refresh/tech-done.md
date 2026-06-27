# PC Keyboard Independent Of Map Refresh

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 移除键盘方向启动时的 `keyboardMapWysiwygBlocked` 硬门禁。
  - 地图 proof/preview 刷新中仍阻止图上路线执行、送达材料和建图验收等依赖当前地图画面的动作。
  - 勾选安全确认并显式启用键盘后，低速键盘脉冲仍可走固定 `POST /api/robot-control/base/manual`；松开/失焦/切页仍走 stop 兜底。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展“地图刷新中阻止路线执行”用例：同一状态下路线执行仍不转发，但键盘方向按钮可以发送固定 manual proxy，且不调用 `/cmd_vel`。
  - 扩展“扫图键盘锁定”用例：地图 preview/proof 刷新中仍可按住低速扫图，保存地图继续等待刷新结果，已停止短轨迹会保留。
- `docs/product/pc_tools_workstation.md`
  - 记录键盘低速手控不再依赖地图刷新状态，建图验收仍需要画面/雷达/地图记录 ready。

## 验证结果

- `npm test -- App.test.ts --testNamePattern "keeps free-roam keyboard locked until map recording starts|blocks visible-route execution while the map preview is refreshing"`：通过，2 passed / 162 skipped。
- `npm run lint`：通过。
- `npm run build`：通过；仅有 Vite chunk size 既有提醒。
- `npm test`：通过，2 files / 287 tests passed。
- `git diff --check`：通过。
- `launchctl kickstart -k gui/$(id -u)/com.rober.pc.api.7001 && sleep 5 && lsof -nP -iTCP:7001 -sTCP:LISTEN`：通过，`node` 监听 `TCP *:7001 (LISTEN)`。
- `curl http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http://192.168.1.11:8787`：只读通过；`safe_command_boundary.manual_motion_entry_status=controlled_jog_requires_safety_confirmation_only`，`non_stop_requires_operator_report_preflight=false`，`operator_report_preflight_required_fields=[]`，`keyboard_control_start_ready=true`，`keyboard_jog_interval_ms=260`，`keyboard_jog_duration_ms=240`。

## 剩余风险

- 本轮只修正 PC 前端键盘手控 gate，不触发真实运动；真实 wheel raw L/R 同窗口非零仍需现场安全确认后再做 HIL。
- 地图刷新中仍禁止图上路线执行，这是 WYSIWYG 路线安全边界；本轮没有放开 Nav2 execute。live summary 显示 Nav2 最近路线为 `goal_succeeded`，但 `goal_execution_base_feedback_nonzero_sample_count=0`，所以同窗口 wheel raw L/R 非零仍未证明。
- 摄像头真实画面仍受 `/dev/video1` 无帧输出影响，不属于本轮修复范围；live summary 的 camera first frame probe 当前仍是 `not_loaded`。
- 雷达当前 lifecycle/配置存在，但 scan preview point count 为 0；小车低速手控入口不再依赖雷达，建图验收仍需要新鲜雷达和地图画面。
