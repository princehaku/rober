# 2026.06.28 04:31 PC Partial Timeout Current Facts

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：把上一轮“部分读取 timeout 已解释”的口径同步到普通首屏 `当前事实`。
- 当 summary 已读到多项状态，但剩余失败全是 `fetch_timeout` 时，当前事实第一行显示“小车：已读到状态；少数读取较慢，下面各项按已读事实显示。”
- 当唯一相机 health timeout 已被共享预览/相机摘要解释为无首帧时，当前事实第一行显示“小车：已读到状态；画面健康读取较慢，画面行显示真实无帧诊断。”
- `pc-tools/workstation/test/App.test.ts`：扩展部分 timeout 与 camera health timeout 用例，验证连接面板和当前事实条口径一致，且不暴露 `fetch_timeout`、不发 goal execute、manual 或 `/cmd_vel`。

## 验证结果

- `npm test -- --run test/App.test.ts -t "camera health timeout as a camera issue|partial timeout readbacks|plain timeout hint when the robot API does not respond"` 通过，3 passed / 189 skipped。
- `npm test` 通过，2 个 test file / 339 个测试通过。
- `npm run lint` 通过。
- `npm run build` 通过；Vite 仍有既有 chunk size warning，未影响构建产物。
- `git diff --check` 通过。
- PC Node 已重启到 `0.0.0.0:7001`，监听 PID `52179`。
- live 只读 summary（未发任何 POST）确认：API 原始状态仍为 `robot_api_connection.status=degraded`，
  `loaded_count=12`、`failed_count=3`，blocked reasons 为 `status/camera_health/camera_devices` 的
  `fetch_timeout_2400ms`；相机分项仍读到 `source_first_frame_failed`、`first_frame_failed`、
  `uvc_no_frame_not_exclusive`；Nav2 仍为 `nav2_stack_running=false/lifecycle=stopped`，
  `robot_control_executed=false`。

## 剩余风险

- 本轮只修普通首屏事实条口径，不处理真实相机无帧、Nav2 stopped 或雷达 stopped 的硬件/服务根因。
