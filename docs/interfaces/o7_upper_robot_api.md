# O7 Upper Robot API

## 目标

上位机统一 API 解决 PC 端分散连接问题。PC 只配置一个 base URL：

```text
http://192.168.1.11:8787
```

8787 统一承接 camera、radar、map/localize、base 四类入口：

- camera：代理本机 8088 WebRTC camera smoke。
- radar：返回 `/dev/ttyACM0 @150000` 雷达设备、启动/停止字节、ROS2 `/scan` 证明状态，并提供 LiDAR/ROS2 driver 一键 start/stop HTTP 合同。
- map/localize：提供建图 start/reset/save/load/list 与定位 reset HTTP 合同；默认 fail-closed，不证明真实 SLAM、真实地图或 AMCL 定位已完成。
- nav2/elevator：提供 Nav2 lifecycle 与电梯 evidence/status 只读边界；默认只消费 artifact 或显式配置命令，不证明真实路径执行、OpenCV 电梯识别或跨楼层送达。
- base：返回 `/dev/ttyS5` 底盘写入口状态，并提供低速点动/停车 API。

## Vendor 来源

已采用本地资料：

- `docs/vendor/VENDOR_INDEX.md`
  - WAVE ROVER 上下位机为 UART JSON 一行一包。
  - Orange Pi 真实串口路径必须现场确认，不能沿用 Raspberry Pi 默认。
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
  - `base_speed_ctrl()` 使用 `{"T":1,"L":...,"R":...}` 写左右轮速度。
  - vendor 参考 baudrate 为 `115200`。
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
  - `T=1` 为底盘速度控制命令。
  - `T=130` 为底盘反馈请求，预期反馈应出现 `T=1001`。
- `docs/vendor/lidar_pkg_ros2-main/src/lidar_node.cpp`
  - ROS2/STC 参考 driver 打开串口 `150000`，启动时发送 `A5 60`，退出时发送 `A5 00 A5 65 A5 65`。
- `docs/vendor/lidar_pkg_ros2-main/scripts/99-lidar.rules`
  - STC `idVendor=34bf`、`idProduct=ff0a` 可映射为 `/dev/lidar`；当前现场设备节点先按 `/dev/ttyACM0` 记录。

## 服务

脚本：

- `onboard/scripts/upper_robot_api.py`
- `onboard/scripts/upper_robot_api.sh`
- `onboard/scripts/install_upper_robot_api_service.sh`

systemd：

- `onboard/systemd/trashbot-upper-robot-api.service`
- unit name：`trashbot-upper-robot-api.service`
- 默认端口：`8787`
- 默认 camera 子服务：`http://127.0.0.1:8088`
- 默认 base 串口：`/dev/ttyS5 @115200`

安装：

```bash
cd /root/rober
bash onboard/scripts/install_upper_robot_api_service.sh --dry-run --repo-root /root/rober
bash onboard/scripts/install_upper_robot_api_service.sh --repo-root /root/rober
```

## Endpoints

| Method | Path | 说明 |
| --- | --- | --- |
| `GET` | `/health` | 统一 API 进程健康 |
| `GET` | `/api/status` | camera/radar/base 总览；`base.feedback_samples_latest` 只读摘要 latest feedback samples artifact |
| `GET` | `/api/camera/health` | 代理 8088 `/health` |
| `GET` | `/api/camera/devices` | 代理 8088 `/devices` |
| `POST` | `/api/camera/offer` | 代理 8088 `/offer`，只用于 recvonly WebRTC 视频 |
| `POST` | `/api/camera/peers/{peer_id}/close` | 代理 8088 peer cleanup |
| `GET` | `/api/radar/status` | 雷达设备和 `/scan` 证明状态 |
| `POST` | `/api/radar/start` | 雷达一键启动合同；默认 dry-run/stub，只能配置 LiDAR/ROS2 driver 命令，不触碰 `/dev/ttyS5` 或底盘运动命令 |
| `POST` | `/api/radar/stop` | 雷达一键停止合同；默认 dry-run/stub，只能配置 LiDAR/ROS2 driver 停止命令，不触碰 `/dev/ttyS5` 或底盘运动命令 |
| `POST` | `/api/radar/scan-proof/refresh` | 只读刷新 LiDAR `/scan` proof artifact；只运行 collector 读取既有 ROS2 topic，不启动 driver、不打开串口、不发送运动命令 |
| `GET` | `/api/radar/scan-proof/latest` | 只读回放最近一次 LiDAR `/scan` proof artifact；不启动 ROS2、不打开串口、不发送 `A5 60` |
| `GET` | `/api/radar/raw-packet-proof/latest` | 只读回放最近一次 LiDAR raw packet proof artifact；不执行 collector、不启动 ROS2、不打开串口、不发送 `A5 60` 或底盘命令 |
| `POST` | `/api/map/start` | 建图 lifecycle start 合同；默认 dry-run/stub，返回 `not_proven` 与 artifact 入口 |
| `POST` | `/api/map/reset` | 建图 reset 合同；默认 dry-run/stub，返回 `not_proven` 与 artifact 入口 |
| `POST` | `/api/map/save` | 地图 save 合同；默认 dry-run/stub，保留 `map_name`/`artifact_path` 回显，不证明地图已保存 |
| `POST` | `/api/map/load` | 地图 load 合同；默认 dry-run/stub，不证明 map server/Nav2 已消费地图 |
| `GET` | `/api/map/list` | 只读列出 `ROBER_MAP_ARTIFACT_DIR` 下 `*.yaml/*.pgm/*.pbstream` 候选文件；文件存在不等于地图质量验收 |
| `GET` | `/api/map/proof/latest` | 只读回放最近一次 SLAM/map lifecycle runtime artifact；不启动 SLAM、不调用保存服务 |
| `POST` | `/api/localize/reset` | 定位 reset 合同；默认 dry-run/stub，预留 `/initialpose`/AMCL 入口，不证明定位恢复 |
| `GET` | `/api/localize/proof/latest` | 只读回放最近一次 AMCL/TF/pose freshness artifact；不发布 `/initialpose` |
| `GET` | `/api/nav2/status` | 只读回放 Nav2 lifecycle artifact 和 start/stop 配置；不探 ROS graph |
| `POST` | `/api/nav2/start` | Nav2 lifecycle start 合同；默认 dry-run/stub，显式配置后仍需 artifact 证明 |
| `POST` | `/api/nav2/stop` | Nav2 lifecycle stop 合同；默认 dry-run/stub，不触碰底盘串口 |
| `GET` | `/api/elevator/status` | 只读回放 OpenCV/电梯状态链 evidence artifact；不证明真实电梯识别或送达 |
| `POST` | `/api/operator/report` | 写入 PC/operator 人工现场报告 latest artifact；只作为 evidence/readback，不替代 stop/status/ACK/T=1001/HIL |
| `GET` | `/api/operator/report` | 只读回放最近一次 operator report artifact；缺失返回 `404`，坏 JSON 返回 `422` |
| `GET` | `/api/base/status` | `/dev/ttyS5`、pyserial、反馈/ACK 状态；只读摘要 latest feedback samples artifact |
| `POST` | `/api/base/stop` | 发送 `{"T":1,"L":0,"R":0}` 停车 |
| `POST` | `/api/base/feedback-request` | 发送一次非运动 `{"T":130}` 反馈请求并短窗口读取 JSON |
| `POST` | `/api/base/feedback-samples` | 重复发送非运动 `{"T":130}`，采集多样本 `T=1001` evidence |
| `GET` | `/api/base/feedback-samples/latest` | 只读回放最近一次 feedback samples JSON artifact；不打开串口、不发送命令 |
| `POST` | `/api/base/manual` | 低速方向点动，自动停车 |

## Operator report evidence contract

`/api/operator/report` 是 O7 PC/operator workflow 的人工材料入口，当前合同优先解决真实
8787 对 PC 同源代理 POST 返回 `405 Method Not Allowed` 的阻断。它只负责把 operator 当前
`evidence_ref`、备注和现场安全/观察字段写入 latest JSON artifact，默认路径：

```text
runtime/operator_report_latest.json
```

可配置：

| env / CLI | 用途 |
| --- | --- |
| `ROBER_OPERATOR_REPORT_ARTIFACT_PATH` / `--operator-report-artifact-path` | operator report latest artifact，默认 `runtime/operator_report_latest.json` |

POST 示例：

```json
{
  "evidence_ref": "operator_field_report_pending",
  "note": "not_proven: waiting for field evidence",
  "operator_present": true,
  "physical_clearance_confirmed": true,
  "emergency_stop_ready": true
}
```

状态语义沿用 O1 safe pulse runner 的两阶段报告合同：

- preflight 三项 `operator_present`、`physical_clearance_confirmed`、`emergency_stop_ready`
  均为 true 时，`operator_report_status="ready_for_execution"`。
- preflight 三项为 true，且 `observed_motion`、`observed_stop`、`operator_notes`、`reported_at`
  都完整时，`operator_report_status="ready_for_review"`。
- 缺失、false 或无法解析的字段保持 `unsafe_or_incomplete`；GET artifact 缺失返回 `404`，
  坏 JSON 或非 object 返回 `422`。

安全边界：

- POST 的唯一副作用是原子写 `ROBER_OPERATOR_REPORT_ARTIFACT_PATH` 指向的 JSON 文件。
- GET 只做 `Path.read_text()` 和 `json.loads()` readback。
- 不调用 `/api/base/manual`、`/api/base/stop`、`/api/base/status` 或 feedback endpoints。
- 不打开 `/dev/ttyS5`，不发送 `T=1/T=13/T=130/T=131`，不发布 `/cmd_vel`，不启动 ROS2。
- 响应固定保留 `safe_to_control=false`、`robot_control_executed=false`、`hil_pass=false`、
  `delivery_success=false`、`primary_actions_enabled=false`。
- operator report 只是人工现场材料，不能替代 stop response、post-status、`T=1001`
  vendor material、robot ACK、真实 HIL、ROS `/odom`/`/imu/data`/`/battery` 或视频/现场记录。

## Base 控制安全边界

`/api/base/manual` 接收：

```json
{"direction":"forward","speed":0.08,"duration_ms":260}
```

规则：

- `direction` 只允许 `forward/back/left/right/stop`。
- `speed` 会被限制到 `ROBER_BASE_MAX_SPEED`，默认 `0.12`。
- `duration_ms` 会被限制到 `800ms` 以内。
- 每次方向命令后都会自动发送 `{"T":1,"L":0,"R":0}`。
- 当方向写入和 auto-stop 写入都成功后，`/api/base/manual` 会在 stop 之后通过同一
  `base_port/base_baudrate` 发送一次 vendor `{"T":130}`，短窗口读取 `T=1001`，并把结果放入
  `feedback_ack`、`t1001_feedback_status` 和 `feedback_evidence`。
- `feedback_ack.robot_ack_connected`、`safe_to_control` 和 `hil_pass` 仍固定为 `false`。
  `T=1001` 只代表 vendor feedback material，不代表项目 robot ACK、HIL pass 或闭环安全控制。

因此，8787 只能声明“低速点动写入口可用”，不能声明“闭环安全控制完成”。

### Manual left/right vendor mapping

本轮按本地 vendor 资料复核 `/api/base/manual` 的 `left/right` 映射，没有发现 onboard 映射反向问题：

- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py` 的 `base_speed_ctrl(input_left, input_right)` 直接发送 `{"T":1,"L":input_left,"R":input_right}`。
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h` 在 `CMD_SPEED_CTRL` 下把 JSON `L/R` 传给 `setGoalSpeed(L,R)`。
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h` 注释写明 `A-left, B-right`，且 `setGoalSpeed()` 将左输入送入 `setpointA/leftCtrl()`、右输入送入 `setpointB/rightCtrl()`。
- `docs/vendor/waveshare_wave_rover/ugv_rpi/templates/control.js` 的官方 Web 控制同样使用纯左转 `L=-max_speed,R=+max_speed`、纯右转 `L=+max_speed,R=-max_speed`。

所以当前差速点动方向语义为：

| manual direction | vendor `T=1` wheel command | 含义 |
| --- | --- | --- |
| `forward` | `{"T":1,"L":+speed,"R":+speed}` | 左右轮同向前进 |
| `back` | `{"T":1,"L":-speed,"R":-speed}` | 左右轮同向后退 |
| `left` | `{"T":1,"L":-speed,"R":+speed}` | 左轮后退、右轮前进，原地左转 |
| `right` | `{"T":1,"L":+speed,"R":-speed}` | 左轮前进、右轮后退，原地右转 |
| `stop` | `{"T":1,"L":0,"R":0}` | 停车 |

`T=130/T=1001` 语义也按 vendor 边界处理：`json_cmd.h` 定义 `CMD_BASE_FEEDBACK=130`、`FEEDBACK_BASE_INFO=1001`；`uart_ctrl.h` 收到 `T=130` 后调用 `baseInfoFeedback()`；`ugv_advance.h` 的 `baseInfoFeedback()` 输出 `T=1001`，字段包含 `L/R` 轮速、`r/p/y` IMU 姿态和 `v` 电源电压。它能作为 vendor feedback material，不能单独证明手控闭环、安全准入、ROS `/odom` 或 HIL pass。

如果现场反馈“左右转还不行”，优先按 `docs/hardware/o1_base_manual_turn_smoke.md` 做低速短 pulse 复核：净空、急停、左右轮物理方向、auto-stop 和 stop 后 `T=130 -> T=1001` 回读必须同场记录。

### 2026-06-03 硬件安全收口

本轮只收口 8787 API 的硬件/API 安全语义，不新增真实上车材料：

- `direction` 非 `forward/back/left/right/stop` 时返回结构化失败，不写串口，不应由 aiohttp 冒泡为 500。
- `speed` 强制取绝对值并限制到 `ROBER_BASE_MAX_SPEED`，默认 `0.12`；`duration_ms` 强制限制到 `800ms`。
- 每次 accepted manual pulse 都先写 vendor `{"T":1,"L":...,"R":...}\n`，短窗口后再写 `{"T":1,"L":0,"R":0}\n`。
- 响应保留 `command_result`、`stop_result`、`serial_write_failures`、`manual_command_executed`、`auto_stop_attempted`、`auto_stop_executed`。
- `/api/base/stop` 的 `robot_control_executed` 只跟随 stop JSON 写入结果；pyserial 缺失、串口打开失败或写失败时必须为 `false`。
- `/api/base/manual` 的反馈证据链严格排在 auto-stop 之后：方向 `T=1` 写入成功、停车 `T=1,L=0,R=0`
  写入成功后，才用同一串口配置发送 `T=130` 并短窗口读取 `T=1001`。
- 若方向写入或 stop 写入失败，`manual` 响应保留 `command_result`、`stop_result` 和
  `serial_write_failures`，`feedback_after_stop_attempted=false`，
  `t1001_feedback_status="skipped_due_to_manual_write_failure"`，不会把失败包装成成功。
- `manual` 响应里的 `feedback_ack.t1001_observed=true` 只说明 stop 后的显式 `T=130` 读取到了
  vendor `T=1001` 材料；`robot_ack_connected=false`、`safe_to_control=false`、`hil_pass=false`
  不变，不能把 `T=1` 写入成功或 `T=1001` 材料当成 ACK/HIL。
- `/api/base/feedback-request` 是非运动请求入口，只允许发送一次 vendor `{"T":130}` 并读取短窗口反馈；HTTP 200、写入成功或坏帧计数都不能外推为真实 ACK/HIL。
- `/api/base/feedback-samples` 是非运动多样本 evidence collector，只重复同一条 `T=130` 路径并聚合每个 sample 的 `T=1001` 观察状态；它不调用 `/api/base/manual`，不发送 `T=1/T=13/T=131` 或 `/cmd_vel`。
- `/api/base/feedback-samples/latest` 只读取 `ROBER_BASE_FEEDBACK_SAMPLES_ARTIFACT_PATH` / `--feedback-samples-artifact-path` 指向的 JSON artifact，默认 `runtime/base_feedback_samples_latest.json`；artifact 不存在或坏 JSON 时 fail-closed，不打开串口、不发送 `T=130` 或任何运动命令。
- `/api/base/status` 和统一 `/api/status` 的 `base.feedback_samples_latest` 只做 latest artifact `stat/read_text/json.loads` 摘要，默认 15 分钟新鲜度窗口；该 freshness 只是材料文件新鲜度，不是 HIL、ACK、`safe_to_control` 或可运动准入。

本轮单元测试只使用 fake pyserial/mock 串口，不打开真实 `/dev/ttyS5`，不 SSH，不发送真实 WAVE ROVER JSON、`cmd_vel` 或运动命令。

## Radar / LiDAR ROS2 接入

`/api/radar/status` 不打开雷达串口，只返回 PC 可消费的上位机事实和 ROS2 下一步命令。当前现场确认：

- 雷达设备：`/dev/ttyACM0`
- 波特率：`150000`
- 启动命令：`A5 60`
- 停止序列：`A5 00 A5 65 A5 65`
- ROS2 driver：`ros2_trashbot_hardware lidar_driver`
- 目标 topic：`/scan`
- 原始 packet topic：`/lidar/raw_packet`
- frame：`laser_frame`

上位机预检：

```bash
modprobe ch341
modprobe cp210x
modprobe ftdi_sio
modprobe pl2303
modprobe cdc_acm
ls -l /dev/ttyACM0 /dev/lidar 2>/dev/null || true
```

ROS2 启动入口：

```bash
source /opt/ros/humble/setup.bash
source /root/rober/onboard/install/setup.bash
ros2 launch ros2_trashbot_bringup learn.launch.py \
  lidar_enabled:=true \
  lidar_serial_port:=/dev/ttyACM0 \
  lidar_serial_baudrate:=150000 \
  lidar_publish_raw_packets:=true
```

8787 返回 `scan_status="not_proven"` 是刻意保留的验收边界：只有后续分别采到
`ros2 topic echo --once /scan`、`ros2 topic hz /scan`、`ros2 topic echo --once /lidar/raw_packet`
和 `tf2_echo base_link laser_frame` 后，才能把雷达材料从设备已识别提升为 ROS2
runtime proof。PC 的“实时雷达 ready”只能认 `/scan` once + `/scan` hz；raw packet 与 TF 是
工程诊断/坐标链材料，不能单独替代 `/scan` ready。

### LiDAR scan proof artifact readback

`GET /api/radar/scan-proof/latest` 读取
`ROBER_LIDAR_SCAN_PROOF_ARTIFACT_PATH` / `--lidar-scan-proof-artifact-path`
指向的 JSON，默认 `runtime/lidar_scan_proof_latest.json`。该 artifact 应由
`onboard/scripts/o1_lidar_scan_proof_collector.py` 生成。

`POST /api/radar/scan-proof/refresh` 是 O3/O7 的只读刷新入口。它默认用当前
Python 解释器执行同目录 `onboard/scripts/o1_lidar_scan_proof_collector.py`：

```bash
python3 onboard/scripts/o1_lidar_scan_proof_collector.py \
  --once-json \
  --expect-existing-topics \
  --output runtime/lidar_scan_proof_latest.json \
  --upper-api-base-url http://127.0.0.1:8787
```

refresh 入口的唯一目标是把“当前已有 ROS2 graph 是否能读到 `/scan`、`/scan` hz、
`/lidar/raw_packet` 和 `base_link -> laser_frame` TF”刷新成 latest artifact。它不会启动
LiDAR driver，不会打开 `/dev/ttyACM0` 或 `/dev/lidar`，不会发送 vendor `A5 60`
启动字节，也不会触碰 `/dev/ttyS5`、`T=1/T=13/T=130/T=131`、`/api/base/manual`
或 `/cmd_vel`。

refresh 响应固定包含：

- `command_result`：collector 子进程执行结果；脚本缺失时为
  `reason="collector_script_missing"`，用于定位部署 blocker。
- `artifact_path` / `artifact`：latest artifact 路径和 schema。
- `proof_summary`：collector 的 `/scan` once、hz、raw packet、TF 摘要。
- `blockers_summary`：ROS2 setup/install、topic 未观察、artifact 写入失败或 collector
  JSON parse 失败等 blocker。
- `safe_to_control=false`、`sends_commands=false`、`sends_motion_commands=false`、
  `robot_control_executed=false`、`opens_lidar_serial=false`、`starts_lidar_driver=false`。

实现上 refresh handler 会在线程里运行 collector 子进程，避免 collector 反查本机
`/health`、`/api/radar/status` 时被当前 aiohttp request handler 阻塞。若 live 上位机没有同步
collector 脚本，或者 8787 重启方式不明确，必须把结果写成部署 blocker，不能把本地单测写成
fresh runtime material。

readback 边界：

- 只做 `Path.read_text()` 和 `json.loads()`。
- artifact 缺失返回 `404`，坏 JSON 返回 `422`。
- 不启动 ROS2 LiDAR driver。
- 不打开 `/dev/ttyACM0`、`/dev/lidar` 或 `/dev/ttyS5`。
- 不发送 `A5 60`、`T=1/T=13/T=130/T=131` 或 `/cmd_vel`。
- 固定 `safe_to_control=false`、`sends_commands=false`、`sends_motion_commands=false`、`robot_control_executed=false`、`hil_pass=false`。

`o1_lidar_scan_proof_collector.py --expect-existing-topics` 仍然只读 ROS2 graph：

- 不启动 `ros2_trashbot_hardware lidar_driver`。
- 不打开 `/dev/ttyACM0`、`/dev/lidar` 或 `/dev/ttyS5`。
- 不发送 LiDAR `A5 60` start bytes。
- 不发送 WAVE ROVER `T=1/T=13/T=130/T=131`，不发布 `/cmd_vel`。
- 四个观测命令并发执行，artifact 中 `topic_reads.mode` 为
  `parallel_topic_and_tf_observation`。这样做是为了配合 API-managed LiDAR-only
  runtime 的短生命周期窗口，避免串行先读 `/scan` once 和 raw packet 后，`scan_hz` 或
  TF 已错过 driver/static TF 窗口。
- 如果 direct topic/TF proof 四项全部通过，collector 会把旧的
  `upper_api_scan_not_proven` 状态摘要 blocker 清掉；如果只观察到部分字段，该 blocker
  仍保留，用于提示 8787 常态 radar status 还未升级为 continuous scan ready。
- API-managed runtime 场景下，如果 collector 子进程错过短窗口，但同轮
  `o1_lidar_ros2_scan_smoke.sh` 的 `summary.json` 已经证明 `scan_once`、`scan_hz`、
  `raw_packet_once` 和 `tf` 四项全量 observed，8787 会把该 summary 作为
  `runtime_summary_fallback` 写回 latest artifact。artifact 会标注
  `proof.runtime_summary_fallback_used=true` 和每个 observation 的
  `source="api_managed_lidar_runtime_summary"`，避免把 fallback 误读成 collector 直接观测。

collector artifact 的 `proof.required_observations` 必须独立包含四个 key：

| key | 证明对象 | ready 作用 |
| --- | --- | --- |
| `scan_once` | `ros2 topic echo --once /scan` | 证明 `/scan` 至少有一帧 LaserScan |
| `scan_hz` | `ros2 topic hz /scan` | 证明 `/scan` 有连续频率输出，可供 PC 判断实时雷达 |
| `raw_packet_once` | `ros2 topic echo --once /lidar/raw_packet` | 证明 driver 发布原始包，只作为工程诊断 |
| `tf` | `tf2_echo base_link laser_frame` | 证明 base 到 LiDAR frame 的 TF 链，只作为坐标链诊断 |

顶层 `proof` 同步保留机器可读摘要字段：

- `scan_once_observed`
- `scan_hz_observed`
- `scan_hz_average_rate_hz`
- `raw_packet_once_observed`
- `tf_observed`
- `all_required_observations_observed`

`o1_lidar_ros2_scan_smoke.sh` 是 LiDAR-only runtime smoke，允许启动 LiDAR driver 和静态 TF，
因此会在 driver 内发送 LiDAR `A5 60` start bytes；它必须拒绝 `/dev/ttyS5`，并继续固定
`safe_to_control=false`、`sends_base_motion_commands=false`、`calls_base_manual=false`、
`publishes_cmd_vel=false`。它的 `summary.json` 使用同一套 `required_observations`
四项字段，便于 PC 或人工脚本按 `/scan` once、`/scan` hz、raw packet once、TF 分开判读。

`GET /api/radar/status` 的 `scan_proof_latest` 暴露 latest proof artifact 的 compact
摘要，包括 `artifact.status`、`latest_proof_status`、`latest_scan_once_observed`、
`latest_scan_hz_observed`、`latest_scan_hz_average_rate_hz`、
`latest_raw_packet_once_observed`、`latest_tf_observed`、
`latest_all_required_observations_observed`、`latest_required_observations`、
`latest_runtime_summary_fallback_used` 和 `latest_runtime_summary_path`。旧 artifact
缺少 hz/TF 字段时这些新增字段保持 `null`，不能把缺省解释成 observed。

同一个 status 响应会把 latest artifact 派生成 PC 更容易消费的顶层字段：

- `scan_status="fresh_scan_proof_observed"`：只表示 latest artifact 已同时证明
  `/scan` once、`/scan` hz、`/lidar/raw_packet` once 和 TF。
- `fresh_scan_proof_observed=true|false`：缺 artifact、坏 JSON、partial proof 都必须为
  `false`。
- `latest_scan_proof_state`：直接来自 proof `status`，缺失或坏 JSON 时为 artifact
  状态，例如 `missing` 或 `bad_json`。
- `latest_scan_hz_average_rate_hz`：直接来自 latest artifact，不在 status 中重新执行
  `ros2 topic hz`。
- `runtime_summary_fallback_used`：表示 latest artifact 是否采用同轮
  `o1_lidar_ros2_scan_smoke.sh` 的 `summary.json` fallback。
- `latest_scan_proof.missing_required_observations`：partial proof 时给出缺失机器项，
  例如 `scan_hz`、`tf` 或 `all_required_observations`；`failure_reason` 同步使用
  `latest_scan_proof_required_observations_missing:<comma-list>`。
- `continuous_scan_status="not_proven"` 与 `continuous_blocked_reasons`：保留常态连续
  雷达未证明的边界，避免把一次 fresh proof 外推成长稳 radar ready。
- `latest_scan_proof`：包含 artifact 状态、四项 observed 字段、fallback 来源、fail-closed
  `failure_reason` 和固定安全假值。

PC 主状态灯如果要区分 O9 fresh proof，可读取 `fresh_scan_proof_observed` 和
`latest_scan_hz_average_rate_hz`；如果要宣称连续雷达 ready，必须另看
`continuous_scan_status`，当前仍固定 `not_proven`。raw packet 与 TF 只作为工程诊断和坐标链
proof；该摘要只代表最近 artifact 的读取状态，不证明当前 ROS2 `/scan` 正在连续输出。

### Radar start/stop HTTP contract

`POST /api/radar/start` 和 `POST /api/radar/stop` 是给 PC 工作站的一键入口。本轮只实现
software-guarded HTTP 合同，默认不启动真实 ROS2、不打开 LiDAR 串口、不发送 `A5 60`，
更不会触碰底盘 `/dev/ttyS5` 或发送 WAVE ROVER `T=1` 运动命令。

可配置环境变量：

| env / CLI | 用途 |
| --- | --- |
| `ROBER_RADAR_START_COMMAND` / `--radar-start-command` | 显式配置 LiDAR/ROS2 driver start 命令 |
| `ROBER_RADAR_STOP_COMMAND` / `--radar-stop-command` | 显式配置 LiDAR/ROS2 driver stop 命令 |
| `ROBER_LIDAR_SCAN_PROOF_ARTIFACT_PATH` / `--lidar-scan-proof-artifact-path` | `/scan` proof latest artifact 路径 |

响应固定包含：

- `status="not_proven"`、`software_guard=true`、`not_proven=true`。
- `safe_to_control=false`、`robot_control_executed=false`、`sends_base_motion_commands=false`。
- `blocked_devices_not_touched` 包含 `/dev/ttyS5`，`blocked_commands_not_sent` 包含 `T=1`、`/cmd_vel`、`/api/base/manual`。
- `command_result.mode="dry_run_stub"` 表示命令未配置；即使命令配置并返回 0，也只表示 start/stop 命令进程执行过，不证明 `/scan` runtime ready。

从 `not_proven` 转正必须另有 runtime evidence：`ros2 topic echo --once /scan`、
`ros2 topic hz /scan`，并写入 `lidar_scan_proof_latest_artifact.path`。

## Map / Localization lifecycle contract

Map/localize 入口服务 O3/O7 的 PC 工作站按钮合同，不让浏览器直连 ROS graph。默认行为是
fail-closed dry-run/stub，只返回可读状态和 artifact path。

可配置环境变量：

| env / CLI | 用途 |
| --- | --- |
| `ROBER_MAP_ARTIFACT_DIR` / `--map-artifact-dir` | 地图 artifact 目录，默认 `runtime/maps` |
| `ROBER_MAP_LIFECYCLE_PROOF_ARTIFACT_PATH` / `--map-lifecycle-proof-artifact-path` | SLAM/map lifecycle latest proof，默认 `runtime/map_lifecycle_latest.json` |
| `ROBER_LOCALIZATION_ARTIFACT_PATH` / `--localization-artifact-path` | 定位 reset latest artifact，默认 `runtime/localization_reset_latest.json` |
| `ROBER_MAP_START_COMMAND` / `--map-start-command` | 显式配置 SLAM/map start 命令 |
| `ROBER_MAP_RESET_COMMAND` / `--map-reset-command` | 显式配置 map reset 命令 |
| `ROBER_MAP_SAVE_COMMAND` / `--map-save-command` | 显式配置 map save 命令 |
| `ROBER_MAP_LOAD_COMMAND` / `--map-load-command` | 显式配置 map load 命令 |
| `ROBER_LOCALIZE_RESET_COMMAND` / `--localize-reset-command` | 显式配置 AMCL `/initialpose` 或定位 reset 命令 |
| `ROBER_NAV2_LIFECYCLE_ARTIFACT_PATH` / `--nav2-lifecycle-artifact-path` | Nav2 lifecycle latest proof，默认 `runtime/nav2_lifecycle_latest.json` |
| `ROBER_NAV2_START_COMMAND` / `--nav2-start-command` | 显式配置 Nav2/lifecycle start 命令 |
| `ROBER_NAV2_STOP_COMMAND` / `--nav2-stop-command` | 显式配置 Nav2/lifecycle stop 命令 |
| `ROBER_ELEVATOR_STATUS_ARTIFACT_PATH` / `--elevator-status-artifact-path` | OpenCV/电梯状态链 latest evidence，默认 `runtime/elevator_status_latest.json` |
| `ROBER_OPERATOR_REPORT_ARTIFACT_PATH` / `--operator-report-artifact-path` | PC/operator latest report evidence，默认 `runtime/operator_report_latest.json` |

`POST /api/map/save` 和 `POST /api/map/load` 可接收上层 body，例如：

```json
{"map_name":"lab","artifact_path":"runtime/maps/lab.yaml"}
```

`POST /api/localize/reset` 可接收上层 pose body，例如：

```json
{"pose":{"x":1.0,"y":2.0,"yaw":0.0}}
```

这些 body 目前只回显给 PC/operator workflow；默认不会发布 ROS2 topic/service。每个响应固定保留：

- `status="not_proven"`、`software_guard=true`、`not_proven=true`。
- `map_artifact_proven=false`、`localization_proven=false`、`ros2_runtime_proven=false`。
- `safe_to_control=false`、`robot_control_executed=false`、`sends_base_motion_commands=false`、`uses_base_uart=false`。
- `artifact.path` 指向 map/localization 材料入口。

转正条件必须另行提供 ROS2 runtime 材料：`/map` once、地图 YAML/image 或 pbstream artifact、
load 后 AMCL `/amcl_pose`、TF freshness、pose timestamp freshness。仅有 HTTP 200、dry-run、
fixture、文件候选或命令 returncode 0，均不得宣称真实 SLAM、真实地图保存/加载或真实定位恢复。

新增只读 proof 入口：

- `GET /api/map/proof/latest` 读取 `ROBER_MAP_LIFECYCLE_PROOF_ARTIFACT_PATH`，压缩暴露
  `latest_map_once_observed`、`latest_map_file_observed`、`latest_map_metadata_observed` 和
  `latest_slam_toolbox_state`。
- `GET /api/localize/proof/latest` 读取 `ROBER_LOCALIZATION_ARTIFACT_PATH`，压缩暴露
  `latest_initialpose_published`、`latest_amcl_pose_observed`、`latest_tf_fresh` 和
  `latest_pose_fresh`。

这些 readback 入口统一 fail-closed：artifact 缺失返回 `404`/`artifact.status="missing"`，
坏 JSON 或 JSON root 非 object 返回 `422`/`artifact.status="bad_json|json_not_object"`，
文件读取失败返回 `500`/`artifact.status="read_failed"`。无论 artifact 是否成功读取，
响应都固定 `status="not_proven"`、`software_guard=true`、`readback_sends_commands=false`、
`sends_commands=false`、`starts_ros2=false`、`safe_to_control=false` 和
`robot_control_executed=false`。这层只回放 evidence，不启动 SLAM、不调用 save/load service，
不发布 `/initialpose`，也不触碰 `/dev/ttyS5`、`/cmd_vel` 或任何 WAVE ROVER 命令。

Nav2 lifecycle 入口：

- `GET /api/nav2/status` 读取 `ROBER_NAV2_LIFECYCLE_ARTIFACT_PATH`，压缩暴露 map server、
  AMCL、planner/controller lifecycle、`/scan`+map 消费和 path 生成状态。
- `POST /api/nav2/start|stop` 只执行显式配置的非 shell 命令；默认 dry-run/stub。命令成功只代表
  操作入口执行成功，仍固定 `status="not_proven"`，必须等 Nav2 artifact 证明 runtime。

`/api/nav2/status` 内的 `proof_latest` 使用同一套 readback 规则，并通过
`proof_latest.http_status` 暴露 `404/422/500/200`。即使命令配置存在或 artifact 中出现
`map_server_active=true`、`scan_consumed=true`，HTTP 状态仍只表示材料读取状态，不能写成
真实 Nav2 已运行、已消费 `/scan`+map 或已生成可执行路径。

电梯 evidence/status 入口：

- `GET /api/elevator/status` 读取 `ROBER_ELEVATOR_STATUS_ARTIFACT_PATH`，用于把 OpenCV
  `evidence_ref`、电梯 phase、目标楼层、安全驶出和人工接管原因回放给 PC/operator。
- artifact 存在、fixture 通过或 OpenCV baseline 输出，都不等于真实电梯识别、真实楼层确认、
  真实驶出、电梯 HIL 或 `delivery_success=true`。
- `/api/elevator/status.proof_latest` 同样只读 artifact；缺失、坏 JSON 或非 object 必须保持
  `not_proven`，并保留 `elevator_runtime_proven=false`、`delivery_success=false`、
  `primary_actions_enabled=false`。PC 只能把它展示成 operator evidence/readback，不得当成
  ROS2 状态机已完成真实电梯流程。

### LiDAR raw packet proof artifact readback

`GET /api/radar/raw-packet-proof/latest` 读取最近一次
`trashbot.o1.lidar_raw_packet_proof.v1` artifact。它的目标是把绕开 ROS2 runtime
blocker 的 raw bytes、`0xAA55` sync header、packet parse 和 point 统计材料回放给
PC/O7 operator。

raw packet proof 与 `/scan` proof 的边界：

- raw packet proof 可以证明 LiDAR 串口 raw bytes、sync header、packet parse 和 points
  material readiness。
- raw packet proof 不证明 ROS2 `LaserScan` 已发布，不证明 `/scan` hz，不证明 TF，不证明
  SLAM/Nav2 可消费。
- PC 的实时雷达状态不能把 `latest_raw_packet_once_observed=true` 或
  `latest_raw_bytes_observed=true` 当成 `/scan` ready。
- `/scan` proof 才是 PC 实时雷达的主判定来源，且应优先读取 `scan_once` 与 `scan_hz`
  两个字段。

readback 边界：

- 只做 artifact 读取、JSON 解析和摘要。
- 不执行 `onboard/scripts/o1_lidar_raw_packet_proof_collector.py`。
- 不启动 ROS2 LiDAR driver。
- 不打开 `/dev/ttyACM0`、`/dev/lidar` 或 `/dev/ttyS5`。
- 不发送 `A5 60`、停止序列、`T=1/T=13/T=130/T=131` 或 `/cmd_vel`。
- 固定 `sends_commands=false`、`sends_motion_commands=false`、
  `robot_control_executed=false`、`safe_to_control=false`、`hil_pass=false`。

`GET /api/radar/status` 与统一 `GET /api/status` 的
`radar.raw_packet_proof_latest` 摘要至少可包含：

- `endpoint="/api/radar/raw-packet-proof/latest"`
- `http_status`
- `artifact.status`
- `freshness.status`
- `artifact.age_ms` 或等价 age 字段
- `latest_proof_status`
- `latest_raw_bytes_observed`
- `latest_sync_header_observed`
- `latest_packet_parse_ok`
- `latest_points_observed`
- `latest_bytes_read`
- `latest_sync_header_count`
- `latest_packets_parse_ok`
- `latest_points_total`
- `sends_commands=false`
- `sends_motion_commands=false`
- `robot_control_executed=false`
- `safe_to_control=false`
- `hil_pass=false`

PC workstation 只消费这些摘要字段并做兼容降级；字段缺失时显示
`not_loaded` / `unknown` / `n/a`，不得因为摘要缺失导致 UI 500。

## PC 配置

PC 端优先读取：

```bash
ROBER_UPPER_API_BASE_URL=http://192.168.1.11:8787
```

如果该变量存在，PC 的 `GET /api/o7/local-webrtc-camera` 会通过统一 API 读取：

- `GET /api/camera/health`
- `GET /api/camera/devices`
- `POST /api/camera/offer`
- `POST /api/camera/peers/{peer_id}/close`

旧变量 `ROBER_LOCAL_WEBRTC_CAMERA_BASE_URL=http://192.168.1.11:8088` 仍保留为兼容 fallback。

PC workstation 还提供本机 direct upper API，详见 `docs/interfaces/o7_direct_upper_pc_api.md`：

- `GET /api/o7/direct-upper/status`
- `POST /api/o7/direct-upper/base/stop`
- `POST /api/o7/direct-upper/base/feedback-request`
- `POST /api/o7/direct-upper/base/manual`

该 direct mode 只用于 PC 本地开发/现场操作。它绕过 cloud relay 作为必需路径，但不改变生产 4G 云路线；PC 响应必须继续保留 `safe_to_control=false`、`robot_control_executed=false`、`robot_ack_connected=false`、`t1001_observed=false`，直到有同源 ACK/HIL 材料。

## 2026-06-03 实测结果

部署：

- `trashbot-upper-robot-api.service` installed and enabled。
- 远端 `0.0.0.0:8787` listening。
- 主进程：`python3 /root/rober/onboard/scripts/upper_robot_api.py ... --base-port /dev/ttyS5`。

统一状态：

- `GET http://192.168.1.11:8787/health` 返回 `status=ready`。
- `GET http://192.168.1.11:8787/api/status` 返回：
  - `camera.status=ready`
  - `radar.observed_lidar_port=/dev/ttyACM0`
  - `radar.baudrate=150000`
  - `radar.start_command_hex=a5 60`
  - `radar.scan_status=not_proven`
  - `base.port=/dev/ttyS5`
  - `base.write_control_available=true`
  - `base.feedback_ack.t1001_observed=false`
- `2026.06.03_13-14_o1-8787-feedback-deploy` 已将当前 `onboard/scripts/upper_robot_api.py` 通过 `scp` 部署到远端 `/root/rober/onboard/scripts/upper_robot_api.py`，并重启 `trashbot-upper-robot-api.service`。部署后 `POST http://192.168.1.11:8787/api/base/feedback-request` 返回 HTTP `200`，`serial_open.ok=true`、`serial_write.command={"T":130}`、`serial_write.bytes_written=10`、`read_line_count=2`、`parsed_json_count=2`、`observed_feedback_types=[130,1001]`、`t1001_feedback_status=observed`。
- `2026.06.03_14-15_o1-8787-feedback-samples` 已将新增 `/api/base/feedback-samples` 的 `onboard/scripts/upper_robot_api.py` 部署到远端并重启 `trashbot-upper-robot-api.service`。部署后 `POST http://127.0.0.1:8787/api/base/feedback-samples` 返回 HTTP `200`，`schema=trashbot.upper_robot_api.v1.base_feedback_samples_result`、`requested_sample_count=3`、`completed_sample_count=3`、`t1001_observed_count=3`、`observed_feedback_types=[130,1001]`、`all_samples_observed_t1001=true`、`partial_samples_observed_t1001=false`、`samples[].t1001_feedback_status=["observed","observed","observed"]`、`feedback_ack.t1001_observed=true`、`feedback_ack.robot_ack_connected=false`。
- 该验证只发送非运动 `T=130` feedback request；没有调用 `/api/base/manual`，没有发送 `T=1`、`T=13`、`T=131` 或 ROS `/cmd_vel`。响应仍固定 `feedback_ack.robot_ack_connected=false`、`safe_to_control=false`、`sends_motion_commands=false`、`robot_control_executed=false`、`hil_pass=false`，所以不能写成 robot ACK connected、HIL pass、闭环安全控制、真实 `/odom`、`/imu/data`、`/battery` 或 delivery success。

PC 页面验证：

- `ROBER_UPPER_API_BASE_URL=http://192.168.1.11:8787 npm run dev -- --host 127.0.0.1 --port 5173`
- 浏览器打开 `http://127.0.0.1:5173/`
- console errors：0
- `<video>` 存在
- `videoWidth=640`
- `videoHeight=480`
- `readyState=4`
- `srcObject=true`
- 页面显示 `摄像头画面已连接`
- 截图：`/tmp/rober-upper-api-camera-preview.png`

远端 peer cleanup：

- `GET http://192.168.1.11:8088/health`
- `active_peer_connections=0`
- `active_peer_ids=[]`
- `last_closed_frames_read=631`

## O1 Safe Pulse Acceptance Runner

脚本：

- `onboard/scripts/o1_ttyS5_safe_pulse_acceptance.py`

用途：

- 为 O1 现场短时点动验收生成一次性 JSON artifact。
- 默认只读 `GET /api/status`，汇总 camera/radar/base 状态、base `/dev/ttyS5`、`115200`、`T=1001`/ACK 边界和 fail-closed 安全字段。
- 只有同时传入 `--execute-motion --confirm-physical-clearance` 时才允许 POST `/api/base/manual`。
- 执行模式使用 runner 侧 `speed <= 0.08`、`duration_ms <= 350` 的更严格上限，再交给 8787 API 自身的低速/限时/auto-stop guardrail。
- 执行模式在 manual response 后会追加 POST `/api/base/stop`，记录独立 stop evidence。
- 执行模式在 manual + extra stop 后会自动再读一次 `GET /api/status`，记录 `post_status_request`、`post_status_summary` 和 `post_t1001_feedback_status`，避免只凭 manual HTTP 200 或 stop HTTP 200 判断 ACK。
- 输出 `acceptance_verdict` 作为机器可读收口字段，状态包括 `dry_run_only`、`blocked_before_motion`、`motion_posted_without_ack`、`motion_posted_with_t1001`；其中任一步失败都必须带 `failed_step` 并保持 fail-closed。
- runner 不打开串口、不绕过 8787 API、不发送 ROS `/cmd_vel`。

默认 dry-run：

```bash
python3 onboard/scripts/o1_ttyS5_safe_pulse_acceptance.py --dry-run --once-json
```

dry-run 或执行模式都可以附带 operator report：

```bash
python3 onboard/scripts/o1_ttyS5_safe_pulse_acceptance.py \
  --dry-run \
  --operator-report-json /safe/runtime/operator_report.json \
  --once-json
```

`--operator-report-json -` 可从 stdin 读取对象 JSON。runner 会归一化执行前安全字段 `operator_present`、`physical_clearance_confirmed`、`emergency_stop_ready`，以及执行后观察字段 `observed_motion`、`observed_stop`、`operator_notes`、`reported_at`，并输出 `operator_report_status=missing|ready_for_execution|ready_for_review|unsafe_or_incomplete`。preflight 三项为 true 时是 `ready_for_execution`，可通过执行前 operator report gate；preflight 为 true 且执行后观察字段完整时是 `ready_for_review`。该报告只作为人工 preflight/观察材料；dry-run 带完整或半完整报告仍不 POST `/api/base/manual`，也不会把 `safe_to_control` 或 `hil_pass` 改成 true。

现场有人看护且 CEO 明确授权真实短 pulse 后，才允许使用：

```bash
python3 onboard/scripts/o1_ttyS5_safe_pulse_acceptance.py \
  --base-url http://192.168.1.11:8787 \
  --execute-motion \
  --confirm-physical-clearance \
  --operator-report-json /safe/runtime/operator_report.json \
  --direction forward \
  --speed 0.05 \
  --duration-ms 250 \
  --once-json \
  --output /safe/runtime/o1-ttyS5-safe-pulse-acceptance.json
```

证据边界：

- 默认 dry-run：`api_status_dry_run_not_hil`
- 执行模式：`api_manual_short_pulse_with_extra_stop_not_hil`
- 执行模式缺失或不安全 preflight operator report：`acceptance_verdict.failed_step=operator_report_missing_or_incomplete`，不发送 manual POST。
- 没有 `T=1001` 或等价 ACK 前，`acceptance_verdict.status` 必须是 `motion_posted_without_ack` 或更保守状态，runner 输出必须保持 `safe_to_control=false`、`delivery_success=false`。
- 即使 `acceptance_verdict.status=motion_posted_with_t1001` 且 `operator_report_status=ready_for_execution` 或 `ready_for_review`，也只代表 8787 status/manual response 中出现 ACK 线索并携带人工材料；仍不是 HIL pass，不能替代同源 `feedback_T1001.log`、ROS `/odom`、`/imu/data`、`/battery` 和 operator HIL report。
- 本轮未执行真实 `/api/base/manual`，未发送任何运动 POST。

## 2026-09-18 控制与状态性能契约

单个 `UpperRobotApi` 实例使用专用串口线程执行完整动作。普通请求在串口忙或 Stop 待执行时返回 HTTP `409`，顶层 `accepted=false`、`preempted=false`、`error.type=serial_busy`、`sends_commands=false`；请求不会进入运动队列。未知方向继续返回 HTTP `400`。动作生产者为 PC/本地 HTTP 客户端，消费者为本 API；既有正常响应字段保留。

`POST /api/base/stop` 不受普通动作 busy 拦截：它抢占当前 pulse/反馈等待，已有动作先在 `finally` 中停车，随后执行显式 Stop。客户端取消与异常同样不能跳过停车。已接受的 manual 被抢占时仍返回 HTTP `200`、`accepted=true`、`preempted=true`，实际写入由 `command_result` / `stop_result` / `auto_stop_executed` 表达；尚未反馈时 `feedback_after_stop_attempted=false`、`t1001_feedback_status=skipped_due_to_preemption`。开始反馈后被抢占，可由 `feedback_evidence.serial_read.interrupted=true` 识别。

兼容的 `POST /api/base/manual {"direction":"stop"}` 同样走停止优先入口，保持 manual schema，`duration_ms=0`，跳过 pulse 和反馈采样；它与独立 Stop 并发时只共享底层停车结果，各自返回自己的 schema。Stop 完成前不接受其他动作，Stop 后允许用户发起全新的动作。

串口读片上限 `50 ms`，单次写设置 `200 ms` timeout；这是调度配置，实机停止时延还包含 OS 调度、驱动和下位机响应。普通反馈见到 `T=1001` 即完成，显式 `feedback-samples` 保留完整采样窗。限速与 pulse 最大值保持原合同。仲裁只覆盖本实例/进程：`esp32_bridge` 或其他程序不得同时占用该 UART；跨进程独占和实机时延仍需部署/HIL 验证。

`radar/map/localize/nav2` 的配置型命令在后台运行，HTTP 事件循环可继续服务 Stop/health；重复配置命令返回 `error.type=command_busy`。命令仍使用既有 timeout 与 fail-closed 响应。HTTP 取消不会提前解除配置命令的 single-flight 状态。

`GET /api/status` 不等待摄像头网络请求：首次返回 camera `status=unknown`，后台单飞采样。camera 新增可选字段：`sampled_at_ms`（实际采样完成时间）、`sample_age_ms`、`stale`、`refreshing`。成功采样保存 1 秒后允许刷新；达到 3 秒或没有样本时 `stale=true` 且 `status=unknown`，不会沿用旧成功状态生成新的采样时间。失败样本仍保留对应 HTTP 错误码。相机显式接口复用服务生命周期中的 HTTP session；服务退出会取消并等待采样任务并关闭 session。

本地状态文件在后台构造摘要，同一次请求内同一路径只读取/解析一次；下一次请求重新读取，因此文件替换、坏 JSON、缺失、freshness 变化都能继续 fail-closed 呈现。根路径只返回静态路由，不再触发整套状态查询。

硬件协议依据：`docs/vendor/VENDOR_INDEX.md`、`docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h` 与 `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`；本轮不改 vendor 命令、端口、波特率或速度映射。

离线回归：`python -m unittest onboard.scripts.test_upper_robot_performance`；性能探针：`python onboard/scripts/control_status_performance_probe.py --baseline-ref 869dfe5aaf95bcd1759583752a1a433b9ff1e83c --output <output.json>`。探针对 git 基线和改后代码使用同样 fake UART/camera，记录 baseline/after 与环境。结果仅为软件 mock 性能，不能用作 HIL、真实 4G 或机器人 ACK。
