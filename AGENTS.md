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
- **ros2_trashbot_vision** - 未来可选摄像头感知/样本边界；当前 MVP 不默认发布散落垃圾 detector
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
- **文档同步更新**：任何功能开发、修复或架构调整，必须同步更新 `docs/` 目录下的相关文档。`docs/` 目录中的文档必须始终反映项目的最新状态，不得滞后于代码实现。
- **技术要求与注释规范**：代码中的所有技术注释必须使用**中文**。注释比例必须**超过 20%**（即每 5 行代码中应包含至少 1 行有意义的中文注释）。注释应解释“为什么”这样做，特别是对于复杂逻辑。
- **最终回复要求**：最终说明必须包含实际改动、验证结果，以及未完成事项或风险；如果没有未完成事项，也要明确说明验证范围。

## 本地环境记忆

- 当前 Windows 主机有 WSL `Ubuntu-24.04`，但本项目目标是 ROS2 Humble。不要为了 Humble 强行改造 Ubuntu 24.04。
- ROS2 Humble 构建验证优先使用 Docker 官方 Humble 容器挂载仓库，例如挂载 `E:\rober` 到容器 `/ws` 后运行 `colcon build --symlink-install`。
- 本项目已有本地 Docker/Humble 环境：`docker/humble/Dockerfile` 默认使用清华 Ubuntu APT、ROS2 APT、pip、rosdep/rosdistro 镜像源，适合 WSL + Docker Desktop/Engine。
- 构建并验证工作区：`bash scripts/docker_humble_build.sh`。脚本会构建 `ros-rbs-humble:dev`，再在容器内清理 `build/ install/ log/` 并执行 `colcon build --symlink-install`。
- 只构建镜像不跑 colcon：`SKIP_COLCON=1 bash scripts/docker_humble_build.sh`。需要换源时覆盖 `UBUNTU_APT_MIRROR`、`ROS_APT_MIRROR`、`PIP_INDEX_URL`、`ROSDEP_SOURCE_MIRROR`、`ROSDISTRO_INDEX_URL`。
- 进入开发容器：`bash scripts/docker_humble_dev.sh`。容器挂载仓库到 `/ws`、持久化 `.ros_home` 到 `/root/.ros`、使用 `--network host`，登录 shell 会自动 source `/opt/ros/humble/setup.bash` 和 `/ws/install/setup.bash`。
- 串口或图形参数通过 `EXTRA_DOCKER_ARGS` 传入，例如 `EXTRA_DOCKER_ARGS="--device=/dev/ttyUSB0" bash scripts/docker_humble_dev.sh`。
- 最近验证：`bash scripts/docker_humble_build.sh` 可完成镜像构建和 `colcon build`；`docker run --rm -v "$PWD:/ws" -w /ws ros-rbs-humble:dev bash -l -c "ros2 pkg prefix ros2_trashbot_bringup"` 能返回 `/ws/install/ros2_trashbot_bringup`。

## 执行优先与精简团队

默认先交付可验证结果，再同步更新迭代记录。流程服务于执行，不得替代执行；但所有任务都必须进入 sprint 留档，不能口头收口。

### 5 人 agent 编制

1 个产品负责人和 4 个编码和测试的技术同学：

- **Product Manager / OKR Owner**：拉齐产品北极星，维护 `OKR.md`，拆 KR，定抓手、优先级、范围边界和验收口径。只在方向不清、用户价值不清、范围冲突、阶段收口时介入。
- **Robot Platform Engineer** ：机器人软件中台，负责 ROS2 主链路、接口 glue、bringup、行为状态机、包间集成和最小验证。
- **Hardware Infra Engineer**：硬件基建与履约，负责 WAVE ROVER、ESP32、Orange Pi、UART、底盘协议、电气接线和上车证据。
- **Autonomy Algorithm Engineer**：自主能力增长引擎，负责 SLAM、Nav2、巡逻、定位、未来可选视觉感知、送达闭环。
- **User Touchpoint Full-Stack Engineer**：用户触点全栈，负责手机操作界面、Web/API、远程控制、状态展示、任务下发和 ROS2 后端联调。

除 `Product Manager / OKR Owner` 外，不使用 Lead 角色。

编码、测试、修复和交付 必须由子agent
"product-okr-owner"
"robot-software-engineer"
"hardware-engineer"
"full-stack-software-engineer"
"autonomy-engineer"
来完成，严禁主节点自己写产品代码、测试代码或硬件配置。

### 子 Agent 启动 SOP（主节点必读）

主节点（Cursor Agent / Codex 主会话）的唯一职责是：读文件、任务拆解、子 agent 启动、等待子 agent、集成验收、sprint 文档更新、最终汇总。**写产品代码、写测试代码、改硬件配置、运行实现/测试/修复命令，一律由子 agent 完成。**

主节点白名单：

- 只读查看 `AGENTS.md`、`OKR.md`、当前 sprint 文档、相关代码和配置。
- 拆分任务、确认 owner、生成子 agent prompt。
- 通过运行时支持的子 agent 工具派发任务，并等待结果。
- 汇总子 agent 结果，做集成验收判断，必要时要求子 agent 重试。
- 更新 sprint 留档和最终汇总；若用户明确限定文件范围，则只在允许范围内更新。

主节点禁区：

- 不直接修改产品代码、测试代码、硬件配置、launch 参数或业务文档。
- 不直接运行构建、测试、硬件 smoke、格式化或修复命令；验收命令必须交给对应子 agent 执行。
- 不覆盖他人改动，不回滚无关文件，不扩大文件范围。
- 无子 agent 工具时，不得假装已经派发；只能做只读排查、计划拆解，并明确说明当前运行时缺少子 agent 能力。

#### 可机械执行决策树

1. read-only：用户明确要求只读排查、解释、review、状态同步时，主节点可只读文件并输出结论；不得改文件或运行测试。
2. planning：方向不清、文件范围/验收命令/接口边界不清，或当前 sprint 缺少 `tech-plan.md` 时，主节点补计划或要求 Product Manager / OKR Owner 产出计划；计划完成前不得进入实现。
3. implementation：需求、owner、文件范围、验收命令清楚时，必须派子 agent 执行实现、测试和修复。1 owner 必须派 1 个子agent；2+ owner 且文件范围互不重叠必须并行派多个子agent；2+ owner 但接口耦合时指定 1 个主责 owner，其他 owner 只做只读咨询或接口事实补充。
4. acceptance：子 agent 返回后，主节点只做结果验收、证据核对、sprint 留档和最终汇总；如果验证失败或证据不足，必须把失败定位和重试任务再派给对应子 agent。

#### Role → Runtime 映射

| 业务角色 | Cursor Task subagent_type | Codex agent_type | 读取 prompt 来源 | 可改范围 |
|---|---|---|---|---|
| product-okr-owner | `generalPurpose` | `worker` | `.codex/agents/product-okr-owner.toml` 的 `prompt` 字段 | `OKR.md`、`sprints/`、`docs/product/` |
| robot-software-engineer | `generalPurpose` | `worker` | `.codex/agents/robot-software-engineer.toml` 的 `prompt` 字段 | ROS2 主链路、接口、behavior、bringup、脚本和相关文档 |
| hardware-engineer | `generalPurpose` | `worker` | `.codex/agents/hardware-engineer.toml` 的 `prompt` 字段 | 硬件驱动、bringup 硬件参数、硬件/vendor 文档 |
| autonomy-engineer | `generalPurpose` | `worker` | `.codex/agents/autonomy-engineer.toml` 的 `prompt` 字段 | nav、vision、behavior 自主能力和相关文档 |
| full-stack-software-engineer | `generalPurpose` | `worker` | `.codex/agents/full-stack-software-engineer.toml` 的 `prompt` 字段 | 手机/Web/API/UI、接口文档和触点联调 |

运行时调用规则：

- Cursor：使用 Cursor Task，`subagent_type=generalPurpose`。
- Codex：使用 `spawn_agent(agent_type=worker)`，prompt 中显式写入角色 id 和完整 System Prompt。
- 其他运行时：若没有等价子 agent 工具，只能降级为 read-only/planning，并向用户说明不能执行实现。

#### 子 Agent Prompt 固定结构

主节点在调用 Cursor Task 或 Codex `spawn_agent(agent_type=worker)` 时，prompt 必须包含以下五段，不得省略：

```
[角色 System Prompt]
（从对应 .codex/agents/<role>.toml 的 prompt 字段完整复制，不裁剪）

[本轮任务]
（清晰描述这次要做什么，包括背景和目标）

[文件范围]
（明确列出允许改动的文件路径；范围外的文件不得改动）

[验收命令]
（从 tech-plan.md 复制验证命令，子 agent 必须运行并给出结果）

[输出要求]
必须返回：
1. 实际改动的文件列表
2. 验证命令输出结果（截图或日志片段）
3. 失败定位（如有）
4. 剩余风险
```

#### 并行启动强制规则

- **tech-plan 有清晰文件范围且任务互不重叠时，必须在同一条消息里并行发起多个 Task / spawn_agent 调用**（每个角色一个子 agent，不序列化等待）。
- 1 owner 任务（整个 sprint 只有一个工程师负责）也**必须派 1 个子agent**，不得主节点自己动手。
- 2+ owner 且文件范围互不重叠时，必须并行派多个子agent。
- 2+ owner 但接口耦合、共享文件或验收链路强相关时，指定 1 个主责 owner 负责实现和集成，其他 owner 只读咨询或补专业事实。
- "单线闭环"的含义是：**一个子 agent 单线负责到底**，不是主节点自己写。
- 主节点收到子 agent 返回后，只做：验收结果、更新 sprint 文档、决定是否需要重试或集成。

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
- SLAM、Nav2、巡逻、未来可选视觉感知、送达闭环：交给 `Autonomy Algorithm Engineer`。
- 手机界面、Web/API、远程控制、状态展示、任务下发：交给 `User Touchpoint Full-Stack Engineer`。

跨角色任务由最相关一线同学主责，其他同学只补专业事实或接口边界，不新增管理层。并行只适用于互不重叠的复杂任务；若单个一线同学能在清晰边界内完成并验证，应优先单线闭环。

### Tech Plan 自动执行规则

当当前 sprint 的 `tech-plan.md` 已完成，并且已经写清任务分工、文件范围、接口影响、验收命令和风险边界时，默认进入实现阶段，不再停留在计划阶段：

- 1 owner 任务由主责 Engineer 子 agent 直接实现、验证并更新 `tech-done.md`。
- 2+ owner 且文件范围互不重叠的任务必须并行启动对应 Engineer 子 agent；必须明确每个 Engineer 的文件范围、接口边界和验证命令。
- 跨角色或接口耦合任务必须指定一个主责 owner 做最终集成验证，默认由 `Robot Platform Engineer` 承担 ROS2 主链路集成。
- 如果 `tech-plan.md` 缺少验收命令、文件范围或接口边界，先补齐计划再执行；不得用模糊计划触发并行改代码。
- 只有用户明确要求“只做计划 / 不要实现 / 等我确认”时，才在 `tech-plan.md` 后暂停。

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
