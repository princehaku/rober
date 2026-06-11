# PC 简易首屏恢复/验证

## Sprint 类型

sprint_type: micro

## 本轮收束

用户反馈 PC 界面被改成不想要的工程风格后，本轮从原计划真实上位机
PC proxy smoke 立刻收束为“普通用户简易首屏恢复/验证”。本轮未继续新增工程首屏能力，
也未继续执行真实板端 control smoke。

## 核对范围

- `pc-tools/workstation/src/App.vue`
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
- `pc-tools/workstation/src/styles.css`
- `pc-tools/workstation/test/App.test.ts`

核对结论：当前默认可见首屏已经满足普通用户简易风格契约：

- 页面标题为 `Rober 小车控制台`。
- `.simple-user-console` 默认可见区只保留五卡片：`小车连接`、`实时画面`、`雷达`、`地图`、`移动/导航`。
- 首屏只保留短状态、连接/刷新、打开/关闭画面、刷新雷达、刷新地图、地图列表、停止等少量普通按钮。
- `HIL`、`proof`、`Nav2`、`/cmd_vel`、`/api/base/manual`、`task_id`、`Mock`、现场材料、速度/点动、导航目标预检等工程项仍在默认关闭的 `高级诊断` 或 `高级工具` 中。

## 实际改动

- 未改 PC UI 代码。
- 未改首屏样式。
- 未改测试断言。
- 新增本文件记录本轮用户投诉响应、首屏契约核对和验证结果。

## 验证结果

运行时间：2026-06-11 18:05:59 CST。

### `cd pc-tools/workstation && npm run test`

通过。

关键结果：

```text
Test Files  2 passed (2)
Tests  92 passed (92)
Duration  7.84s
```

覆盖点：现有 `App.test.ts` 已验证默认首屏 `.simple-user-console` 五卡片、标题、普通按钮，以及默认可见首屏禁词；同时确认 `高级诊断` 与 `高级工具` 默认关闭。

### `cd pc-tools/workstation && npm run build`

通过。

关键结果：

```text
tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json
✓ built in 2.33s
```

### Node proxy 清理状态

原计划真实板端 smoke 前曾临时启动 `PORT=18792 npm run api`，收到用户收束要求后已停止。

检查结果：

```text
lsof -nP -iTCP:18792 -sTCP:LISTEN
```

无输出，表示端口无监听残留。

## 未执行项

- 未继续执行 PC Node proxy 到 `http://192.168.1.11:8787` 的真实上位机 smoke。
- 未新增 artifacts 记录真实雷达、地图、Nav2、camera、stop/manual gate 返回。

原因：用户最新要求明确将当前任务收束为 PC 简易首屏恢复/验证，不要新增工程首屏能力。

## 剩余风险

- 本轮证明的是 PC 默认首屏契约和构建/测试通过，不证明真实上位机控制、真实图传、真实雷达、真实地图、真实 Nav2 或真实手动控制可用。
- 若用户看到的仍是工程风格，优先排查浏览器缓存、旧 dev server、旧构建产物或打开了默认关闭的 `高级诊断` / `高级工具`。
