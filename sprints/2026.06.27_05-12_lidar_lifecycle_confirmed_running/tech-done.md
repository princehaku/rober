# Tech Done

sprint_type: micro

## 实际改动

- 修改 `onboard/scripts/o1_lidar_lifecycle.sh`：`start` 现在等待 LiDAR lifecycle manager 进入稳定 `running` 状态后才返回成功，避免 PC 看到“start 成功但立刻 stopped”的假阳性。
- manager 现在会记录 `lidar_driver` 和 static TF pid 文件；driver 退出时写入 `failed` 状态并清理子进程，减少旧 TF/driver 残留影响下一轮雷达诊断。
- 同步更新 `docs/product/pc_tools_workstation.md`，记录本轮 live 结果：雷达 lifecycle/driver 已能保持运行，但 `/scan` 与 `/lidar/raw_packet` 仍无消息；摄像头首帧仍 timeout；Nav2 不再被雷达 gate 阻塞，但真实自动驾驶验收仍缺当前轮速/HIL 运动闭环。

## 验证结果

- `bash -n onboard/scripts/o1_lidar_lifecycle.sh`：通过。
- `python3 -m unittest onboard.tests.test_lidar_lifecycle_script`：3 tests OK。
- `python3 -m unittest onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_radar_lifecycle_validation_accepts_lidar_only_start_stop onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_radar_status_defaults_to_managed_lifecycle_commands onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_radar_control_uses_default_managed_lifecycle_command onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_radar_lifecycle_validation_rejects_base_uart_and_motion_tokens onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_radar_control_uses_validated_lifecycle_command_contract onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_radar_control_rejects_unsafe_lifecycle_command_without_execution`：6 tests OK。
- 已部署脚本到 `root@192.168.1.11:/root/rober/onboard/scripts/o1_lidar_lifecycle.sh`，远端 `bash -n` 通过。
- PC 7001 固定代理 `POST /api/robot-control/radar/start?baseUrl=http://192.168.1.11:8787` 返回 `command_result.ok=true`，随后远端 `o1_lidar_lifecycle.sh status` 显示 `running=true`、`state=running`、`pid=198390`。
- 远端 `lsof /dev/ttyACM0` 显示 `lidar_driver` 独占 LiDAR 串口；`ros2 topic list` 可见 `/scan`、`/lidar/raw_packet`、`/tf`、`/tf_static`。
- 远端 `ros2 topic echo --once /scan` 与 `/lidar/raw_packet` 在短窗口内无消息；PC summary 显示 `continuous_scan_status=latest_proof_incomplete_while_lifecycle_running`、`scan_preview_point_count=0`，符合“雷达运行但无新点”的 WYSIWYG。
- 摄像头 `POST /api/camera/first-frame/probe` 仍返回 `first_frame_timeout`，`failure_reason=capture_read_call_timeout`，`open_ok=true`、`read_ok=false`。
- Nav2 latest 仍显示 `goal_succeeded`、`base_command_mode=pwm`、`nonzero_command_count=49`，但 `wheel_feedback_lr_nonzero_proven=false`、`hil_pass=false`。

## 剩余风险

- LiDAR lifecycle 已能维持运行，但真实 scan/raw packet 仍无消息；下一轮应继续查 LiDAR 电机/供电、串口数据格式、驱动解析与 topic 发布链。
- 摄像头不是 PC 多人独占问题；底层 DV20/UVC 仍打开成功但不出首帧，需要继续检查输入源、USB 线/供电、采集卡模式或更换 known-good UVC。
- 自动驾驶 action 已有命令下发材料，但完整验收仍缺当前轮速 L/R 非零与现场 HIL 运动闭环；不能声明 delivery success。
