# 2026.06.28 04:25 PC Camera Timeout Explained Connection

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通连接面板新增窄口径判断。若 summary 顶层唯一降级原因是 `camera_health:fetch_timeout...`，且同一份相机摘要已经证明 `uvc_no_frame_not_exclusive` 或首帧失败，则连接面板仍显示“已连接”，并提示“画面健康读取较慢，具体看画面行的无帧诊断”。
- 同时覆盖 live 重启后一拍的部分读取超时：若已读到多项状态且剩余 blocked reasons 全部是 `fetch_timeout`，普通连接面板显示“部分读取较慢，下面按画面、雷达、地图和行程分项显示已读事实”，不再泛化成“部分项目未通过”。
- 该判断只改变普通首屏文案，不改 `robot_api_connection.status/degraded`、blocked reason 或高级诊断 raw 字段，避免隐藏真实 timeout。
- `pc-tools/workstation/test/App.test.ts`：新增 live 形状测试，验证 camera health timeout 被归为画面问题、部分 readback timeout 被归为分项事实，同时保留全上位机 timeout 的“上位机没回应”提示。
- `docs/product/pc_free_roam_mapping_design.md`：同步记录 camera health timeout 已解释时的普通首屏 WYSIWYG 口径。

## 验证结果

- `npm test -- --run test/App.test.ts -t "camera health timeout as a camera issue|partial timeout readbacks|plain timeout hint when the robot API does not respond"` 通过，3 passed / 189 skipped。
- `npm test` 通过，2 个 test file / 339 个测试通过。
- `npm run lint` 通过。
- `npm run build` 通过；Vite 仍有既有 chunk size warning，未影响构建产物。
- `git diff --check` 通过。
- PC Node 已重启到 `0.0.0.0:7001`，监听 PID `42896`。
- live 只读 summary（未发任何 POST）确认：API 原始状态仍保留 `robot_api_connection.status=degraded`，
  `loaded_count=13`、`failed_count=2`、blocked reasons 为 `status:fetch_timeout_2400ms` 和
  `camera_health:fetch_timeout_2400ms`；相机分项同时读到
  `status=source_first_frame_failed`、`source_readiness=first_frame_failed`、
  `source_diagnosis_status=uvc_no_frame_not_exclusive`、`source_diagnosis_not_exclusive=true`；
  Nav2 仍为 `nav2_stack_running=false/lifecycle=stopped`，`robot_control_executed=false`。

## 剩余风险

- 本轮不处理真实摄像头无帧根因；live 仍需要检查 USB/输入/供电或更换 known-good UVC。
