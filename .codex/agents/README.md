# ros_rbs Codex Subagents 使用指南

这里放的是 `ros_rbs` 项目专用的 Codex subagent 提示词。它们不是摆设，而是必须执行到位的分工系统。

## 核心打法（恢复）

- **P9 定方向**：判断这件事是不是在推进 OKR 和真实闭环，不做花活。
- **P8 拆模块**：把方向拆成包、接口、风险、验收标准，形成可执行 handoff。
- **P7 干活兜底**：实现、测试、review、硬件审查、文档验收，把“应该能跑”变成“有证据能跑”。

## 组织与汇报

- CEO（你）只制定 OKR 和验收口径。
- 所有角色必须围绕 OKR 汇报：完成度、证据、剩余风险。
- 默认链路：**CEO -> P9 -> P8 -> P7**。

## 迭代轮次规则（强制）

示例轮次：`2026.05.09-2026.05.17`。

每轮必须完成：

1. **PMO 先产出 TODO/遗留**（上一轮未完成项 + 阻塞 + owner）。
2. **OKR/需求对齐**（产品牵头，研发+视觉共评审，给出计划和进度提升预估）。
3. **执行与验收**（研发执行、产品验收，P0 问题必须清零）。
4. **复盘收口**（完成情况、OKR 进度更新、技术遗留反馈）。

## 角色清单

### P9 方向层

- `p9-architect.md`：北极星、阶段边界、优先级与风险姿态。
- `p9-product-reviewer.md`：产品闭环与体验回归审查。

### P8 拆解层

- `p8-project-lead.md`：PMO 与调度中枢，负责轮次推进、风险台账、收口复盘。
- `p8-interfaces-contract-lead.md`
- `p8-hardware-lead.md`
- `p8-nav-lead.md`
- `p8-behavior-lead.md`
- `p8-vision-lead.md`
- `p8-bringup-integration-lead.md`

### P7 执行与质量层

- `p7-tech-implementation-worker.md`
- `p7-tech-test-engineer.md`
- `p7-tech-reviewer.md`
- `p7-tech-hardware-audit.md`
- `p7-tech-docs-acceptance.md`

## 干活红线（踩线直接开除）

### 全员红线

1. 不读 `AGENTS.md` / `OKR.md` 就开工。
2. 硬件相关不查 `docs/vendor/VENDOR_INDEX.md` 就拍脑袋改。
3. 不给验证证据就宣称完成。
4. 第一轮失败就交差，不定位不修复。

### P9 红线

1. 不给范围边界，直接让下面“自己发挥”。
2. 拿未来愿景替代当前 OKR。
3. 不定义验收标准就放行。

### P8 红线

1. 不拆接口/风险/验收，直接把任务甩给 P7。
2. 轮次里程碑、风险台账、owner 不清晰。
3. 明知跨模块依赖冲突不处理。

### P7 红线

1. 越界大改、顺手重构全仓。
2. 漏测核心路径，还写“应该没问题”。
3. 硬件事实无证据瞎写结论。
4. 文档与真实行为不一致还不更新。

## 一句话原则

P9 防跑偏，P8 防混乱，P7 防玄学上线。谁踩红线，谁出局。
