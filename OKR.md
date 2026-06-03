# rober 项目设计与前瞻 OKR

## 1. 北极星

把 `rober` 做成一台面向普通手机用户的低成本 ROS2 自主垃圾投递机器人：用户把垃圾交给小车后，小车沿固定路线出发，把垃圾送到垃圾站/垃圾桶点位，必要时跨楼层进出电梯，再安全返回或等待下一次任务。不是一次性 demo，不依赖机械臂捡垃圾。

当前项目核心包：

- `ros2_trashbot_interfaces`：msg/srv/action 契约层。
- `ros2_trashbot_hardware`：Orange Pi 到 WAVE ROVER ESP32 下位机的串口桥。
- `ros2_trashbot_nav`：Nav2、航点、地图、固定路线、关键帧调试。
- `ros2_trashbot_behavior`：任务编排、送达/投放 action。

项目的核心是把"能跑"升级为"可验证地可靠交付垃圾"：协议可信、固定路线可靠、任务可恢复、用户交互足够简单、数据可复盘、云端可运营。

---

## 2. 战略定位

1. **目标用户是不会电脑和硬件的普通人**
   - 用户默认只有手机，不要求会 SSH、ROS2、串口、地图文件或硬件调试。
   - 产品体验围绕手机端一键发车、状态查看、异常提示、人工接管和售后诊断设计。
   - 语音、喇叭和简单灯光/提示音降低使用门槛。

2. **核心任务是"送垃圾"，不是"捡垃圾"**
   - MVP 闭环：用户放入垃圾 → 手机/语音确认 → 小车出发 → 到达垃圾站点位 → 完成投放/提醒人工取走 → 返回或待命。
   - 当前预算和条件下不承诺机械臂抓取、地面散落垃圾拾取、复杂分类分拣。
   - 摄像头优先用于路线辅助、站点识别、障碍/异常记录和远程查看。

3. **预算有限，必须按量产约束做取舍**
   - 默认硬件边界：小车底盘、Orange Pi 上位板、随身 WiFi、摄像头、麦克风、喇叭。
   - 新增能力必须回答：是否降低用户使用难度、是否提高送达成功率、是否适合低成本量产。
   - 硬件事实来源：`docs/vendor/VENDOR_INDEX.md`。本文仅写产品战略，不新增引脚/电压/波特率假设。

---

## 3. 设计原则

1. **硬件事实必须本地可追溯**
   - WAVE ROVER、Orange Pi、UART、波特率、JSON 指令、速度映射、反馈协议、引脚、电压、固件和机械尺寸，以 `docs/vendor/VENDOR_INDEX.md` 及其指向资料为准。
   - 底盘通信按 WAVE ROVER 官方 UART newline-delimited JSON 处理，下位机不改动。

2. **ROS2 接口稳定，内部实现可替换**
   - 上层面向 `/cmd_vel`、`/odom`、`/imu/data`、`/battery`、`/trashbot/patrol`、`/trashbot/collect_trash` 等接口。
   - 底层硬件桥、视觉模型、导航实现可以迭代，不随意破坏接口契约。

3. **先送达闭环，再智能**
   - 第一优先级是完整送达闭环。复杂模型、动态规划、多机协同建立在稳定送达和可观测数据之上。

4. **每个关键行为要可观测、可回放、可解释**
   - 任务状态、导航目标、检测结果、失败原因、硬件反馈都落日志或状态文件。
   - 路线、关键帧、检测样本和失败案例形成持续改进数据集，上传云端存档。

5. **默认安全、低速、可停**
   - 任何自主行为必须有停止路径、超时策略、失败恢复策略。
   - 未经硬件验证的能力只能以参数关闭或 dry-run 形式存在。

6. **量产优先，少硬件、少配置、少售后**
   - 功能默认考虑批量装机、远程诊断、参数模板、用户误操作和售后成本。

7. **电梯识别是必须实现的 assisted delivery**
   - 跨楼层送垃圾是 MVP 必须能力：小车看门、进门、语音求助按键、判断目标楼层、开门后驶出，进入主 `task_orchestrator` 状态机。
   - 按"文档/合同 → 软件 dry-run → 受控实景"三层验收推进，写明必须不等于已完成实机。
   - 小车不按电梯按钮，不改造电梯，人工协助按目标楼层是产品边界。

8. **数据通路：Orange Pi → 隧道 → 云中转（核心后端）**
   - 上位机 Orange Pi 通过安全隧道（如 frp/ngrok/WireGuard）接入公网云中转，不依赖手机直连 WiFi。
   - 云中转是核心后端：命令/状态/ACK 控制面中转、任务记录与事件存档、模型推理与数据打标、OSS 大对象存储。
   - 控制面不暴露 `/cmd_vel`、不接受 inbound 直连小车。凭证只走 `.env`/环境变量，不进入仓库。

9. **手机端是普通用户唯一操作入口**
   - 美观、能直接使用、不依赖命令行/SSH/ROS2 知识。4G 场景走云端中转。
   - 实时可见机器人位置、任务状态、电梯状态，支持一键发车和人工接管。

10. **PC 端是运营调试与数据训练平台**
    - 实时可见 ROS2 路径、地图、机器人位置、电梯状态、楼层信息。
    - 历史路线回放、数据标注/打标、模型训练数据管理。
    - 实时 ASR 监听、TTS 发言操作、手动转向控制、自动寻路下发。
    - 与云端后端数据层对接，不绕过云端直连小车。

11. **允许各接口与硬件分阶段 Mock**
    - 软件逻辑开发与测试不应被物理硬件、公网/云端和真实电梯/路线环境的到位情况所阻塞。
    - 允许且鼓励在串口驱动、云端 API、ASR/TTS、雷达/ToF 传感器等接口设计并使用 `mock` 模式或本地/内存仿真。
    - 在推进 OKR 过程中，若在 Docker/本地环境中使用 Mock 运行且测试通过，可判定为『软件侧完成』，不必等到真实硬件实测后再合并推进，直到最终集成测试阶段再用真实数据和硬件实跑验证。

---

## 4. 2026 H1 OKR（当前推进中）

### Objective 1：打通官方硬件协议，建立可信底盘控制层

**当前进度：约 97% software_reference + ttyS5 control write observed + manual forward/back/left/right HTTP 200 with auto-stop observed + stop-only manual 后 T=130/T=1001 observed + LiDAR ROS2 `/scan` smoke observed + `/lidar/raw_packet` once observed + static TF observed + PC/8787 material entry ready / HIL、ACK、SLAM/Nav2、长稳、production udev、ROS feedback topics、左右转现场闭环和 `safe_to_control=true` 仍 not_proven** | Task A 已用 mock serial / virtual HIL packet 证明 JSON newline 编码、`T=1` wheel command、`T=1001` 反馈解析、IMU/Battery 发布、坏帧容错和参数边界。

LiDAR 当前实现依据已收敛为 `docs/vendor/lidar_pkg_ros2-main/`，历史 `docs/vendor/lidar_ros/` 仍保留为 ROS1/protocol comparison；当前已确认 `/dev/ttyACM0 @150000` 是上位机雷达口，`A5 60` 启动命令、`A5 00 A5 65 A5 65` 停止序列、`0xAA 0x55`、`LSN`、`/scan`、`/lidar/raw_packet` 为 `source=software_reference + user_manual_serial_observed_start + upper_api_observed_lidar_port + raw_serial_packet_observed + ros2_scan_smoke_observed`。2026-06-04 远端 `/opt/ros/humble/setup.bash` 与 `/root/rober/onboard/install/setup.bash` 均已存在，`colcon build` 6 packages finished [2min 8s]；LiDAR-only smoke 只发送 LiDAR `A5 60` start 与退出 stop sequence，观察到 `/scan` once、`/scan` hz 约 295-300 Hz、`/lidar/raw_packet` once、`tf2_echo base_link laser_frame`，summary `all_required_observations_observed=true`。

2026-06-03 现场事实确认当前 WAVE ROVER 底盘可写控制口是 Orange Pi `/dev/ttyS5 @115200`，不是 USB STC `/dev/ttyACM0`；CEO 观察到 `T=1,L=0.08,R=0.08` 低速命令让底盘响应，随后现场发送 `T=1,L=0,R=0` 停车。8787 统一上位机 Robot API 已真实部署并监听，`GET /health` 与 `GET /api/status` ready，`GET /api/status` 同时返回 camera ready、radar `/dev/ttyACM0 @150000`、base `/dev/ttyS5 @115200`、`write_control_available=true`、`t1001_observed=false`、`robot_ack_connected=false`、`safe_to_control=false`；PC live panel 与 PC 本机 direct upper API 已通过 `ROBER_UPPER_API_BASE_URL=http://192.168.1.11:8787` 消费同一状态面，并新增 `POST /api/o7/direct-upper/base/feedback-request` 软件入口。本轮已将当前上位机 API 脚本部署到远端 `/root/rober/onboard/scripts/upper_robot_api.py` 并重启 `trashbot-upper-robot-api.service`；远端真实 `POST /api/base/feedback-request` 返回 HTTP 200，`serial_open.ok=true`，`serial_write.command={"T":130}`，`bytes_written=10`，3 秒窗口读到 `observed_feedback_types=[130,1001]` 且 `t1001_feedback_status=observed`。随后新增并部署 `POST /api/base/feedback-samples`，真实远端只调用该非运动 endpoint，HTTP 200，`requested_sample_count=3`、`completed_sample_count=3`、`t1001_observed_count=3`、`observed_feedback_types=[130,1001]`、`all_samples_observed_t1001=true`，三个 sample 状态均为 `observed`。`POST /api/base/feedback-request` 与 `POST /api/base/feedback-samples` 的目标合同仍是显式非运动反馈请求：只发送 vendor `{"T":130}` 并短窗口读取 newline-delimited JSON；fake serial 单测已覆盖 status 不触发串口、只写 `T=130`、解析 `T=1001`、坏 JSON 计数和写失败 fail-closed；该材料已证明远端 endpoint 部署可用，并在真实 `/dev/ttyS5` 上完成 3/3 非运动 `T=130 -> T=1001` 多样本观察；但仍不证明 HIL pass、运动控制安全、真实 ROS feedback topic、真实 ROS `/odom`、`/imu/data`、`/battery` 或 `safe_to_control=true`。

O1 safe pulse acceptance runner、post-status verdict 和 execution preflight report 已准备好受控现场点动的证据链，执行模式必须按 `GET status -> POST manual -> POST stop -> GET post-status` 采集同源证据，并区分 `dry_run_only`、`blocked_before_motion`、`motion_posted_without_ack`、`motion_posted_with_t1001`。当前不能把这些状态面、raw bytes、非运动 `T=130 -> T=1001` 或首个 `/scan` smoke 写成 HIL pass：SLAM/Nav2 消费、长稳 `/scan`、量产 udev `/dev/lidar`、robot ACK 语义、真实 `/imu/data`、`/battery`、`/odom`、自动停车/急停现场演练和 HIL packet 仍未闭环。下一步最高优先级拆成两条可并行验证线：1）LiDAR 线继续补 driver 优雅退出、production udev、长稳 smoke、SLAM/Nav2 消费与地图质量证据；2）底盘线在现场看护、物理净空、人工急停可用时，基于已部署的 8787 `/api/base/feedback-samples` 复跑多帧 `T=130 -> T=1001`，再经 `/api/base/manual` 做低速短 pulse，并采集 status/manual/stop/post-status、operator report、ACK 或 `T=1001`、日志与安全复位证据。未完成前不得写成 `safe_to_control=true`、闭环安全控制、真实 ROS `/cmd_vel` 接入或 delivery success。（开发阶段支持通过 Mock/虚拟串口模式完成软件控制链路并进行验证，真机实测留待后期集成）

2026-06-03 15-16 继续推进 O1，但不调整百分比：8787 `POST /api/base/feedback-samples` 现在会把 latest 多样本结果原子写入 `runtime/base_feedback_samples_latest.json`（可由 `ROBER_BASE_FEEDBACK_SAMPLES_ARTIFACT_PATH` / `--feedback-samples-artifact-path` 覆盖），并新增只读 `GET /api/base/feedback-samples/latest` 回放该 artifact。远端验证中，POST 仍只发送 vendor `{"T":130}`，返回 3/3 `T=1001` observed 且 artifact write `ok=true`；随后 GET latest HTTP 200，artifact `status=loaded`，顶层 `readback_sends_commands=false`、`sends_commands=false`、`sends_motion_commands=false`、`robot_control_executed=false`、`hil_pass=false`。该增量让 O1 真实反馈材料可持久化和回放，但仍不是 robot ACK、HIL、运动控制安全、真实 ROS feedback topic、`/scan` 或 delivery success。

2026-06-03 16-17 继续推进 O1，但不调整百分比：8787 `GET /api/base/status` 和统一 `GET /api/status` 现在通过 `base.feedback_samples_latest` 直接暴露 latest feedback samples artifact 的只读摘要，包括 endpoint、artifact status/ok/path/config source、mtime/updated_at/age、新鲜度、`latest_t1001_observed_count` 和 `latest_all_samples_observed_t1001`。该摘要只做 artifact `stat/read_text/json.loads`，不打开串口、不发送 `T=130/T=1/T=13/T=131/cmd_vel` 或 `/api/base/manual`，并固定 `readback_sends_commands=false`、`sends_commands=false`、`sends_motion_commands=false`、`robot_control_executed=false`、`hil_pass=false`。默认 15 分钟 stale window 只代表材料文件新鲜度，不证明 HIL、ACK、`safe_to_control=true`、真实 manual、ROS feedback topic 或 `/scan`。

2026-06-03 17-18 继续推进 O1，但不调整百分比：新增 `onboard/scripts/o1_lidar_scan_proof_collector.py` 和 8787 只读 `GET /api/radar/scan-proof/latest` 合同，用 `trashbot.o1.lidar_scan_proof.v1` artifact 记录 LiDAR `/scan` proof/readiness/blocker。远端 no-motion 检查已通过 `ssh root@192.168.1.11 -p 37878` 到达上位机，确认 `/dev/ttyACM0` 与 STC by-id 存在、8787 `/health` ready、`/api/radar/status.scan_status=not_proven`、`trashbot-upper-robot-api.service` active；但 `/opt/ros/humble/setup.bash`、`/root/rober/onboard/install/setup.bash` 和 `ros2` 均不可用，因此 collector 写入 `/tmp/o1_lidar_scan_proof_latest.json` 后只得到 `proof.status=blocked_or_not_observed`、`topic_reads.attempted=false`、`blockers=[ros2_humble_setup_missing, rober_install_setup_missing, ros2_command_unavailable, upper_api_scan_not_proven]`。该增量只证明 scan proof collection path ready 和 `blocked_pending_ros2_runtime` 已机器可读分类；不证明真实 `/scan`、`/lidar/raw_packet`、TF、SLAM/Nav2、HIL、ACK、`safe_to_control=true`、真实 manual 或 delivery success。

2026-06-03 18-19 继续推进 O1/O7 可见性，但不调整百分比：PC workstation 现在消费 8787 `radar.scan_proof_latest` 摘要，在 O7 Live Operator Panel 和 direct upper status 中展示 LiDAR scan proof artifact status、freshness/age、latest proof status、一次性 `/scan`/`/lidar/raw_packet` 观测标记和 top blockers。远端只读验收确认 `GET /api/radar/scan-proof/latest` 已返回 HTTP 200、artifact `loaded`，`GET /api/radar/status.scan_proof_latest.http_status=200` 且 `latest_proof_status=blocked_or_not_observed`；PC 端仅消费该只读摘要，不执行 collector、不启动 ROS2、不打开 LiDAR 串口、不发送 `A5 60` 或底盘命令。该增量让 O1 scan proof blocker 对 operator 可见，但不证明真实 `/scan`、`/lidar/raw_packet`、TF、SLAM/Nav2、HIL、ACK、`safe_to_control=true`、真实 manual 或 delivery success。

2026-06-03 19-20 继续推进 O1，但不调整百分比：新增 LiDAR raw packet proof collector，用当前 vendor 边界内的 `/dev/ttyACM0 @150000`、`A5 60` 启动、`A5 00 A5 65 A5 65` 停止、`0xAA55` sync header 和 `lidar_packets.py` parser/fallback 生成 `trashbot.o1.lidar_raw_packet_proof.v1` artifact。该 collector 会打开 LiDAR 串口并发送 LiDAR start/stop bytes，这是本轮目标行为；同时固定不发送 WAVE ROVER 底盘 `T=1/T=13/T=130/T=131`、不发布 `/cmd_vel`、不调用 `/api/base/manual`、不启动 ROS2 driver 或 launch。artifact 只能证明 raw bytes/packet/point parse material readiness，不证明真实 ROS2 `/scan`、TF、SLAM/Nav2、HIL、ACK、`safe_to_control=true`、真实 manual 或 delivery success。

2026-06-03 20-21 继续推进 O1，但不调整百分比：8787 统一上位机 Robot API 新增只读 `GET /api/radar/raw-packet-proof/latest`，默认读取 `runtime/lidar_raw_packet_proof_latest.json`（可由 `ROBER_LIDAR_RAW_PACKET_PROOF_ARTIFACT_PATH` / `--lidar-raw-packet-proof-artifact-path` 覆盖），并在 `GET /api/radar/status` 与统一 `GET /api/status` 的 `radar.raw_packet_proof_latest` 暴露 artifact status、mtime/age、`proof.status`、raw bytes / sync header / packet parse / points observed 和 `bytes_read/sync_header_count/packets_parse_ok/points_total` 摘要。该 readback/status 只做 `stat/read_text/json.loads`，固定 `readback_sends_commands=false`、`sends_lidar_start_command=false`、`opens_lidar_serial=false`、`starts_ros2=false`、`calls_base_manual=false`、`safe_to_control=false`、`hil_pass=false`；不打开 LiDAR 串口、不发送 `A5 60`、不启动 ROS2、不发送 WAVE ROVER 底盘命令、不调用 `/api/base/manual`。该增量只让上一轮 raw packet artifact 像 scan proof 一样可被 PC/OKR 只读消费，不证明真实 ROS2 `/scan`、TF、SLAM/Nav2、HIL、ACK、`safe_to_control=true`、真实 manual 或 delivery success。

2026-06-03 21-22 继续推进 O1，但不调整百分比：`o1_upper_computer_readiness_probe.py` 新增 LiDAR ROS2 bootstrap/runtime 分类，不再只停留在 artifact readback。新增 `lidar_ros2_bootstrap.status` 与 `ros2_runtime_remediation_plan`，可区分 `runtime_missing`、`repo_missing`、`install_missing`、`driver_missing`、`lidar_device_missing`、`ready_for_scan_bootstrap`、`docker_arm64_unavailable`、`topics_not_running`，并给出下一条补救动作。远端只读 SSH probe 到 `root@192.168.1.11:37878` 成功，host 为 `op-z3-b6.home aarch64`，fail-closed boundary 仍为 `safe_to_control=false`、`sends_commands=false`、`opens_serial_devices=false`、`starts_ros2_control=false`；当前远端分类为 `bootstrap=runtime_missing`，blockers 为 `runtime_missing/install_missing/driver_missing`，remediation 为 `install_or_provide_ros2_humble_runtime`。该增量只把 `/scan` blocker 精准化为上位机 ROS2 Humble/runtime/install/driver 缺口，不启动 ROS2 driver、不打开 LiDAR 串口、不发送 `A5 60`、不发送 WAVE ROVER `T=1/T=13/T=130/T=131`、不调用 `/api/base/manual`，也不证明真实 `/scan`、`/lidar/raw_packet` topic、TF、SLAM/Nav2、HIL、ACK、`safe_to_control=true` 或 delivery success。

2026-06-03 22-23 继续推进 O1，但不调整百分比：本轮不再扩展 readback/status UI，而是新增可执行的上位机 runtime remediation。`onboard/scripts/o1_ros2_humble_arm64_bootstrap.sh` 面向 Ubuntu 22.04 arm64 安装 ROS2 Humble ros-base/tf2/colcon/pyserial 并重建 `/root/rober/onboard`；`onboard/scripts/o1_lidar_ros2_scan_smoke.sh` 只启动 LiDAR driver 与 `base_link -> laser_frame` 静态 TF，采集 `/scan` once/hz、`/lidar/raw_packet` once 和 `tf2_echo` artifact，并显式拒绝 `/dev/ttyS5`。远端只读检查确认上位机是 Ubuntu 22.04.5 aarch64，`/dev/ttyACM0` 与 STC by-id 存在，pyserial 可用，Docker daemon 是 arm64 但仅有 amd64 `osrf/ros:humble-desktop`，apt 当前没有 ROS2 source，`/opt/ros/humble/setup.bash`、`/root/rober/onboard/install/setup.bash` 和远端旧源码 `lidar_driver.py` 均缺失；随后只同步当前 `onboard/src` 和 `onboard/scripts` 到远端，没有执行 apt install、colcon build 或启动 ROS2 driver。真实 `/scan`、`/lidar/raw_packet` topic、TF 和 HIL 仍 `not_proven`，O1 保持 95.5%。

2026-06-03 24-25 保守调整 O1 当前比例：基于当前状态，只把 `/dev/ttyS5 @115200` 可写、manual forward/back/left/right HTTP 200、auto-stop observed、stop-only manual 后 `T=130/T=1001 observed`、PC/8787 材料入口和 LiDAR raw/status 材料入口计入当前推进度，O1 从约 95.5% 小幅调到约 96%。该调整不越过 HIL 门槛：左右转现场效果、robot ACK 语义、HIL packet、真实 ROS `/odom`、`/imu/data`、`/battery`、真实 `/scan`、`safe_to_control=true` 和完整 delivery success 仍 `not_proven`。

2026-06-04 00-01 Product/OKR 收口保守调整 O1 当前比例：基于 `sprints/2026.06.04_00-01_o1-upper-ros2-bootstrap-continue/tech-done.md`，首次承认真实上位机 ROS2 LiDAR `/scan` smoke observed，O1 从约 96% 小幅调到约 97%。证据只覆盖 `/opt/ros/humble/setup.bash` exists、`/root/rober/onboard/install/setup.bash` exists、`colcon build` 6 packages finished [2min 8s]、`/scan` once、`/scan` hz 约 295-300 Hz、`/lidar/raw_packet` once、`base_link -> laser_frame` 静态 TF 和 summary `all_required_observations_observed=true`。本轮未发送底盘运动命令，只发送 LiDAR `A5 60` start 和 stop sequence；仍不证明 HIL、SLAM/Nav2、长稳、production udev、ACK、`/odom`、`/imu/data`、`/battery`、`safe_to_control=true` 或完整 delivery success。

**Key Results**

- KR1（软件协议入口已完成）：`ros2_trashbot_hardware` 默认使用 UTF-8 JSON + `\n` 与 ESP32/WAVE ROVER 通信，mock serial / virtual HIL packet 已覆盖 JSON 编码、`T=1` 速度命令、`T=1001` 解析、坏帧容错和参数边界。
- KR2（材料入口已完成）：8787 统一上位机 API 与 PC direct upper API 已提供 status、stop、feedback-request、feedback-samples/latest 和 manual 软件入口；材料入口必须继续标注 `safe_to_control=false`，不得把 HTTP 200 写成 HIL。
- KR3（现场底盘材料部分 observed）：`/dev/ttyS5 @115200` 已确认可写；manual forward/back/left/right HTTP 200 与 auto-stop 成功可作为受控点动材料入口；stop-only manual 后 `T=130/T=1001 observed` 可作为 vendor feedback material。左右转现场效果、robot ACK 语义和真实安全闭环仍未完成。
- KR4（真实 ROS feedback topic 未完成）：真实 `/odom`、`/imu/data`、`/battery` 仍 `not_proven`；`T=1001` 只是 vendor feedback material，不等于项目 robot ACK connected。
- KR5（首个真实 LiDAR `/scan` smoke 已 observed）：上位机 ROS2 runtime/build 已可用，LiDAR-only smoke 已观察到 `/scan` once、`/scan` hz 约 295-300 Hz、`/lidar/raw_packet` once 和 `base_link -> laser_frame` 静态 TF；SLAM/Nav2 消费、长稳 `/scan`、production udev `/dev/lidar`、driver 优雅退出和地图质量仍未完成。
- KR6（HIL 与安全准入未完成）：HIL packet、自动停车/急停现场复核、左右转现场闭环、`safe_to_control=true`、真实 `/cmd_vel` 接入和 delivery success 均必须另行实机验收。

---

### Objective 5：云中转控制面产品化（原 O5/O6）

**当前进度：约 96% software + material acceptance queue visible in PC workstation；real material not_proven** | Task B 已用本地/mock control plane smoke 覆盖 `trashbot.remote.v1` commands/status/ack、bearer/env credential、mock 4G interruption、mock DB/queue artifact、mock OSS/CDN manifest 和 graceful degradation。`2026.06.01_14-15_o5-readiness-live-health` 新增 bearer-gated `GET /api/o5/readiness/health`，schema 固定为 `trashbot.o5.readiness_health.v1`，capability 固定为 `o5_readiness_live_health`，复用 `production_preflight_payload()` 但只输出脱敏 readiness 缺口摘要，并固定 `production_ready=false`、`safe_to_control=false`、`sends_commands=false`、`robot_control_executed=false`、`delivery_success=false`。`2026.06.01_17-18_o5-o6-cloud-relay-health` 进一步在 PC workstation 后端实现只读 `GET /api/o5-o6/cloud-relay-health`，聚合 O5 readiness health 与 O6 archive health；该 probe 只允许 loopback/private LAN `baseUrl`，bearer 只从 env 读取，固定 fail-closed false fields，不发控制、不 POST、不碰 `/robots/*`。`2026.06.01_18-19_o5-o6-external-live-probe` 新增 Node 版 external probe；`2026.06.01_21-22_o5-o6-python-external-probe` 补充同 schema 的 Python stdlib runner，标记 `runner=python_stdlib`，兼容 `python3 -s - --once-json` stdin 运行。`2026.06.01_23-24_o5-o6-external-probe-artifact-ui` 已给 Python runner 增加 `--output` 落盘能力，并让 PC workstation 暴露只读 `GET /api/o5-o6/external-probe-artifact` 与 O7 Console 摘要，展示 `probe_status`、runner、endpoint reachability、blocked reasons、fail-closed safety fields 和更新时间；该入口不执行 probe、不联网、不访问 `/robots/*`、不读取硬件、不回显 bearer/token/raw URL/artifact path/traceback。`2026.06.02_05-06_o5-o6-tls-evidence-summary` 进一步让 Python stdlib runner 在 HTTPS cloud base URL 时采集脱敏 TLS evidence summary，并由 PC workstation artifact API/contract 消费展示；边界仍是只读、GET-only、no POST、no `/robots/*`、no hardware read、no raw host/base URL/token/cert DN/traceback/artifact path。`2026.06.02_08-09_real-material-acceptance-queue` 新增只读 `GET /api/real-material/acceptance` 和 `RealMaterialAcceptancePanel.vue`，聚合 O5/O6 external probe artifact 与 O7 browser smoke JSON，形成真实材料验收队列、缺口和 next actions；`2026.06.02_09-10_real-material-runbook` 进一步让每条 item 包含 `artifact_freshness` 和 `collection_runbook`，operator 可见 artifact mtime/age/fresh/stale/missing 与手动采集 recipe，但 API 仍只返回 recipe 与只读 `stat` 摘要，不执行采集。该入口不执行 probe、不联网、不 SSH、不 POST、不访问 `/robots/*`、不读取硬件、不创建 WebRTC session、不发送控制，并固定 `safe_to_control=false`、`sends_commands=false`、`robot_control_executed=false`、`delivery_success=false`。验证证据为 PC `npm run test` 57 tests passed、`npm run build` 通过、`npm run lint` 通过、scoped diff-check 通过。真实生产云 TLS 验收、真实公网 HTTPS、真实 4G/SIM、production DB/queue、production worker/cutover、OSS/CDN live traffic、真实 phone/browser 证据仍为 `not_proven`。（开发与测试阶段支持基于本地/Docker 的 Mock Cloud 进行控制面业务逻辑联调验证）

**Key Results**

- KR1：云中转服务端最小契约（commands/status/ack）按 `trashbot.remote.v1` 实现：HTTPS、outbound polling 优先，幂等键 + bearer token 鉴权，不暴露 `/cmd_vel`、不接受 inbound 直连。
- KR2：服务端基线规格写入 `docs/product/cloud_4g_infrastructure.md`（4C 8G 无 GPU、SSH 端口、防火墙策略、容量边界）。
- KR3：OSS 写入策略明确：bucket `bytegallop`，region `oss-cn-hangzhou`，对象前缀 `rober/<robot_id>/<date>/<task_id>/`；小车侧写入使用 STS 临时凭证或受限 AK。
- KR4：CDN base URL `https://cdn.bytegallop.com/rober/` 只作公开只读视图入口；私有数据走 API 网关 + bearer。
- KR5：凭证管理 contract：`.env` 不入仓库，服务端/CI/上车均通过环境变量注入；密钥泄露有 rotate 流程。
- KR6：4G 中断、OSS 写失败、CDN 不可达三类失败必须 graceful degradation，任务不丢，远程诊断能区分"网络问题"与"机器人问题"。

---

### Objective 6：云端核心后端——数据存档、模型推理与打标平台

**当前进度：约 96% software + material acceptance queue visible in PC workstation；real material not_proven** | Task C 已把 O6 archive task/event/annotation/inference/query、机器人侧 event publisher、algorithm feed 和 `trashbot.archive.v1` schema 兼容做成可复验 mock evidence，并证明 `o6_cloud_archive_state.json` 不落仓库根目录。`2026.06.01_13-14_o6-archive-live-health` 新增 bearer-gated `GET /api/o6/archive/health`，schema 固定为 `trashbot.o6.archive_health.v1`，capability 固定为 `o6_archive_live_health`，可返回 `empty` / `ready` / `store_unavailable`，并保持 `storage_backend=json_file_proof`、`production_ready=false`、`production_db_connected=false`、`real_oss_upload=false`、`real_inference_model_runtime=false`、`safe_to_control=false`、`sends_commands=false`、`robot_control_executed=false`、`delivery_success=false`。`2026.06.01_17-18_o5-o6-cloud-relay-health` 进一步通过 PC workstation 只读 `GET /api/o5-o6/cloud-relay-health` 将 O6 archive health 与 O5 readiness health 合并成运营侧单点 live-health 视图；该 probe 只读、不 POST、不访问 `/robots/*`，并固定 fail-closed false fields。`2026.06.01_18-19_o5-o6-external-live-probe` 新增 Node 版 external probe；`2026.06.01_21-22_o5-o6-python-external-probe` 新增 Python stdlib runner，让上位机缺 Node.js 时仍可通过 SSH stdin 采集同一 O5/O6 external live probe schema。`2026.06.01_23-24_o5-o6-external-probe-artifact-ui` 已把该 runner 的 `--output` artifact 接入 PC workstation 只读摘要和 O7 Console，运维能看到 O6 archive endpoint 的 reachability/schema/fail-closed 结果，而浏览器不接触 raw base URL、token、artifact path 或 traceback。`2026.06.02_05-06_o5-o6-tls-evidence-summary` 已把 HTTPS cloud base URL 下的脱敏 TLS evidence summary 纳入同一 Python runner 与 PC workstation artifact contract，让 O6 archive endpoint 相关 TLS 摘要可见；该能力仍不回显 raw host/base URL/token/cert DN/traceback/artifact path。`2026.06.02_08-09_real-material-acceptance-queue` 新增只读 `GET /api/real-material/acceptance` 和 `RealMaterialAcceptancePanel.vue`，把 O6 archive/external probe 相关真实材料缺口纳入 PC workstation 验收队列、缺口和 next actions；`2026.06.02_09-10_real-material-runbook` 进一步让每条 item 包含 `artifact_freshness` 和 `collection_runbook`，operator 可见 artifact mtime/age/fresh/stale/missing 与手动采集 recipe，但不执行 probe 或采集。该入口不联网、不 SSH、不 POST、不访问 `/robots/*`、不读取硬件、不创建 WebRTC session、不发送控制，并固定 `safe_to_control=false`、`sends_commands=false`、`robot_control_executed=false`、`delivery_success=false`。验证证据为 PC `npm run test` 57 tests passed、`npm run build` 通过、`npm run lint` 通过、scoped diff-check 通过。真实安全隧道、production DB/queue、真实 OSS upload、真实模型或外部推理 runtime、真实云、真实 4G/SIM、真实 phone/browser、真实生产 TLS 验收和上车数据仍为 `not_proven`。

**目标说明**：把云中转从轻量控制面升级为核心后端：持久化存档任务记录和感知事件，提供模型推理和数据打标能力，作为 PC 端/手机端的统一数据源。

**Key Results**

- KR1：Orange Pi 上位机通过安全隧道（frp/WireGuard/ngrok 任选，参数可配）接入公网，隧道断线后自动重连，云端能感知在线/离线状态。
- KR2：任务记录和感知事件（路线帧、关键帧、检测结果、电梯门状态、楼层证据、失败原因）持久化存档到云端数据库，支持按 `robot_id / task_id / date` 查询。
- KR3：摄像头帧/快照等大对象通过 OSS 存档，云端数据库只保留对象引用（`evidence_ref`），不直接存大文件。
- KR4：云端提供数据打标/标注 API：接受标注任务（路线帧标注、电梯楼层标注、障碍物标注），支持 PC 端提交和查询标注结果。
- KR5：模型推理接口（电梯门开/关、楼层识别）可在云端调用，推理结果写入事件存档，不要求 GPU 上线即可用（优先 CPU 轻量模型或调用外部推理 API）。
- KR6：REST API（或 WebSocket）供 PC 端和手机端消费：历史任务列表、任务详情、轨迹数据、事件流、标注状态。

---

### Objective 7：PC 端运营调试与数据训练平台

**当前进度：约 98.9% same-LAN camera/systemd + PC Live Operator consuming unified upper API live status + PC direct manual buttons/WASD/direct API path ready + camera first-screen no auto-offer + realtime radar/map split accepted；production path / real operator workflow / Nav2 task loop / ACK / HIL not_proven** | Task D 已让 PC workstation 消费 O6/O7 mock archive bundle，覆盖实时地图/位置、电梯状态、历史路线回放、数据标注、推理摘要、ASR/TTS stub、手控/寻路 stub，并固定 `safe_to_control=false`、`robot_control_executed=false`。

O7 已形成 LAN-only WebRTC camera smoke、PC Chromium/browser smoke、30s smoke、180s long-stability collector、真实材料验收队列和 recovery readiness 的证据链。`2026.06.02_20-21_o7-camera-offer-recovery` 已证明 same-LAN 180s real browser material accepted / camera source guardrail ready。`2026.06.03_01-02_o7-camera-systemd-persistence` 已确认 8088 camera smoke 由 fixed systemd unit 接管，`enabled/active/loaded/running`，`MainPID` 与 listener pid 一致，`/health` 返回 ready 和 fail-closed 字段。8787 统一上位机 Robot API 已真实监听并提供 camera/radar/base 聚合状态；PC dev server 以 `ROBER_UPPER_API_BASE_URL=http://192.168.1.11:8787` 启动后，`GET /api/o7/live-operator-panel` 已显示 `workstation_api_8787_status=ready`、camera ready、LiDAR `/dev/ttyACM0`、base `/dev/ttyS5`、`T=1001 not observed` 和 manual control fail-closed。

2026-06-03 10-11 PC 本机 direct upper API 已补齐 `GET /api/o7/direct-upper/status`、`POST /api/o7/direct-upper/base/stop`、`POST /api/o7/direct-upper/base/feedback-request`、`POST /api/o7/direct-upper/base/manual` 并展示 path；2026-06-03 23-24 PC direct manual 按钮已从本地 locked 文案改为同源 `/api/o7/direct-upper/base/manual` 请求，前进/后退/左转/右转/Stop 与 WASD 同一键控口径展示发送中、HTTP 状态、失败原因、ACK/T=1001 和锁定状态；camera 首屏改为只读，不再自动调用 `/offer` 抢占预览。2026-06-03 24-25 口径小幅调整到 98.8%，只承认 operator 软件入口和 direct API path 更完整，不承认 production path、真实 complete operator workflow 或真实底盘控制。

2026-06-04 O1 已有首个 LiDAR ROS2 `/scan` smoke observed，因此 O7 不再把“真实 radar `/scan` 未证明”作为当前缺口；`sprints/2026.06.04_00-01_o1-o7-realtime-scan-map-split/tech-done.md` 已返回 Full-Stack 验证，PC 首屏拆成 `实时雷达 (/scan)` 与 `实时图 (SLAM/map)`，raw packet 不参与 radar ready，`/scan observed + map absent` 显示等待建图，原组合标题 `雷达未接入 / 等待建图` 已被 rendered smoke 证明不再出现。验证证据为 `npm test -- --run` 81 tests passed、`npm run build` 通过、`npm run lint` 通过、Playwright rendered smoke 通过且浏览器请求不直连 `:8787`/`:18787`、不访问 `/api/base/manual` 或 `/cmd_vel`。O7 从约 98.8% 小幅调到约 98.9%，只承认 operator 软件/渲染验收更完整；robot ACK、真实 `/odom`、`/imu/data`、`/battery`、真实 `/api/base/manual` 受控灰度、reboot 后自恢复、真实 8787 rendered smoke、云 relay/TURN/auth/phone/browser production path、弱网、ASR/TTS、真实 SLAM/map、手控/Nav2 和完整上车任务闭环仍 `not_proven`。

**目标说明**：PC 端面向开发者和运营人员，提供实时监控、历史回放、数据标注、手动控制和语音调试能力，与云端数据层对接，不绕过云端直连小车。

**Key Results**

- KR1：**实时地图与机器人位置**——PC 端展示当前地图、机器人实时位置（基于 ROS2 `/tf` 或云端转发位置），可见是否在路线上、是否进入电梯区域，刷新延迟 < 2 秒；真实 `/scan` 后地图预览仍需补齐。
- KR2：**电梯状态展示**——实时展示电梯状态（等待/进入/运行中/到达楼层/驶出），当前楼层证据，人工接管原因；历史任务可回放电梯完整状态链。
- KR3：**历史路线回放**——从云端拉取历史任务的轨迹数据，在地图上逐帧回放，可查看每一帧的位置、速度、关键帧截图和状态转移。
- KR4：**数据标注/打标界面**——展示待标注的路线帧、关键帧、检测截图，支持标注电梯门状态、楼层信息、障碍物类型；标注结果提交云端，可导出训练数据集。
- KR5：**实时 ASR 监听 + TTS 发言控制**——PC 端可实时查看小车当前 ASR 输入流；可手动下发 TTS 文本，小车喇叭播报；支持测试电梯语音场景。
- KR6（PC 手控软件入口已完成）：PC direct manual 按钮与 WASD 键控按同一 PC 同源 direct API path 对齐，方向请求走 `/api/o7/direct-upper/base/manual`，UI 展示 HTTP 状态、失败原因、ACK/T=1001 状态和 `safe_to_control=false`；这只是 operator 软件入口，不等于真实控制闭环。
- KR7（生产 operator workflow 未完成）：production path、云 relay/TURN/auth/phone/browser、真实 complete operator workflow、真实手控/Nav2 下发和完整任务闭环仍 `not_proven`。
- KR8（实时雷达/实时图拆分已完成软件验收）：PC 首屏已拆成 `实时雷达 (/scan)` 与 `实时图 (SLAM/map)`；raw packet proof 只留在诊断材料，不点亮 `/scan` ready；`/scan observed + map absent` 时显示等待建图。该 KR 只代表 PC 软件/渲染验收，不证明真实 SLAM/map artifact 或 production operator workflow。

---

## 4.1 当前 OKR 进度快照

更新时间：2026-06-04（对应 `2026.06.04_00-01_o1-upper-ros2-bootstrap-continue` micro sprint 与 Product/OKR 收口）。

| Objective | 进度 | 主要缺口 |
| --- | --- | --- |
| O1：硬件协议可信底盘 | 约 97% software_reference + ttyS5 control write observed + manual forward/back/left/right HTTP 200 with auto-stop observed + stop-only manual 后 T=130/T=1001 observed + LiDAR ROS2 `/scan` smoke observed + `/lidar/raw_packet` once observed + static TF observed + PC/8787 material entry ready | 首个上位机 ROS2 LiDAR smoke 已 observed：`/opt/ros/humble/setup.bash` 与 `/root/rober/onboard/install/setup.bash` 存在，`colcon build` 6 packages finished [2min 8s]，`/scan` once、`/scan` hz 约 295-300 Hz、`/lidar/raw_packet` once、`tf2_echo base_link laser_frame` 和 `all_required_observations_observed=true` 已记录。本轮只发送 LiDAR `A5 60` start/stop sequence，未写 `/dev/ttyS5`、未调用 `/api/base/manual`、未发布 `/cmd_vel`。底盘侧 `/dev/ttyS5 @115200` 可写、manual HTTP 200 + auto-stop、非运动 `T=130 -> T=1001` samples observed 仍只是材料入口；HIL、ACK、SLAM/Nav2、长稳、production udev、ROS feedback topics `/odom`/`/imu/data`/`/battery`、左右转现场闭环、急停演练、`safe_to_control=true` 和 delivery success 仍 `not_proven`。 |
| O1 补充证据 | 百分比不变 | `2026.06.03_15-16_o1-feedback-artifact-readback` 新增 `GET /api/base/feedback-samples/latest`，把上一条 3/3 非运动 `T=130 -> T=1001` samples 结果原子保存并只读回放；远端 GET latest 返回 artifact loaded，顶层 `readback_sends_commands=false`、`sends_commands=false`、`sends_motion_commands=false`、`robot_control_executed=false`、`hil_pass=false`。这是运营材料可回放能力，不证明 robot ACK、HIL、真实 manual、真实 ROS feedback topic 或 `/scan` |
| O1 状态可见性补充 | 百分比不变 | `2026.06.03_16-17_o1-feedback-status-summary` 让 8787 `GET /api/base/status` 和统一 `GET /api/status` 直接暴露 latest feedback samples artifact 的只读摘要与 15 分钟材料新鲜度。该摘要只做文件 `stat/read_text/json.loads`，不打开串口、不发送 `T=130/T=1/T=13/T=131/cmd_vel` 或 `/api/base/manual`，固定安全字段 fail-closed；它提升 PC/运维重启后可观测性，但不证明 HIL、ACK、safe_to_control、真实 manual、ROS feedback topic 或 `/scan` |
| O1 LiDAR scan proof 补充 | 百分比不变 | `2026.06.03_17-18_o1-lidar-scan-proof-artifact` 新增 no-motion LiDAR scan proof collector 和 8787 只读 `/api/radar/scan-proof/latest` 合同；远端 SSH 可达，`/dev/ttyACM0` 与 STC by-id 存在，8787 ready，但缺 ROS2 Humble setup、rober install setup 和 `ros2`，collector artifact 结论为 `blocked_pending_ros2_runtime` / `proof.status=blocked_or_not_observed`。该能力让 `/scan` blocker 可机器回放，不证明真实 `/scan`、`/lidar/raw_packet`、TF、SLAM/Nav2、HIL 或 `safe_to_control=true` |
| O1/O7 scan proof PC 可见性补充 | 百分比不变 | `2026.06.03_18-19_o7-scan-proof-pc-visibility` 让 PC workstation 消费 8787 `radar.scan_proof_latest` 摘要，并显示 artifact status、freshness/age、latest proof status 和 blocker。远端 readback 当前 HTTP 200、artifact loaded，但 proof 仍 `blocked_or_not_observed`；PC 不执行 collector、不启动 ROS2、不打开串口、不发送 `A5 60` 或底盘命令。该能力只提升 operator 可见性，不证明真实 `/scan`、`/lidar/raw_packet`、TF、SLAM/Nav2、HIL 或 `safe_to_control=true` |
| O1 LiDAR raw packet proof 补充 | 百分比不变 | `2026.06.03_19-20_o1-lidar-raw-packet-proof` 新增 raw packet proof collector，允许打开 LiDAR `/dev/ttyACM0 @150000` 并发送 vendor LiDAR start/stop bytes，输出 raw bytes、`0xAA55`、packet parse 和 point 统计 artifact；该 collector 不发送底盘 `T=1/T=13/T=130/T=131`、不发布 `/cmd_vel`、不调用 `/api/base/manual`、不启动 ROS2。该材料只证明 raw packet parse/material readiness，不证明真实 ROS2 `/scan`、TF、SLAM/Nav2、HIL 或 `safe_to_control=true` |
| O1 LiDAR raw packet status/readback 补充 | 百分比不变 | `2026.06.03_20-21_o1-lidar-raw-packet-status` 新增 8787 只读 `/api/radar/raw-packet-proof/latest`，并在 `/api/radar/status` 与统一 `/api/status` 的 radar 区域暴露 latest raw packet artifact 摘要。该 readback/status 只读 artifact 文件，不打开 LiDAR 串口、不发送 `A5 60`、不启动 ROS2、不发送底盘命令、不调用 `/api/base/manual`，固定 fail-closed 安全字段；它只提升 PC/OKR 材料消费能力，不证明真实 `/scan`、TF、SLAM/Nav2、HIL、ACK、`safe_to_control=true` 或 delivery success |
| O1 LiDAR ROS2 runtime bootstrap 分类 | 百分比不变 | `2026.06.03_21-22_o1-lidar-runtime-bootstrap` 增强上位机 readiness probe，输出 `lidar_ros2_bootstrap` 与 `ros2_runtime_remediation_plan`，把 `/scan` blocker 从泛化的 runtime missing 拆成 runtime/repo/install/driver/device/docker/topic 分类。远端只读 SSH probe 仍显示 `runtime_missing`、`install_missing`、`driver_missing`，下一步是提供 aarch64 ROS2 Humble runtime 或 arm64 Humble 镜像并重建 `/root/rober/onboard/install`；该 probe 不启动 driver、不打开串口、不发送底盘命令、不证明 `/scan` 或 HIL |
| O1 LiDAR ROS2 `/scan` smoke observed | O1 从约 96% 调整到约 97% | `2026.06.04_00-01_o1-upper-ros2-bootstrap-continue` 在远端完成上位机 ROS2 bootstrap/build，并运行 LiDAR-only smoke。已观察 `/scan` once/hz、`/lidar/raw_packet` once 和静态 TF；仍不证明 SLAM/Nav2、长稳、production udev、driver 优雅退出、HIL、ACK、`safe_to_control=true` 或完整上车任务。 |
| O5：云中转控制面 | 约 96% software + material acceptance queue visible in PC workstation | Task B mock control plane 已覆盖 commands/status/ack、bearer/env、mock 4G/DB/queue/OSS/CDN graceful degradation；O5 readiness live health endpoint、PC aggregate health、Node/Python external probe 均已存在；Python runner 已支持 `--output` 和 HTTPS cloud base URL 下的脱敏 TLS evidence summary，PC workstation artifact API/contract 能展示 probe status、endpoint reachability、TLS summary、blocked reasons、fail-closed safety fields；只读 `GET /api/real-material/acceptance` 与 UI `RealMaterialAcceptancePanel.vue` 已把 O5/O6 external probe artifact 与 O7 browser smoke JSON 聚合成真实材料验收队列，本轮 `2026.06.02_09-10_real-material-runbook` 增加 `artifact_freshness` 和 `collection_runbook`，operator 可见 artifact mtime/age/fresh/stale/missing 与手动采集 recipe；该入口不执行 probe、不联网、不 SSH、不 POST、不访问 `/robots/*`、不读取硬件、不创建 WebRTC session、不发送控制，固定 `safe_to_control=false`、`sends_commands=false`、`robot_control_executed=false`、`delivery_success=false`；真实生产 TLS 验收、真实公网 HTTPS、真实 4G/SIM、production DB/queue、OSS/CDN live traffic、真实 phone/browser 仍 `not_proven` |
| O6：云端核心后端 | 约 96% software + material acceptance queue visible in PC workstation | Task C mock archive/query/annotation/inference、board event publisher、algorithm feed、state path fence 已可复验；O6 archive live health、PC aggregate health、Node/Python external probe 均已存在；PC workstation 现在能读取最近一次 external probe artifact 的脱敏摘要，显示 O6 archive endpoint 的 reachability/schema/fail-closed/TLS evidence summary 状态；只读 `GET /api/real-material/acceptance` 已把 O6 archive/external probe 相关真实材料缺口纳入验收队列和 next actions，本轮新增 `artifact_freshness` 和 `collection_runbook`，把 artifact 新鲜度与手动采集 recipe 暴露给 operator；真实隧道、production DB/queue、真实 OSS upload、真实推理 runtime、真实云、真实 4G/SIM、真实 phone/browser、真实生产 TLS 验收和上车数据仍 `not_proven` |
| O7：PC 端运营调试平台 | 约 98.9% same-LAN camera/systemd + PC Live Operator consuming unified upper API live status + PC direct manual buttons/WASD/direct API path ready + camera first-screen no auto-offer + realtime radar/map split accepted | PC direct upper status/stop/feedback-request/manual path、按钮/WASD、camera 首屏 no auto-offer 和 realtime radar/map split 已进入 operator 软件验收口径。Full-Stack `tech-done.md` 记录 `npm test -- --run` 81 tests passed、`npm run build` passed、`npm run lint` passed、rendered smoke 通过；首屏包含 `实时雷达 (/scan)` 与 `实时图 (SLAM/map)`，不包含 `雷达未接入 / 等待建图`。这仍不证明真实 SLAM/map artifact、真实 `/api/base/manual`、robot ACK、真实 `/odom`/`/imu/data`/`/battery`、production path、真实 complete operator workflow、真实手控/Nav2 或完整上车任务闭环。 |

补充：截至 `2026.06.04_00-01_o1-upper-ros2-bootstrap-continue`、`2026.06.04_00-01_o1-o7-realtime-scan-map-split` 与本轮 Product/OKR 收口，O1 当前口径调整为约 97%，新增只承认首个 ROS2 LiDAR `/scan` smoke observed、`/lidar/raw_packet` once observed 和静态 TF observed；仍不承认 HIL、robot ACK 语义、真实 ROS `/odom`/`/imu/data`/`/battery`、SLAM/Nav2、长稳、production udev、左右转现场效果闭环或 `safe_to_control=true`。O7 调整为约 98.9%，只承认 PC direct manual 按钮、WASD、direct API path、camera 首屏不自动抢 offer 和 realtime radar/map split 软件/渲染验收；production path、真实 complete operator workflow、真实手控/Nav2 和完整任务闭环仍 `not_proven`。O5/O6 仍约 96%，按完成度是最低当前 Objective。

`2026.06.03_15-16_o1-feedback-artifact-readback` 继续在 O1 最低优先级上推进：`POST /api/base/feedback-samples` 现在会原子保存 latest JSON artifact，`GET /api/base/feedback-samples/latest` 只读回放该 artifact。远端真实验证仍只调用非运动 endpoint：POST samples 返回 3/3 `T=1001` observed 且 artifact write `ok=true`，GET latest 返回 artifact `status=loaded` 和 latest `t1001_observed_count=3`，顶层 readback 安全字段全部 fail-closed。O1 百分比保持约 95.5%，因为该能力只提高材料留存和回放，不证明 `/scan`、robot ACK、HIL、运动控制安全、真实 manual 或完整上车任务。

`2026.06.03_16-17_o1-feedback-status-summary` 继续在 O1 最低优先级上推进：`GET /api/base/status` 与统一 `GET /api/status` 现在通过 `base.feedback_samples_latest` 暴露 latest artifact 摘要、mtime/age、`freshness.status` 和最新 `T=1001` 多样本计数。实现只读 artifact 文件，不触发采样、不打开串口、不发送命令；O1 百分比仍保持约 95.5%，因为这只提升 status 可见性和重启后材料可观测性，不证明 `/scan`、robot ACK、HIL、运动控制安全、真实 manual、ROS feedback topic 或完整上车任务。

`2026.06.03_17-18_o1-lidar-scan-proof-artifact` 继续在 O1 最低优先级上推进：新增 LiDAR scan proof collector 和 8787 只读 readback path，让 `/scan` proof/blocker 可形成 artifact 并被 status 面消费。远端 SSH 可达，但 ROS2 Humble setup、当前 install 和 `ros2` 均缺失；collector 只写入 blocked artifact，没有启动 driver、没有发送 `A5 60`、没有读取 `/scan` 或 `/lidar/raw_packet`。O1 百分比仍保持约 95.5%，因为这只关闭了 scan proof 材料入口和 blocker 分类缺口，不证明真实 `/scan`、TF、SLAM/Nav2、HIL、ACK、safe_to_control 或完整上车任务。

`2026.06.03_18-19_o7-scan-proof-pc-visibility` 继续消费 O1 最低优先级材料：PC workstation 已把 8787 `radar.scan_proof_latest` 展示到 O7 Live Operator Panel 与 direct upper status，远端 readback 当前 HTTP 200、artifact loaded，但 latest proof 仍为 `blocked_or_not_observed`。O1/O7 百分比均不调整，因为该增量只提升 operator 可见性，不证明真实 `/scan`、`/lidar/raw_packet`、TF、SLAM/Nav2、HIL、ACK、safe_to_control 或完整上车任务。

`2026.06.03_19-20_o1-lidar-raw-packet-proof` 继续在 O1 最低优先级上推进：新增 LiDAR raw packet proof collector 和 `docs/hardware/o1_lidar_raw_packet_proof.md` runbook，支持远端 stdin 运行并生成 raw packet/point 统计 artifact。该 collector 会发送 LiDAR start/stop bytes，但不触发任何底盘/API/ROS2 控制；O1 百分比仍保持约 95.5%，因为该增量只是绕开 ROS2 runtime blocker 的前置 raw material 切片，不证明真实 `/scan`、TF、SLAM/Nav2、HIL、ACK、safe_to_control 或完整上车任务。

`2026.06.03_20-21_o1-lidar-raw-packet-status` 继续在 O1 最低优先级上推进：8787 Robot API 已把 latest raw packet artifact 接入只读 readback 和 status 摘要，PC workstation 可消费 `radar.raw_packet_proof_latest` 的 artifact status、proof status 与 raw packet/point 统计。该入口不执行 collector、不打开串口、不发送 `A5 60`、不启动 ROS2、不调用底盘控制；O1 百分比仍保持约 95.5%，因为该增量只是材料可见性和重启后可回放能力，不证明真实 `/scan`、TF、SLAM/Nav2、HIL、ACK、safe_to_control 或完整上车任务。

**已归档 Objective（软件侧完成，等待真实现场验证）：**

| Objective | 软件侧进度 | 归档原因 |
| --- | --- | --- |
| O2：可送垃圾任务 + 电梯 assisted delivery | 软件完成 ~99% | 状态机、行为链、电梯状态链、任务记录软件侧全部完成；等待真实路线/电梯/现场跑通后升回当前 |
| O3：可验证导航与固定路线 | 软件完成 ~99% | learn.launch/fixed_route/Nav2 dry-run 全部完成；等待真实路线采集、Nav2 实跑、关键帧实景证据 |
| O4：手机用户体验与量产边界 | 软件完成 ~99% | 手机 UI、地图首屏、任务下发、状态展示软件侧全部完成；等待真实 iPhone/Android 设备验收和真实送达 |

> 归档 KR 详情见 `docs/process/okr_progress_log.md`。真实现场材料到位后重新激活对应 Objective。

---

## 5. 当前最高优先级

按完成度从低到高排序：

1. **O5（约 96% software + material acceptance queue visible in PC workstation；real material not_proven）**：按完成度已与 O6 并列最低。下一轮应实际采集真实生产 TLS 验收、真实公网 HTTPS、真实 4G/SIM、production DB/queue、OSS/CDN live traffic、真实 phone/browser 材料，避免继续只扩 runbook/status 面。
2. **O6（约 96% software + material acceptance queue visible in PC workstation；real material not_proven）**：与 O5 并列最低。下一步优先把 archive core 推进到真实隧道、production DB/queue、真实 OSS upload、真实推理 runtime、真实云、真实 4G/SIM、真实 phone/browser、真实生产 TLS 验收和上车数据。
3. **O1（约 97% software_reference + ttyS5 material observed + LiDAR ROS2 `/scan` smoke observed；HIL / ACK / SLAM/Nav2 / 长稳 / safe_to_control not_proven）**：O1 已从 `/scan` not_proven 推进到首个 LiDAR-only smoke observed，但仍是硬件主链路最大风险项。下一步分两条：LiDAR 线补 driver 优雅退出、production udev、长稳 smoke、SLAM/Nav2 消费与地图质量证据；底盘线在现场看护、物理净空、人工急停可用时，经 8787 `/api/base/manual` 做低速短 pulse，并采集 status/manual/stop/post-status、operator report、ACK 或 `T=1001`、日志与安全复位证据。未完成前不能提升为 HIL pass 或 `safe_to_control=true`。
4. **O7（约 98.9% same-LAN camera/systemd + PC direct manual buttons/WASD/direct API path ready + camera first-screen no auto-offer + realtime radar/map split accepted；production workflow not_proven）**：PC/operator 软件入口继续保持。O1 首个 `/scan` smoke 已 observed 后，O7 已完成 realtime radar/map split 软件/渲染验收；下一步不再是拆 UI，而是补真实 SLAM/map artifact、production path、真实 `/api/base/manual` 受控灰度、ACK/HIL、reboot 自恢复、真实 8787/browser 复跑、云 relay/TURN/auth/phone/browser production path、弱网、ASR/TTS、手控/Nav2 和完整上车任务闭环。

> 当前 90%+ 只代表 mock/software completion。真实材料未完成时，任何 Objective 都不得表述为真实硬件、真实生产云、真实 4G、真实 OSS/CDN、真实 PC/手机或真实上车完成。

---

## 6. OKR 完成路线

### 近期（O6 MVP）

- 确定隧道方案（frp/WireGuard/ngrok），Orange Pi → 云端稳定连通，断线自动重连。
- 云端建任务/事件存档表，小车侧完成后 POST 到云端，PC/手机可查询。
- 大对象走 OSS，云端只存引用。
- 提供最小 REST API：任务列表、任务详情、轨迹数据。

### 近期（O7 MVP）

- PC 端接入云端 API，展示历史任务列表和轨迹回放。
- 实时地图接入 ROS2 位置数据（通过云端转发或本地直连调试）。
- LAN-only WebRTC camera smoke 已完成机器级 `/offer` answer、connected、`first_frame_received=true`、640x480 first_frame 和连续自检 peer cleanup；PC Chromium browser smoke 已证明同 LAN首帧、30s smoke 和 180s long-stability。`2026.06.02_20-21` 修复 camera source guardrail 后，same-LAN 180s browser material 已 `accepted`：首帧 1928ms、估算 13.92 fps、`framesDecoded=2507`、console/page errors 为 0、peer close 后 active connections 为 0。`2026.06.03_01-02` 已补远端 8088 camera smoke systemd persistence active 证据。下一步补产品入口安全边界、公网/云 relay、TURN、鉴权、phone/browser production path、reboot 后自恢复和 browser 180s 复跑证据。
- 基本标注界面：拉取待标注帧，提交标注结果。

### 中期

- 模型推理上云（电梯门开/关、楼层识别）；推理结果写入存档。
- PC 端电梯状态实时展示，ASR/TTS 调试界面。
- PC 端手控和自动寻路下发（走云端 API）。
- O5 接入真实部署（production DB/queue/OSS/CDN）。
- LiDAR 从 `source=software_reference` + mock skeleton 推进到真实串口 `/scan`、TF、Nav2/SLAM 消费链路，但未完成前不得作为 O1 真实硬件闭环。

### 后期（真实现场验证，激活归档 Objective）

- 真实 WAVE ROVER 与真实 LiDAR 上车实测，O1 闭环。
- 真实路线采集 + Nav2/固定路线实跑，激活 O3。
- 真实电梯场景验证，激活 O2。
- 真实手机/browser 验收，激活 O4。
