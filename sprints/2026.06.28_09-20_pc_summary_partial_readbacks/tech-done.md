# PC Summary 部分读数可见

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 新增 PC 首屏 summary 只读预算 `ROBOT_CONTROL_SUMMARY_HTTP_READBACK_TIMEOUT_MS=2400`。
  - `buildRobotControlSummary()` 支持可选 `readbackTimeoutMs`，保留默认宽超时给离线验证；HTTP 首屏可用短预算返回部分读数。
  - 将 fetch timeout 视为连接 degraded，不再把 `console_status` 直接打成硬 blocked；危险字段和 HTTP blocked 仍保持 hard block。
- `pc-tools/workstation/src/server/index.ts`
  - `/api/robot-control/summary` 的相机 source failure 覆盖读取最多等待 600ms。
  - `/api/robot-control/summary` 调用 builder 时使用 2400ms 首屏只读预算，避免慢 camera/status 让普通页面空壳。
- `pc-tools/workstation/test/catalog.test.ts`
  - 新增短预算测试：慢 `status` 与慢 `camera/health` timeout 时，free-roam、Nav2、雷达、camera devices 等已返回读数仍进入 summary。
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录 summary 首屏短预算、共享 MJPEG 多页面观看口径、自由移动不依赖雷达 ready，以及当前 Nav2 planner/controller inactive 根因。

## 验证结果

- 已通过 focused 测试：
  - `npm test -- --testNamePattern "first-screen budget|slow status and camera" --maxWorkers=1 --no-fileParallelism`
  - 结果：2 passed。
- 已做本机 7001 只读复验：
  - `GET http://127.0.0.1:7001/api/robot-control/summary`
  - 返回 `console_status=loaded_fail_closed_summary`、`loaded_count=15`、`failed_count=0`。
  - 摄像头：`shared_preview_contract=single_shared_capture_for_multiple_clients`、`exclusive=false`、`source_failure_reason=first_frame_total_timeout`。
  - 自由移动：`free_roam_motion_start_ready=true`、`free_roam_mapping_ready=false`。
  - Nav2：`planner_server_active=false`、`controller_server_active=false`，下一步为先恢复 Nav2 planner/controller。

## 剩余风险

- 本轮未发送真实运动命令，也未点击 Nav2 restore/start；自动驾驶恢复仍需现场 operator 明确安全确认后执行。
- 摄像头源仍未出首帧；PC 只能证明不是页面独占，不能替代检查 USB/供电/摄像头输入或换 known-good UVC。
- 雷达 runtime scan 当前 stale，建图验收仍不能通过；这不阻塞低速自由移动，但会阻塞“建图已验收”结论。
