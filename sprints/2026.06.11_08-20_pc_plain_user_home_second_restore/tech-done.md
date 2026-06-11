# PC Plain User Home Second Restore

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：把 `移动/导航` 默认首屏收敛为普通状态 + `停止`，移除首屏 `检查路径` 和现场材料提示；`检查路径（高级）`、定位重置、导航目标预检、现场 HIL 材料、点动设置和 proof/readback 细节继续保留在默认关闭的 `高级诊断`。
- `pc-tools/workstation/test/App.test.ts`：新增默认首屏工程词禁入词表，更新 Robot Control 回归测试，并在测试中写出 `artifacts/pc_plain_user_home_dom_smoke.json`，证明默认首屏不包含工程词且高级入口仍存在。
- `docs/product/pc_tools_workstation.md`、`pc-tools/README.md`：同步说明 PC workstation 默认首屏不再展示工程控制；高级区仍保留诊断和调试入口。

## 验证结果

- `cd pc-tools/workstation && npm run build`：通过。最终输出包含 `✓ 33 modules transformed.`、`✓ built in 997ms`。
- `cd pc-tools/workstation && npm run test`：通过。`Test Files  2 passed (2)`、`Tests  89 passed (89)`。
- `cd pc-tools/workstation && npm run lint`：通过。`eslint .` 无报错。
- `git diff --check`：通过，无 whitespace 错误。
- DOM smoke artifact：`sprints/2026.06.11_08-20_pc_plain_user_home_second_restore/artifacts/pc_plain_user_home_dom_smoke.json` 记录默认首屏 `检查路径`、`现场材料`、`HIL`、`Nav2`、`proof`、`key values`、`/cmd_vel`、`/api/base/manual`、`可点动` 均为 `false`；高级诊断仍保留检查路径、导航目标预检、HIL 材料和 proof readback 入口。

## 剩余风险

- 本轮只做 PC workstation 前端首屏收敛和本地 DOM/test 验证，未连接真实浏览器视频、真实上位机、真实机器人或 HIL；后端代理合同、onboard、硬件、串口、WAVE ROVER、Nav2 API 行为均未改动。
