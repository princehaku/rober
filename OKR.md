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

更新时间：2026-05-10 03:22 Asia/Shanghai。

| Objective | 当前进度 | 本轮新增证据 | 剩余关键缺口 |
| --- | --- | --- | --- |
| Objective 1 硬件协议可信底盘 | 约 70% | 本地 smoke 持续覆盖硬件桥 JSON 编码、速度映射、反馈解析、坏数据容错 | Docker/Humble 与 WAVE ROVER HIL 仍未在本轮通过 |
| Objective 2 可恢复送垃圾任务闭环 | 约 66% | 主 `task_orchestrator` 已具备装载确认、delivery、dropoff、return、action result、task record 和 fixed-route status reader 证据；终态失败字段已进入 diagnostics 消费链 | `use_saved_map=false` 学习阶段仍有模拟完成口径；legacy server 仍保留 sleep demo |
| Objective 3 可验证导航与固定路线 | 约 60% | fixed-route dry-run 在 `enable_visual_gate=true` 时不再绕过 keyframe/camera 准入，会写出 `waiting_visual_gate`、checkpoint 和 failure reason | 仍需真实 keyframe/live frame 匹配样例、Nav2 waypoint 实跑和 Docker/Humble build |
| Objective 4 感知模块产品化 | 约 50% | 视觉节点已支持原图、标注图、检测 JSON、manifest 落盘，样本 JSON 增加 task/route/checkpoint/event/anomaly 上下文；支持可选空检测负样本入口；感知升级评估表已成文 | 仍需真实路线数据集、runtime 文件写入单测和持续标注流程 |
| Objective 5 手机体验与量产边界 | 约 64% | operator gateway 本地页面升级为手机优先操作台；所有 status-style payload 输出 `phone_copy` / `speaker_prompt`；页面展示任务流程、位置、诊断摘要和主操作按钮 | 真实手机浏览器、喇叭/TTS、量产硬件约束实物验收仍需落地 |

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

3. **移除行为层占位逻辑**
   - 主 `task_orchestrator` 的 patrol/collection/delivery 已进入 waypoint/fixed-route/action-result 路径；继续清理 `use_saved_map=false` 学习阶段模拟完成口径。
   - legacy `trash_collection_server.py` 仍是 sleep demo，只能保留为旧入口或删除，不能作为当前闭环完成证据。

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
