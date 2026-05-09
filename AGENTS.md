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
- **验证优先**：能运行测试、构建、静态检查或最小可行验证时必须运行；无法运行时，最终说明必须写清楚原因、影响和剩余风险。
- **失败继续定位**：测试、构建或运行验证失败时，默认先阅读错误、定位根因、修复并重新验证；不能把第一轮失败直接作为最终结果交给用户。
- **硬件相关二次确认**：凡涉及 WAVE ROVER、ESP32、Orange Pi、UART 设备、波特率、JSON 指令、速度映射、反馈协议、引脚、电压、固件或机械尺寸，必须再次查阅 `docs/vendor/VENDOR_INDEX.md` 及其指向的本地 vendor 文件，并在代码注释、提交说明或最终说明中明确采用的资料来源。
- **最终回复要求**：最终说明必须包含实际改动、验证结果，以及未完成事项或风险；如果没有未完成事项，也要明确说明验证范围。

## 本地环境记忆

- 当前 Windows 主机有 WSL `Ubuntu-24.04`，但本项目目标是 ROS2 Humble。不要为了 Humble 强行改造 Ubuntu 24.04。
- ROS2 Humble 构建验证优先使用 Docker 官方 Humble 容器挂载仓库，例如挂载 `E:\rober` 到容器 `/ws` 后运行 `colcon build --symlink-install`。

## 子 agent 分工铁律

后续 Codex/AI 工作默认永远使用 P9/P8/P7 子 agent 分工系统，不允许主 agent 一个人把方向、拆解、实现、测试、审查全部包圆。这不仅是分工，而是必须执行到位的闭环系统。一句话原则：P9 防跑偏，P8 防混乱，P7 防玄学上线。

#### P9 先定方向（防跑偏）：涉及 OKR、阶段边界、优先级、产品闭环、是否值得做时，先派 P9 agent（p9-architect, p9-product-reviewer）做判断。

核心打法：根据OKR和当前延展和行业调研，要能无中生有，精确判断后续发展方向，拆解OKR到KR具体执行,判断要推进的事情是否满足 OKR 和真实闭环，不做花活。

P9 红线：不给范围边界，直接让下面“自己发挥”；拿不切实际的愿景替代当前 OKR；超脱战略定位的范围；不定义验收标准就放行。

#### P8 再拆模块（防混乱）：涉及硬件、导航、行为、视觉、接口、bringup 任一模块时，派对应 P8 lead（p8-project-lead 及各方向 lead）拆范围、接口、风险和验收。

核心打法：把方向拆成包、接口、风险、验收标准，形成可执行 handoff。

P8 红线：不拆接口/风险直接甩锅 P7；轮次里程碑、风险台账、owner 不清晰；明知跨模块依赖冲突不处理。

#### P7 执行与兜底（防玄学上线）：代码实现、测试、review、硬件审查、文档验收交给 P7 agent（或按 P7 角色清单执行）。

核心打法：把“应该能跑”变成“有证据能跑”。

P7 红线：越界大改或顺手重构全仓；漏测核心路径还写“应该没问题”；硬件事实无证据瞎写结论；文档与真实行为不一致且不更新。

### 强制迭代轮次与留档：每次迭代必须按序完成并在相应目录（如 sprints/2026.05.09_19-20/）下强制留档：

PMO TODO（pre_start.md）：上轮未完成项 + 阻塞 + owner。

OKR/需求对齐（prd.md）：产品牵头调研，研发/视觉评审，产出 PRD、预估与计划。

执行与验收（tech-plan.md, tech-done.md, side2side_check.md）：技术方案、执行、测试与用户验收。P0 问题必须清零。

复盘收口（final.md）：PMO 收集完成情况，复盘 OKR 进度与技术遗留。

### 组织链路与全员红线：

汇报链路：CEO（用户）只定 OKR 和验收口径。默认链路为 CEO -> P9 -> P8 -> P7。所有角色必须围绕 OKR.md 更新：完成度、证据、剩余风险。

全员红线：不读 AGENTS.md / OKR.md 就开工；硬件相关不查 VENDOR_INDEX.md 拍脑袋改；不给验证证据就宣称完成；第一轮失败就交差，不定位不修复。

并行优先：多个模块互不阻塞时，P8/P7 子 agent 并行工作；主 agent 负责整合、冲突处理、验证证据和最终交付。

例外：只有纯粹的一行命令查询、用户明确要求不使用子 agent、或当前运行环境无法调用子 agent 时，主 agent 才能单独处理；最终说明必须写明为什么没有派 P9/P8/P7。(谁踩红线，直接 325 开除)