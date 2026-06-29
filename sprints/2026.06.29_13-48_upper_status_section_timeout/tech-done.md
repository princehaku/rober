# 上位机 status 分区超时 micro sprint

sprint_type: micro

## 实际改动

- `onboard/scripts/upper_robot_api.py` 的 `GET /api/status` 从串行聚合改为相机、雷达、地图、Nav2、自由移动、电梯和底盘分区并发读取。
- 每个只读区块增加软超时兜底；单区块卡住时返回 `status_section_unavailable`，并保持 `safe_to_control=false`、`robot_control_executed=false`、`sends_motion_commands=false`。
- 清理上位机上一条已卡住 1 天多的旧只读 `ros2 lifecycle get /controller_server` 诊断进程。

## 验证结果

- `python3 -m unittest onboard.tests.test_upper_robot_api`：通过，82 个 tests。
- `python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/tests/test_upper_robot_api.py`：通过。
- 已同步并重启上位机 `0.0.0.0:8787`；新进程 PID `355355`。
- 上位机只读验证：`curl --max-time 8 http://127.0.0.1:8787/api/status` 成功返回，用时约 4.3s，`safe_to_control=false`、`robot_control_executed=false`。
- PC 侧只读验证：`GET http://127.0.0.1:7001/api/robot-control/summary` 仍正常返回当前事实。

## 剩余风险

- 摄像头仍是 UVC 首帧失败，当前证据支持“不是页面独占，而是设备没有输出视频帧”。
- 雷达仍未运行或扫描已停，地图雷达点当前显示 0 个，旧来源点只作诊断。
- Nav2 上次路线 action 成功但同窗口轮速 L/R=0/0 未非零；完整运动闭环仍需要现场安全确认后按 ROS 模式重跑。
