# O1 WAVE ROVER Nonzero Feedback HIL Gate PRD

## 用户价值和产品北极星

产品北极星仍是“机器人可以安全、可验证地完成垃圾收取与送达”。对 O1 来说，用户价值不是再看到一个 UI surface 或 wrapper 摘要，而是把“底盘是否真的给出了可用轮速反馈、是否满足 HIL 准入前置条件”变成可复现、可审计、fail-closed 的软件证据链。只有这样，后续真实上车时才不会把零值反馈、串口假阳性或危险 payload 误判成可控底盘。

## OKR 映射和方向判断

- 映射 Objective：O1 硬件协议可信底盘。
- 方向判断：**继续 O1，暂停 O5 的新增百分比推进**。
- 理由：
  1. O1 / O5 当前同为最低进度。
  2. O5 最近几轮已明确进入“只有真实 production 证据才可继续增长”的阶段，本轮再做 local/mock probe wrapper 没有 OKR 增量价值。
  3. O1 最近没有被连续 sprint 消费，且存在明确的软件前置缺口：需要一个面向真实 WAVE ROVER nonzero L/R 反馈和 HIL 准入的采集/判定/证据包工具链。

## KR 拆解

1. 把 WAVE ROVER vendor feedback 资料收敛为本轮唯一事实来源，并在实现文档中明确引用。
2. 为 `robot-hardware-engineer` 规划单线闭环任务：反馈采集、mock/虚拟串口输入、fail-closed 判定、HIL 准入摘要、最小文档同步。
3. 把本轮证据边界固定为软件 proof，防止实现后误报真实 nonzero wheel 或真实 HIL pass。

## 本轮核心抓手

围绕 `T1001` / vendor feedback 流建立一个“能采、能判、能拒绝、能留档”的软件 gate，而不是直接追逐真实现场结果。实现完成后，下一次现场只需要替换输入源，就能验证真实 nonzero L/R 是否出现，以及 HIL 准入是否满足。

## 需要做什么

- 补一个面向 WAVE ROVER feedback 的硬件软件证据链计划：
  - 明确允许修改的硬件包、测试、硬件 docs、本 sprint `tech-done.md`；
  - 明确不可修改 `OKR.md`、`final.md` 和其他产品收口文档；
  - 明确本地 macOS 可跑的 py_compile、unittest、`git diff --check` 验收组合；
  - 明确 Docker/Humble build 只作为可选补充，不阻塞本轮。

## 优先级和验收口径

- 优先级：P0，单 owner 闭环。
- 验收口径：
  1. 能在当前 macOS 环境用 mock/虚拟串口验证 WAVE ROVER feedback 采集与 fail-closed 判定。
  2. 能输出 HIL gate ready/not-ready 软件摘要，但不宣称真实 HIL pass。
  3. 缺真实 nonzero L/R 时，结果必须保持 blocked/not-proven。
  4. 文档需同步说明资料来源与证据边界。

## 对应责任 Engineer

- `robot-hardware-engineer`

## 风险、阻塞和需要补齐的证据链

- 当前没有真实 WAVE ROVER nonzero L/R 原始反馈，无法在本轮证明底盘真实运动。
- 当前没有真实 HIL 现场执行，无法在本轮证明 safe-to-control 或 pass。
- 如现有硬件包对 vendor feedback 字段命名理解不一致，后续实现需先对齐本地 vendor 文件与现有代码事实。
- 若 macOS 本地缺少虚拟串口依赖，实现需提供纯 Python mock fallback，避免计划落地后被环境卡住。

## 已完成 KR 的历史记录位置、证据来源和剩余风险

- 本轮不移动已完成 KR，也不更新 `OKR.md` 历史区。
- 相关方向事实来源：
  - `OKR.md` 4.1 与 5 节，确认 O1/O5 同为最低优先级且 O5 不能再靠 local/mock probe 提升。
  - `sprints/2026.06.22_14-03_plain_wheel_record_status/tech-done.md`，确认 `T1001` 的 `L/R` 已被当作底盘反馈字段消费，但当时未证明真实 nonzero。
  - `sprints/2026.06.23_16-25_wheel_zero_direct_radar_focus/tech-done.md`，确认现场流程仍把“先启动雷达再试动读非零 L/R”作为后续动作，真实 nonzero 仍待补证。
- 剩余风险：这些历史材料能证明需求与缺口，但不能替代本轮目标中的真实 nonzero L/R 或真实 HIL pass。

## 需要创建或更新的 sprint 文档

- 本轮创建/更新：
  - `sprints/2026.07.10_10-30_o1_wave_rover_nonzero_feedback_hil_gate/pre_start.md`
  - `sprints/2026.07.10_10-30_o1_wave_rover_nonzero_feedback_hil_gate/prd.md`
  - `sprints/2026.07.10_10-30_o1_wave_rover_nonzero_feedback_hil_gate/tech-plan.md`
- implementation 完成后由 `robot-hardware-engineer` 继续补：
  - `tech-done.md`
  - `side2side_check.md`
  - `final.md`
