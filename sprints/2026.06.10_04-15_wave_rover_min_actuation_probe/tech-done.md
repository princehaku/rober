# WAVE ROVER Min Actuation Probe

## sprint_type: micro

## 目标

在真实上位机 `root@192.168.1.11 -p 37878` 上，使用现有 ROS2
`esp32_bridge` + `/cmd_vel` 路径做阶梯式最小起动阈值 probe。背景是上一轮
`linear.x=0.03 m/s`、`duration=0.236s` 可安全 stop，但未证明 LiDAR
physical motion delta，也未证明 WAVE ROVER `T=1001` 的 `left_speed/right_speed`
非零。

本轮目标是判断 `linear.x=[0.03,0.05,0.07,0.09] m/s` 中是否存在一个仍低速、
短窗口、可停止的阶梯，能证明真实物理运动或 wheel feedback 非零。

## 已读资料来源

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_protocol.py`
- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/bridge_config.py`
- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/esp32_bridge_node.py`

## 采用的硬件事实

- WAVE ROVER 上下位机链路是 UART，一行 UTF-8 JSON 以 `\n` 结束。
- vendor Raspberry Pi 默认底盘串口是 `/dev/ttyAMA0 @ 115200`；Orange Pi
  实板串口必须以现场为准。本轮继续使用已实测可打开的 `/dev/ttyS5 @ 115200`。
- `json_cmd.h` 定义 `CMD_SPEED_CTRL=1`，示例 `{"T":1,"L":0.5,"R":0.5}`。
- `json_cmd.h` 定义 `CMD_ROS_CTRL=13`，但本轮不切换 `command_mode=ros`，
  继续使用当前项目默认 `command_mode=speed` 的 `T=1` 差速速度命令。
- `json_cmd.h` 定义 `CMD_BASE_FEEDBACK=130`、`CMD_BASE_FEEDBACK_FLOW=131`、
  `CMD_FEEDBACK_FLOW_INTERVAL=142`、`CMD_UART_ECHO_MODE=143`、
  `FEEDBACK_BASE_INFO=1001`。
- 当前 `esp32_bridge` 的 `/trashbot/stop` 发送 `{"T":1,"L":0,"R":0}`。
- `/odom` 是 ROS-side command integration，不是实测轮速里程计。

## 设计决策

- 不改产品代码、launch、底盘控制逻辑、LiDAR driver、camera 代码或 firmware。
- 只通过 ROS2 `/cmd_vel` 发布运动脉冲，并用 `/trashbot/stop` 停车；不直接写 UART
  运动命令，不绕过 bridge。
- `command_mode=speed` 下 expected JSON 只按项目公式记录：
  `L=R=linear.x/max_wheel_speed_mps`，其中 `max_wheel_speed_mps=1.3`。
  该值是 expected command，不是硬件反馈。
- 阶梯边界：
  - step 1：`linear.x=0.03`，expected `{"T":1,"L":0.023077,"R":0.023077}`
  - step 2：`linear.x=0.05`，expected `{"T":1,"L":0.038462,"R":0.038462}`
  - step 3：`linear.x=0.07`，expected `{"T":1,"L":0.053846,"R":0.053846}`
  - step 4：`linear.x=0.09`，expected `{"T":1,"L":0.069231,"R":0.069231}`
- 每步 publish 窗口目标 `<=0.16s`，硬上限 `<=0.18s`；每步后立即零速并调用
  `/trashbot/stop`。
- 任一步出现 LiDAR delta 证明、wheel feedback 非零、异常反馈、stop 失败或串口异常，
  立即停止后续阶梯。

## 安全预检

- SSH 必须可达：`ssh root@192.168.1.11 -p 37878 'echo connected && hostname && date'`。
- source `/opt/ros/humble/setup.bash` 与 `/root/rober/onboard/install/setup.bash`
  后，`ros2 pkg prefix ros2_trashbot_hardware` 必须可解析。
- `/dev/ttyS5` 与 `/dev/ttyACM0` 必须存在，且能释放给本轮最小 ROS stack。
- 若 `trashbot-upper-robot-api.service` 占用 `/dev/ttyS5`，只允许记录后临时停止，
  本轮结束必须恢复 `active`。
- `lidar_driver` 必须在 `/dev/ttyACM0 @ 150000` 产出健康 `/scan`；baseline 至少
  3 帧健康聚合帧。
- `esp32_bridge` 必须在 `/dev/ttyS5 @ 115200 command_mode:=speed` 启动，并提供
  `/trashbot/stop`。
- 预停车 `/trashbot/stop` 必须返回 `success=True`；否则不得发送 `/cmd_vel`。

## 验收阈值

- `physical_motion_lidar_delta_proven=true` 只在单步同时满足：
  - `paired_bins >= 40`
  - `median_abs_diff_m >= 0.03`
  - `changed_bin_ratio >= 0.12`
  - baseline/post 均至少 3 个健康 `/scan` 聚合帧，健康帧满足
    `ranges_count>=80`、`finite_count>=80`、`angle_span_deg>=90`
- `wheel_feedback_lr_nonzero_proven=true` 只在本轮 WAVE ROVER feedback debug
  中观测到任一 step/post 帧 `abs(left_speed)>0` 或 `abs(right_speed)>0` 时成立。
- `min_actuation_step_proven` 记录第一步满足 LiDAR delta 或 wheel feedback 非零的
  `linear.x`；如果全部失败则为 `null`。
- `safe_to_control=true` 只表示本轮 bounded probe 的 stop 与清场成功，不等于自主发车。
- `delivery_success=false` 固定为 false；本轮不是送达任务。

## 清场检查

- 每步结束都发布零速并调用 `/trashbot/stop`。
- probe 退出时再次发布零速并调用 `/trashbot/stop`。
- 停止本轮启动的 `lidar_driver`、`esp32_bridge` 和 probe 进程。
- 检查 `lsof /dev/ttyS5 /dev/ttyACM0` 无异常占用。
- 若本轮停过 `trashbot-upper-robot-api.service`，必须恢复并确认 `active`。

## 执行记录

### 实际改动

- 新增 `artifacts/wave_rover_min_actuation_probe.py`
  - 订阅 `/scan`、`/odom`，发布 `/cmd_vel`，调用 `/trashbot/stop`。
  - 每步采集 baseline/post `/scan` profile、WAVE ROVER feedback debug、command integration
    `/odom` delta。
  - 脚本 `finally` 中再次零速和 `/trashbot/stop`，避免异常退出留下运动命令。
- 新增 `artifacts/run_remote_wave_rover_min_actuation_probe.sh`
  - 远端启动最小 `lidar_driver` + `esp32_bridge` stack。
  - 临时停止并最终恢复 `trashbot-upper-robot-api.service`。
  - 记录预检、stop、topic、driver、probe、cleanup 日志。
- 拉回远端 artifacts：
  - `artifacts/remote_capture/01_connection.log`
  - `artifacts/remote_capture/02_ros_workspace.log`
  - `artifacts/remote_capture/03_precheck_devices_service.log`
  - `artifacts/remote_capture/run_dir/precheck.log`
  - `artifacts/remote_capture/run_dir/after_service_stop.log`
  - `artifacts/remote_capture/run_dir/stack_precheck.log`
  - `artifacts/remote_capture/run_dir/stop_precheck.log`
  - `artifacts/remote_capture/run_dir/scan_echo_once.log`
  - `artifacts/remote_capture/run_dir/wave_rover_min_actuation_probe_summary.json`
  - `artifacts/remote_capture/run_dir/step_metrics.csv`
  - `artifacts/remote_capture/run_dir/wave_rover_feedback_debug.jsonl`
  - `artifacts/remote_capture/run_dir/scan_frame_stats.jsonl`
  - `artifacts/remote_capture/run_dir/odom_samples.jsonl`
  - `artifacts/remote_capture/run_dir/esp32_bridge.log`
  - `artifacts/remote_capture/run_dir/lidar_driver.log`
  - `artifacts/remote_capture/run_dir/final_cleanup_check.log`
  - `artifacts/remote_capture/05_strict_cleanup_check.log`
- 更新 `docs/hardware/board_sensor_stack_smoke.md`，追加本轮 0.03-0.09 m/s
  起动阈值 probe 结论。
- 更新 `docs/hardware/wave_rover_json_bridge.md`，补充 `speed` 模式低速起动阈值
  未证明边界。
- 未修改产品代码、launch、底盘控制逻辑、LiDAR driver、camera 代码或 firmware。

### 远端连接与工作区

```text
$ ssh root@192.168.1.11 -p 37878 'echo connected && hostname && date'
connected
op-z3-b6.home
Wed Jun 10 03:59:00 AM CST 2026
```

ROS 工作区检查通过：

```text
ROS_DISTRO=humble
/root/rober/onboard/install/ros2_trashbot_hardware
Wed Jun 10 03:59:09 AM CST 2026
```

### 安全预检

设备存在：

```text
crw-rw---- 1 root dialout 166,  0 Jun 10 03:43 /dev/ttyACM0
crw-rw---- 1 root dialout   4, 69 Jun 10 03:43 /dev/ttyS5
```

`trashbot-upper-robot-api.service` 预检为 `active`，但 `lsof /dev/ttyS5 /dev/ttyACM0`
无输出。本轮为避免串口竞争，probe 窗口内临时停止该服务；`after_service_stop.log`
记录为 `inactive` 且串口无占用。

最小 ROS stack 启动成功：

```text
[esp32_bridge]: Connected to WAVE ROVER ESP32 on /dev/ttyS5 @ 115200
[esp32_bridge]: ESP32Bridge ready: ... command_mode=speed; publish_odom_tf=True;
feedback_debug_log_enabled=True; odom source=ROS-side command integration until measured wheel odometry is validated
[lidar_driver]: LiDAR serial started: /dev/ttyACM0 @ 150000
```

`/trashbot/stop` 预检通过：

```text
std_srvs.srv.Trigger_Response(success=True, message='Motors stopped')
```

`/scan` 预检有真实聚合样本，`scan_echo_once.log` 记录 `frame_id=laser_frame`、
`angle_span` 约 179.9 度、`ranges_count` 大于 80。

### 运行说明

第一次远端包装命令没有进入 probe：artifact shell 脚本在 source ROS setup 前启用了
`set -u`，触发 `/opt/ros/humble/setup.bash` 的 `AMENT_TRACE_SETUP_FILES` 未定义变量错误。
该次没有启动 stack，也没有发送运动命令。已修正为 source 完成后再启用 nounset，
随后重跑并完成本轮 probe。

### Step-by-step 指标

本轮 feedback debug 共 685 行，summary 按 probe 起始时间过滤后有效 `T=1001`
记录 353 条；所有 step/post 记录中 `left_speed/right_speed` 均未出现非零。

| step | `linear.x` | duration | expected JSON | stop | paired_bins | median_abs_diff_m | changed_bin_ratio | healthy post scans | wheel L/R nonzero | command integration odom delta |
| --- | ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | --- | ---: |
| 1 | 0.03 m/s | 0.164106s | `{"T":1,"L":0.023077,"R":0.023077}` | success | 719 | 0.008000 | 0.312935 | 22 | false | 0.004503 m |
| 2 | 0.05 m/s | 0.166476s | `{"T":1,"L":0.038462,"R":0.038462}` | success | 716 | 0.006750 | 0.284916 | 22 | false | 0.004998 m |
| 3 | 0.07 m/s | 0.167155s | `{"T":1,"L":0.053846,"R":0.053846}` | success | 719 | 0.007000 | 0.255911 | 22 | false | 0.006891 m |
| 4 | 0.09 m/s | 0.177252s | `{"T":1,"L":0.069231,"R":0.069231}` | success | 720 | 0.007500 | 0.298611 | 22 | false | 0.017972 m |

说明：

- 四步 duration 均小于 `0.18s` 硬上限，最大 `linear.x=0.09 m/s` 未越界。
- 四步 `paired_bins` 与 `changed_bin_ratio` 足够，但 `median_abs_diff_m` 均远低于
  `0.03m` 阈值，因此不能证明 LiDAR physical motion delta。
- `/odom` delta 是 command integration，不能当作实测轮速或物理位移。
- expected JSON 是项目公式 `linear.x/max_wheel_speed_mps` 的 expected command，
  不是额外硬件反馈。

### 补充 rerun artifacts

主会话后续状态核对时发现同一 probe 脚本在 `2026-06-10T04:08` 又留下了一组未归档
remote capture 文件。为避免丢失现场证据，已将这些文件收敛到：

- `artifacts/remote_capture/rerun_dir/`

该 rerun 的结论与主记录一致，没有把任何布尔值翻转为 true：

| step | `linear.x` | duration | median_abs_diff_m | changed_bin_ratio | wheel L/R nonzero | command integration odom delta |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| 1 | 0.03 m/s | 0.162466s | 0.004500 | 0.205841 | false | 0.004500m |
| 2 | 0.05 m/s | 0.163676s | 0.009000 | 0.327731 | false | 0.007587m |
| 3 | 0.07 m/s | 0.168769s | 0.005500 | 0.250696 | false | 0.007008m |
| 4 | 0.09 m/s | 0.164173s | 0.009000 | 0.353933 | false | 0.013464m |

`rerun_dir/final_cleanup_check.log` 记录 API 服务为 `active`，`lsof` 与本轮 ROS 进程检查无异常。
因此 rerun 只增强“低速短脉冲可 stop，但仍无物理运动或 wheel feedback 非零证据”的结论，
不改变 `physical_motion_lidar_delta_proven=false`、`wheel_feedback_lr_nonzero_proven=false`、
`min_actuation_step_proven=null`。

### 清场检查

本轮 probe 退出后执行 stop 与进程清理，并恢复 API 服务。最终严格复查：

```text
[strict service]
active
[strict lsof]
[strict processes]
[api]
root ... python3 /root/rober/onboard/scripts/upper_robot_api.py ... --base-port /dev/ttyS5 --base-baudrate 115200 --max-speed 0.12
Wed Jun 10 04:01:24 AM CST 2026
```

`lsof /dev/ttyS5 /dev/ttyACM0` 无输出，`esp32_bridge`、`lidar_driver`、
`wave_rover_min_actuation_probe` 无残留。driver 日志中的 shutdown traceback
来自清场时 `rclpy` context 已被关闭后的退出路径，不影响本轮 stop 成功与串口释放结论。

## 结论布尔值

- `motion_commands_sent`: `true`
- `max_step_linear_x_mps_sent`: `0.09`
- `physical_motion_lidar_delta_proven`: `false`
- `wheel_feedback_lr_nonzero_proven`: `false`
- `min_actuation_step_proven`: `null`
- `safe_to_control`: `true`
- `delivery_success`: `false`

失败定位：`low_speed_steps_no_physical_or_wheel_feedback_proof`。在
`linear.x=0.03/0.05/0.07/0.09 m/s`、每步 `<=0.18s` 的 bounded 阶梯内，能证明
ROS2 命令发送、stop 成功、LiDAR 与 WAVE ROVER feedback 可采集，但仍不能证明真实物理
运动或 wheel feedback 非零。

## 剩余风险

- 现场没有肉眼或外部视频同步观察，本轮无法排除“轮子轻微尝试但不足以形成 LiDAR
  median delta”的情况。
- `T=1001.L/R` 在本轮仍为 0，可能表示命令低于底盘起动阈值、电机供电/急停/模式未满足、
  底盘架空或反馈字段并不代表当前受控低速轮速；需要现场人工确认。
- 下一步建议人工在场做外部视频/肉眼确认，检查电机供电、急停、遥控/模式、底盘是否架空；
  若仍无运动，再考虑 vendor direct `T=1` 更高 PWM/速度受控 HIL，但必须有人在场并保留
  `/trashbot/stop` 或 UART 零速兜底。
