# Live Closure Free Move Mapping API Contract Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - `RobotControlLiveClosureSummary` 新增自由移动与建图分层字段：自由移动 safety-only 预检、相机/雷达不阻塞自由移动、固定 free-roam start/stop endpoint、建图启动相机首帧/雷达新鲜要求、建图启动/验收缺口数组和固定 map start/preview endpoint。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `buildLiveClosureSummary()` 输出上述 API 字段，让外部脚本只读 summary 时也能确认“可先低速自由移动”和“传感器就绪后再建图”是两层合同。
- `pc-tools/workstation/test/robotControlSummary.test.ts`
  - 新增 builder 单测，模拟自由移动 stop 兜底 ready 但相机/雷达未就绪，验证自由移动仍 safety-only、建图启动缺口为 `camera_first_frame,lidar_fresh`。
- `pc-tools/workstation/test/App.test.ts`
  - fixture 同步补齐新合同字段。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步记录 API 级 live closure 自由移动/建图分层合同。

## 验证结果

- `npm test -- robotControlSummary.test.ts`：通过，1 个测试文件、3 个测试通过。
- `npm test -- --run`：通过，3 个测试文件、402 个测试通过。
- `npm run lint`：通过，0 error；保留既有 4 个 `vue/multiline-html-element-content-newline` warning。
- `npm run build`：通过，生成 `dist/assets/index-Q7ojBxrt.js` 与 `dist/assets/index-BBcFFzNr.css`。
- `git diff --check`：通过。
- 7001 重启：已停止旧 `node` PID `66033`，新监听进程为 `node` PID `78116`，地址 `TCP *:7001`。
- live 只读 smoke：`GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `live_closure_summary.free_move_start_ready=true`、
  `free_move_minimal_precheck_safety_only=true`、`free_move_safety_confirm_required=true`、
  `free_move_camera_preflight_required=false`、`free_move_radar_preflight_required=false`、
  `free_move_blocked_by_camera_wysiwyg=false`、`free_move_blocked_by_radar_wysiwyg=false`、
  `fixed_free_roam_start_endpoint=/api/robot-control/free-roam/autonomy/start`、
  `fixed_free_roam_stop_endpoint=/api/robot-control/free-roam/autonomy/stop`、
  `mapping_start_ready=false`、`mapping_start_requires_camera_first_frame=true`、`mapping_start_requires_lidar_fresh=true`、
  `mapping_start_missing_reasons=camera_first_frame,lidar_fresh`、
  `mapping_acceptance_missing_reasons=camera_first_frame,lidar_fresh,mapping_active,fresh_map_preview`、
  `fixed_mapping_start_endpoint=/api/robot-control/map/start`、`fixed_mapping_preview_endpoint=/api/robot-control/map/preview`、
  `sends_motion_when_clicked=false`。

## 剩余风险

- 本轮只补只读 API 合同，不自动启动自由移动、不启动建图、不执行 Nav2、不发送 manual、keyboard、delivery、stop 或 `/cmd_vel`。
- 真实自由移动、键盘连续控制、建图记录和 Nav2 wheel L/R 复验仍需要现场安全确认后的真实动作验证。
