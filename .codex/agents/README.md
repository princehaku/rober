# ros_rbs Codex Subagents 使用指南

这里放的是 `ros_rbs` 项目专用的 Codex subagent 提示词。它们不是摆设，也不是“赛博组织架构图”，而是给 Codex 分工时可以直接复制、引用、派活的角色卡。

核心打法：

- **P9 定方向**：判断这事是不是在把机器人从“能演示”推向“能长期稳定干活”。少做赛博盆栽，多做真实闭环。
- **P8 拆模块**：把方向拆成包、接口、风险、验收标准。别让任务变成“一把梭改全仓”。
- **P7 干活兜底**：实现、测试、review、硬件审查、验收文档。让代码别只在想象中跑赢世界。

## 全员铁律

所有 agent 都必须遵守：

- 先读 `AGENTS.md` 和 `OKR.md`，别上来就灵感施工。
- 保护 ROS2 架构：interfaces、hardware、nav、vision、behavior、bringup 各司其职。
- topic/action/srv、消息语义、launch 参数不能随手整活。
- 不回滚用户已有改动。看到脏工作区，先稳住，别开大。
- 小步可验证优先，拒绝“大重构式梭哈”。
- 每次交付都要说明：改了啥、怎么验证、还剩啥风险、下一个谁接。
- 涉及硬件事实时，必须先读 `docs/vendor/VENDOR_INDEX.md`，再读它指向的本地 vendor 文件。

硬件事实包括：WAVE ROVER、ESP32、Orange Pi、UART 设备、波特率、JSON 指令、速度映射、反馈协议、引脚、电压、固件、机械尺寸。

## 推荐派活姿势

1. 方向不清、优先级打架、阶段边界模糊：先派 `p9-architect.md`。
2. 担心做成花活、不是真闭环：派 `p9-product-reviewer.md`。
3. 需要拆包、拆接口、拆验收：按模块派 P8 lead。
4. 要写代码：派 `p7-implementation-worker.md`。
5. 要补测试和 smoke：派 `p7-test-engineer.md`。
6. 要审 diff：派 `p7-reviewer.md`。
7. 一碰硬件：加派 `p7-hardware-audit.md`，别凭肌肉记忆猜串口。
8. 要收尾交付：派 `p7-docs-acceptance.md`。

## Agent 名单

### P9 方向层

- `p9-architect.md`：北极星、OKR、阶段边界、风险姿态。负责问“这事值不值得做”。
- `p9-product-reviewer.md`：产品/任务闭环审查。负责问“这机器人真的更会捡垃圾了吗”。

### P8 模块拆解层

- `p8-interfaces-contract-lead.md`：msg/srv/action 契约、字段语义、兼容性。
- `p8-hardware-lead.md`：底盘串口桥、WAVE ROVER JSON、反馈、launch 参数。
- `p8-nav-lead.md`：Nav2、固定路线、route 数据、dry-run、debug web。
- `p8-behavior-lead.md`：task_orchestrator、巡逻/收集/投放/返回状态机。
- `p8-vision-lead.md`：TrashStatus、OpenCV 检测、样本沉淀、模型升级边界。
- `p8-bringup-integration-lead.md`：learn/autonomous/bringup launch 和系统集成。

### P7 执行与质量层

- `p7-implementation-worker.md`：按边界干活，别乱改。
- `p7-test-engineer.md`：把“应该没问题”变成“有证据”。
- `p7-reviewer.md`：专抓 bug、回归、漏测和危险假设。
- `p7-hardware-audit.md`：硬件事实审查，专治“我记得应该是”。
- `p7-docs-acceptance.md`：文档、验收清单、runbook 收尾。

## 典型编队

硬件桥改动：

1. `p9-architect` 判断是否推进 Objective 1。
2. `p8-hardware-lead` 定协议、参数、反馈、测试。
3. `p8-interfaces-contract-lead` 看 ROS topic/action 是否被影响。
4. `p7-implementation-worker` 写代码。
5. `p7-test-engineer` 跑协议测试和 smoke。
6. `p7-hardware-audit` 查 vendor 证据。
7. `p7-reviewer` 最终审 diff。

行为编排改动：

1. `p9-product-reviewer` 判断是不是在做真实巡逻/收集/投放闭环。
2. `p8-behavior-lead` 拆状态机、失败路径、action result。
3. `p8-nav-lead` 拆路线和 waypoint 依赖。
4. `p7-implementation-worker` 实现一个小切片。
5. `p7-test-engineer` 补状态转移、取消、失败、dry-run 测试。
6. `p7-reviewer` 抓可靠性和边界条件。

## 一句话原则

P9 防止方向跑偏，P8 防止模块糊成一锅粥，P7 防止代码靠玄学上线。大家一起努力，让小车别只会“看起来很努力”，而是真的能低速、可停、可复盘地把垃圾送回家。

