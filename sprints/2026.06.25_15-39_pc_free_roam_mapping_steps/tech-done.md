# PC 扫地式建图步骤条 Micro Sprint

- sprint_type: micro
- owner: full-stack-software-engineer
- started_at: 2026-06-25 15:36 CST
- finished_at: 2026-06-25 15:39 CST
- scope: 在 PC 普通用户首屏的扫地式建图向导中补明确步骤条，让用户知道当前处于安全确认、启动记录、低速扫图、停止收口、保存地图的哪一步。

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `plainFreeRoamMappingSteps`，把扫图会话拆成 5 个普通用户可理解步骤。
  - 每一步显示状态 chip 和下一步提示。
  - 文案避免在普通首屏暴露高级“开始建图”表述，改为“启动记录 / 启动地图记录”。
  - 保存地图 gate 收紧为：必须已勾安全确认且本轮地图记录已启动后才可保存。
- `pc-tools/workstation/src/styles.css`
  - 复用现有进度行样式，并为扫图步骤条收紧为三列布局。
- `pc-tools/workstation/test/App.test.ts`
  - 断言扫图步骤条存在、包含 5 个步骤、默认处于待确认状态。
  - 保留页面加载不调用 `/api/robot-control/map/start` 的断言。

## 验证结果

- `cd pc-tools/workstation && npm test`
  - 通过：2 个 test files，154 个用例全部通过。
- `cd pc-tools/workstation && npm run lint`
  - 通过：ESLint 无报错。
- `cd pc-tools/workstation && npm run build`
  - 通过：`tsc -p tsconfig.app.json`、`vite build`、`tsc -p tsconfig.server.json` 全部通过。
- PC 端 `screen -dmS rober-pc-7001 ... npm run api:public`
  - 通过：Node API 监听 `0.0.0.0:7001`，进程 PID 为 `63573`。
- 浏览器 DOM smoke：`http://127.0.0.1:7001`
  - 通过：普通用户首屏加载成功，默认小车地址为 `192.168.1.11:8787`。
  - 通过：真实地图显示为“地图可见”。
  - 通过：“扫地式建图”步骤条显示 5 步：安全确认、启动记录、低速扫图、停止收口、保存地图。
  - 通过：未勾安全确认时“开始扫地式建图”和“保存当前地图”均为 disabled，停止按钮保持 enabled。

## 剩余风险

- 本轮没有触发真实 `/api/map/start`、`/api/base/manual`、`/api/base/stop`、`/cmd_vel` 或无人值守自动探索。
- 扫图步骤条是 PC 向导层状态；真正自动覆盖探索仍需要上车端策略、避障、watchdog、artifact 和 HIL。
