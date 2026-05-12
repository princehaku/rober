# ros_rbs P9 项目设计与前瞻 OKR

## 1. 北极星

把 `ros_rbs` 做成一台面向普通手机用户的低成本 ROS2 自主垃圾投递机器人：用户把垃圾交给小车后，小车沿固定路线出发，把垃圾送到垃圾站/垃圾桶点位，必要时跨楼层进出电梯，再安全返回或等待下一次任务，而不是一次性 demo，也不是依赖机械臂到处捡垃圾的机器人。

**跨楼层送垃圾是 MVP 必须能力**：在受控楼宇内，小车识别电梯是否开门，进入电梯后通过语音请求好心人帮忙按目标楼层，持续识别是否到达目标楼层，并在目标楼层开门时尽快驶出。这个能力服务于"普通用户只用手机，小车完成跨楼层 trash delivery"的北极星，**纳入 MVP 必须实现范围，但实机能力需要在受控场景验证**；它不默认要求机械臂、昂贵传感器或新增下位机硬件，人工协助（请旁人帮忙按楼层按钮）仍是产品流程的一部分。

**手机端是普通用户唯一入口**：必须美观、能直接使用、不依赖命令行/SSH/ROS2 知识。4G 场景下走云端中转，手机和小车不要求处于同一 WiFi。本地 `operator_gateway` 仅作 fallback 调试入口，正式手机入口必须满足美观与可用性验收口径。

当前项目已经具备 6 个核心包的雏形：

- `ros2_trashbot_interfaces`：msg/srv/action 契约层。
- `ros2_trashbot_hardware`：Orange Pi 到 WAVE ROVER ESP32 下位机的串口桥。
- `ros2_trashbot_nav`：Nav2、航点、地图、固定路线、关键帧调试。
- `ros2_trashbot_vision`：摄像头垃圾检测。
- `ros2_trashbot_behavior`：任务编排、送达/投放 action。
- `ros2_trashbot_bringup`：学习、自主、完整系统启动。

P9 视角下，项目下一阶段的核心不是继续堆节点，而是把“能跑”升级为“可验证地可靠交付垃圾”：协议可信、固定路线可靠、任务可恢复、用户交互足够简单、数据可复盘、硬件假设可追溯。

## 2. 战略定位

1. **目标用户是不会电脑和硬件的普通人**
   - 用户默认只有手机，不要求会 SSH、ROS2、串口、地图文件或硬件调试。
   - 产品体验必须围绕手机端的一键发车、状态查看、异常提示、人工接管和售后诊断设计。
   - 语音、喇叭和简单灯光/提示音用于降低使用门槛：提示“请放入垃圾”“准备出发”“已到垃圾站”“需要人工处理”等关键状态。

2. **核心任务是“送垃圾”，不是“捡垃圾”**
   - MVP 任务闭环是：用户放入垃圾 -> 手机/语音确认 -> 小车出发 -> 到达垃圾站/垃圾桶点位 -> 完成投放/提醒人工取走 -> 返回或待命。
   - 当前预算和机构条件下不承诺机械臂抓取、地面散落垃圾拾取、复杂分类分拣。
   - 摄像头优先用于路线辅助、站点识别、障碍/异常记录和远程查看；垃圾检测能力作为后续增强，不作为核心价值前提。

3. **预算有限，必须按量产约束做取舍**
   - 默认硬件边界是：小车底盘、上位板、随身 WiFi、摄像头、麦克风、喇叭，不把昂贵传感器、机械臂、深度相机、多板卡作为默认方案。
   - 所有新增能力必须回答三个问题：是否降低普通用户使用难度、是否提高送达成功率、是否适合低成本量产。
   - 硬件事实来源采用 `docs/vendor/VENDOR_INDEX.md`；本文仅写产品战略，不新增引脚、电压、串口设备名、波特率或机械尺寸假设。

4. **电梯能力是 MVP 必须实现的 assisted delivery，而不是无人全自动乘梯**
   - 跨楼层送垃圾是 MVP 必须能力：小车看门、进门、语音求助按键、判断目标楼层、开门后驶出，必须进入主 `task_orchestrator` 状态机，不再作为可选 H2 分支默认关闭。
   - 实机完成度需要在受控场景中按"文档/合同 → 软件 dry-run → 受控实景"三层验收逐步推进；OKR 写明必须并不等于已完成实机闭环。
   - 小车不按电梯按钮，不改造电梯，不新增机械臂或电梯控制硬件；人工协助（请旁人按目标楼层）仍是产品流程边界。
   - 能力归属在 Orange Pi/ROS2 上位机的行为、感知和语音编排，ESP32/WAVE ROVER 下位机只保持底盘执行与反馈职责。

5. **4G 数据通路走云端中转，不走手机直连 WiFi**
   - 正式 4G 链路：手机 web/app → 云端 API → 小车 `remote_bridge` outbound polling → ROS2 behavior。
   - 云端服务端基线：4C 8G 无 GPU，公网入口，仅作命令/状态/ACK 控制面中转；详见 `docs/product/cloud_4g_infrastructure.md`。
   - 图片大对象通过阿里云 OSS（bucket `bytegallop`）+ CDN（`https://cdn.bytegallop.com/rober/`）流转，云中转节点不承担大文件带宽。
   - 控制面任何时候都不暴露 `/cmd_vel`、不接受 inbound 直连小车。敏感凭证（OSS AK/SK、bearer token）只走 `.env`/环境变量，不进入仓库。

## 3. 设计原则

1. **硬件事实必须本地可追溯**
   - 涉及 WAVE ROVER、ESP32、Orange Pi、UART、波特率、JSON 指令、速度映射、反馈协议、引脚、电压、固件和机械尺寸时，以 `docs/vendor/VENDOR_INDEX.md` 及其指向资料为准。
   - 当前底盘通信应按 WAVE ROVER 官方 UART newline-delimited JSON 处理，不再继续扩展旧二进制协议假设。

2. **ROS2 接口稳定，内部实现可替换**
   - 上层继续面向 `/cmd_vel`、`/odom`、`/imu/data`、`/battery`、`/trashbot/patrol`、`/trashbot/collect_trash` 等 ROS2 接口。
   - 底层硬件桥、视觉模型、导航实现可以迭代，但不能随意破坏接口契约。

3. **先送达闭环，再智能**
   - 第一优先级是用户交付垃圾、装载确认、固定路线导航、到站投放/提醒、返回/待命的完整闭环。
   - 复杂模型、动态规划、自动识别散落垃圾、多机器人协同都必须建立在稳定送达闭环和可观测数据之上。

4. **每个关键行为都要可观测、可回放、可解释**
   - 任务状态、导航目标、检测结果、失败原因、硬件反馈都要能落日志或状态文件。
   - 路线、关键帧、检测样本和失败案例要形成持续改进数据集。

5. **文档同步更新与工程质量**
   - 任何功能开发、修复或架构调整，必须同步更新 `docs/` 目录下的相关文档。文档必须始终反映项目的最新状态。
   - 采用中文注释规范：代码中的所有技术注释必须使用**中文**，且注释比例必须**超过 20%**，以确保代码的可读性和可维护性。

6. **默认安全、低速、可停**
   - 任何自主行为必须有停止路径、超时策略、失败恢复策略。
   - 未经硬件验证的能力只能以参数关闭或 dry-run 形式存在。

6. **量产优先，少硬件、少配置、少售后**
   - 任何功能默认要考虑批量装机、远程诊断、参数模板、用户误操作和售后成本。
   - 能用软件流程、固定路线、手机交互和语音提示解决的问题，不优先增加昂贵硬件。

## 4. 2026 H1 OKR

### Objective 1：打通官方硬件协议，建立可信底盘控制层

**目标说明**：让 Orange Pi 通过 ROS2 以官方 WAVE ROVER UART JSON 协议稳定控制底盘，并发布最小可用状态反馈。

**Key Results**

- KR1：`ros2_trashbot_hardware` 默认使用 UTF-8 JSON + `\n` 与 ESP32 通信，启动时配置 echo、反馈间隔和反馈流。
- KR2：`/cmd_vel` 默认映射到 `T=1` 左右轮速度命令，`T=13` ROS 控制模式只通过参数启用，并标注需要硬件验证。
- KR3：解析 `T=1001` 底盘反馈，发布 `/imu/data` 和 `/battery`，并明确 `/odom` 是临时命令积分还是实测里程计。
- KR4：硬件桥协议单元测试覆盖 JSON 编码、速度映射、反馈解析、坏数据容错。
- KR5：launch 参数暴露 `serial_port`、`serial_baudrate`、`command_mode`、`track_width_m`、`max_wheel_speed_mps`，不硬编码 Orange Pi 实际设备名。

### Objective 2：把“巡逻 demo”升级成可恢复送垃圾任务闭环

**目标说明**：让行为层不再只是 sleep 和占位逻辑，而是能完成“用户已把垃圾交给小车”之后的送达任务：确认装载、导航到垃圾站、投放或提醒人工取走、失败后恢复。

**Key Results**

- KR1：`task_orchestrator` 状态机覆盖 `IDLE -> LOADED -> DELIVERING -> DROPOFF -> RETURNING -> IDLE/ERROR` 的真实转换。
- KR2：送达 action 使用 garbage station waypoint/fixed route 输入，不再使用固定 `waypoints_total = 5` 占位逻辑。
- KR3：装载确认支持手机按钮、语音/麦克风触发或本地参数模拟；在没有可靠传感器前，不把“自动判断是否装了垃圾”写成强依赖。
- KR4：投放失败、导航失败、未找到垃圾站/垃圾桶点位、超时取消都返回明确 action result 和 error message。
- KR5：每次任务产出可复盘记录：起止时间、目标、状态转移、失败原因、导航结果、检测快照引用。
- KR6：行为状态机必须覆盖 elevator assisted delivery 完整状态链：等待电梯开门 → 进入电梯 → 语音请求"你好,好心人,.我要去1楼扔垃圾,请帮我按一下电梯," → 等待目标楼层 → 目标楼层开门后驶出 → 继续送达；失败、超时、未确认目标楼层、未开门必须返回明确 action result + error code，并触发人工接管。MVP 写明必须并不等于已完成受控实景验证，仍需按三层验收推进。

### Objective 3：建立可验证导航与固定路线能力

**目标说明**：让学习路线、固定路线、自主往返垃圾站和关键帧调试形成一条清晰可重复的工程流程。

**Key Results**

- KR1：`learn.launch.py` 能稳定完成 SLAM/人工驾驶/航点或 route 数据采集流程。
- KR2：`route_data_recorder`、`route_csv_to_yaml`、`fixed_route_autonomy` 的输入输出格式在文档中固化，并有静态/单元测试覆盖。
- KR3：fixed route dry-run 能在无 Nav2/无硬件环境下验证路线读取、关键帧匹配和状态输出。
- KR4：自主模式能选择 Nav2 waypoint 送达或 fixed route 送达，两者参数边界清晰。
- KR5：关键帧调试页面能展示当前位置、目标点、匹配状态、失败原因和最近一次任务状态。

### Objective 4：把摄像头从“捡垃圾检测”收敛为送达任务的可选感知能力

**目标说明**：当前 MVP 不随包发布默认散落垃圾 detector。摄像头能力先作为固定路线、垃圾站识别、障碍/异常记录、远程查看和数据沉淀的未来可选模块；垃圾检测只作为增强能力，不作为没有机械臂阶段的核心闭环前提。

**Key Results**

- KR1：`TrashStatus` 字段语义作为未来可选感知 contract 保留：坐标系、置信度、垃圾类型、是否垃圾桶、时间戳。
- KR2：当前 launch 不默认启动散落垃圾 detector；未来恢复视觉节点必须有显式 launch flag、参数边界和验证证据。
- KR3：未来视觉样本目录和 manifest contract 保留为可选诊断引用；当前 MVP 不声明默认生产原图、标注图或检测 JSON。
- KR4：行为层只依赖稳定感知契约，不直接耦合具体视觉算法；没有机械臂前，不把散落垃圾拾取作为任务成功标准。
- KR5：形成一份感知升级评估表：OpenCV、YOLO、RT-DETR、深度相机各自成本、算力、鲁棒性、量产成本和落地条件。
- KR6：感知 contract 必须覆盖电梯门开/关、是否已进入轿厢、目标楼层到达证据、目标楼层开门可驶出证据；P0 字段（door_open / inside_car / target_floor_reached / target_floor_door_open）作为 MVP 必交付，P1 字段（楼层显示屏识别、快照引用）作为后续增强。优先用现有摄像头识别/语音/日志证据验证，不把新硬件作为默认前提。

### Objective 5：建立手机用户体验与低成本量产边界

**目标说明**：让不会电脑和硬件的用户可以用手机完成核心任务，同时把硬件方案控制在低成本、可批量装配、可售后诊断的范围内。

**Key Results**

- KR1：定义手机端最小流程：连接设备 -> 选择/确认垃圾站 -> 确认已放入垃圾 -> 一键发车 -> 查看状态 -> 处理异常。
- KR2：定义语音/喇叭提示词和状态触发点，覆盖待装载、准备出发、行驶中、到达、失败、需要人工接管。
- KR3：形成量产硬件约束表，默认只包含小车底盘、上位板、随身 WiFi、摄像头、麦克风、喇叭；新增硬件必须有成本、装配、维护和软件收益说明。
- KR4：建立远程诊断最小数据包：软件版本、地图/路线版本、最近任务状态、失败原因、关键日志、摄像头快照引用。
- KR5：形成用户验收标准：普通用户不接触命令行、不插线调试、不理解 ROS2，也能完成一次送垃圾任务并知道失败时该怎么做。
- KR6 ：跨楼层 trash delivery 的手机/语音体验必须落地：用户只选择目标楼层和垃圾站，小车在电梯内主动求助按键，失败时能在手机端解释"未开门、未确认目标楼层、需要人工接管"；手机端不暴露 raw JSON 或 ROS topic 名。
- KR7 ：手机端 UI **美观且能直接使用**：视觉系统统一（配色 token、字号、间距、卡片、按钮态）、主操作主路径 ≤ 3 步、文案中文优先、iPhone/Android 主流尺寸适配、最小可点击区域 ≥ 44pt、首屏可交互 < 3 秒。当前可用流程与 readiness gate 口径见 `docs/product/mobile_user_flow.md`；本地 phone-first HTML 仍是 fallback 调试入口，正式手机端必须另行完成真实手机浏览器/设备验收。

### Objective 6：4G 云中转 + OSS/CDN 数据通路产品化

**目标说明**：让小车通过 4G 走云端中转完成手机用户控制与数据回传，不依赖手机和小车处于同一 WiFi。图片/快照/任务记录类大对象通过阿里云 OSS + CDN 沉淀，云中转节点只承担轻量 JSON 控制面。

**Key Results**

- KR1：云中转服务端最小契约（commands/status/ack）按 `trashbot.remote.v1` 实现：HTTPS、outbound polling 优先，幂等键 + bearer token 鉴权，不暴露 `/cmd_vel`、不接受 inbound 直连小车。
- KR2：服务端基线规格写入 `docs/product/cloud_4g_infrastructure.md`，包含 4C 8G 无 GPU、SSH 端口、网络方向、防火墙策略、容量边界、运维与产品流量分离。
- KR3：OSS 写入策略明确：bucket `bytegallop`，region `oss-cn-hangzhou`，对象前缀 `rober/<robot_id>/<date>/<task_id>/`；小车侧写入使用 STS 临时凭证或受限 AK，主 AK 不直放小车；超期对象可回收。
- KR4：CDN base URL `https://cdn.bytegallop.com/rober/` 只作为公开只读视图入口，diagnostics 引用以 URL 形式给出，不在小车本地暴露密钥；CDN 不承担私有任务数据，私有数据走云端 API 网关 + bearer。
- KR5：凭证管理 contract：`.env` 不入仓库，`.env.example` 仅占位；服务端、CI、上车机器人均通过环境变量注入；密钥泄露有 rotate 流程。任何 tracked 文件不得包含真实 `OSS_ACCESS_KEY_SECRET`、bearer token 或 root 密码。
- KR6：4G 中断、OSS 写失败、CDN 不可达三类失败必须有 graceful degradation：本地 operator gateway fallback 可用，状态可恢复，任务不丢；远程诊断能区分"网络问题"与"机器人问题"。

## 4.1 当前 OKR 进度快照

更新时间：2026-05-11 21:14 Asia/Shanghai。

补充：`2026.05.11_10-11_hil-docker-preflight-to-real-run` 继续执行 O1→O2→O3 顺序。O1 Docker preflight 因 `osrf/ros:humble-desktop` 拉取/解包异常 blocked，且本机仍无真实串口硬件；`2026.05.11_10-11_o2-task-recovery-route-replay-docker-proof` 只补强 O2/O3 same-`evidence_ref` 软件复盘支撑，不声明 `hil_pass`。

补充：`2026.05.11_21-22_o1-docker-humble-preflight-unblock` 增强 Docker/Humble preflight 诊断，确认 Docker daemon 与 `desktop-linux` builder 可用，当前阻断归因为 registry mirror/proxy 对 `docker.io/osrf/ros:humble-desktop` metadata/layer 返回 `text/html`。本轮仍无真实串口设备，只记录 `software_proof` readiness/blocked evidence，不新增 `hil_pass`。

| Objective | 当前进度 | 本轮新增证据 | 剩余关键缺口 |
| --- | --- | --- | --- |
| Objective 1 硬件协议可信底盘 | 约 75% | `sprints/2026.05.11_21-22_o1-docker-humble-preflight-unblock` 已增强 Docker preflight；`SKIP_COLCON=1 bash scripts/docker_humble_build.sh` 输出 Docker Desktop 4.45.0、Engine 28.3.3、`desktop-linux` builder 可用、registry mirrors 列表，并将 `osrf/ros:humble-desktop` 的 `encountered unknown type text/html` 归因为 `registry mirror/proxy`。`hardware_smoke_wave_rover.py --status` 继续输出 `pyserial_available=true`、`hil_ready=false`、`blocked_reason=no_serial_candidates_found` 与 required evidence files/source boundary。 | 仍缺本轮真实 WAVE ROVER `hil_pass` evidence packet（`command.txt`/`serial.log`/`feedback_T1001.log`）与 `/odom`、`/imu/data`、`/battery` 实机样本；还需 operator 关闭/更换 Docker registry mirror/proxy 或换网络/cache 后重建镜像，并接入真实串口设备。 |
| Objective 2 可恢复送垃圾任务闭环 | 约 77% | `2026.05.11_10-11_o2-task-recovery-route-replay-docker-proof` 补强 O1 real run 后的 O2 消费链路：`task_record.route_progress` 顶层持久化，`nav_results[-1].evidence.route_progress`、`failure_code`、`state_transition_history`、`human_intervention_required`、`evidence_ref` 可严格对账；targeted behavior tests 为 `Ran 46 tests ... OK`。 | 仍缺真实 Nav2/fixed-route 运行下的任务复盘 evidence；O1 `hil_pass` 未解锁前，O2 不能声明实机 closed。 |
| Objective 3 可验证导航与固定路线 | 约 77% | `scripts/evidence_crosscheck.py` 支持 `--task-record-dir` 按同一 `evidence_ref` 自动查找 task record，并在缺 route-level 字段时返回 mismatch；本轮软件样例输出 `CHECK summary: mismatches=0`，缺匹配 task record 样例返回非 0。 | 仍缺真实路线采集、Nav2 waypoint/fixed-route 实跑、关键帧实景证据，以及与 O1 HIL 同一 `evidence_ref` 的上车复账。 |
| Objective 4 感知模块产品化 | 约 76% | 本轮补齐电梯场景 dry-run evidence schema：`door_open`、`door_closed_or_unknown`、`inside_elevator`、`target_floor_confirmed`、`target_floor_unconfirmed`、`safe_to_exit`、`unsafe_to_exit`；visual gate 只输出保守离线证据，即使 passed 也保持目标楼层未确认口径；Autonomy targeted `Ran 19 tests ... OK`，py_compile 和 scoped diff check 通过。此前 review progress metrics 已让视觉复核进度进入 operator/diagnostics | 仍未完成真实硬件/HIL、真实相机采集与上车验证；没有相机门识别、楼层 OCR、目标楼层到达或可驶出实景证据；当前证据是软件/离线环境，不等于实机闭环 |
| Objective 5 手机体验与量产边界 | 约 80% | 本轮补齐 `elevator_assist` operator status/diagnostics 和手机可读状态：等待电梯、请求帮忙按楼层、等待目标楼层、目标楼层未确认、需要人工接管；speaker prompt contract 保留 `你好,好心人,.我要去1楼扔垃圾,请帮我按一下电梯,`，Full-stack targeted `Ran 53 tests ... OK`，py_compile 和 scoped diff check 通过。此前 operator 页面与 diagnostics 已可观察人工复核进度 | 仍未完成真实硬件/HIL、真实相机/上车验证与普通用户实机验收；本轮只有 speaker prompt 字段 contract，没有真实 TTS/喇叭播放；跨楼层手机体验尚未经过用户侧实机验收 |



更新时间：2026-05-12 14:33 Asia/Shanghai。

补充：`2026.05.12_04-05_remote-auth-degradation-gate` 完成 local/mock cloud bearer auth gate、`remote_readiness.auth_state/degradation_state/safe_phone_copy`、敏感字段过滤，以及 `remote_bridge` 对 cloud unreachable/auth failed/malformed response 的保守降级和 cursor safety。Task A targeted operator tests `Ran 66 tests ... OK`，Task B remote bridge tests `Ran 23 tests ... OK`，Task C 合并 smoke `Ran 89 tests in 25.691s OK`，相关 `py_compile` 与 scoped `git diff --check` 通过。该证据边界仍是 `software_proof_docker_only` / local mock cloud，不提升 O1/HIL、真实云、真实 4G、OSS/CDN 或真实送达完成度。

补充：`2026.05.12_05-06_remote-cloud-service-docker-proof` 完成 independent Docker/local HTTP relay service proof、file-backed persistence、bearer auth、phone-safe errors、robot client compatibility，并补齐 `docs/product/cloud_4g_infrastructure.md` 的云服务端基线、网络方向、OSS/CDN 目标和 Docker proof 边界。Task A relay tests `Ran 6 tests ... OK`，Task B robot compatibility tests `Ran 31 tests ... OK`，Task C merged integration fence `Ran 37 tests in 17.884s OK`，相关 `py_compile` 与 scoped `git diff --check` 通过。该证据边界仍是 `software_proof_docker_only`，不提升真实云、HTTPS/TLS、公网入口、真实 4G/SIM、OSS/CDN、生产 DB、真实送达、Nav2/fixed-route、WAVE ROVER 或 HIL。

补充：`2026.05.12_06-07_remote-cloud-entry-docker-deploy` 将 independent relay 推进到 `software_proof_docker_deploy`：新增 Dockerfile/compose/env 入口、`/healthz`、`/readyz`、state store writable check、phone-safe failure redaction self-check 和 Docker smoke。Task A/B `test_remote_cloud_relay.py` 输出 `Ran 8 tests in 4.167s OK`，Task C `test_remote_bridge_protocol.py` + `test_remote_bridge.py` 输出 `Ran 31 tests in 15.223s OK`，相关 `py_compile`、Docker smoke 和 scoped `git diff --check` 通过。该证据只支持 O6 Docker deploy/readiness/robot compatibility 小幅进展，O5 只获得 phone-safe readiness 支撑；不等于真实云、HTTPS/TLS、公网、4G/SIM、OSS/CDN、正式手机 UI、Nav2/fixed-route、WAVE ROVER 或 HIL。

补充：`2026.05.12_07-08_remote-cloud-production-preflight` 将 O6 从 Docker deploy/readiness 推进到 `software_proof_docker_preflight_gate`：新增 production preflight gate，能在 Docker/local 环境下以 blocked/warning/pass 方式暴露 credential provisioning、TLS/public ingress、OSS/CDN、state store 和 phone-safe output 缺口；Docker smoke 继续证明 command/status/ack 主路径可用，robot compatibility fence `Ran 31 tests in 15.218s OK`。该证据只支持 O6 小幅上调到约 30%；O5 仅获得 phone-safe readiness 支撑，不提升；O1/O2/O3/O4 不提升。本轮没有真实云、真实 4G/SIM、HTTPS/TLS 公网实证、OSS/CDN 实流量、生产 DB/queue、Nav2/fixed-route、WAVE ROVER 或 HIL。

补充：`2026.05.12_08-09_remote-cloud-sqlite-state-proof` 将上一轮仍偏 file-backed/preflight 的 O6 状态层推进到 SQLite-backed state store software proof：`TRASHBOT_REMOTE_CLOUD_STATE_BACKEND=sqlite` 下 command/status/ack 可跨 store reopen 或 relay/container restart 恢复，preflight 输出 `evidence_boundary=software_proof_docker_sqlite_state_store`，并继续阻断 production DB/queue、多实例一致性、backup/restore 与 disaster recovery 缺口。Task A relay tests 输出 `Ran 16 tests in 5.803s OK`，SQLite Docker smoke 通过；Task B remote bridge compatibility 输出 `Ran 31 tests in 15.221s OK`，确认 status-command-ack HTTP shape 与 cursor/ACK 保守语义未退化。该证据只支持 O6 从约 30% 保守小幅上调到约 32%；O5/O1/O2/O3/O4 不提升。本轮仍没有真实云、真实 4G/SIM、HTTPS/TLS 公网实证、OSS/CDN 实流量、生产 DB/queue、多实例、正式手机 UI、Nav2/fixed-route、WAVE ROVER 或 HIL。

补充：`2026.05.12_09-10_remote-cloud-backup-restore-drill` 在 SQLite state store proof 之上完成 Docker/local backup/restore drill：新增 backup artifact、checksum、restore 到新 SQLite state path、CLI drill 和 preflight artifact check；Task A relay unit fence 输出 `Ran 19 tests ... OK`，Docker smoke 输出 `backup_status=passed`、`restore_status=passed`、`drill_status=passed` 与 `evidence_boundary=software_proof_docker_backup_restore_drill`，Task B robot compatibility 输出 `Ran 31 tests in 15.219s OK`，相关 `py_compile` 与 scoped `git diff --check` 通过。该证据只支持 O6 从约 32% 保守小幅上调到约 34%；O5/O1/O2/O3/O4 不提升。本轮仍没有真实云、真实 4G/SIM、HTTPS/TLS 公网入口、OSS/CDN 实流量、生产 DB/queue、多实例一致性、生产备份策略、真实灾备、正式手机 UI、Nav2/fixed-route、WAVE ROVER 或 HIL。

补充：`2026.05.12_10-11_phone-ui-readiness-gate` 完成 O5 phone UI readiness gate 的本地/Docker software proof：`/api/status` 新增兼容字段 `phone_readiness`（`trashbot.phone_readiness.v1`），本地 operator 首屏聚合 local delivery、action permissions、local/mock `remote_readiness`、可选 preflight 和 backup/restore drill 摘要，覆盖 `status_stale`、`command_pending`、`auth_failed`、`cloud_unreachable`、`malformed_response` 与 ACK 不等于 delivery success 的用户解释。Full-stack targeted tests 输出 `Ran 68 tests in 15.452s OK`，`operator_gateway_http.py` py_compile 通过，scoped `git diff --check` 通过。该证据只支持 O5 从约 33% 保守上调到约 38%；O6 保持约 34%，O1/O2/O3/O4 不提升。本轮仍没有生产手机 app、真实手机设备/浏览器验收、真实云、真实 4G/SIM、HTTPS/TLS 公网入口、OSS/CDN 实流量、Nav2/fixed-route 送达、WAVE ROVER 或 HIL。

补充：`2026.05.12_11-12_remote-cloud-oss-cdn-manifest-proof` 完成 O6 OSS/CDN manifest artifact software proof：manifest 可生成并校验 bucket `bytegallop`、region `oss-cn-hangzhou`、prefix `rober/<robot_id>/<date>/<task_id>/`、CDN base URL `https://cdn.bytegallop.com/rober/`、对象引用、checksum 和 phone-safe 输出；preflight 新增 `oss_cdn_manifest` check，有效 artifact 使 evidence boundary 到 `software_proof_docker_oss_cdn_manifest`，同时整体仍按生产缺口保持 blocked。Full-stack targeted tests 输出 `Ran 23 tests in 6.388s OK`，`remote_cloud_relay.py` py_compile 通过，CLI smoke 输出 manifest generate `ok=True`、preflight consume `oss_cdn_manifest=pass`，Robot compatibility 输出 `Ran 31 tests in 15.132s OK`，scoped diff check 通过。该证据只支持 O6 从约 34% 保守小幅上调到约 36%；O1/O2/O3/O4/O5 不提升。本轮仍没有真实 OSS upload、STS issuance、CDN origin fetch、lifecycle policy、production account、真实云、真实 4G/SIM、HTTPS/TLS 公网入口、生产 DB/queue、正式手机 UI 消费 manifest、Nav2/fixed-route、WAVE ROVER 或 HIL。

补充：`2026.05.12_12-13_remote-oss-cdn-phone-consumption-gate` 完成 O6 phone/API manifest consumption gate：operator 首屏显示 phone-readable 诊断对象引用状态 `诊断对象引用已准备/缺失/损坏/过期` 和 retry hint，`/api/status.phone_readiness.oss_cdn_manifest` 与 `/api/diagnostics.oss_cdn_manifest` 共用 summary helper，覆盖 `ready/missing/invalid/stale`，并保留 `not_proven` 与 `software_proof_docker_phone_manifest_consumption` 边界。Full-stack targeted tests 输出 `Ran 62 tests in 16.283s OK`，remote cloud relay tests 输出 `Ran 24 tests in 6.374s OK`，py_compile 与 scoped diff check 通过；Robot compatibility fence 输出 `Ran 31 tests in 15.206s OK`，仅一次 `ResourceWarning` 不影响通过。该证据只支持 O6 从约 36% 保守小幅上调到约 38%；O1/O2/O3/O4/O5 不提升。本轮仍没有真实 OSS upload、STS issuance、CDN origin fetch、真实云、真实 4G/SIM、HTTPS/TLS 公网入口、生产 DB/queue、正式手机 app/真实手机浏览器验收、Nav2/fixed-route 送达、WAVE ROVER 或 HIL。

补充：`2026.05.12_13-14_phone-command-safety-browser-gate` 完成 O5/O6 phone command safety browser/API gate：`/api/status.phone_readiness.command_safety` 新增 `trashbot.command_safety.v1`，operator 首屏 Start、Confirm dropoff、Cancel、Diagnostics 消费 `command_safety.actions.*.enabled`，覆盖 ready、status stale、command pending、auth failed、cloud unreachable、malformed response、manifest missing/invalid/stale 和 manual takeover；ACK 文案明确只代表 command accepted/processing evidence，不等于 delivery success。Full-stack targeted tests 输出 `Ran 64 tests in 17.299s OK`，Robot compatibility 输出 `Ran 31 tests in 15.230s OK`，py_compile 和 scoped diff check 通过。Browser/API fence 采用 HTTP handler/unit test 覆盖 HTML 按钮 wiring 和 API payload shape，没有真实浏览器/手机设备截图。该证据只支持 O5 从约 38% 保守上调到约 40%、O6 从约 38% 保守上调到约 39%；O1/O2/O3/O4 不提升。本轮仍没有真实手机 app、真实手机浏览器/设备验收、真实云、真实 4G/SIM、HTTPS/TLS 公网入口、真实 OSS upload、CDN origin fetch、生产 DB/queue、Nav2/fixed-route 送达、WAVE ROVER 或 HIL。

补充：`2026.05.12_14-15_remote-network-recovery-drill` 完成 O6 Docker/local network recovery drill：Task A relay/phone-safe 侧新增 network recovery drill artifact、preflight consumption、`/api/status.phone_readiness.network_recovery` 和 `/api/diagnostics.network_recovery_drill` 摘要，targeted tests 输出 `Ran 93 tests in 23.778s OK`，CLI drill 输出 `ok=true`、`network_recovery_status=passed`、`step_count=4`、`evidence_boundary=software_proof_docker_network_recovery_drill`，preflight consumption 输出 `network_recovery_drill=pass`、`software_proof_ready=true`、`production_ready=false`、`overall_status=blocked`；Task B robot compatibility fence 输出 `Ran 33 tests in 16.192s OK`，确认 malformed status/ACK response 和 ACK post failure 不触发本地 action、不推进/持久化 cursor，恢复后同一 command 只重发缓存 terminal ACK。该证据只支持 O6 从约 39% 保守上调到约 41%；O5 只记录 phone-safe network recovery 摘要支撑但不提升；O1/O2/O3/O4 不提升。本轮仍没有真实云部署、HTTPS/TLS、公网入口、真实 4G/SIM、生产鉴权/rotate、STS/受限 AK、真实 OSS upload、CDN origin fetch、生产 DB/queue、多实例一致性、正式手机 app/真实手机设备验收、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

补充：`2026.05.12_15-16_phone-browser-acceptance-gate` 完成 O5 本地真实 Chrome browser acceptance gate：`390x844` 与 `768x900` 两组 viewport 均输出 `hit_area_status=passed`、`overlap_status=passed`、`overflow_status=passed`、`ack_copy_visible=true`、`diagnostics_accessible=true`、`primary_actions_disabled=true`、`first_screen_buttons_visible=true`、`phone_safe_status=passed`，summary artifact `sprints/2026.05.12_15-16_phone-browser-acceptance-gate/evidence/phone_browser_acceptance_summary.json` 为 `ok=true`，browser 为 `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`。Full-stack targeted tests 输出 `Ran 73 tests in 17.910s OK`，py_compile 与 scoped diff check 通过。该证据只支持 O5 从约 40% 保守上调到约 43%，因为 KR7 从 API/handler proof 推进到真实本地浏览器 proof；O6 保持约 41%，O1/O2/O3/O4 不提升。本轮仍没有真实手机设备 Safari/Chrome、正式 app、真实云/4G、OSS/CDN 实流量、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

补充：`2026.05.12_16-17_remote-credential-rotation-gate` 完成 O6 Docker/local credential rotation gate：Task A 新增 `trashbot.credential_rotation_gate` artifact、`--write-credential-rotation-artifact`、`TRASHBOT_REMOTE_CLOUD_CREDENTIAL_ROTATION_ARTIFACT` preflight 消费、`/preflightz` credential rotation check，以及 `/api/status.phone_readiness.credential_rotation` / `/api/diagnostics.credential_rotation` phone-safe 摘要；Full-stack targeted tests 输出 `Ran 98 tests in 24.359s OK`，artifact CLI 输出 `ok=true`、`credential_rotation_status=passed`、`evidence_boundary=software_proof_docker_credential_rotation_gate`，preflight CLI 输出 `credential_rotation=pass`、`software_proof_ready=true`、`production_ready=false`、`overall_status=blocked`。Task B remote bridge compatibility fence 输出 `Ran 27 tests in 12.614s OK`，确认 credential/preflight/artifact metadata 不改变 command/status/ack envelope、GET outage 不触发本地 action、不 ACK、不推进或持久化 cursor，且 ACK 仍不等于 delivery success。该证据只支持 O6 从约 41% 保守小幅上调到约 43%；O5 保持约 43%，O1/O2/O3/O4 不提升。本轮仍没有真实云、真实 4G/SIM、真实 OSS upload、真实 STS issuance、CDN origin fetch、生产账号 provisioning、真实 audit log、production-ready、生产 DB/queue、正式手机 app/真实手机设备、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

| Objective | 当前进度 | 本轮新增证据 | 剩余关键缺口 |
| --- | --- | --- | --- |
| Objective 1 硬件协议可信底盘 | 约 75% | 18-19 hardware diagnostics proof 新增 `hardware_diagnostics_proof.py` 离线 proof helper/CLI；19-20 hardware proof diagnostics 已把 software proof 接入 `/api/diagnostics.hardware_proof` 和 operator 页面；本轮再补齐 `operator_hardware_proof_ref` launch 参数 -> `operator_gateway.hardware_proof_ref` 参数链路，支持通过 launch 显式指向 software proof 产物并进入 diagnostics；targeted tests、py_compile、full smoke、diff check 通过 | 真实 WAVE ROVER HIL、真实 UART/轮向/速度单位/反馈频率/IMU/电池实测仍缺；software proof 仍不等于 HIL 或实机通过 |
| Objective 2 可恢复送垃圾任务闭环 | 约 74% | `TrashCollection` fixed-route 送达会把 fixed-route status JSON 的结构化证据写入 `nav_results` 和 task record；legacy `trash_collection_server.py` 已被 quarantine，旧入口被调用时返回 `legacy_server_quarantined`，不再 sleep 后伪造成功 | 真实 fixed-route/Nav2 行驶、真实 SLAM/Nav2 学习到巡逻 E2E 还缺实测 |
| Objective 3 可验证导航与固定路线 | 约 76% | `sprints/2026.05.10_23-24_route-proof-coverage/` 本轮在既有 route proof contract 上补强稳定性：`route_proof_summary.missing_checkpoints` 增加归一化规则（过滤已覆盖索引，避免与 `covered_checkpoints` 矛盾），新增回归测试并同步 `docs/navigation/fixed_route_workflow.md` 口径；子 agent 验证为 nav `Ran 44 tests ... OK`、behavior/operator `Ran 48 tests ... OK`、smoke `Ran 128 tests ... OK` 与 `Ran 13 tests ... OK` | 仍需真实 keyframe/live frame 匹配样例、真实 Nav2 waypoint/fixed-route 实跑、真实路线采集、真实相机接入和上车验证；本轮软件证据不等于 Nav2/相机/HIL 实机成功 |
| Objective 4 感知模块产品化 | 约 75% | 21-22 sprint 完成 review progress metrics 软件侧闭环：`/api/vision/review-queue` 与 diagnostics 同口径输出 `progress_summary`、`decision_distribution`、`next_pending_sample`，operator 页面新增 Progress/Decision distribution/Next pending sample 与 `Jump To Next Pending` 入口；`test_*operator*py`、`py_compile`、full smoke、scoped `git diff --check` 通过。按保守口径仅上调 +1pp（从 74% 到 75%），因为这次新增价值集中在“复核进度可观测性”而非实机能力提升 | 仍未完成真实硬件/HIL、真实相机采集与上车验证；当前证据是软件/离线环境，不等于实机闭环；`test_*review*py` 仍存在命名 pattern 无匹配（`NO TESTS RAN`） |
| Objective 5 手机体验与量产边界 | 约 43%（software_proof_docker_phone_browser_acceptance_gate） | 电梯 assisted delivery 已升级为 MVP 必须；手机端 UI 美观可直接使用作为新 KR7 写入。02-03 remote 4G command loop 只补充 operator HTTP local mock cloud 的 phone-safe command/status/ack 入口，不暴露 `/cmd_vel`、串口或硬件参数。03-04 sprint 新增 `remote_readiness` / phone-readable readiness 口径，手机侧未来可区分 cloud/status/ack/cursor 状态，且敏感字段过滤不展示 token、串口、ROS topic 或硬件参数。04-05 sprint 进一步补齐 `auth_state`、`degradation_state`、`safe_phone_copy` 和用户可读 retry hint；05-06 independent relay 补齐 `status_missing`、`status_stale`、auth failed、bad request、not found、malformed JSON 等 phone-safe errors；06-07 Docker relay `/readyz` 增加 credential gate、state store 和 phone-safe failure checks，支撑 future phone UI API contract；07-08 production preflight gate 继续输出 `safe_summary` / `retry_hint` / phone-safe blocked reason，只作为未来手机提示素材；10-11 sprint 在本地 operator 首屏与 `/api/status.phone_readiness` 中落地 `trashbot.phone_readiness.v1` readiness gate，聚合 local delivery、action permissions、remote readiness、可选 preflight/backup restore 和普通用户恢复提示，targeted tests `Ran 68 tests ... OK`；13-14 sprint 新增 `trashbot.command_safety.v1` 按钮级 gate，Start/Confirm/Cancel/Diagnostics 消费 `command_safety.actions.*.enabled`，覆盖 stale/pending/auth/cloud/malformed/manifest/manual takeover，并明确 ACK 不等于送达成功，Full-stack targeted tests `Ran 64 tests in 17.299s OK`；14-15 sprint 新增 network recovery phone-safe summary，可解释 missing/invalid/stale/failed/ready，但只作为 O6 支撑不提升 O5；15-16 sprint 把 O5 从 API/handler proof 推进到真实本地 Chrome browser proof，`390x844` 与 `768x900` 均通过 44px hit area、首屏主按钮可见、无重叠/无溢出、ACK copy 可见、Diagnostics accessible 且 primary actions disabled，targeted tests `Ran 73 tests in 17.910s OK`。 | 仍无生产手机 app、真实手机设备 Safari/Chrome、普通用户实机验收、生产账号或真实远程手机流程；本轮是 local/Docker/browser software proof，不等于真实云、真实 4G、OSS/CDN、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。 |
| Objective 6 4G 云中转 + OSS/CDN | 约 43%（software_proof_docker_credential_rotation_gate） | 23-24 sprint 顶层设计纳入 4G 云中转、OSS/CDN 和凭证边界；02-03 sprint 完成本地 mock cloud / remote bridge 最小命令闭环。03-04 sprint 在 local mock control-plane 上补齐 `MockCloudStore(state_path=...)` 原子持久化、队列/status/ack reload、敏感字段过滤、`remote_readiness` 派生；`remote_bridge` 新增 `cursor_state_path`，能恢复 `last_terminal_ack_id` 并在 terminal ACK 成功后原子持久化 cursor。04-05 sprint 补齐 bearer auth gate、phone-safe readiness/degradation、敏感字段过滤、`RemoteCloudError` 分类、cloud unreachable/auth failed/malformed response 不推进 cursor/不触发本地 action 的保守语义；05-06 sprint 完成 independent Docker/local HTTP relay service、file-backed persistence、bearer auth、phone-safe errors、robot client compatibility，并补齐 `docs/product/cloud_4g_infrastructure.md`；06-07 sprint 完成 Dockerfile/compose/env、`/healthz`、`/readyz`、state store writable check、phone-safe failure redaction self-check 和 Docker deploy smoke；07-08 sprint 新增 production preflight gate；08-09 sprint 新增 SQLite state backend proof；09-10 sprint 新增 SQLite backup/restore drill；11-12 sprint 新增 OSS/CDN manifest artifact proof；12-13 sprint 把 manifest artifact 推进到 phone/API consumption gate；13-14 sprint 把 remote degradation、ACK pending、status stale 和 manifest 异常消费到手机命令 gate；14-15 sprint 完成 network recovery drill artifact、preflight/diagnostics/phone-safe consumption 和 remote_bridge cursor compatibility fence；16-17 sprint 新增 credential rotation artifact/preflight/phone-safe 摘要与 robot compatibility fence，Full-stack targeted tests `Ran 98 tests in 24.359s OK`，Robot targeted tests `Ran 27 tests in 12.614s OK`，artifact CLI 输出 `evidence_boundary=software_proof_docker_credential_rotation_gate`，preflight 仍输出 `production_ready=false`、`overall_status=blocked`。 | 真实云部署、HTTPS/TLS、公网入口、真实 4G/SIM、生产鉴权/rotate、真实 STS issuance、受限 AK、真实 OSS upload、CDN origin fetch、生命周期策略、production account、生产账号 provisioning、真实 audit log、OSS/CDN 实流量、生产云端持久化 DB/queue、多实例一致性、生产备份策略、真实灾备、正式手机 app/真实手机设备验收和生产运维仍未实现或验证；Docker relay/auth/readiness/degradation/ack/status/cursor/preflight gate、SQLite 单实例恢复 proof、backup/restore drill、manifest artifact、phone/API 摘要消费、按钮级降级消费、Docker/local 弱网恢复语义和 credential rotation gate 只证明控制面入口形态、恢复语义、上线前置阻断能力、本地恢复演练、对象引用 contract、手机/API 摘要消费和本地凭证轮换边界，不等于真实云、真实 4G、真实垃圾送达、Nav2/fixed-route、WAVE ROVER 或 HIL。 |

## 5. 2026 H2 前瞻路线

### 阶段 A：工程闭环稳定化

- 完成官方 JSON 底盘桥硬件实测，确认 `T=1` 与 `T=13` 的实际运动表现。
- 明确 `/odom` 来源：短期命令积分，中期轮速/编码器融合，长期与 Nav2/SLAM/IMU 融合。
- 引入 launch 参数配置文件，减少命令行长参数和硬编码默认值。
- 为每个包建立最小 CI：导入检查、静态测试、核心单元测试。

### 阶段 B：任务自治能力

- 行为层引入任务队列：装载确认任务、送达任务、投放/提醒任务、返回任务。
- 增加恢复策略：导航失败重试、目标过期丢弃、连续失败降级、人工接管。
- 增加运行状态 topic 或 JSON 状态文件，供 debug web 和日志系统消费。
- 将 action feedback 从“进度数字”升级为可读状态机事件。

### 阶段 C：数据闭环与模型升级

- 把送达过程中的关键帧、站点识别结果、异常/失败案例沉淀为数据集。
- 使用固定路线场景先训练/验证轻量目标检测模型。
- 建立离线回放工具：输入 route/keyframes/detections，复现行为层决策。
- 引入指标面板：站点识别准确率、异常记录覆盖率、平均送达耗时、任务成功率。

### 阶段 D：产品化与安全边界

- 增加急停、限速、低电压处理、通信丢失停车、近障停车。
- 明确支持场景：封闭区域、低速、固定路线、可控光照；不承诺开放道路或复杂人群环境。
- 梳理安装文档：Orange Pi 系统、串口权限、ROS2 环境、WAVE ROVER 固件、摄像头、地图路径。
- 形成上车验收清单和回归测试清单。

### 阶段 E：电梯 assisted delivery 受控场景

- 在楼宇内定义可控测试路线：出发点 -> 电梯厅 -> 进入电梯 -> 人工协助按目标楼层 -> 目标楼层驶出 -> 垃圾站/垃圾桶点位。
- 行为层增加电梯子状态，但默认关闭；只有明确进入 H2 受控测试时启用。
- 感知层先验证电梯门开/关、目标楼层到达和可驶出证据，不把楼层识别写成无证据的全自动能力。
- 语音层由 Orange Pi/ROS2 编排，进入电梯后播放：“你好,好心人,.我要去1楼扔垃圾,请帮我按一下电梯,”。
- 人工协助是产品边界：小车不按按钮，不改造电梯，不默认新增机械臂或电梯控制硬件。

## 6. 当前最高优先级

- 验收顺序：`O1（hil_pass 边界与补齐）→ O2（失败恢复任务证据）→ O3（fixed-route 软件/实机复盘对齐）`

1. **修正项目事实源**
   - README 中仍可能残留旧 ESP32 二进制协议描述，应统一到 WAVE ROVER 官方 UART JSON 协议。
   - 所有硬件相关说明必须指向 `docs/vendor/VENDOR_INDEX.md`。

2. **完成硬件桥上车验证**
   - 先验证串口设备名、波特率、`T=1` 左右轮速度方向、停止命令。
   - 再验证 `T=1001` 反馈字段、IMU yaw 单位、电池电压。
   - 最后验证 `T=13` 是否适合直接作为 `/cmd_vel` 映射。

3. **补齐行为层真实运行证据**
   - 主 `task_orchestrator` 的 patrol/collection/delivery 已进入 waypoint/fixed-route/action-result 路径；`use_saved_map=false` 学习阶段已要求真实 waypoint proof，不再模拟完成。
   - legacy `trash_collection_server.py` 已 quarantine，仅作为旧入口兼容保留；被调用时返回 `legacy_server_quarantined`，不能作为当前闭环完成证据。
   - Objective 2 剩余缺口集中在真实 fixed-route/Nav2 行驶，以及真实 SLAM/Nav2 学习到巡逻 E2E 实测。

4. **建立最小回归测试**
   - 硬件桥：协议函数测试。
   - 导航：route CSV/YAML 转换、fixed route dry-run。
   - 行为：action result、取消、失败路径、状态转移静态测试。

## 7. 风险与决策

| 风险 | 影响 | 决策 |
| --- | --- | --- |
| README/代码/厂商资料协议不一致 | 硬件无法通信或误判实现正确 | 以 `docs/vendor/` 为硬件事实源，README 后续修正 |
| Orange Pi 串口设备名不确定 | launch 默认值可能上车不可用 | 保持参数可覆盖，上车前确认实际设备 |
| `/odom` 不是实测里程计 | Nav2 定位和路线复现可能漂移 | 短期明确标注，中期接入轮速/编码器融合 |
| 把“捡垃圾”误当核心目标 | 在没有机械臂和高成本传感器时需求失焦 | 核心闭环固定为用户交付后的送达任务 |
| 普通用户不会电脑和硬件 | 上手失败、售后成本高 | 手机一键流程、语音提示、远程诊断优先 |
| 视觉检测启发式不足 | 站点识别或异常记录不稳定 | 先数据闭环，再模型升级，不作为送达 MVP 前提 |
| 行为层模拟逻辑过多 | 系统看似完整但无法真实运行 | 优先替换 sleep 和占位逻辑，建立真实状态机 |
| 缺少硬件在环测试 | 单元测试通过但上车失败 | 增加上车验收清单和硬件测试脚本 |
| 电梯场景被误读成全自动乘梯 | 用户以为小车能按按钮、控制电梯或已完成跨楼层实机闭环 | 定位为 H2/受控 assisted delivery；人工按键是流程边界，验证前不抬完成度 |
| 目标楼层识别不可靠 | 小车可能提前驶出或错过目标楼层 | 需要目标楼层到达证据、开门证据、超时/人工接管策略和任务记录 |
| 电梯门识别误判 | 可能撞门、挡门或错过驶出窗口 | 默认低速、可停、门开确认、驶出超时和手机端人工接管 |

## 8. P9 评审标准

一个阶段不能只以“代码写完”作为完成标准，必须同时满足：

- **功能闭环**：能从启动、用户装载确认、送达垃圾站、投放/提醒、返回形成完整路径。
- **接口稳定**：ROS2 topic/action/srv 契约清楚，内部替换不破坏上层。
- **硬件可信**：协议、参数、速度映射、反馈字段均有 vendor 资料或实测记录。
- **可验证**：有自动化测试、dry-run、上车验收三层证据。
- **可恢复**：失败不是卡死，而是进入明确错误状态、重试、降级或等待接管。
- **可复盘**：每次任务留下足够日志和数据，能回答“为什么这样决策”。
- **可使用**：普通用户只靠手机和语音提示即可完成核心任务，不需要理解电脑、ROS2 或硬件调试。
- **可量产**：默认方案不依赖机械臂、昂贵传感器或复杂装配，新增硬件必须有明确成本收益。

## 9. 下一步执行建议

1. 修正 README 的旧二进制协议描述，与当前 WAVE ROVER JSON 驱动保持一致。
2. 为硬件桥补一份 `docs/hardware/wave_rover_json_bridge.md`，记录命令、参数、实测结果和注意事项。
3. 把 `task_orchestrator` 的模拟巡逻/收集替换为真实“装载确认 -> 送达垃圾站 -> 投放/提醒 -> 返回”状态机和 waypoint/fixed route 驱动。
4. 增加 `run_smoke_tests.sh` 或等价脚本，在 WSL/Windows 混合开发环境上至少跑 Python 静态测试；在 Orange Pi 上跑 ROS2 build 和硬件 smoke test。
5. 建立 `docs/acceptance/robot_bringup_checklist.md`，作为每次上车前后的验收标准。
6. 补一份手机端最小流程和量产硬件约束表，明确用户只用手机、默认硬件只包含小车底盘、上位板、随身 WiFi、摄像头、麦克风和喇叭。
7. 为 H2 电梯 assisted delivery 建立受控场景产品文档和后续技术计划：先做流程、语音、状态机边界和验收口径，再由 Robot Platform、Autonomy、User Touchpoint 分别补行为、感知和语音/手机触点证据。

## 10. 进度快照（2026-05-10 01:14）

本轮 hourly iteration 优先推进完成度较低的 Objective 3。`fixed_route_autonomy` 的 dry-run 不再绕过 visual gate；启用视觉门控时，缺 keyframe、缺 camera frame、缺 descriptor 或匹配不足都会停在 `waiting_visual_gate`，并在 debug status 中写出 `visual_gate_status`、`visual_gate_detail`、`visual_gate_checkpoint`。只有 visual gate 通过后，dry-run 才推进 checkpoint。

| Objective | 当前进度判断 | 证据与缺口 |
| --- | --- | --- |
| Objective 1：硬件控制层 | 软件侧中高，实机侧未 closed | smoke 覆盖硬件桥软件测试；Docker/Humble 与 HIL 仍未完成。 |
| Objective 2：送垃圾任务闭环 | 中高 | action result、task record、timeout/cancel/failure 路径逐步可判定；patrol 仍有硬编码 5 waypoint 占位债务。 |
| Objective 3：导航与固定路线 | 中等，今天明显推进 | fixed-route dry-run 已覆盖 visual gate 等待与通过路径；还缺 route-wide keyframe coverage 预检和真实 Nav2/摄像头验证。 |
| Objective 4：感知模块 | 低到中 | 视觉状态已进入固定路线准入诊断；样本沉淀、检测 JSON、模型评估表仍未完成。 |
| Objective 5：手机用户体验与量产边界 | 中 | 远程/手机可消费诊断字段增加；完整手机 UX、语音提示词和量产硬件约束表仍待落地。 |

本轮验证：`PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh` 通过，覆盖 interfaces 4、hardware 14、nav 20、bringup 7、behavior 91、vision 1。

## 11. 进度快照（2026-05-10 01:58）

本轮 hourly iteration 使用 team 模式推进两个低完成度方向：Objective 5 由本地实现加 worker 复查，新增 operator gateway `/api/diagnostics` 和手机/喇叭提示合同；Objective 4 由 vision worker 复查样本上下文改动，确认视觉样本 JSON 已能携带 task、route、checkpoint、event、anomaly 上下文。测试仍作为护栏，重点是把手机诊断和感知数据沉淀往可用功能推进。

| Objective | 当前进度判断 | 证据与缺口 |
| --- | --- | --- |
| Objective 1：硬件控制层 | 软件侧中高，实机侧未 closed | 本轮未改硬件；Docker/Humble 与 WAVE ROVER HIL 仍未完成。 |
| Objective 2：送垃圾任务闭环 | 中高 | 任务终态、error_code、task_record_path 可继续被 `/api/diagnostics` 消费；patrol 学习阶段模拟口径和 legacy server 债务仍在。 |
| Objective 3：导航与固定路线 | 中等偏高 | fixed-route visual gate 状态可继续进入诊断链；真实 Nav2/摄像头验证仍缺。 |
| Objective 4：感知模块 | 中等 | 样本落盘具备原图、标注图、检测 JSON 和 delivery/anomaly 上下文；还缺 manifest、无检测异常帧捕获和真实数据集。 |
| Objective 5：手机用户体验与量产边界 | 中等偏高 | 本地手机/浏览器网关新增诊断包入口，文档定义状态提示词；还缺完整手机 UI、量产硬件约束表和普通用户实测。 |

## 12. 进度快照（2026-05-10 02:31）

本轮 hourly iteration 继续用 team 模式推进低完成度功能：Objective 5 把 diagnostics payload 组装拆成无 ROS 依赖纯函数，并用单测覆盖最新 status 优先、last_task fallback、日志引用归一化和空 map/route 版本不伪造文件存在；Objective 4 把视觉样本从“单个 JSON/JPG”推进为 raw image、annotated image、JSON、bounded manifest、任务上下文和可选空检测负样本入口。修复了 `scripts/run_smoke_tests.sh` 的 CRLF 问题，恢复 WSL/Linux smoke gate。

| Objective | 当前进度判断 | 证据与缺口 |
| --- | --- | --- |
| Objective 1：硬件控制层 | 软件侧中高，实机侧未 closed | 本轮未改硬件事实；hardware 软件 smoke 14 tests OK，但 Docker/Humble 与 WAVE ROVER HIL 仍未完成。 |
| Objective 2：送垃圾任务闭环 | 中高 | 任务终态、error_code、task_record_path 已稳定进入 diagnostics 消费链；patrol 学习阶段模拟口径和 legacy server 债务仍在。 |
| Objective 3：导航与固定路线 | 中等偏高 | fixed-route visual gate 状态可继续进入诊断链；真实 Nav2/摄像头验证仍缺。 |
| Objective 4：感知模块 | 中等 | 样本 raw/annotated/json/manifest 证据链、delivery/anomaly 上下文和可选负样本入口已具备；还缺真实路线数据集、runtime 文件写入单测和持续标注流程。 |
| Objective 5：手机用户体验与量产边界 | 中等偏高 | `/api/diagnostics`、payload fallback 测试、状态提示词合同已落地；还缺完整手机 UI、量产硬件约束表和普通用户实测。 |

本轮验证：`PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh` 通过，覆盖 interfaces 6、hardware 14、nav 20、bringup 8、behavior 96、vision 8。

## 13. 进度快照（2026-05-10 19:59）

本轮 `sprints/2026.05.10_19-20_hardware-proof-diagnostics/` 收口 Objective 5 的远程/手机诊断能力：`/api/diagnostics` 总是包含 `hardware_proof`，operator 页面新增 Hardware proof 诊断卡，能把上一轮 hardware diagnostics software proof 以 `software_proof`、`needs_hil`、`invalid_config`、`read_error` 四类保守状态展示给手机/售后用户。产品判断上，O5 可从约 74% 上调到约 77%；O1 只小幅上调到约 74%，因为 software proof 已被产品化消费，但真实 HIL 仍没有发生。

| Objective | 当前进度判断 | 证据与缺口 |
| --- | --- | --- |
| Objective 1：硬件控制层 | 软件证据消费链更完整，实机侧仍未 closed | 19-20 已把 hardware proof 接入 diagnostics API 和 operator 页面，targeted tests、py_compile、full smoke、diff check OK；但没有真实 WAVE ROVER HIL，没有真实 UART、轮向、速度单位、反馈频率、IMU、电池证据，`operator_gateway.py` 也还没有 `hardware_proof_ref` ROS 参数入口。 |
| Objective 2：送垃圾任务闭环 | 无直接上调 | full smoke 覆盖 behavior 118 tests OK，证明本轮 operator diagnostics 改动未明显回归行为包；真实 fixed-route/Nav2 行驶和学习到巡逻 E2E 仍缺。 |
| Objective 3：导航与固定路线 | 无直接上调 | nav 39 tests OK 作为不回归证据；真实路线采集、真实 Nav2/fixed-route 实跑、真实相机接入仍缺。 |
| Objective 4：感知模块 | 无直接上调 | vision 13 tests OK 作为不回归证据；真实 camera/odom manifest、数据集和上车验证仍缺。 |
| Objective 5：手机体验与量产边界 | 明显推进到中高 | `/api/diagnostics.hardware_proof` 和 operator Hardware proof 卡片让手机/售后能看到硬件 proof 状态和下一步动作；仍缺真实手机浏览器截图、真实 HIL、喇叭/TTS、量产硬件约束实物验收。 |

本轮验证：targeted diagnostics 14 tests OK、HTTP 16 tests OK、static 8 tests OK、`python3 -m py_compile` OK、完整 smoke 通过 interfaces 6、hardware 24、nav 39、bringup 9、behavior 118、vision 13 tests OK、`git diff --check` OK。

## 13. 进度快照（2026-05-10 03:22）

本轮 hourly iteration 继续优先推进完成度较低的 Objective 5。`operator_gateway` 的本地页面从极简按钮/JSON 面板升级为手机优先操作台，展示状态卡、五步送垃圾流程、主操作按钮、机器人位置和诊断摘要；同时把手机文案与喇叭提示下沉为 `status_payload()` 的稳定字段 `phone_copy` / `speaker_prompt`，让 `/api/status`、`/api/collect`、`/api/dropoff/confirm`、`/api/cancel`、`/api/diagnostics` 都能被手机 UI 或未来 speaker/TTS 层直接消费。

| Objective | 当前进度判断 | 证据与缺口 |
| --- | --- | --- |
| Objective 1：硬件控制层 | 软件侧中高，实机侧未 closed | 本轮未改硬件；hardware 软件 smoke 14 tests OK，但 Docker/Humble 与 WAVE ROVER HIL 仍未完成。 |
| Objective 2：送垃圾任务闭环 | 中高 | 本轮未直接改动；team 复查确认 `use_saved_map=false` 学习阶段仍需用真实 waypoint/route 文件证明完成，不能继续靠模拟成功口径。 |
| Objective 3：导航与固定路线 | 中等偏高 | fixed-route visual gate 和 route 状态仍是现有证据；下一步高价值项是 learning waypoint proof 与真实 keyframe/live frame 样例。 |
| Objective 4：感知模块 | 中等 | 本轮未直接改动；样本 manifest 和负样本入口仍保持，真实路线数据集仍缺。 |
| Objective 5：手机体验与量产边界 | 中高 | 本地手机操作台、`phone_copy`、`speaker_prompt`、诊断摘要和流程 stepper 已落地；还缺真实手机浏览器、喇叭/TTS、生产账号体系和量产实物验收。 |

本轮验证：`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src/ros2_trashbot_behavior python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_static.py src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py` 通过，26 tests OK；`PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh` 通过，覆盖 interfaces 6、hardware 14、nav 20、bringup 8、behavior 98、vision 8。

## 14. 进度快照（2026-05-10 04:20）

本轮 hourly iteration 继续用 team 模式推进低完成度 OKR。Vision/User Touchpoint 侧选择把视觉样本 manifest 接入 operator diagnostics：`/api/diagnostics` 新增 `vision_samples` 摘要，能报告 manifest 是否存在、schema、样本数量、最新样本引用、最新上下文、检测数量、最高置信度和读取错误；手机诊断面板同步展示视觉样本数量和最新样本引用。Autonomy 侧复查确认下一轮高价值 Objective 3 任务是把 `learn.launch.py` 显式接入 `route_data_recorder`，让路线/keyframe 采集进入学习阶段标准流程。

| Objective | 当前进度判断 | 证据与缺口 |
| --- | --- | --- |
| Objective 1：硬件控制层 | 软件侧中高，实机侧未 closed | 本轮未改硬件；hardware 软件 smoke 14 tests OK，但 Docker/Humble 与 WAVE ROVER HIL 仍未完成。 |
| Objective 2：送垃圾任务闭环 | 中高 | 本轮未直接改动；任务终态与诊断消费链保持稳定，仍需清理学习阶段模拟完成口径和 legacy sleep demo。 |
| Objective 3：导航与固定路线 | 中等偏高 | team 复查明确下一步：`learn.launch.py` 应通过显式参数启动 `route_data_recorder`，把固定路线采集纳入学习流程；真实 Nav2/摄像头验证仍缺。 |
| Objective 4：感知模块 | 中等偏上 | manifest 不再只是文件产物，已进入远程诊断摘要；还缺真实路线样本集、runtime 文件写入单测和持续标注流程。 |
| Objective 5：手机体验与量产边界 | 中高 | 手机诊断面板能显示视觉样本状态和最新样本引用；还缺真实手机浏览器、喇叭/TTS 和量产实物验收。 |

本轮验证：目标 diagnostics/http/static tests 通过；完整 `scripts/run_smoke_tests.sh` 通过，覆盖 interfaces 6、hardware 14、nav 20、bringup 8、behavior 101、vision 8；`git diff --check` 通过。Docker/Humble colcon build 因当前 WSL distro 找不到 `docker` 命令未执行成功。

## 15. 进度快照（2026-05-10 05:16）

本轮 hourly iteration 按 team 建议推进 Objective 3 route learning closure。`learn.launch.py` 新增 `route_recorder:=false` 安全默认开关，以及 `route_output_dir`、`route_camera_topic`、`route_odom_topic`、`route_min_distance_m`、`route_frame_id` 参数；启用后会在学习阶段同时启动 `route_data_recorder`，让 SLAM/人工驾驶/waypoint 学习和 fixed-route CSV/keyframe 采集进入同一标准入口。`docs/navigation/fixed_route_workflow.md` 已把一键学习采集命令写入流程，静态 launch contract 测试覆盖参数声明、条件启动和参数透传。

| Objective | 当前进度判断 | 证据与缺口 |
| --- | --- | --- |
| Objective 1：硬件控制层 | 软件侧中高，实机侧未 closed | 本轮未改硬件；hardware 软件 smoke 14 tests OK；WAVE ROVER HIL 仍未完成。 |
| Objective 2：送垃圾任务闭环 | 中高 | 本轮未直接改动；任务终态与诊断消费链保持稳定，仍需清理学习阶段模拟完成口径和 legacy sleep demo。 |
| Objective 3：导航与固定路线 | 约 64% | 学习 launch 现在可显式启动 route/keyframe 采集；bringup launch contract 测试和完整 smoke 已覆盖入口契约。仍缺真实 `/odom` + `/camera/image_raw` 采集、keyframe/live frame 匹配样例、Nav2 实跑和 Docker/Humble build。 |
| Objective 4：感知模块 | 约 54% | 本轮未抬进度；视觉样本 manifest/诊断链保持，仍缺真实路线数据集和 runtime 文件写入单测。 |
| Objective 5：手机体验与量产边界 | 约 67% | 本轮未抬进度；手机操作台和诊断摘要保持，仍缺真实手机浏览器、喇叭/TTS 和量产实物验收。 |

本轮验证：`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_bringup/test/test_launch_contract_static.py` 通过，9 tests OK；`PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_bringup/launch/learn.launch.py` 通过；`PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh` 通过，覆盖 interfaces 6、hardware 14、nav 20、bringup 9、behavior 101、vision 8；`git diff --check` 通过。`bash scripts/docker_humble_build.sh` 已尝试，但当前 WSL 2 distro 未启用 Docker Desktop integration，docker 命令不可用，无法完成 Humble colcon build。

## 16. 进度快照（2026-05-10 06:17）

本轮 hourly iteration 按 team 建议继续推进 Objective 3。`fixed_route_autonomy` 新增 `keyframe_preflight` 调试状态：视觉门控开启时，节点会在第一步 dry-run/导航推进前检查整条路线的关键帧覆盖，列出 `loaded_keyframes`、`missing_keyframes`、`invalid_keyframes` 和 `route_visual_ready`。如果后续 checkpoint 缺图或 keyframe 无法读取/无 descriptor，状态停在 `waiting_visual_gate`，不会先通过 checkpoint 0 再在后续点位暴露问题。

| Objective | 当前进度判断 | 证据与缺口 |
| --- | --- | --- |
| Objective 1：硬件控制层 | 约 70% | 本轮未改硬件；vendor 入口已按规则复读，hardware 软件 smoke 仍作为护栏；WAVE ROVER HIL 仍未完成。 |
| Objective 2：送垃圾任务闭环 | 约 66% | 本轮未直接改动；任务终态与诊断消费链保持稳定，仍需清理学习阶段模拟完成口径和 legacy sleep demo。 |
| Objective 3：导航与固定路线 | 约 67% | fixed-route dry-run 现在具备路线级 keyframe coverage 预检，调试状态可提前暴露缺失/无效关键帧；仍缺真实 `/odom` + `/camera/image_raw` 采集、keyframe/live frame 匹配样例、Nav2 实跑和 Docker/Humble build。 |
| Objective 4：感知模块 | 约 54% | 本轮未抬进度；Vision/User Touchpoint team 复查建议下一步把 `route_data_recorder` 输出接入 `trashbot.vision_samples.v1` manifest，让路线 keyframe 也进入 diagnostics。 |
| Objective 5：手机体验与量产边界 | 约 67% | route debug/status 信息更适合远程诊断消费；真实手机浏览器、喇叭/TTS 和量产实物验收仍缺。 |

本轮验证：目标 fixed-route 测试、nav 包测试、完整 smoke、`py_compile`、`git diff --check` 和 Docker/Humble 尝试结果见 `sprints/2026.05.10_06-07/tech-done.md`。

## 17. 进度快照（2026-05-10 07:07）

本轮 hourly iteration 继续推进完成度较低的 Objective 4。`route_data_recorder` 在成功写入学习阶段 keyframe JPG 后，会同步生成 `keyframes/<index>.json` companion sample，并追加 `trashbot.vision_samples.v1` 的 `manifest.json`。样本上下文包含 `route_id`、`checkpoint_id`、`event_type=route_keyframe`，per-sample JSON 包含 `route_pose` 和空 `detections`，让 operator diagnostics 已有的 manifest summary 可以直接消费路线关键帧证据。`learn.launch.py` 同步新增 `route_id`、`route_sample_manifest_name`、`route_sample_manifest_max_entries` 参数，学习入口不需要额外手工脚本就能产出 route/keyframe/manifest 证据链。

| Objective | 当前进度判断 | 证据与缺口 |
| --- | --- | --- |
| Objective 1：硬件控制层 | 约 70% | 本轮未改硬件；未新增协议、串口、波特率或电气假设；WAVE ROVER HIL 仍未完成。 |
| Objective 2：送垃圾任务闭环 | 约 66% | 本轮未直接改动；Product/Robot Platform team 复查建议下一轮优先把 `use_saved_map=false` patrol 学习模拟成功改为 proof-gated。 |
| Objective 3：导航与固定路线 | 约 68% | 学习阶段产物从 route CSV/keyframe JPG 扩展为 companion JSON + manifest，固定路线数据更可复盘；仍缺真实 `/odom` + `/camera/image_raw` 采集、keyframe/live frame 匹配样例和 Nav2 实跑。 |
| Objective 4：感知模块 | 约 58% | route keyframe 现在进入 `trashbot.vision_samples.v1` manifest，并通过现有 diagnostics summary 验证兼容；仍缺真实路线样本集、持续标注流程和现场 runtime 验证。 |
| Objective 5：手机体验与量产边界 | 约 67% | 远程诊断可读的数据类型从 detector 样本扩展到学习路线关键帧；真实手机浏览器、喇叭/TTS 和量产实物验收仍缺。 |

本轮验证：route recorder manifest 测试、bringup launch contract 测试、`py_compile` 已通过；完整 smoke、`git diff --check` 和 Docker/Humble 尝试结果见 `sprints/2026.05.10_07-08/tech-done.md`。

## 18. 进度快照（2026-05-10 08:18）

本轮 hourly iteration 按 team 复查建议推进 Objective 2。`task_orchestrator._execute_patrol()` 不再在 `use_saved_map=false` 时打印 fake learning drive 并直接递增 `learn_count`；现在必须能从 `waypoint_file` 读取到非空 waypoint proof，才把本次视为学习证据并进入巡逻导航。缺失、不可解析或空 waypoint 文件会让 patrol action abort，状态进入 `ERROR`，避免把未完成学习阶段伪装成成功巡逻。

| Objective | 当前进度判断 | 证据与缺口 |
| --- | --- | --- |
| Objective 1：硬件控制层 | 约 70% | 本轮未改硬件；未新增协议、串口、波特率或电气假设；WAVE ROVER HIL 仍未完成。 |
| Objective 2：送垃圾任务闭环 | 约 69% | patrol 学习阶段已 proof-gated，缺 waypoint 证据不能继续巡逻或自增学习次数；回归测试覆盖无证据 abort 和有证据继续巡逻。legacy server sleep demo 与真实学习到巡逻 E2E 仍缺。 |
| Objective 3：导航与固定路线 | 约 68% | 本轮未抬进度；学习 launch、route/keyframe/manifest 证据链保持，仍缺真实 `/odom` + `/camera/image_raw` 采集和 Nav2 实跑。 |
| Objective 4：感知模块 | 约 58% | 本轮未抬进度；route keyframe manifest 与 diagnostics 兼容性保持，仍缺真实路线样本集和现场 runtime 验证。 |
| Objective 5：手机体验与量产边界 | 约 67% | 本轮未抬进度；手机操作台和诊断摘要保持，仍缺真实手机浏览器、喇叭/TTS 和量产实物验收。 |

本轮验证：patrol execution 目标测试、`py_compile`、完整 smoke、`git diff --check` 和 Docker/Humble 尝试结果见 `sprints/2026.05.10_08-09/tech-done.md`。

## 19. 进度快照（2026-05-10 09:25）

本轮 hourly iteration 继续优先推进当前完成度最低的 Objective 4。`/api/diagnostics` 的 `vision_samples` 不再只给最新样本引用，现在会统计 manifest 内的 `event_type` 分布，并生成 bounded `review_queue`：优先放入 anomaly、route_keyframe、低置信度检测和未复核样本。手机诊断页同步展示复盘队列数量和下一条待复核样本，支持售后/调试直接从 manifest 判断“哪些图该先看”，而不是只知道“有多少张图”。

| Objective | 当前进度判断 | 证据与缺口 |
| --- | --- | --- |
| Objective 1：硬件控制层 | 约 70% | 本轮未改硬件；未新增协议、串口、波特率或电气假设；WAVE ROVER HIL 仍未完成。 |
| Objective 2：送垃圾任务闭环 | 约 69% | 本轮未直接改动；team 复查建议下一步补 fixed-route dry-run status 到 `TrashCollection` action 的集成证明。 |
| Objective 3：导航与固定路线 | 约 68% | 本轮未直接改动；team 复查建议下一步补 `route_data_recorder` callback runtime-style 文件写入验证。 |
| Objective 4：感知模块 | 约 61% | 视觉样本 manifest 已进入可复盘队列，诊断可输出 event 分布、待复核样本、复核理由和上下文；仍缺真实路线数据集、真实 runtime 文件写入验证和持续标注闭环。 |
| Objective 5：手机体验与量产边界 | 约 68% | 手机诊断页能显示视觉 review queue 数量和下一条待复核样本；真实手机浏览器、喇叭/TTS 和量产实物验收仍缺。 |

本轮验证：operator diagnostics/http 目标测试、`py_compile`、完整 smoke、`git diff --check` 和 Docker/Humble 尝试结果见 `sprints/2026.05.10_09-10/tech-done.md`。

## 20. 进度快照（2026-05-10 10:16）

本轮 hourly iteration 继续优先推进当前完成度最低的 Objective 4。Autonomy Algorithm Engineer 没有改 production recorder，而是补了 `route_data_recorder` 的 runtime-style callback 验证：测试用 fake image 和 fake odometry 直接驱动真实 `_on_image()` / `_on_odom()`，并检查 `route.csv`、`keyframes/000.jpg`、`keyframes/000.json` 和 `manifest.json` 都按 `trashbot.vision_samples.v1` 契约落盘。

| Objective | 当前进度判断 | 证据与缺口 |
| --- | --- | --- |
| Objective 1：硬件控制层 | 约 70% | 本轮未改硬件；未新增协议、串口、波特率或电气假设；WAVE ROVER HIL 仍未完成。 |
| Objective 2：送垃圾任务闭环 | 约 69% | 本轮未直接改动；Robot Platform 只读复查建议下一轮补 fixed-route status 到 `TrashCollection` action 的集成证明。 |
| Objective 3：导航与固定路线 | 约 68% | route recorder callback 产物有软件级运行式验证；仍缺真实 `/odom` + `/camera/image_raw` 采集、Nav2 waypoint 实跑和 keyframe/live-frame 匹配样例。 |
| Objective 4：感知模块 | 约 63% | route keyframe 样本链路从 helper 单测推进到真实 callback 路径文件写入证明；仍缺真实路线数据集、真实 ROS2 camera/odom 采集和持续标注闭环。 |
| Objective 5：手机体验与量产边界 | 约 68% | 本轮未直接改动；手机诊断页和视觉 review queue 保持，真实手机浏览器、喇叭/TTS 和量产实物验收仍缺。 |

本轮验证：route recorder manifest 目标测试、`py_compile`、完整 smoke、`git diff --check` 和 Docker/Humble 尝试结果见 `sprints/2026.05.10_10-11/tech-done.md`。

## 21. 进度快照（2026-05-10 11:34）

本轮 hourly iteration 按上一轮 handoff 推进 Objective 2。Robot Platform Engineer 把 `TrashCollection` 的 fixed-route 送达结果从简单 `NavigationResult` 扩展为带 `evidence` 的结构化记录：当 `delivery_mode=fixed_route` 消费 fixed-route status JSON 时，`nav_results` 和 task record 会保留 `route_contract_version=fixed_route.v1`、`route_file`、`current_index`、`current_target`、`total`、`visual_gate_status`、`visual_gate_detail`、`keyframe_preflight`、`last_nav_result`、`updated_at` 等字段。Autonomy Algorithm Engineer 只读复核确认这些字段对 fixed-route 复盘最关键。

| Objective | 当前进度判断 | 证据与缺口 |
| --- | --- | --- |
| Objective 1：硬件控制层 | 约 70% | 本轮未改硬件；未新增协议、串口、波特率或电气假设；WAVE ROVER HIL 仍未完成。 |
| Objective 2：送垃圾任务闭环 | 约 72% | fixed-route status JSON 已进入 `TrashCollection` task record，远程复盘能看到 route contract、checkpoint/index、visual gate 和 last nav result；legacy sleep server、真实 fixed-route/Nav2 行驶和真实学习到巡逻 E2E 仍缺。 |
| Objective 3：导航与固定路线 | 约 68% | fixed-route 产出的状态 contract 被行为层保留消费；仍缺真实 `/odom` + `/camera/image_raw` 采集、Nav2 waypoint 实跑和 keyframe/live-frame 匹配样例。 |
| Objective 4：感知模块 | 约 63% | 本轮未直接改动；route keyframe 样本 callback 证据链保持，仍缺真实路线数据集、真实 ROS2 camera/odom 采集和持续标注闭环。 |
| Objective 5：手机体验与量产边界 | 约 69% | 手机/远程诊断链现在能通过 task record 看到 fixed-route 送达证据，不只看任务成败；真实手机浏览器、喇叭/TTS 和量产实物验收仍缺。 |

本轮验证：行为目标测试、`py_compile`、完整 smoke 和 `git diff --check` 结果见 `sprints/2026.05.10_11-12/tech-done.md`。

## 22. 进度快照（2026-05-10 12:15）

本轮 hourly iteration 按 Objective 2 的剩余债务推进：Robot Platform Engineer 将 legacy `trash_collection_server.py` 从 sleep-demo action server 改为 quarantine 兼容入口。`legacy_trash_collection_server` console script 保留，但收到 `/trashbot/collect_trash` goal 时只发布失败反馈、`abort()` goal，并返回 `success=false`、`error_code=legacy_server_quarantined`、`final_state=error`，明确要求使用 `task_orchestrator`。旧的 `_navigate_to_trash()` / `_collect_trash()` / `_deliver_to_bin()` / `_sleep()` pipeline 已移除，避免它继续被误当作闭环完成证据。

| Objective | 当前进度判断 | 证据与缺口 |
| --- | --- | --- |
| Objective 1：硬件控制层 | 约 70% | 本轮未改硬件；未新增协议、串口、波特率或电气假设；WAVE ROVER HIL 仍未完成。 |
| Objective 2：送垃圾任务闭环 | 约 74% | legacy sleep-demo 已隔离，默认 product action entry 继续是 `task_orchestrator`；静态测试证明旧入口不再 `succeed()` 或 `asyncio.sleep()` 伪造成功。仍缺真实 fixed-route/Nav2 行驶和真实学习到巡逻 E2E。 |
| Objective 3：导航与固定路线 | 约 68% | 本轮未直接改导航；fixed-route 证据链保持，仍缺真实 `/odom` + `/camera/image_raw` 采集、Nav2 waypoint 实跑和 keyframe/live-frame 匹配样例。 |
| Objective 4：感知模块 | 约 63% | 本轮未直接改感知；route keyframe 样本 callback 证据链保持，仍缺真实路线数据集和持续标注闭环。 |
| Objective 5：手机体验与量产边界 | 约 69% | 本轮未直接改手机体验；远程诊断链保持，真实手机浏览器、喇叭/TTS 和量产实物验收仍缺。 |

本轮验证：legacy/action contract 目标测试、`py_compile`、完整 smoke 和 `git diff --check` 结果见 `sprints/2026.05.10_12-13/tech-done.md`。

## 23. 进度快照（2026-05-10 13:35）

本轮功能迭代响应“继续13-14的迭代，代码编写多一点”，由 Autonomy Algorithm Engineer 推进 Objective 4：新增 `vision_sample_manifest.py` 离线检查/汇总能力和对应测试，让真实采集后的 vision sample manifest 能在无 ROS2 daemon、无硬件、无真实相机的环境里被解析、检查并输出结构化 summary。summary 覆盖样本数量、raw/annotated/json 文件引用完整性、route/task/checkpoint/event/anomaly 上下文覆盖、负样本/异常样本计数、缺失引用和 error/warning，为后续 diagnostics 接入和人工复盘补上前置护栏。

| Objective | 当前进度判断 | 证据与缺口 |
| --- | --- | --- |
| Objective 1：硬件控制层 | 约 70% | 本轮未改硬件；未新增协议、串口、波特率或电气假设；WAVE ROVER HIL 仍未完成。 |
| Objective 2：送垃圾任务闭环 | 约 74% | 本轮未直接改行为闭环；legacy quarantine 和 task record 证据链保持，仍缺真实 fixed-route/Nav2 行驶和真实学习到巡逻 E2E。 |
| Objective 3：导航与固定路线 | 约 68% | 本轮未直接改导航；route/keyframe/manifest 采集链保持，仍缺真实 `/odom` + `/camera/image_raw` 采集、Nav2 waypoint 实跑和 keyframe/live-frame 匹配样例。 |
| Objective 4：感知模块 | 约 66% | vision sample manifest 已能离线检查和汇总，目标测试 13 OK，full smoke 全包通过；仍缺真实路线数据集、真实 ROS2 camera/odom 采集、持续标注闭环和 diagnostics/API 消费。 |
| Objective 5：手机体验与量产边界 | 约 70% | manifest summary 可作为手机 diagnostics/人工复盘前置检查输入，帮助远程支持判断样本证据链是否完整；真实手机浏览器、喇叭/TTS、量产实物验收和 API 展示仍缺。 |

本轮验证：vision tests 13 OK、`py_compile` OK、`git diff --check` OK、完整 smoke 全部 OK（interfaces 6 / hardware 14 / nav 27 / bringup 9 / behavior 110 / vision 13），结果见 `sprints/2026.05.10_13-14_okr-function/tech-done.md`。

## 24. 进度快照（2026-05-10 14:35）

本轮 hourly iteration 继续“功能往前走”，由 User Touchpoint Full-Stack Engineer 把上一轮 Objective 4 的离线 manifest checker 接入 `/api/diagnostics.vision_samples`。诊断包保留旧的 `manifest_ref`、latest sample、event counts 和 review queue 字段，同时新增 `integrity_summary`、`integrity_errors`、`integrity_warnings`、`missing_file_refs`、`context_field_coverage` 和 `file_counts`。手机/远程支持后续不需要人工翻目录，就能先判断视觉样本链是 `ok`、`warning`、`error`，以及缺的是 raw image、annotated image 还是 JSON。

| Objective | 当前进度判断 | 证据与缺口 |
| --- | --- | --- |
| Objective 1：硬件控制层 | 约 70% | 本轮未改硬件；未新增协议、串口、波特率或电气假设；WAVE ROVER HIL 仍未完成。 |
| Objective 2：送垃圾任务闭环 | 约 74% | 本轮未直接改行为闭环；legacy quarantine 和 task record 证据链保持，仍缺真实 fixed-route/Nav2 行驶和真实学习到巡逻 E2E。 |
| Objective 3：导航与固定路线 | 约 68% | 本轮未直接改导航；route/keyframe/manifest 采集链保持，仍缺真实 `/odom` + `/camera/image_raw` 采集、Nav2 waypoint 实跑和 keyframe/live-frame 匹配样例。 |
| Objective 4：感知模块 | 约 67% | manifest checker 已进入 diagnostics 消费链，能把样本完整性和上下文覆盖暴露给远程诊断；仍缺真实路线数据集、真实 ROS2 camera/odom 采集和持续标注闭环。 |
| Objective 5：手机体验与量产边界 | 约 72% | `/api/diagnostics` 已能直接返回视觉证据链健康度、缺失文件和错误/warning 计数；真实手机浏览器、喇叭/TTS、量产实物验收和 UI 展示仍缺。 |

本轮验证由 `full-stack-software-engineer` 完成：behavior diagnostics 目标测试 8 OK、vision manifest 目标测试 5 OK、`py_compile` OK、`git diff --check` OK、完整 smoke 全部 OK（interfaces 6 / hardware 14 / nav 27 / bringup 9 / behavior 111 / vision 13），结果见 `sprints/2026.05.10_14-15_diagnostics-manifest-summary/tech-done.md`。

## 25. 进度快照（2026-05-10 15:45）

本轮 `sprints/2026.05.10_15-16_integrity-status-ui/` 完成产品收口：Full-Stack Engineer 已把 operator 页面 Support Diagnostics 从 raw diagnostics 展示推进为 Vision evidence chain 诊断卡片。用户或现场支持在手机本地页面上能看到视觉证据链状态、最多 3 条关键缺失/错误/警告原因、context coverage、file counts 和恢复建议。这不是新的视觉算法或上车闭环，而是把上一轮 manifest checker 的诊断结果变成普通用户触点可消费的信息。

| Objective | 当前进度判断 | 证据与缺口 |
| --- | --- | --- |
| Objective 1：硬件控制层 | 保持不变 | 本轮未改硬件、UART、WAVE ROVER、Orange Pi 或 launch 参数；硬件实机/HIL 缺口不变。 |
| Objective 2：送垃圾任务闭环 | 保持不变 | 本轮未改 behavior action 或任务状态机；真实 fixed-route/Nav2 行驶和 E2E 上车仍待补证。 |
| Objective 3：导航与固定路线 | 保持不变 | 本轮未改 nav、route 或 keyframe 逻辑；真实路线采集、Nav2 waypoint 实跑和 camera frame 匹配样例仍待补证。 |
| Objective 4：感知模块产品化 | 约 68% | Vision evidence chain 诊断结果已从 `/api/diagnostics.vision_samples` 进入 operator 页面；仍没有真实 camera/odom manifest 上车验证，也没有真实路线数据集闭环。 |
| Objective 5：手机体验与量产边界 | 约 74% | 手机本地 operator 页面已有视觉证据链诊断灯、原因和恢复建议；验证证据为 HTTP 页面测试 16 OK、py_compile OK、git diff --check OK、完整 smoke 通过。仍没有真实手机浏览器截图、普通用户验收或喇叭/TTS 联动证明。 |

## 26. 进度快照（2026-05-10 16:50）

本轮 `sprints/2026.05.10_16-17_route-debug-status-panel/` 按完成度低优先推进 Objective 3。Autonomy Engineer 把 `route_debug_web.py` 从只显示 raw JSON 的页面升级为 fixed-route 可读 debug panel：现场打开页面后能看到 route state badge、checkpoint progress、current target、visual gate 状态、keyframe preflight 覆盖、failure reason、last nav result 和 recent task/task record 引用。页面仍保留 raw JSON，便于工程排查；`/api/status` 路径和 fixed-route status payload shape 不变。

| Objective | 当前进度判断 | 证据与缺口 |
| --- | --- | --- |
| Objective 1：硬件控制层 | 约 70% | 本轮未改硬件、UART、WAVE ROVER、Orange Pi 或 launch 参数；硬件实机/HIL 缺口不变。 |
| Objective 2：送垃圾任务闭环 | 约 74% | 本轮未改 behavior action 或任务状态机；debug 页面能辅助 fixed-route 失败复盘，但真实 fixed-route/Nav2 行驶和 E2E 上车仍待补证。 |
| Objective 3：导航与固定路线 | 约 71% | fixed-route debug 页面已覆盖当前位置、目标点、匹配/视觉门控状态、失败原因和最近任务引用；route debug web 目标测试 4 OK、nav 包 31 OK、完整 smoke 通过。仍缺真实 route/keyframe 采集、keyframe/live-frame 匹配样例和 Nav2 waypoint 实跑。 |
| Objective 4：感知模块产品化 | 约 68% | 本轮未改 vision manifest 或 detector；视觉证据链诊断能力保持，仍缺真实 camera/odom manifest 上车验证和真实路线数据集闭环。 |
| Objective 5：手机体验与量产边界 | 约 74% | 本轮主要是工程 debug 页面，不直接抬手机 operator 体验；手机本地诊断能力保持，真实手机浏览器截图、普通用户验收和喇叭/TTS 联动仍缺。 |

## 27. 本轮进度快照（2026-05-10 22:31）

本轮 `sprints/2026.05.10_21-22_review-progress-metrics/` 完成 Objective 4 的 review progress metrics 切片，Objective 5 小幅受益。新增证据聚焦复核统计可观测性：统一输出 `progress_summary`、`decision_distribution`、`next_pending_sample`，并在 operator 页面给出 `Jump To Next Pending`。本轮为软件侧闭环，不是 HIL/上车证据。

| Objective | 当前进度判断 | 证据与缺口 |
| --- | --- | --- |
| Objective 1：硬件控制层 | 无新增，仅护栏 | 本轮未改硬件协议/串口/launch 参数；硬件相关仅保持既有测试护栏。真实 WAVE ROVER HIL、真实 UART/IMU/电池证据仍缺。 |
| Objective 2：送垃圾任务闭环 | 无新增，仅护栏 | 本轮未改任务状态机和送达路径；behavior 包 smoke 通过，作为不回归证据。真实 fixed-route/Nav2 行驶与 E2E 仍缺。 |
| Objective 3：导航与固定路线 | 无新增，仅护栏 | 本轮未改 nav/route 逻辑；nav 包 smoke 通过，作为不回归证据。真实相机/路线采集与上车验证仍缺。 |
| Objective 4：感知模块产品化（主） | 小幅推进 | `/api/vision/review-queue` 与 diagnostics 同口径输出 `progress_summary.total/decided/pending/coverage_rate`、`decision_distribution.approved|rejected|needs_retry.{count,ratio}`、`next_pending_sample`；operator 页面新增 Progress/Decision distribution/Next pending sample 和 `Jump To Next Pending`，提升复核覆盖率与 pending 压力可观测性。仍缺真实相机与上车链路验证。 |
| Objective 5：手机体验与量产边界（次） | 小幅推进 | operator 本地触点从“能提 decision”扩展到“能看复核进度与分布并跳转下一条待处理样本”，提升售后/运营复盘效率；仍缺真实手机实测、真实 HIL 和量产实物验收。 |

本轮验证证据：`test_*operator*py` 42 tests OK、`python3 -m py_compile` OK、`bash scripts/run_smoke_tests.sh` OK、scoped `git diff --check -- <allowed files>` OK；`test_*review*py` 因命名 pattern 无匹配返回 `NO TESTS RAN`，全量 `git diff --check` 受范围外 `README.md` trailing whitespace 影响失败。

本轮仍未完成事项：真实硬件/HIL、真实相机采集与上车验证；`next_pending_sample` 在窗口外时仅提示不可直跳。

## 28. 本轮进度快照（2026-05-11 00:31）

本轮 `sprints/2026.05.10_23-24_route-proof-coverage/` 完成 route proof coverage 收口补强。核心变化是在既有 `route_proof_summary` contract 上新增 `missing_checkpoints` 归一化规则并补回归测试，配套更新 `docs/navigation/fixed_route_workflow.md` 与 behavior/operator 文档一致性复核；本轮 full-stack 未新增代码，仅补收口记录。证据基于两位工程子 agent 的实现与测试回传；本轮无 HIL/实机验证。

| Objective | 当前进度判断 | 证据与缺口 |
| --- | --- | --- |
| Objective 1：硬件控制层 | 保持不变（约 74%） | 本轮无硬件链路改动；仍无真实 WAVE ROVER HIL、真实 UART/反馈频率/IMU/电池实测证据。 |
| Objective 2：送垃圾任务闭环 | 保持不变（约 74%） | 本轮未改任务状态机主链；仍缺真实 fixed-route/Nav2 行驶与学习到巡逻 E2E。 |
| Objective 3：可验证导航与固定路线 | 保守小幅上调（约 76%） | `route_proof_summary` 在 coverage/阻塞语义之外补齐了 `missing_checkpoints` 归一化 contract，降低 coverage 与缺口点位自相矛盾风险；nav 与 behavior/operator 口径保持一致。测试证据为 nav `Ran 44 tests ... OK`、behavior/operator `Ran 48 tests ... OK`、smoke `Ran 128 tests ... OK` 与 `Ran 13 tests ... OK`。仍缺真实路线采集、真实相机输入和实车验证。 |
| Objective 4：感知模块产品化 | 保持不变（约 75%） | 本轮未新增 detector/样本链主能力，仅保持既有不回归信号。 |
| Objective 5：手机体验与量产边界 | 保守小幅上调（约 80%） | 仅因 operator 对 route-proof 可解释性增强（可读状态与阻塞原因更清晰）上调 +1pp；未新增真实手机实测、TTS/喇叭联动、量产实物验收。 |

本轮结论边界：上述提升均为软件/离线证据，不代表 HIL 或实机闭环完成。

## 29. 本轮产品方向快照（2026-05-11 01:02）

本轮 `sprints/2026.05.11_01-02_elevator-assisted-delivery-okr/` 只做产品/OKR 纳入，不改代码、不改硬件、不跑 ROS2 构建。电梯 assisted delivery 被定位为 H2/受控场景：它服务于跨楼层 trash delivery，但当前只完成北极星、Objective/KR、风险、下一步建议和产品流程定义，不代表小车已经具备实机进出电梯能力。

| Objective | 本轮映射 | 证据与边界 |
| --- | --- | --- |
| Objective 2：可恢复送垃圾任务闭环 | 新增 KR6，要求行为层未来覆盖等待开门、进入电梯、语音求助、等待目标楼层、目标楼层开门驶出 | 当前证据是产品 contract；未改 `task_orchestrator`，未完成状态机实现 |
| Objective 4：感知模块产品化 | 新增 KR6，要求电梯门开/关、目标楼层到达和可驶出证据进入感知 contract | 当前未新增 detector、模型或真实相机证据 |
| Objective 5：手机体验与量产边界 | 下调到30% | 新增 KR6，要求手机/语音体验解释人工协助边界和失败原因 | 当前未新增 TTS/喇叭实现、真实手机验收或量产实物验证 |

责任 Engineer：后续行为状态机由 `robot-software-engineer` 主责；电梯门/楼层/驶出感知证据由 `autonomy-engineer` 主责；手机状态与语音触点由 `full-stack-software-engineer` 主责；若涉及 WAVE ROVER、ESP32、Orange Pi、UART、电气或安装变更，必须由 `hardware-engineer` 先按 `docs/vendor/VENDOR_INDEX.md` 做事实确认。
