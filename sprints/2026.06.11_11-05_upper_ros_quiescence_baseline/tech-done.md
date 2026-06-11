# Upper ROS Quiescence Baseline

## sprint_type

micro

## 实际改动

- 在真实上位机 `root@192.168.1.11:37878` 采集清场前 readback：
  `ps -eo pid,ppid,stat,cmd` 目标过滤、`ros2 node list`、`ss -lntup` 摘要、
  `/dev/ttyS5 /dev/ttyACM0 /dev/video0 /dev/video1 /dev/video2` 的 `lsof/fuser`、
  systemctl active 状态，以及 Robot API readback。
- 只对明确匹配的历史 ROS 应用残留执行精确 PID SIGINT：
  `waypoint_manager` PID `89708`、`90724`、`95878`；
  `map_recorder` PID `89710`、`90726`、`95880`；
  `task_orchestrator` PID `89714`、`90730`、`95884`。
- SIGINT 后 5 秒内目标进程全部退出，未进入 SIGTERM。未使用 `killall python3`，未杀
  `trashbot-upper-robot-api.service`、`trashbot-local-webrtc-camera.service`、`frpc`、
  `sshd`、`ros2 daemon`、LiDAR lifecycle 或系统服务。
- 在清场后采集同一组 readback，并确认 `upper_ros_quiescent=true`。
- 同步更新 `docs/hardware/board_sensor_stack_smoke.md` 和
  `docs/navigation/fixed_route_workflow.md`，说明本清场基线只是不运动前置条件，不等于
  motion/HIL/pass、Nav2 execution、真实路线执行或 delivery success。

## 真实上位机关键证据

artifact：

- `artifacts/pre_clear_readback.log`
- `artifacts/clear_actions.log`
- `artifacts/post_clear_readback.log`

清场前目标残留：

```text
89708 waypoint_manager
89710 map_recorder
89714 task_orchestrator
90724 waypoint_manager
90726 map_recorder
90730 task_orchestrator
95878 waypoint_manager
95880 map_recorder
95884 task_orchestrator
```

清场动作：

```text
SIGINT pid=89708 ... waypoint_manager
SIGINT pid=89710 ... map_recorder
SIGINT pid=89714 ... task_orchestrator
SIGINT pid=90724 ... waypoint_manager
SIGINT pid=90726 ... map_recorder
SIGINT pid=90730 ... task_orchestrator
SIGINT pid=95878 ... waypoint_manager
SIGINT pid=95880 ... map_recorder
SIGINT pid=95884 ... task_orchestrator
remaining_after_sigint: empty
matched_after: empty
```

清场后 readback：

```text
target_process_ps: empty
ros2_node_list: empty
trashbot-upper-robot-api.service=active
trashbot-local-webrtc-camera.service=active
ssh.service=active
sshd.service=active
/dev/ttyS5 lsof/fuser: no output
/dev/ttyACM0 lsof/fuser: no output
/dev/video0 /dev/video1 /dev/video2 lsof/fuser: no output
```

Robot API readback 只读端点：

- `/api/status`
- `/api/base/status`
- `/api/camera/health`
- `/api/radar/status`
- `/api/radar/scan-proof/latest`
- `/api/operator/report`

关键安全字段仍为 false：`safe_to_control=false`、`delivery_success=false`、
`primary_actions_enabled=false`、`robot_control_executed=false`、
`sends_motion_commands=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`。

## 验证结果

- 真实上位机清场前 readback：通过，保存到 `artifacts/pre_clear_readback.log`。
- 真实上位机精确 PID 清场：通过，保存到 `artifacts/clear_actions.log`；9 个目标 PID
  均在 SIGINT 后退出。
- 真实上位机清场后 readback：通过，保存到 `artifacts/post_clear_readback.log`；
  目标 stale 进程消失，上位机服务仍 active。
- `git diff --check`：通过，无输出。

## 剩余风险

- 本轮只清理三类历史 ROS 应用残留，不启动 LiDAR/camera/map/Nav2 新 runtime，不证明
  当前传感器 live、地图质量、AMCL 定位、Nav2 planner readiness、路径执行或固定路线运行。
- Robot API `/api/radar/scan-proof/latest` 等 readback 仍是已有 artifact 状态，不是本轮新
  LiDAR refresh；不能据此声明 fresh HIL 或 motion delta。
- `ss` 中仍可见非目标 ROS/DDS 相关 `python3` PID `170272` 和 `frpc` 进程；它们不匹配
  本轮允许清理的三类 stale 应用，按要求未处理。
- `frpc.service=inactive` 但 `ss` 摘要可见 `frpc` 进程 PID `1269`；本轮未排查隧道服务
  管理方式，因为任务范围是 ROS 应用清场。

## 当前运行时间

2026-06-11 10:57:06 CST
