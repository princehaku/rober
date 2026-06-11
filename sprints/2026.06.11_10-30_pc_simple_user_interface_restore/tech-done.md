# sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：把默认可见首屏包进 `.simple-user-console`，首屏只展示 `Rober 小车控制台` 下的小车连接、实时画面、雷达、地图、移动/导航五个普通区域和普通动作按钮。
- `pc-tools/workstation/src/styles.css`：新增 `.simple-user-console` 作用域样式，方便测试和后续维护把普通首屏与高级诊断分开。
- `pc-tools/workstation/test/App.test.ts`：补齐默认首屏禁词清单：`检查路径`、`现场材料`、`HIL`、`Nav2`、`proof`、`key values`、`/cmd_vel`、`/api/base/manual`、`可点动`、`task_id`、`O6`、`O7`、`Mock`、`field manifest`；测试改为只读取默认可见首屏作用域，避免关闭的 details 文本污染断言。
- `docs/product/pc_tools_workstation.md`、`pc-tools/README.md`：同步记录普通用户首屏边界和禁词回归测试要求。
- `sprints/2026.06.11_10-30_pc_simple_user_interface_restore/artifacts/pc_plain_user_home_dom_smoke.json`：由前端测试生成默认首屏 DOM smoke 证据。

## 验证结果

- `cd pc-tools/workstation && npm run test -- --run`：通过，`Test Files 2 passed (2)`，`Tests 89 passed (89)`。
- `cd pc-tools/workstation && npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成，Vite 输出 `✓ built in 1.13s`。
- `cd pc-tools/workstation && npm run lint`：通过，`eslint .` 无报错。
- DOM smoke artifact 显示五个首屏卡片均存在，所有禁词 presence 均为 `false`，高级诊断保持默认关闭且高级入口仍保留。

## 剩余风险

- 本轮只修 PC workstation 前端默认首屏和文档/测试，没有做真实上位机、摄像头、雷达、地图或运动控制 smoke。
- 工程能力仍保留在默认关闭的 `高级工具` / `高级诊断` 中；后续新增工程入口时必须继续使用 `.simple-user-console` 禁词测试防止回流到普通首屏。

## 运行时间

- 本轮记录时间：2026-06-11 09:46:25 CST。
