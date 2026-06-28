# sprint_type: micro

## 实际改动

- PC 普通用户界面新增 `robot-camera-shared-preview-guidance`，直接展示共享预览的结论和下一步。
- 该结论优先消费 `/api/robot-control/camera/mjpeg/status` 的 `preview_plain_hint` / `preview_next_action`，缺失时回退到 summary 的同名字段。
- 已把 `check_usb_camera_input_power_or_known_good_uvc` 等后端 action token 翻译成普通中文，避免普通界面暴露底层状态名。
- 只改展示和测试，不改变 WebRTC/MJPEG 连接策略，不新增任何运动控制调用。

## 验证结果

- `npm --prefix pc-tools/workstation test -- -t "explains a live not-in-use camera first-frame failure as not exclusive access|uses camera diagnosis when source usage is not loaded"`：通过，2 passed。
- `npm --prefix pc-tools/workstation test -- -t "shared preview|camera"`：通过，56 passed。
- 第一轮误用了 Jest 参数 `--runInBand`，Vitest 报 `Unknown option --runInBand`，随后改用 `-t` 重新验证通过。
- `npm --prefix pc-tools/workstation test`：通过，366 passed。
- `npm --prefix pc-tools/workstation run build`：通过，Vite 仍提示现有 chunk 大于 500 kB 的非阻塞 warning。
- `git diff --check -- pc-tools/workstation/src/components/RobotControlConsolePanel.vue pc-tools/workstation/test/App.test.ts sprints/2026.06.29_11-50_pc_camera_shared_preview_guidance/tech-done.md`：通过。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN`：确认 Node 仍监听 `*:7001`，PID 44426。
- 只读 live `GET /api/robot-control/camera/mjpeg/status`：`preview_status=source_first_frame_failed`、`exclusive_camera_claim=false`、`shared_capture=true`、`preview_plain_hint=不是页面独占...UVC 设备没有输出视频帧...`、`robot_control_executed=false`。
- 只读 live `GET /api/robot-control/summary`：自由移动 next action 为勾安全确认后可先移动；Nav2 next action 为上次路线 action 成功但 `wheel raw L/R=0/0`，下次用 ROS 重跑并启动 runtime；`robot_control_executed=false`。

## 剩余风险

- 当前改动只能把“不是页面独占、UVC 无首帧、下一步查 USB/输入/供电”显示得更清楚，不能替代真实摄像头出帧。
- 本轮没有发车、没有执行自由移动、没有重跑 Nav2；自动驾驶真实移动仍需要现场安全确认后由 operator 执行。当前 live 仍未证明 `wheel raw L/R` 非零。
