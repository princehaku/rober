# Codex Subagents 落地计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**目标：** 为 `ros_rbs` 建立一套 Codex 可直接使用的 P9/P8/P7 subagent 角色库。

**架构：** 把项目本地 agent 提示词放在 `.codex/agents/`。P9 负责方向和阶段边界，P8 负责模块拆解和接口/验收，P7 负责实现、测试、review、硬件审查和文档收口。整体风格改成中文，并加入适量互联网黑话，让它既好笑、好记，又不是赛博废话。

**技术栈：** Markdown 文档、Codex subagent prompts、ROS2 Humble 项目约定。

---

### Task 1: Agent 索引

**Files:**
- Create/Modify: `.codex/agents/README.md`

- [x] **Step 1: 写中文索引**

说明 P9/P8/P7 分工、派活顺序、共享铁律和 agent 目录。

- [x] **Step 2: 调整语气**

加入“别灵感施工”“赛博盆栽”“开盲盒”等记忆点，但保留硬件事实、验证、review 等刚性约束。

### Task 2: P9 方向层

**Files:**
- Create/Modify: `.codex/agents/p9-architect.md`
- Create/Modify: `.codex/agents/p9-product-reviewer.md`

- [x] **Step 1: 写战略角色**

覆盖北极星、OKR、阶段边界、产品闭环、demo-vs-reliable-operation 审查。

- [x] **Step 2: 控制边界**

明确 P9 不写代码，不编硬件事实，只负责判断、收窄和交给 P8。

### Task 3: P8 模块拆解层

**Files:**
- Create/Modify: `.codex/agents/p8-hardware-lead.md`
- Create/Modify: `.codex/agents/p8-nav-lead.md`
- Create/Modify: `.codex/agents/p8-behavior-lead.md`
- Create/Modify: `.codex/agents/p8-vision-lead.md`
- Create/Modify: `.codex/agents/p8-bringup-integration-lead.md`
- Create/Modify: `.codex/agents/p8-interfaces-contract-lead.md`

- [x] **Step 1: 写模块负责人**

把硬件、导航、行为、视觉、bringup、接口契约分别拆成职责、必读上下文、输出格式和红线。

- [x] **Step 2: 保持硬件事实源**

硬件相关 agent 明确要求先读 `docs/vendor/VENDOR_INDEX.md`，并继续读取本地 vendor 文件。

### Task 4: P7 执行与质量层

**Files:**
- Create/Modify: `.codex/agents/p7-implementation-worker.md`
- Create/Modify: `.codex/agents/p7-test-engineer.md`
- Create/Modify: `.codex/agents/p7-reviewer.md`
- Create/Modify: `.codex/agents/p7-hardware-audit.md`
- Create/Modify: `.codex/agents/p7-docs-acceptance.md`

- [x] **Step 1: 写执行角色**

覆盖按边界实现、测试证据、代码审查、硬件审查、文档验收。

- [x] **Step 2: 写清输出合同**

每个 P7 agent 都要求输出改动、验证、风险和下一步，不允许“我觉得差不多了”式收工。

### Task 5: 最终验证

**Files:**
- Read: `.codex/agents/*.md`
- Read: `docs/superpowers/plans/2026-05-08-codex-subagents.md`

- [x] **Step 1: 文件数量检查**

确认 `.codex/agents` 下共有 14 个 Markdown 文件。

- [x] **Step 2: 未完成标记扫描**

扫描常见未完成标记，确认没有遗留占位内容。

- [x] **Step 3: 工作区检查**

确认本轮只新增/修改 `.codex/agents` 和这份计划文档，不触碰 ROS2 代码。
