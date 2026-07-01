# Current Free Move Action Alias

## sprint_type

micro

## 实际改动

- `GET /api/robot-control/summary` 顶层新增 `current_free_move_action_*` 短字段，用同一组值表达自由自助移动的当前动作、入口、停止口、latest/readback、验收端点、缺口和安全边界。
- 新字段直接暴露 `start_free_move`、`/api/robot-control/free-roam/autonomy/start`、`/api/robot-control/free-roam/autonomy/stop`、`/api/robot-control/free-roam/autonomy/latest` 和 `[free-roam latest, map preview, summary]`，现场脚本无需再拼旧 `free_move_*` 字段。
- 新字段明确自由移动只需要现场安全确认，`camera_preflight_required=false`、`radar_preflight_required=false`，相机/雷达 WYSIWYG 缺口不阻塞先低速自由移动。
- 旧 `free_move_*`、`free_roam_*` endpoint/readback 字段复用同一组常量，避免新旧摘要漂移。
- 同步更新 `docs/product/pc_tools_workstation.md`。

## 验证结果

- `npm test -- --run robotControlSummary.test.ts App.test.ts catalog.test.ts`：3 个测试文件、428 个用例通过。
- `npm run lint`：通过。
- `npm run build`：通过，Vite 仅保留既有大 chunk warning。
- `git diff --check`：通过。
- PC Node 已重启到 `0.0.0.0:7001`，监听 PID `78976`。
- 真实 summary smoke：
  - `current_free_move_action_id=start_free_move`
  - `current_free_move_action_ready=true`
  - `current_free_move_action_start_endpoint=/api/robot-control/free-roam/autonomy/start`
  - `current_free_move_action_stop_endpoint=/api/robot-control/free-roam/autonomy/stop`
  - `current_free_move_action_latest_endpoint=/api/robot-control/free-roam/autonomy/latest`
  - `current_free_move_action_acceptance_endpoints=[free-roam latest, map preview, summary]`
  - `current_free_move_action_requires_safety_confirm=true`
  - `current_free_move_action_minimal_precheck_safety_only=true`
  - `current_free_move_action_camera_preflight_required=false`
  - `current_free_move_action_radar_preflight_required=false`
  - `current_free_move_action_without_camera_allowed=true`
  - `current_free_move_action_without_radar_allowed=true`
  - `current_free_move_action_blocked_by_camera_wysiwyg=false`
  - `current_free_move_action_blocked_by_radar_wysiwyg=false`
  - `current_free_move_action_sends_motion=true`
- `GET http://127.0.0.1:7001/map` 返回 HTTP 200。
- 当前目标状态 smoke：`current_motion_action_id=run_nav2_route`、`current_free_move_action_ready=true`、`radar_overlay_wysiwyg_complete=true`、`camera_current_visible=false`、`mapping_start_ready=false`、`mapping_start_missing_reasons=[camera_first_frame]`。

## 剩余风险

- 本轮只补 summary 只读合同，不执行任何 motion/control POST。
- 完整 Nav2 路线的同窗口 wheel L/R 非零、送达确认、PC 键盘连续手控和自由移动真实运动仍需要现场安全确认后验收。
- 相机 WYSIWYG 仍受 USB 12M full-speed / 首帧不可见影响；需要现场换高速 USB/线/供电 Hub 后复测。
