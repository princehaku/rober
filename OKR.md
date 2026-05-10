# ros_rbs P9 项目设计与前瞻 OKR

## 1. 北极星

把 `ros_rbs` 做成一台面向普通手机用户的低成本 ROS2 自主垃圾投递机器人：用户把垃圾交给小车后，小车沿固定路线出发，把垃圾送到垃圾站/垃圾桶点位，再安全返回或等待下一次任务，而不是一次性 demo，也不是依赖机械臂到处捡垃圾的机器人。

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

5. **默认安全、低速、可停**
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

### Objective 5：建立手机用户体验与低成本量产边界

**目标说明**：让不会电脑和硬件的用户可以用手机完成核心任务，同时把硬件方案控制在低成本、可批量装配、可售后诊断的范围内。

**Key Results**

- KR1：定义手机端最小流程：连接设备 -> 选择/确认垃圾站 -> 确认已放入垃圾 -> 一键发车 -> 查看状态 -> 处理异常。
- KR2：定义语音/喇叭提示词和状态触发点，覆盖待装载、准备出发、行驶中、到达、失败、需要人工接管。
- KR3：形成量产硬件约束表，默认只包含小车底盘、上位板、随身 WiFi、摄像头、麦克风、喇叭；新增硬件必须有成本、装配、维护和软件收益说明。
- KR4：建立远程诊断最小数据包：软件版本、地图/路线版本、最近任务状态、失败原因、关键日志、摄像头快照引用。
- KR5：形成用户验收标准：普通用户不接触命令行、不插线调试、不理解 ROS2，也能完成一次送垃圾任务并知道失败时该怎么做。

## 4.1 当前 OKR 进度快照

更新时间：2026-05-10 15:45 Asia/Shanghai。

| Objective | 当前进度 | 本轮新增证据 | 剩余关键缺口 |
| --- | --- | --- | --- |
| Objective 1 硬件协议可信底盘 | 约 70% | 本地 smoke 持续覆盖硬件桥 JSON 编码、速度映射、反馈解析、坏数据容错 | Docker/Humble 与 WAVE ROVER HIL 仍未在本轮通过 |
| Objective 2 可恢复送垃圾任务闭环 | 约 74% | `TrashCollection` fixed-route 送达会把 fixed-route status JSON 的结构化证据写入 `nav_results` 和 task record；legacy `trash_collection_server.py` 已被 quarantine，旧入口被调用时返回 `legacy_server_quarantined`，不再 sleep 后伪造成功 | 真实 fixed-route/Nav2 行驶、真实 SLAM/Nav2 学习到巡逻 E2E 还缺实测 |
| Objective 3 可验证导航与固定路线 | 约 68% | fixed-route dry-run 在 `enable_visual_gate=true` 时已有全路线 keyframe preflight；`learn.launch.py` 现在可通过 `route_recorder:=true` 同步启动 `route_data_recorder`，学习阶段能标准化产出 route CSV/keyframes/manifest | 仍需真实 keyframe/live frame 匹配样例、Nav2 waypoint 实跑、Docker/Humble build 和真实路线采集 |
| Objective 4 感知模块产品化 | 约 68% | vision sample manifest 离线 checker 结果已被 `/api/diagnostics.vision_samples` 消费，本轮 operator 页面新增 Vision evidence chain 诊断卡片，能把 `integrity_summary`、missing refs、error/warning、context coverage 和 file counts 展示给用户触点 | 仍需真实路线数据集、真实 ROS2 camera/odom 采集、持续标注/人工标注闭环、真实 manifest 复盘和上车验证 |
| Objective 5 手机体验与量产边界 | 约 74% | 本轮 operator 页面把 Vision evidence chain 健康状态、缺失原因和恢复建议转成手机可读诊断灯；Full-Stack Engineer 记录 HTTP 页面测试 16 OK、py_compile OK、git diff --check OK、完整 smoke 通过，Coordinator 复跑前三项通过 | 真实手机浏览器截图、真实 camera/odom manifest 上车验证、喇叭/TTS、量产硬件约束实物验收仍需落地 |

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

## 6. 当前最高优先级

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
