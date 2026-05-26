# PC Hardware HIL Material Coverage PRD

## 1. 背景

Objective 1 当前约 81%，主要缺口反复集中在真实 WAVE ROVER/UART/HIL、2D LiDAR/ToF、PR #5 材料和 reviewer resolution。继续把“缺真实硬件材料”作为 sprint 主结论会触发 repeated blocker 红线；本轮要把散落的 `pc-tools/evidence/fixtures/wave_rover_*` 材料变成 PC 工作站可读、可排序、可复核的 coverage 视图。

本轮不是恢复旧 Python evidence gate。`pc-tools` 当前主入口是 `pc-tools/workstation` 的 Node/Vue 工作站，Evidence Tools 已由 Node API 读取 JSON fixture。WAVE ROVER HIL/material coverage 必须延续这个架构。

## 2. 用户价值和产品北极星

用户价值：

- Product / CEO 能快速判断 Objective 1 的材料链到底缺什么，不再靠聊天或历史 sprint 猜测。
- Hardware 能按 required materials 清单补齐真机证据，避免重复提交不满足 reviewer 的材料。
- Full-Stack / PC 工具用户能在同一个工作站查看 coverage、缺口和 `not_proven` 边界。

产品北极星对齐：可信底盘控制层必须有可追溯证据。PC 工具不直接让机器人变“已验证”，但它要让真实验证前的材料准备变成可执行流程。

## 3. OKR 映射

### Objective 1：打通官方硬件协议，建立可信底盘控制层

直接对齐：

- KR3：`T=1001` 底盘反馈、`/imu/data`、`/battery`、`/odom` 等证据材料需要能被 coverage 视图识别和标注。
- KR4：硬件桥协议测试和 HIL fixture 要形成可复核材料入口。
- KR5：真实串口、波特率、命令模式、速度/尺寸参数仍需后续真机证明；本轮只做材料 coverage，不宣称实机参数验证完成。

预期 OKR 影响：若 Engineer 后续交付可运行 coverage/API/UI/tests/docs，可把 Objective 1 从“重复缺材料”推进到“材料缺口可视化且可执行补齐”。是否提升百分比由 final 阶段基于实现和验证证据判断；Product plan 阶段不提前承诺提升。

### Objective 3 / Objective 4 的间接受益

- Objective 3：PC 工具的证据可视化能力增强，但本轮不证明 Nav2/fixed-route runtime。
- Objective 4：工作站体验更清晰，但它面向 PC 调试用户，不是普通手机端验收。

## 4. KR 拆解或更新

本轮不修改 `OKR.md` KR 文本，只拆解 Objective 1 的执行性材料 KR：

1. Material discovery：扫描 `pc-tools/evidence/fixtures/wave_rover_*`，列出 fixture group、文件、大小、解析状态、pass/fail/intake/review 类别。
2. Required coverage：把 required materials 映射为可检查项，五件套精确为 `feedback_T1001.log`、`odom_once.jsonl`、`imu_once.jsonl`、`battery_once.jsonl`、`operator_hil_report`；execution/review/intake pack 仅作为辅助上下文，不替代五件套。
3. Gap classification：输出 `covered`、`missing`、`partial`、`not_proven`，其中 `not_proven` 是默认安全边界，不因文件存在而翻成 pass。
4. PC UI：Evidence Tools 或新增 Hardware HIL Material Coverage 区块能展示覆盖率、缺口和边界文案。
5. Verification：Node/Vue build/test/lint 覆盖 scanner、API contract 和 UI copy，不运行旧 Python gate。

## 5. 本轮核心抓手

以 Full-Stack 为实现主责，在 Node-native 工作站中新增只读能力：

- 后端：新增或扩展 scanner，读取 `pc-tools/evidence/fixtures/wave_rover_*`。
- 契约：在 `src/shared/contracts.ts` 中定义 coverage 响应字段，保留 fail-closed flags。
- API：新增本地只读 endpoint 或扩展 Evidence Tools endpoint，不暴露控制动作。
- UI：展示 required materials 覆盖、缺口、fixture 组和 `not_proven` 边界。
- 测试：补 Vitest 单元/组件测试，覆盖 pass/fail/missing/边界 copy。
- 文档：更新 PC 工作站和 evidence 说明，明确 Node/Vue 主入口与旧 Python gate 禁止恢复。

## 6. 需要做什么

必须做：

- 使用 Node.js/TypeScript 实现材料扫描和 coverage 计算。
- 只读读取仓库 fixture，不写入 fixture，不执行脚本，不读取真实串口。
- 所有 API/UI 保持 `source=software_proof`、`proof_status=not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`pc_only=true`。
- UI 文案明确：材料存在不等于 HIL pass、不等于 WAVE ROVER/UART 真机验证、不等于 delivery success。
- 更新 `docs/product/pc_tools_workstation.md` 或 `pc-tools/evidence/README.md`，同步工具边界。

不得做：

- 不恢复 `pc-tools` 旧 Python evidence gate。
- 不新增真实控制按钮、串口写入、ROS2 launch、HIL 执行动作。
- 不把 `wave_rover_*` fixture 解释为真实硬件通过。
- 不改 `OKR.md`，直到实现和验证完成后的 closeout 阶段。

## 7. 优先级和验收口径

P0 验收：

- `pc-tools/workstation` 有 Node-native WAVE ROVER HIL/material coverage 只读能力。
- 能扫描 `pc-tools/evidence/fixtures/wave_rover_*`。
- 能显示 required materials 覆盖、缺口和 `not_proven` 边界。
- `npm run build`、`npm run test`、`npm run lint` 通过。
- 文档同步更新，并写明不恢复 Python gate。

P1 验收：

- UI 能按材料组区分 pass/fail/intake/review/execution 类 fixture。
- 缺口文案能直接指导 Hardware 下一步需要补哪类材料。
- 测试覆盖缺文件、坏 JSON、空 fixture、pass/fail 混合等情况。

不作为本轮验收：

- 真实 WAVE ROVER 上电、真实 UART、真实 HIL、2D LiDAR/ToF 安装、PR #5 resolved。
- 真实 Nav2/fixed-route、真实投放、delivery success。

## 8. 对应责任 Engineer

- 主责实现：`full-stack-software-engineer`，使用 `.codex/agents/full-stack-software-engineer.toml` 的 prompt。
- 硬件事实咨询：`robot-hardware-engineer`，使用 `.codex/agents/robot-hardware-engineer.toml` 的 prompt，先读 `docs/vendor/VENDOR_INDEX.md` 及必要 vendor 文件。
- 产品收口：`product-okr-owner`，实现完成后检查 PRD/验收/OKR/sprint 文档链路。

## 9. 风险、阻塞和需要补齐的证据链

- 现有 fixture 可能不足以构成 required coverage 的完整 pass，只能输出缺口，不能输出 HIL 通过。
- Hardware required materials 需要 vendor/source 事实支持；如果 Hardware 只读咨询发现 required materials 命名不准确，Full-Stack 需按咨询结果调整。
- 本轮不能把“缺真实硬件”作为最终 blocker 主结论；如果真实材料仍缺，应输出可执行补齐列表和 reviewer follow-up 状态。
- 后续 closeout 必须根据实现证据判断 Objective 1 是否提升；计划阶段不更新 OKR 百分比。

## 10. 需要创建或更新的 sprint 文档

本阶段创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

实现后必须补齐：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
