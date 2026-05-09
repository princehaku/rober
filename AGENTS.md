# ros_rbs - Autonomous Trash Collection Robot

ROS2 自主自动驾驶扔垃圾小车项目。

## 必读资料入口

硬件、线路、串口、底盘协议、Orange Pi Zero 3、WAVE ROVER、固件、机械安装相关任务，必须先读：

`docs/vendor/VENDOR_INDEX.md`

AI coding / Agent 工作不允许凭记忆猜测硬件细节。涉及引脚、电压、UART 设备、波特率、JSON 指令、速度映射、反馈协议、机械尺寸时，必须以 `docs/vendor/` 下的本地资料为准，并在代码或说明中明确采用的资料来源。

## 架构

5 个包协同工作：

- **ros2_trashbot_interfaces** - 自定义 msg/srv/action
- **ros2_trashbot_nav** - Nav2 导航 + waypoint_manager + map_recorder
- **ros2_trashbot_vision** - 摄像头垃圾检测 (cv_bridge)
- **ros2_trashbot_behavior** - task_orchestrator 状态机 + action server
- **ros2_trashbot_bringup** - 启动文件

## 工作流程

1. **学习阶段**: `learn.launch.py` -> SLAM 建图 + 人工驾驶记录航点
2. **自主阶段**: `autonomous.launch.py` -> 加载地图 -> 巡逻 -> 检测垃圾 -> 导航收集 -> 送至垃圾桶

## 构建命令

```bash
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

## Agent 工作纪律

后续 AI coding / Agent 工作必须保持持续执行和完成前反思：

- **持续执行**：除非用户明确要求只做计划、解释或代码审查，否则默认把任务推进到可交付状态，包括实现、必要验证、修复验证中发现的问题，以及最后总结。
- **完成前反思**：每次代码或文档改动后，必须自检需求是否真正满足，是否误改无关文件，是否留下未处理 TODO，是否存在测试、构建或硬件验证缺口。
- **失败继续定位**：测试、构建或运行验证失败时，默认先阅读错误、定位根因、修复并重新验证；不能把第一轮失败直接作为最终结果交给用户。
- **硬件相关二次确认**：凡涉及 WAVE ROVER、ESP32、Orange Pi、UART 设备、波特率、JSON 指令、速度映射、反馈协议、引脚、电压、固件或机械尺寸，必须再次查阅 `docs/vendor/VENDOR_INDEX.md` 及其指向的本地 vendor 文件，并在代码注释、提交说明或最终说明中明确采用的资料来源。
- **验证围栏**：能运行测试、构建、静态检查或最小可行验证时必须运行；无法运行时，最终说明必须写清楚原因、影响和剩余风险。
- **最终回复要求**：最终说明必须包含实际改动、验证结果，以及未完成事项或风险；如果没有未完成事项，也要明确说明验证范围。

## 本地环境记忆

- 当前 Windows 主机有 WSL `Ubuntu-24.04`，但本项目目标是 ROS2 Humble。不要为了 Humble 强行改造 Ubuntu 24.04。
- ROS2 Humble 构建验证优先使用 Docker 官方 Humble 容器挂载仓库，例如挂载 `E:\rober` 到容器 `/ws` 后运行 `colcon build --symlink-install`。

## 执行优先与精简团队

默认先交付可验证结果，再同步更新迭代记录。流程服务于执行，不得替代执行；但所有任务都必须进入 sprint 留档，不能口头收口。

### 5 人 agent 编制

只保留 1 个产品负责人和 4 个一线交付同学：

- **Product Manager / OKR Owner**：拉齐产品北极星，维护 `OKR.md`，拆 KR，定抓手、优先级、范围边界和验收口径。只在方向不清、用户价值不清、范围冲突、阶段收口时介入。
- **Robot Platform Engineer**：机器人软件中台，负责 ROS2 主链路、接口 glue、bringup、行为状态机、包间集成和最小验证。
- **Hardware Infra Engineer**：硬件基建与履约，负责 WAVE ROVER、ESP32、Orange Pi、UART、底盘协议、电气接线和上车证据。
- **Autonomy Algorithm Engineer**：自主能力增长引擎，负责 SLAM、Nav2、巡逻、定位、视觉检测、垃圾收集自主闭环。
- **User Touchpoint Full-Stack Engineer**：用户触点全栈，负责手机操作界面、Web/API、远程控制、状态展示、任务下发和 ROS2 后端联调。

除 `Product Manager / OKR Owner` 外，不使用 Lead 角色。一线同学必须能直接实现、测试、修复和交付。

### 组织层级

- **L0 CEO（用户）**：定方向、OKR 和验收口径，不参与日常实现。
- **L1 Product Manager / OKR Owner**：承接产品方向，拆 KR，定优先级，裁边界，做阶段验收，并确保 sprint 留档真实更新。
- **L2 IC Engineers**：四个一线交付同学，按领域直接实现、测试、修复和交付。

默认链路：`CEO -> Product Manager / OKR Owner -> IC Engineers`。

升级条件：方向不清、用户价值不清、范围冲突、跨多个 L2、阶段验收、OKR/KR 更新时，升级到 L1。

### 任务路由规则

- OKR/KR、产品方向拆解、用户价值判断、阶段验收、范围冲突：交给 `Product Manager / OKR Owner`。
- ROS2 接口、行为、bringup、launch、包间集成：交给 `Robot Platform Engineer`。
- WAVE ROVER、ESP32、Orange Pi、UART、电气、底盘协议：交给 `Hardware Infra Engineer`。
- SLAM、Nav2、巡逻、视觉检测、自主收集闭环：交给 `Autonomy Algorithm Engineer`。
- 手机界面、Web/API、远程控制、状态展示、任务下发：交给 `User Touchpoint Full-Stack Engineer`。

跨角色任务由最相关一线同学主责，其他同学只补专业事实或接口边界，不新增管理层。并行只适用于互不重叠的复杂任务；若单个一线同学能在清晰边界内完成并验证，应优先单线闭环。

### Sprint 留档原则

Sprint 文档是项目迭代的主线，不允许因为“执行优先”就不写迭代。执行优先的含义是：先推进可验证结果，边做边更新必要记录，不能让写文档替代干活，也不能让干活脱离留档。

所有任务必须归入当前活跃 sprint；如果没有活跃 sprint，必须先创建新的 `sprints/<round>/pre_start.md`，记录目标、owner、验收口径和风险后再推进。

迭代文档顺序固定为：

- `pre_start.md`：上轮未完成项、阻塞、owner。
- `prd.md`：需求、OKR 对齐、验收口径。
- `tech-plan.md`：技术方案、接口、风险、验证计划。
- `tech-done.md`：实际改动、验证结果、偏差。
- `side2side_check.md`：用户验收或对照检查。
- `final.md`：复盘、OKR 进度、技术遗留。

文档契约：

- 每个阶段写清状态后，再进入下一个阶段文档。
- 禁止一次性预生成整轮文档冒充进度。
- 如果历史上已有后续文档草稿，在前置阶段完成前只能视为 draft，不得作为有效收口证据。
- 代码、配置或文档实际改动完成后，必须把验证结果和剩余风险写入 `tech-done.md` 或当前阶段对应文档。
- 验收或复盘任务必须更新 `side2side_check.md` / `final.md`，不能只在聊天里口头收口。

- 所有代码、配置、文档、流程或 agent 变更，都必须至少更新当前 sprint 的 `tech-done.md`；涉及验收或风险状态变化时，同时更新 `side2side_check.md` 或 `final.md`。如果没有当前 sprint，必须先启动新迭代。

### 组织链路与全员红线

汇报链路：CEO（用户）只定 OKR 和验收口径。复杂任务围绕 `OKR.md` 更新完成度、证据和剩余风险。

全员红线：

- 不读 `AGENTS.md` 就开始复杂任务。
- 硬件相关不查 `docs/vendor/VENDOR_INDEX.md` 就下结论或改代码。
- 一轮迭代后对 `OKR.md` 进展毫无帮助。
- 没有验证证据就宣称完成。
- 验证失败后不定位、不修复，直接交差。
- 不按迭代推进。