# PC 扫图覆盖反馈 Micro Sprint

- sprint_type: micro
- owner: full-stack-software-engineer
- started_at: 2026-06-25 15:40 CST
- finished_at: 2026-06-25 15:44 CST
- scope: 在 PC 普通用户首屏的扫地式建图向导中显示地图覆盖度和可通行区域反馈，让用户不看 raw JSON 也能判断是否需要继续扫图。

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `plainFreeRoamCoverageSummary`，从只读 `mapPreviewResult.cell_counts` 计算可通行格、未知区域比例、已知区域比例和地图质量。
  - 在“扫地式建图”卡片内新增“扫图覆盖”摘要、覆盖进度条和普通用户文案。
  - 没有地图预览时显示“待刷新”，避免把缺数据误判成已扫完。
- `pc-tools/workstation/src/styles.css`
  - 新增扫图覆盖条样式，使用卡片内分隔线，不嵌套卡片。
- `pc-tools/workstation/test/App.test.ts`
  - 断言扫图覆盖摘要存在，显示可通行格和未知区域比例。

## 验证结果

- `cd pc-tools/workstation && npm test`
  - 通过：2 个 test files，154 个用例全部通过。
- `cd pc-tools/workstation && npm run lint`
  - 通过：ESLint 无报错。
- `cd pc-tools/workstation && npm run build`
  - 通过：`tsc -p tsconfig.app.json`、`vite build`、`tsc -p tsconfig.server.json` 全部通过。
- PC 端 `screen -dmS rober-pc-7001 ... npm run api:public`
  - 通过：Node API 监听 `0.0.0.0:7001`，进程 PID 为 `76849`。
- 浏览器 DOM smoke：`http://127.0.0.1:7001`
  - 通过：默认小车地址为 `192.168.1.11:8787`，真实地图显示为“地图可见”。
  - 通过：“扫图覆盖”显示真实地图预览计数：`已扫出 394 个可通行格`、`未知区域 98.7%`、`已知区域 1.3%`。
  - 通过：覆盖条样式为 `--coverage-known: 1.3%`。
  - 通过：未勾安全确认时启动/保存禁用，停止按钮保持可用。

## 剩余风险

- 本轮只读取地图预览中的 cell counts，没有触发真实 `/api/map/start`、`/api/base/manual`、`/api/base/stop`、`/cmd_vel` 或无人值守自动探索。
- 覆盖比例是栅格层面的已知/未知反馈，不等价于真实房间清扫覆盖或 HIL 自动探索通过。
