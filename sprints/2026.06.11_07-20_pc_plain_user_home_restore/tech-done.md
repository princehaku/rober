# PC 普通用户首屏回归修复

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/App.vue`：把 `RobotControlConsolePanel` 改为默认常驻首屏；`WorkstationTabs`、Route Debug、O7、预览、证据、硬件、数据和安全边界 panels 全部移入默认关闭的 `高级工具`。
- `pc-tools/workstation/src/components/WorkstationTabs.vue`：移除普通控制台 tab，只保留工程入口 tabs，避免普通用户第一眼看到工程导航。
- `pc-tools/workstation/src/styles.css`：新增 `高级工具` 折叠区样式，保持和现有工作站视觉一致。
- `pc-tools/workstation/test/App.test.ts`：新增/调整首屏作用域断言，验证五卡片、普通动作白名单、工程禁词不在首屏，同时确认高级工具展开后工程 tabs 仍可访问。
- `docs/product/pc_tools_workstation.md`、`pc-tools/README.md`：同步说明普通首屏与默认关闭高级工具的新边界。

## 验证结果

- `cd pc-tools/workstation && npm run build`：通过；`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成，Vite 输出 `✓ built in 1.50s`。
- `cd pc-tools/workstation && npm run test`：通过；`Test Files 2 passed (2)`，`Tests 89 passed (89)`。
- `cd pc-tools/workstation && npm run lint`：通过；`eslint .` 无报错。
- `git diff --check`：通过，无空白错误。
- 本地浏览器/DOM smoke：通过。artifact：`sprints/2026.06.11_07-20_pc_plain_user_home_restore/artifacts/browser_dom_smoke_2026-06-11_07-16.json`。

## 浏览器/DOM smoke 结论

- 使用 `PORT=4174 npm run api` 启动工作站 Node API + 静态 UI，打开 `http://127.0.0.1:4174/`。
- 默认可见 DOM 没有 `API unavailable`。
- 默认可见首屏包含 `Rober 小车控制台`、五张卡片 `小车连接 / 实时画面 / 雷达 / 地图 / 移动/导航`。
- 默认可见按钮只包含 `刷新 / 连接/刷新 / 打开画面 / 关闭画面 / 刷新雷达 / 刷新地图 / 地图列表 / 检查路径 / 停止`。
- 默认可见首屏和可见 body 未命中禁词：`路线`、`预览`、`证据`、`硬件`、`数据`、`安全边界`、`source=software_proof`、`proof_status=not_proven`、`safe_to_control=false`、`readback`、`HIL`、`cmd_vel`、`保存地图`、`开始建图`、`四向点动`、`速度`、`时长`。
- 展开 `高级工具` 后，工程 tabs `路线 / 控制台 / 预览 / 证据 / 硬件 / 数据 / 安全边界` 可见，普通控制台仍可见。

## 失败定位

- 首轮 `npm run build` 曾因测试里 `findAll(...)[0]` 可能为 `undefined` 触发 TypeScript 错误。已改为先断言 route input 数量，再使用非空索引；复跑 build 通过。

## 剩余风险

- 本轮只做 PC UI 默认可见层级回归，不新增机器人能力，不改 onboard，不做真实硬件/HIL 验证。
- 浏览器 smoke 验证的是本地 Node API + 静态 UI；真实上位机连接、视频流和控制代理安全边界沿用既有实现与测试。
