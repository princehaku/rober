# 2026-07-02 06:05 相机唯一缺口只读复测动作

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 新增 no-motion readback action `refresh_camera_first_frame`。
  - 当 WYSIWYG 只剩 `camera` 时，primary no-motion action 从泛化 `refresh_current_wysiwyg` 切到 `refresh_camera_first_frame`。
  - 固定序列为 `/api/robot-control/camera/first-frame/probe -> /api/robot-control/camera/mjpeg/status -> /api/robot-control/summary`，并保持不发车、不启动建图、不启动雷达 lifecycle。
  - 多缺口场景继续使用 `refresh_current_wysiwyg`；雷达贴图过期时仍优先 `refresh_radar_map_overlay`。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 扩展 `RobotControlFieldAcceptanceNoMotionReadbackActionId`。
- `pc-tools/workstation/test/robotControlSummary.test.ts`、`pc-tools/workstation/test/App.test.ts`
  - 增加 camera-only API / DOM 断言，确认 action id、label、endpoint 和 sequence。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步说明相机唯一缺口时的只读复测动作口径。

## 验证结果

- `git diff --check`：通过。
- `cd pc-tools/workstation && npm test -- --run App.test.ts robotControlSummary.test.ts`：通过，2 个测试文件、246 个测试通过。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过；Vite 仍提示单个 bundle 超过 500kB，这是既有体积提醒，不影响本轮只读动作。
- 重启 PC API 后，`lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node` 监听 `TCP *:7001`，PID `69617`。
- `curl http://127.0.0.1:7001/` 读到当前 bundle `index--4XQAMx-.js`。
- 重启后首次 summary 因雷达贴图状态回退，primary no-motion action 合理保持 `refresh_radar_map_overlay`。
- 只读执行 `POST /api/robot-control/radar/scan-proof/refresh?baseUrl=http://192.168.1.11:8787` 后返回：
  - `proxy_status=refresh_forwarded`
  - `last_result_status=refreshed`
  - `latest_scan_proof_fresh=true`
- 随后 `GET /api/robot-control/map/preview?baseUrl=http://192.168.1.11:8787` 返回：
  - `radar_overlay_status=loaded`
  - `radar_overlay_point_count=149`
  - `radar_overlay_source_point_count=154`
- 再读 `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787`：
  - `live_wysiwyg_missing_reasons=["camera"]`
  - `radar_overlay_wysiwyg_complete=true`
  - `mapping_start_missing_evidence=["camera_first_frame"]`
  - `field_acceptance_no_motion_readback_action_ids=["readback_all","refresh_camera_first_frame"]`
  - `field_acceptance_no_motion_readback_action_labels=["复验全部读数","复测相机首帧"]`
  - `field_acceptance_primary_no_motion_readback_action_id=refresh_camera_first_frame`
  - `field_acceptance_primary_no_motion_readback_action_label=复测相机首帧`
  - `field_acceptance_primary_no_motion_readback_action_endpoint=/api/robot-control/camera/first-frame/probe`
  - `field_acceptance_primary_no_motion_readback_action_sequence=["/api/robot-control/camera/first-frame/probe","/api/robot-control/camera/mjpeg/status","/api/robot-control/summary"]`
  - `field_acceptance_primary_no_motion_readback_action_refreshes_camera_first_frame_probe=true`
  - `field_acceptance_primary_no_motion_readback_action_refreshes_camera_mjpeg_status=true`
  - `field_acceptance_primary_no_motion_readback_action_refreshes_radar_scan_proof=false`
  - `field_acceptance_primary_no_motion_readback_action_sends_motion=false`
- `curl http://127.0.0.1:7001/assets/index--4XQAMx-.js | rg -o 'refresh_camera_first_frame|复测相机首帧|data-primary-no-motion-readback-action-id' | sort | uniq -c`：
  - `data-primary-no-motion-readback-action-id`：6 处。
  - `复测相机首帧`：6 处。

## 剩余风险

- 本轮只改相机唯一缺口的只读复测动作，不修复物理 USB 12M/full-speed 相机问题。
- 当前完整目标仍需要现场处理相机首帧，以及安全确认后的真实 Nav2/键盘/自由移动运动读回。
