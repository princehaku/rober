# PC 普通用户控制台当前契约核对

## sprint_type

micro

## 背景

用户反馈 PC 界面不应变成工程风格，要求保持之前面向普通用户的简易风格。本轮只核对默认首屏契约，不触碰真实上位机、硬件配置或运动链路。

## 实际改动

- 未修改 PC 产品代码。
- 只新增本 sprint 留档，记录当前默认首屏契约和剩余风险。

## 当前契约

- `pc-tools/workstation/src/App.vue` 默认展示 `Rober 小车控制台`，说明文案为“连接小车、查看画面和地图，必要时一键停止。”
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue` 默认首屏保留 `.simple-user-console`，包含五个普通用户卡片：`小车连接`、`实时画面`、`雷达`、`地图`、`移动/导航`。
- `高级工具` 和 `高级诊断` 均为 `<details>`，当前源码未设置 `open` 属性，因此默认关闭。
- 工程字段、证据字段、串口/topic/HIL/Nav2 细节仍保留在高级区，不属于普通用户首屏。

## 验证结果

- 主节点只读核对源码和测试契约：
  - `pc-tools/workstation/test/App.test.ts` 已断言默认首屏有 5 个 `.snapshot-panel` 卡片。
  - 测试已断言 `高级工具` 与 `高级诊断` details 默认无 `open` 属性。
  - 测试已断言普通首屏不包含 `task_id`、`safe_to_control`、`/dev/ttyS5`、`path_generation_succeeded`、`导航目标预检` 等工程词。
- 本轮尝试派发 `full-stack-software-engineer` 子 agent 做 `npm run test` / `npm run build` 渲染级复验，但当前 Codex 子 agent 运行时两次返回 `spawn_agent could not resolve the child model for service tier validation`，因此没有新的命令级测试日志。
- 最近一次同类契约验证见提交 `6e6d2738 Verify simple PC console contract`，当时 `npm run test`、`npm run build`、`git diff --check` 均通过；本轮只读核对未发现默认首屏代码漂移。

## 剩余风险

- 如果浏览器仍显示工程风格，优先检查是否展开了 `高级工具` / `高级诊断`，或是否打开了旧 dev server、旧构建产物、浏览器缓存页面。
- 当前高级区内容仍很多，展开后会像工程台；后续新增证据和硬件调试项必须继续放在默认关闭区域，不能进入普通用户首屏。
