# ROS2 Motion Mainline Smoke Tech Done

## sprint_type: epic

## 实际改动

- 新增 `artifacts/ros2_motion_mainline_smoke.md`，整理 vendor 来源、执行步骤和结论。
- 新增 `artifacts/ros2_motion_mainline_smoke_remote_summary.log`，保存远端全流程 summary。
- 新增 `artifacts/ros2_motion_mainline_smoke_bringup.log`，保存 base-only bringup 日志。
- 新增 `artifacts/ros2_motion_mainline_smoke_api_restore.log`，保存 API 恢复日志。
- 新增本文件、`side2side_check.md`、`final.md`，完成本轮 sprint 留档。

## 已执行验证

### 验收命令

```bash
ssh root@192.168.1.11 -p 37878 'true'
ssh root@192.168.1.11 -p 37878 'curl -sS http://127.0.0.1:8787/api/base/status || true'
ssh root@192.168.1.11 -p 37878 'bash -lc '\''source /opt/ros/humble/setup.bash && source /root/rober/onboard/install/setup.bash && ros2 launch ros2_trashbot_bringup bringup.launch.py --show-args'\'''
```

结果：

- SSH 连通成功。
- `/api/base/status` 在 smoke 前后均返回 JSON。
- `bringup.launch.py --show-args` 成功输出 `base_enabled`、`serial_port`、`serial_baudrate`、`command_mode` 等参数。

### 真实上车 smoke

执行结果摘要：

- 真实上位机原始 API 进程：
  - `python3 /root/rober/onboard/scripts/upper_robot_api.py --host 0.0.0.0 --port 8787 --camera-base-url http://127.0.0.1:8088 --base-port /dev/ttyS5 --base-baudrate 115200 --max-speed 0.12`
- 停止原 API 后，`/dev/ttyS5` 成功释放。
- `esp32_bridge` 成功连接：
  - `Connected to WAVE ROVER ESP32 on /dev/ttyS5 @ 115200`
- `esp32_bridge` 以 `command_mode=speed` 运行。
- `/cmd_vel` 有 1 个订阅者。
- `/trashbot/stop` 服务存在并成功返回：
  - `std_srvs.srv.Trigger_Response(success=True, message='Motors stopped')`
- `/odom` 样本：
  - 脉冲前 `position.x=0.0`
  - stop 后样本 `position.x=0.15000877008`

## 已证实的硬件结论

- 真实上位机上，ROS2 `esp32_bridge` 可以打开 `/dev/ttyS5 @ 115200` 并进入可发布 `/cmd_vel` 的状态。
- 在 `command_mode:=speed` 下，低速短脉冲和 `/trashbot/stop` 主链路可执行。
- 本轮 `/odom` 变化只能证明 ROS 侧命令积分链路工作，不能证明真实轮速反馈闭环。
- 本轮没有拿到新的 `/battery` 或 `/imu/data` topic 样本，因此不能宣称本轮拿到了新的底盘 feedback stream 证据。

## 偏差与修正

- 初次 cleanup 时，launch 父进程退出后 `esp32_bridge`、`waypoint_manager`、`map_recorder`、`task_orchestrator` 仍残留。
- 已定点 `pkill` 相关 ROS2 子进程，再次重启 `upper_robot_api.py`。
- 最终 `upper_robot_api.py` 进程恢复，`/api/base/status` 可访问，`0.0.0.0:8787` 在监听。

## 剩余风险

- `/odom` 仍是 ROS-side command integration，不是实测轮编码器里程计。
- `feedback_ack.t1001_observed` 在最终 `/api/base/status` 中仍为 `false`，本轮没有新增 `T=1001` 实时样本证据。
- API 恢复后当前未证明它会持续占用 `/dev/ttyS5`；已证明服务进程和状态接口恢复，但串口持有策略仍需单独复核。

