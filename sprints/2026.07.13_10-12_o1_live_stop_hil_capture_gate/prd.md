# PRD - O1 Live Stop HIL Capture Gate

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_10-12_o1_live_stop_hil_capture_gate/`
- Product owner: `product-okr-owner`
- Implementation owner: `rober-hardware-engineer`
- Product status: requirements ready for Hardware implementation

## 用户价值和产品北极星

用户需要相信小车在执行固定路线前可以被明确、可审计地停下。北极星是“安全可控的垃圾送达闭环”，而本轮只做其中的停车 HIL 采集 gate：让下一次有现场 operator approval 的 run 能产出 `/api/base/stop`、UART zero-stop frame、`T=1001` L/R 归零和 HIL acceptance 的同窗口证据。

当前 run 无 operator approval，所以本轮产品价值是把采集入口、mock 验证和 artifact 合同准备好，不冒充真实 HIL。

## 问题陈述

09:11 sprint 已证明 `/api/base/stop` 的 no-motion zero-stop path readiness，但还没有证明 current live stop HIL。后续 route execution 不能直接从 bounded route command plan 跳到执行；必须先补一个 operator-gated capture helper，并且在没有 operator approval 时 fail-closed。

O5 虽然是最低完成度 Objective，但最近 production readiness packet 已明确 `support_only_reason=no_real_production_external_evidence`。本轮继续 O5 只会新增同类 support-only wrapper，不能产生真实公网/4G/production/browser 证据，因此本 PRD 转向 O1/O3 安全准入链路。

## OKR 映射和方向判断

- O5：约 `85%`，本轮不推进。方向判断为“暂停 support-only 包装，等待真实外部生产证据”；不是替换 Objective。
- O1：约 `94%`，本轮继续推进 current live HIL 前置 gate。方向判断为“继续”，但当前 automation 只接受 mock/local pipeline readiness。
- O3：后续 route execution 依赖 O1 stop HIL 和同窗口 localization/TF/Nav2 result；本轮只解锁下一条安全采集命令。
- O6/O7：本轮不做 readback-only、handoff、surface 或 UI wrapper。
- KR 归档：无已完成 KR 归档；本轮若只产出 mock/local gate，不能归档 O1 HIL KR。

## KR 拆解和历史边界

- O1 current live HIL 缺口拆成四个材料项：
  - explicit operator approval token / record。
  - current live `/api/base/stop` 调用记录。
  - 同窗口 UART zero-stop frame capture。
  - stop 后 `T=1001` feedback 中 L/R 归零和 HIL acceptance。
- 本轮只交付第 0 步：operator-gated capture helper 和 mock/local verification。
- 历史记录位置：计划阶段只引用 `sprints/2026.07.13_09-11_o1_current_stop_path_readiness_probe/final.md` 与 O5 readiness final；不更新 `OKR.md`。KR 历史归档留到 Product closeout。

## 功能需求

1. 新增 operator-gated helper，输出 schema `trashbot.o1.current_stop_hil_capture_gate.v1` artifact。
2. Helper 必须支持 local mock 模式：mock HTTP stop endpoint、mock/fixture `T=1001` feedback、artifact 写出。
3. Helper 必须要求 `--operator-approval-token`；mock 验收只接受 `MOCK_APPROVED_STOP_ONLY` 这类显式 mock token，不代表真实 operator approval。
4. Artifact 必须固定以下字段为 false：
   - `hil_pass=false`
   - `safe_to_control=false`
   - `route_execution_success=false`
   - `delivery_success=false`
   - `robot_control_executed=false`
   - `nonzero_motion_command_sent=false`
   - `uses_real_uart=false`
5. Artifact 必须显式记录 `robot_control_executed=false`，即使 mock HTTP endpoint 被调用成功，也不能宣称真实机器人控制发生。
6. Helper 不得调用 `/api/base/manual`、不得发布 `/cmd_vel`、不得 NavigateToPose、不得打开 WAVE ROVER UART、不得发送非零运动命令。
7. 后续真实硬件模式只能在 explicit operator approval 后启用，并且必须把真实 UART/HIL 字段与 mock 字段分开。
8. 需要同步最小硬件文档 `docs/hardware/wave_rover_stop_hil_capture_gate.md`，说明 vendor 来源、mock/local 边界、真实 run 的证据要求和安全字段。
9. 工程代码技术注释必须使用中文，注释比例超过 20%，重点解释为什么 fail-closed、为什么 mock 不等于 HIL。

## 非目标

- 不执行真实 `/api/base/stop`。
- 不打开真实 UART。
- 不采真实 WAVE ROVER `T=1001` feedback。
- 不证明 current live HIL。
- 不证明 safe-to-control。
- 不推进 Nav2 route execution、fixed-route movement、delivery success 或 operator acceptance。
- 不推进 O5 production external evidence。

## 优先级和验收口径

优先级：P0 safety gate。

Product 接受 implementation 的条件：

- `trashbot.o1.current_stop_hil_capture_gate.v1` artifact 可由 mock 命令稳定生成。
- Artifact 明确区分 mock capture pipeline readiness 与 current live HIL。
- 所有 safety/control/route/delivery/real UART 字段固定 false。
- 单元测试覆盖 operator approval token、mock stop endpoint、`T=1001` fixture、false safety fields 和危险字段 fail-closed。
- `python3 -m json.tool` 能解析 artifact。
- `git diff --check` 通过。
- `tech-done.md` 写清实际改动、验证结果、失败定位和剩余风险。

## 风险、阻塞和待补证据链

- 当前缺 explicit operator approval，不能做真实 HIL。
- 当前 artifact 只能证明 capture helper 和 mock/local pipeline ready。
- 真实 HIL 仍需要现场同窗口证据：`/api/base/stop` 调用、UART zero-stop frame、stop 后 `T=1001` L/R 归零、operator acceptance。
- route execution 仍需等待 stop HIL、LiDAR/localization/TF readiness、Nav2/controller result 和 operator acceptance。
- O5 仍缺真实公网 HTTPS/TLS、4G/SIM、production DB/queue、worker/cutover、OSS/CDN live traffic 和真实手机/browser。

## 责任分工

- `product-okr-owner`：维护本 PRD、计划边界、OKR 映射、验收口径和后续 closeout。
- `rober-hardware-engineer`：实现 helper、测试、硬件文档和 `tech-done.md`。
- `robot-algorithm-engineer`：本轮不介入；等 stop HIL gate 后再处理 route execution evidence。
- `robot-software-engineer` / `full-stack-software-engineer`：本轮不介入，除非 Hardware 发现 `/api/base/stop` mock contract 需要接口事实确认。

## Sprint 文档要求

本 Product plan 阶段创建 `pre_start.md`、`prd.md`、`tech-plan.md`。后续 implementation 必须更新 `tech-done.md`；Product acceptance 后再创建 `side2side_check.md` 和 `final.md`，不得提前预生成。
