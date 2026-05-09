# Sprint 2026.05.09_20-21 Tech Plan

## 总体技术方案

本轮采用“先契约、再实现、再验证”的方式推进送垃圾闭环：

1. 保持硬件事实源只来自 `docs/vendor/VENDOR_INDEX.md` 及其指向资料。
2. 将行为层目标固定为装载确认后的 delivery mission，而不是巡逻 demo。
3. 将导航输入固定为 garbage station waypoint 或 fixed route。
4. 将验证拆成三层：本地 Python/static smoke、Docker Humble ROS2 build、上车 HIL。

## 模块拆解

### 硬件桥

Owner: `p8-hardware-lead`

范围：
- 审查 `ros2_trashbot_hardware` 是否仍与 WAVE ROVER UART newline-delimited JSON 一致。
- 保持 serial port、baudrate、command mode、max speed 等参数可配置。
- 明确 `T=1` 与 `T=13` 的使用边界：`T=13` 只有上车验证后才能作为默认路径。
- `T=1001` 反馈解析、IMU/电池/odom 来源必须区分“已测”和“待测”。

验证：
- `src/ros2_trashbot_hardware/test/test_waveshare_json_bridge.py`
- HIL 待验证记录：串口设备、波特率、停止命令、反馈流、异常断线停车。

### 行为层

Owner: `p8-behavior-lead`

范围：
- 送垃圾状态机：`IDLE -> LOADED -> DELIVERING -> DROPOFF -> RETURNING -> IDLE/ERROR`。
- 装载确认支持手机按钮/语音/本地参数模拟；不强依赖未验证传感器。
- action result 必须包含 success、error_code、error_message、final_state。
- 取消、超时、导航失败、找不到目标点必须进入明确失败路径。
- 每次任务写任务记录，至少包含起止时间、目标、状态转移、失败原因、导航结果、证据引用。

验证：
- `src/ros2_trashbot_behavior/test/test_delivery_state_machine.py`
- `src/ros2_trashbot_behavior/test/test_delivery_navigation.py`
- `src/ros2_trashbot_behavior/test/test_task_record.py`

### 导航与固定路线

Owner: `p8-nav-lead`

范围：
- fixed route / Nav2 waypoint 都必须能作为 delivery mission 的目标输入。
- route CSV/YAML 格式与 debug 状态输出保持文档一致。
- dry-run 不依赖硬件和 Nav2，用于验证路线读取、关键帧匹配和状态输出。

验证：
- `src/ros2_trashbot_nav/test/test_route_csv_to_yaml.py`
- `src/ros2_trashbot_nav/test/test_fixed_route_dry_run_offline.py`
- `src/ros2_trashbot_nav/test/test_fixed_route_status_static.py`

### 接口契约

Owner: `p8-interfaces-contract-lead`

范围：
- 检查 `TrashCollection.action`、`Patrol.action`、`TaskResult.msg`、`TrashStatus.msg` 是否足够表达本轮任务。
- 如果接口不够，优先做兼容扩展，避免破坏已有消费者。
- 明确状态字段给手机端和 debug web 消费。

验证：
- interface static tests。
- producer/consumer matrix 写入 `side2side_check.md`。

### Bringup 与验证环境

Owner: `p8-bringup-integration-lead`

范围：
- `learn.launch.py` 和 `autonomous.launch.py` 参数边界保持清晰。
- 不为 ROS2 Humble 强改本机 Ubuntu-24.04。
- ROS2 构建优先 Docker Humble。

验证：
- `src/ros2_trashbot_bringup/test/test_launch_contract_static.py`
- Docker Humble build，如环境可用。

### 视觉与产品边界

Owner: `p8-vision-lead` + `p9-product-reviewer`

范围：
- 视觉不作为送达成功前提。
- 保留站点识别、异常记录、样本沉淀方向。
- 手机端只定义最小状态和异常接管流程，不做完整 UI。

验证：
- `src/ros2_trashbot_vision/test/test_trash_detector_static.py`
- `docs/product/mobile_user_flow.md` 对照。

## 执行顺序

1. P7 test 先跑 `scripts/run_smoke_tests.sh` 建立基线。
2. P7 implementation 只在 P0 范围内做窄改。
3. 每个模块改动后跑对应 package unittest。
4. P7 reviewer 做代码和接口审查。
5. P7 hardware audit 做 vendor 来源审查。
6. P7 docs acceptance 更新 `tech-done.md`、`side2side_check.md`、`final.md`。

## 测试矩阵

| 层级 | 命令 | 说明 |
| --- | --- | --- |
| 本地 smoke | `scripts/run_smoke_tests.sh` | compileall + package unittest |
| 本地 + Docker gate | `ROBOT_DAILY_DOCKER_BUILD=1 bash scripts/run_smoke_tests.sh` | 本地 smoke 后追加 Docker Humble build |
| 单包测试 | `python3 -m unittest discover -s src/<package>/test -p "test*.py"` | P0 改动后快速回归 |
| ROS2 build | Docker Humble 中 `colcon build --symlink-install` | 目标构建验证 |
| HIL 基础 | `python3 scripts/hardware_smoke_wave_rover.py --serial-port <confirmed-orange-pi-uart> --baudrate 115200` | 串口、反馈、停止路径上车验证 |
| HIL 运动 | `python3 scripts/hardware_smoke_wave_rover.py --serial-port <confirmed-orange-pi-uart> --baudrate 115200 --move-test --reverse-test --turn-test` | 低速方向、转向、最终停车；必须架空或安全场地 |
| 行为 dry-run | `ros2 launch ros2_trashbot_bringup autonomous.launch.py delivery_mode:=dry_run delivery_target:=trash_station` | 验证 delivery 入口和 dry-run 契约 |
| 导航 dry-run | `ros2 run ros2_trashbot_nav fixed_route_autonomy --ros-args -p route_file:=<route.csv-or-yaml> -p dry_run:=true` | 验证固定路线解析和状态输出 |

## 证据字段

每条验证记录至少保留：

- date/time
- operator
- branch/commit
- dirty status
- command
- exit code
- log path
- package test counts
- skipped packages
- Docker image/tag and ROS distro when applicable
- map/route files and launch parameters when applicable
- vendor files cited for hardware claims
- serial port, baudrate, feedback interval, command mode for HIL
- `T=1001` sample, `/battery`, `/imu/data`, `/odom` sample for HIL
- task record JSON path and route debug status path
- photos/video for movement direction when running motion HIL
- P0/P1 failures, owner, retest result

## 回滚策略

- 行为层：保留旧入口，但不得把旧 demo 路径写成完成状态。
- 硬件桥：未验证参数保持可配置，不修改 factory firmware。
- 导航：dry-run 与真实 Nav2 路径分开，失败时保留 route 文件和状态输出。
- 文档：所有未验证项标为待验证，不降级成已完成。
