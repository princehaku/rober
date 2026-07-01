# Field Acceptance Packet Display Label

## sprint_type

micro

## 目标

- 修复 `field_acceptance_packet` 中 primary missing evidence 对应动作缺少普通用户 display label 的问题。
- 让只解析 `field_acceptance_packet` 的现场脚本也能看到“重跑图上行程并复验轮速”，而不是只能看到兼容旧 label “完整行程执行”。

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `field_acceptance_packet` 新增 `primary_missing_evidence_action_label`。
  - `field_acceptance_packet` 新增 `primary_missing_evidence_action_display_label`。
  - 顶层 `field_acceptance_primary_missing_action_*` 与 `field_acceptance_primary_missing_evidence_action_*` 同源到 packet。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 补齐 `RobotControlFieldAcceptancePacket` 和 summary 顶层类型。
- `pc-tools/workstation/test/robotControlSummary.test.ts`
  - 增加 packet 与顶层 display label 断言。
- `docs/product/pc_tools_workstation.md`
  - 同步 packet primary missing evidence action display label 合同。

## 验证结果

- `npm test -- --run robotControlSummary.test.ts App.test.ts catalog.test.ts`
  - 通过：`Test Files 3 passed (3)`、`Tests 428 passed (428)`。
- `npm run lint`
  - 通过。
- `git diff --check`
  - 通过。
- `npm run build`
  - 通过；Vite 仍提示既有 bundle 大小 warning。
- 重启 PC Node：
  - 通过；`node` 监听 `*:7001`。
- 只读 smoke：
  - `field_acceptance_packet.primary_missing_evidence_action_display_label=重跑图上行程并复验轮速`。
  - `field_acceptance_primary_missing_action_display_label=重跑图上行程并复验轮速`。
  - `field_acceptance_primary_missing_evidence_action_display_label=重跑图上行程并复验轮速`。
  - `packet_top_display_same=true`、`packet_evidence_display_same=true`。

## 剩余风险

- 本轮只补现场验收 packet 的显示文案，不执行 Nav2 路线或证明 wheel L/R 非零；真实完整行程仍需现场安全确认后重跑并读回同窗口 wheel L/R 与 delivery success。
