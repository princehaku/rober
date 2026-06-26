# tech-done

sprint_type: micro

## 实际改动

- `onboard/scripts/o11_nav2_goal_execution_proof.py`：新增 `--base-command-mode`，白名单为 `ros/speed/pwm`；O11 Nav2 托管底盘 bridge 默认从硬编码 `pwm` 改为 `ros`，并在 artifact 中保留实际模式。
- `onboard/scripts/upper_robot_api.py`：新增独立 `nav2_base_command_mode`，默认 `ros`；普通手控 `base_command_mode` 继续默认 `pwm`。`/api/nav2/goal/execute` 可按白名单请求覆盖 Nav2 模式，并传给 helper。
- `pc-tools/workstation/src/server/index.ts`、`pc-tools/workstation/src/shared/contracts.ts`：PC Nav2 execute 代理允许透传受限 `base_command_mode=ros|speed|pwm`，默认不传复杂配置。
- `onboard/tests/test_o11_nav2_goal_execution_proof.py`、`onboard/tests/test_upper_robot_api.py`、`pc-tools/workstation/test/catalog.test.ts`：补回归，覆盖默认 `ros`、显式 `pwm` override、PC 透传 `ros`。
- `docs/product/pc_tools_workstation.md`、`docs/hardware/wave_rover_json_bridge.md`：同步记录 vendor `T=13` ROS 控制来源和 Nav2 同窗口 wheel L/R 验收边界。

## 验证结果

- 通过：`python3 -m py_compile onboard/scripts/o11_nav2_goal_execution_proof.py onboard/scripts/upper_robot_api.py`。
- 通过：`python3 -m unittest onboard.tests.test_o11_nav2_goal_execution_proof onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_nav2_goal_execute_lifts_base_motion_flags_from_latest_result onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_nav2_goal_execute_allows_explicit_base_command_mode_override`，`8 tests OK`。
- 通过：`python3 -m unittest onboard.tests.test_o11_nav2_goal_execution_proof onboard.tests.test_upper_robot_api`，`67 tests OK`。
- 通过：`npm test -- --run test/catalog.test.ts`，`113 passed (113)`。
- 通过：`npm test -- --run test/App.test.ts`，`150 passed (150)`。
- 通过：`npm run lint`。
- 通过：`npm run build`；仍有既有 Vite chunk size warning，未影响构建产物生成。
- 通过：已将 `upper_robot_api.py` 与 `o11_nav2_goal_execution_proof.py` 部署到
  `root@192.168.1.11:/root/rober/onboard/scripts/`，远端 sha256 与本地一致，远端
  `python3 -m py_compile` 通过。
- 通过：上位机 API 已重启，PID `207261` 监听 `0.0.0.0:8787`；live
  `/api/status.base.control_policy` 显示 `base_command_mode=pwm`、
  `nav2_base_command_mode=ros`。
- 通过：PC Node 已重启，PID `21248` 监听 `0.0.0.0:7001`；无确认调用
  `POST /api/robot-control/nav2/goal/execute` 返回 `execution_rejected`、
  `robot_control_executed=false`，同时 `goal_request.base_command_mode=ros` 被保留。

## 剩余风险

- 本轮没有在无人确认安全的情况下重新执行真实 Nav2 发车；因此尚未证明 `base_command_mode=ros` 能让本车在同窗口产生非零 `T=1001.L/R`。
- 如果现场固件 `mainType` 或编码器状态不支持 `T=13` PID/ROS 控制，需要通过同一 `base_command_mode=pwm` 或 `speed` override 做 A/B 复验。
- 摄像头首帧仍是板端 `/dev/video1` 打不开/读不到画面的问题，不由本轮 Nav2 命令模式修复。
