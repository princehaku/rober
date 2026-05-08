# ros_rbs 三阶段完善设计规格

## 目标

把 `ros_rbs` 从一组 ROS2 节点雏形推进到可验证、可复盘、可上车迭代的自主送垃圾机器人项目。项目目标不是一次性实现所有远期能力，而是按三阶段交付：

1. 可信底盘与项目事实统一。
2. 送垃圾 MVP 任务闭环。
3. 导航、视觉、验收与产品化收口。

阶段之间允许并行做小的文档和测试补强，但代码实现必须保持每阶段可独立验证、可回滚、可解释。

## 事实来源与硬件边界

硬件相关事实必须采用本地资料，不凭记忆推断。涉及 WAVE ROVER、ESP32、Orange Pi、UART、波特率、JSON 指令、反馈协议、速度映射、引脚、电压、固件或机械尺寸时，必须先读：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`

当前设计采用的硬件事实：

- WAVE ROVER 上下位机链路是 UART。
- UART 帧格式是一行一个 UTF-8 JSON 对象，以 `\n` 结尾。
- vendor Raspberry Pi 默认示例是 `/dev/ttyAMA0` 和 `115200`，Orange Pi 实际设备名必须上车确认，代码和 launch 只能参数化。
- `T=1` 是左右轮速度命令，适合作为默认保守控制路径。
- `T=13` 是 ROS 线速度/角速度控制命令，但必须经硬件验证后再作为默认路径。
- `T=1001` 是底盘反馈，当前可用于 IMU 和电池状态；完整 `/odom` 来源必须明确标注是否为命令积分、轮速积分或实测融合。

## 阶段 1：可信底盘与项目事实统一

### 目标

让项目文档、launch 参数和硬件桥代码统一到 WAVE ROVER 官方 UART JSON 协议，避免 README、代码和 vendor 资料互相冲突。

### 范围

- 修正 `README.md` 中旧二进制串口协议描述，统一为 WAVE ROVER newline-delimited JSON。
- 新增硬件桥说明文档，记录协议来源、命令模式、反馈字段、参数、上车验证清单和未验证假设。
- 保持 `ros2_trashbot_hardware` 默认使用 `T=1` speed 模式，`T=13` ros 模式通过参数启用。
- launch 暴露并传递 `serial_port`、`serial_baudrate`、`command_mode`、`track_width_m`、`max_wheel_speed_mps`。
- 增加本地 smoke test 脚本，在 Windows 开发机上运行可脱离 ROS2 的 Python 静态/单元测试。
- 清理或记录明显生成物，例如 `__pycache__`，避免污染交付视图。

### 不做

- 不硬编码 Orange Pi 实际串口设备名。
- 不改 vendor 固件和 factory binary。
- 不承诺未上车验证的速度方向、轮距、最大轮速和 `T=13` 行为一定正确。

### 验证

- 运行硬件桥协议单元测试。
- 运行导航 route CSV/YAML 静态测试。
- 运行行为 action 契约静态测试。
- 在无法运行 ROS2 `colcon build` 的 Windows 环境中，最终说明必须写明原因和剩余风险。

## 阶段 2：送垃圾 MVP 任务闭环

### 目标

把 `task_orchestrator` 从巡逻/收集占位逻辑升级为面向用户交付垃圾后的送达任务状态机。

### 状态机

核心状态：

- `IDLE`：等待任务。
- `LOADED`：用户已确认垃圾放入小车。
- `DELIVERING`：导航或固定路线前往垃圾站。
- `DROPOFF`：到站后执行投放、提示人工取走或等待确认。
- `RETURNING`：返回起点、等待点或下一任务点。
- `ERROR`：失败后进入明确错误状态，等待人工处理或下一次任务。

状态转换必须记录时间、事件和失败原因。取消、超时、导航失败、目标缺失、投放未确认都不能静默成功。

### 接口设计

- 保留现有 `/trashbot/patrol` 和 `/trashbot/collect_trash`，但逐步把语义从“巡逻捡垃圾”调整为“送垃圾任务闭环”。
- 新增或扩展 action 字段时必须同步更新静态契约测试。
- 行为层不得直接依赖视觉算法细节，只消费稳定 topic/action/srv 契约。
- 送达目标可来自 waypoint YAML 或 fixed route 参数；第一版优先支持参数化目标和 dry-run，降低对完整 Nav2 环境的依赖。

### 任务记录

每次任务产出 JSON 复盘记录，至少包含：

- task id
- start/end time
- requested target
- state transitions
- navigation mode
- final status
- error message
- duration

### 不做

- 不实现机械臂抓取或散落垃圾自动拾取。
- 不把启发式视觉检测作为 MVP 成功前提。
- 不把没有传感器支持的“自动判断是否装载垃圾”写成强依赖。

### 验证

- 行为层新增状态机纯函数或轻量类，优先做无 ROS2 依赖单元测试。
- 覆盖成功、取消、目标缺失、导航失败、投放失败和超时路径。
- 保留现有 action 契约静态测试，并扩展检查结果/反馈字段使用位置。

## 阶段 3：导航、视觉、验收与产品化收口

### 目标

把学习路线、自主运行、固定路线 dry-run、视觉数据沉淀、上车验收和普通用户流程整理成可重复工程流程。

### 导航与固定路线

- 固化 `learn.launch.py`、`autonomous.launch.py`、`fixed_route_autonomy` 的输入输出和推荐流程。
- 保持 fixed route dry-run 能在无硬件、无 Nav2 环境下验证路线读取、关键帧 gate 和 debug status。
- debug status 增加更清晰的失败原因、当前目标、最近一次导航结果和时间戳。
- 文档说明 Nav2 waypoint 模式与 fixed route 模式的使用边界。

### 视觉

- 视觉模块定位为可迭代感知模块，而不是 MVP 的抓取前提。
- 参数化阈值、最小面积、ROI、debug image 和样本保存目录。
- 检测样本保存原图、标注图和 JSON，供后续 YOLO/RT-DETR 训练评估。
- `TrashStatus` 字段语义必须文档化，包括坐标系、置信度、类型和是否垃圾桶。

### 用户体验与验收

- 新增普通手机用户最小流程文档：连接设备、确认垃圾站、确认已放入垃圾、一键发车、查看状态、处理异常。
- 新增上车验收清单：串口、底盘停止、低速前进/后退/转向、反馈、地图、路线、任务闭环、急停。
- 新增量产硬件约束表：默认只包含底盘、上位板、随身 WiFi、摄像头、麦克风、喇叭；新增硬件必须说明成本、装配、维护和软件收益。

### 不做

- 不承诺开放道路自动驾驶。
- 不承诺复杂人群环境、复杂分类分拣、多机器人协同。
- 不把昂贵传感器或机械臂作为默认 MVP 条件。

### 验证

- 运行全部本地可跑单元/静态测试。
- 运行 smoke test 脚本。
- 在 ROS2 Humble/Orange Pi 上需要补充 `colcon build --symlink-install` 和硬件 smoke test；如果当前开发机无法执行，最终交付必须列为硬件验证缺口。

## 分阶段验收标准

### 阶段 1 完成标准

- README 与硬件桥代码不再描述互相冲突的串口协议。
- 硬件桥文档明确引用 vendor 资料。
- 所有本地 Python 单元/静态测试通过。
- smoke test 脚本能一键运行当前可脱离 ROS2 的测试。

### 阶段 2 完成标准

- 行为层没有核心任务 sleep 占位路径。
- 送垃圾任务状态机具备成功、取消、失败和超时路径。
- 每次任务能产出可复盘记录。
- 本地测试覆盖主要状态转换和 action 契约。

### 阶段 3 完成标准

- 学习、自主、固定路线和 dry-run 流程有清晰文档。
- 视觉模块能保存调试数据或明确参数关闭。
- 上车验收清单、手机用户流程和量产边界文档齐全。
- 当前开发机验证和上车验证缺口被明确列出。

## 实施顺序

1. 阶段 1 文档与 smoke test。
2. 阶段 1 硬件桥测试补强和 README 统一。
3. 阶段 2 行为状态机设计与无 ROS2 单元测试。
4. 阶段 2 action/result/任务记录接入。
5. 阶段 3 导航流程文档和 debug status 补强。
6. 阶段 3 视觉样本保存与参数化。
7. 阶段 3 验收清单、手机流程和量产边界文档。

## 风险与决策

| 风险 | 影响 | 决策 |
| --- | --- | --- |
| Windows 开发机没有 ROS2 Humble | 无法本地完整 `colcon build` | 先做可脱离 ROS2 的单元/静态测试，上车或 WSL/Ubuntu 环境补 ROS2 构建 |
| Orange Pi 串口设备名未确认 | launch 默认值可能不可用 | 保持参数化，上车验收确认实际设备 |
| `T=13` 未硬件验证 | 直接映射 `/cmd_vel` 可能运动异常 | 默认 `T=1`，`T=13` 仅参数启用 |
| `/odom` 当前可能是命令积分 | Nav2 定位质量受限 | 文档明确来源，中期接入实测轮速/编码器融合 |
| 行为层直接追求复杂智能 | MVP 失焦 | 第一闭环固定为用户交付后的送达任务 |
| 视觉启发式误检 | 影响任务判断 | 视觉不作为 MVP 成功条件，先用于调试和数据沉淀 |

## 后续计划入口

本设计通过审阅后，下一步应编写分任务实施计划。实施计划需要把每个阶段拆成具体文件、测试和验收步骤，并在每批改动后运行可用验证。
