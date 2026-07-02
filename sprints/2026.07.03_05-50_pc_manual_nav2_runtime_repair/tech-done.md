# 2026.07.03 05:50 PC 手控别名与 Nav2 执行 runtime 修复

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`：`/api/robot-control/base/first-jog` 与
  `/api/robot-control/base/manual` 兼容 `speed_mps`、`linear_x_mps`、`linear_mps` 别名；上游仍转发
  `/api/base/manual` 的 `speed` 字段，保持上位机合同不变。
- `onboard/scripts/o11_nav2_goal_execution_proof.py`：托管 Nav2 goal helper 在启动新 runtime 前先只读
  `/navigate_to_pose` action；若现有 action server 已存在，复用当前 ROS graph，不再启动第二个
  `esp32_bridge` 抢 `/dev/ttyS5`。
- `onboard/scripts/o11_nav2_goal_execution_proof.py`：补充进程级现有 runtime 探针；当坏 ROS graph 导致
  `ros2 action list -t` 超时时，只要观察到常驻 `esp32_bridge`、`autonomous.launch.py` 或
  `nav2_container`，也保守复用现场 runtime，不再打开第二个 `/dev/ttyS5` holder。
- `pc-tools/workstation/test/catalog.test.ts`：新增 PC 手控 `speed_mps` 别名代理测试。
- `onboard/tests/test_o11_nav2_goal_execution_proof.py`：新增 O11 进程级 runtime 复用保护测试。
- `docs/hardware/wave_rover_json_bridge.md`、`docs/navigation/field_route_evidence_preflight.md`：同步本轮现场相机、
  底盘和 Nav2 执行边界。

## 验证结果

- `python3 -m unittest onboard.tests.test_o11_nav2_goal_execution_proof`：通过，`Ran 11 tests`。
- `python3 -m py_compile onboard/scripts/o11_nav2_goal_execution_proof.py`：通过。
- `cd pc-tools/workstation && npm test -- --run test/catalog.test.ts -t "speed_mps|Nav2 goal execution proxy forwards"`：
  通过，`1 passed`。
- `cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts test/catalog.test.ts`：
  通过，`196 tests passed`。
- `cd pc-tools/workstation && npm run build`：通过；仅保留 Vite chunk size warning。
- `git diff --check`：通过。
- 已用 `scp -P 7878` 将 `onboard/scripts/o11_nav2_goal_execution_proof.py` 同步到真实上位机
  `root@192.168.1.11`。
- 真实上位机 `POST http://127.0.0.1:8787/api/nav2/goal/execute`，body 使用
  `managed_runtime_opt_in=true`、`base_command_mode=pwm`、`goal=(0.8,0.05)`、
  `server_timeout_s=5`、`result_timeout_s=4`：13.9s 内返回 `status=goal_rejected`、
  `managed_runtime.reuse_existing_runtime=true`、`reuse_reason=existing_runtime_process_observed`、
  `started=false`、`cleanup.boundary=no_process_started`；未再启动第二套 bridge，未发送运动命令。
- PC Node 已重启到 `0.0.0.0:7001`，`curl http://127.0.0.1:7001/` 返回页面。
- PC 代理手控 `POST /api/robot-control/base/manual?baseUrl=http://192.168.1.11:8787`，
  body 使用 `speed_mps=0.05`：返回 `proxy_status=command_forwarded`、`remote_http_status=200`、
  `requested_speed_mps=0.05`、`clamped_speed_mps=0.05`。
- 上车 `wave_rover_command_debug.jsonl` 显示本次手控写出多帧 `{"T":11,"L":255,"R":255}`，随后写出
  `{"T":11,"L":0,"R":0}` stop；`wave_rover_feedback_debug.jsonl` 仍显示 `T=1001 L/R=0/0`。

## 剩余风险

- 现场相机 `/dev/video1` 直接 `v4l2-ctl` 仍为 `VIDIOC_STREAMON Input/output error`，且 USB 拓扑显示 12M
  full-speed；不是页面独占。
- PC 手控已能发出 `T=11 L/R=255` 并自动 stop，但同窗口 `T=1001 L/R` 当前仍读到 `0/0`，不能宣称 wheel
  raw 非零或真实物理运动完成。
- Nav2 `/navigate_to_pose` action server 可达但拒收目标；日志指向 lifecycle/BT/controller 运行态不健康。
  本轮只修复 helper 不再抢 UART，尚未完成完整路线执行和 delivery success。
