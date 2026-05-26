# O7 Operator Console Acceptance Guard

sprint_type: micro

## 实际改动

- 新增 `pc-tools/workstation/src/server/o7OperatorConsoleAcceptance.ts`，从 `buildO7OperatorConsoleResponse()` 派生 `trashbot.o7.operator_console_acceptance.v1` 只读验收摘要。
- 更新 workstation shared contract、catalog export 和 Express route，新增 `GET /api/o7/operator-console/acceptance`；该 route 不读取硬件、不发送命令、不连接云端生产。
- 增加 catalog/UI 测试断言，复核六个 O7 KR snapshot、关键 fail-closed 字段、command/voice/labeling/route replay 禁用入口，以及危险外推 marker 缺失。
- 更新 `docs/interfaces/o7_realtime_operator_console.md` 和 `docs/product/pc_tools_workstation.md`，说明 acceptance guard 是软件防回归摘要，不是实机证明或 O7 完成度提升。

## 验证结果

- 通过：`cd pc-tools/workstation && npm run build`
  - 关键输出：`✓ 29 modules transformed.`、`✓ built in 1.93s`
- 通过：`cd pc-tools/workstation && npm run test`
  - 关键输出：`Test Files  2 passed (2)`、`Tests  17 passed (17)`
- 通过：`cd pc-tools/workstation && npm run lint`
  - 关键输出：`eslint .` 退出码 0
- 通过：`git diff --check -- pc-tools docs/product/pc_tools_workstation.md docs/interfaces/o7_realtime_operator_console.md sprints/2026.05.27_09-10_o7-operator-console-acceptance-guard`
  - 关键输出：无 whitespace error

## 失败定位与修复

- 首轮 `npm run test` 失败在 `catalog.test.ts` 的 acceptance dangerous marker 断言：guard 的 `checked_marker_ids` 中使用了 `ready_to_control_phrase` 规则名，导致测试扫描 acceptance JSON 时命中自身规则名。
- 已修复：将扫描规则 ID 改为中性名称 `operator_greenlight_phrase`，同时保留对 source response 中 `ready[-_ ]?to[-_ ]?control` 危险短语的实际扫描；重跑测试通过。

## 剩余风险

- 当前 guard 只验证 O7 operator console 软件响应没有安全语义漂移，不证明真实 RTC/视频、ASR/TTS、地图、电梯、回放、标注、手控、寻路、robot ACK、cancel/stop/recovery、底盘安全或云端生产链路。
- 本轮不修改 `OKR.md`，不提升 O7 百分比。
