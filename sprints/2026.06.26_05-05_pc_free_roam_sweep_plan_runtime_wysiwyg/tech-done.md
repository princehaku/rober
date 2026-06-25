# PC 自动扫图草图运行态 WYSIWYG

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增自动扫图运行态判断：本轮 start 已转发，或上车端 runtime 为 `running/avoiding/turning_for_coverage/stopping` 时，认为自动扫图状态机正在运行或收口。
  - 地图 `扫地图草图` label 和扫地图草图 summary 在自动扫图运行中改为“用于监看覆盖，不是固定路线”，避免同屏同时出现“自动扫图已启动”和“不会自动移动”的矛盾口径。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展自动扫图 start 用例，验证运行中草图显示“自动扫图运行中 / 不是固定路线”，并且不再显示“不会自动移动”。
- `docs/product/pc_tools_workstation.md`
  - 同步记录自动扫图 runtime 下草图只作覆盖监看参考，不生成 Nav2 路线或额外控制。

## 验证结果

- 通过：`cd pc-tools/workstation && npx vitest run test/App.test.ts -t "starts free-roam autonomy through the fixed proxy only after ready readback and safety confirmation"`
  - 1 个 test file passed，1 个测试通过，91 个跳过。
- 第一轮全量 `cd pc-tools/workstation && npm test` 失败：
  - 默认 fixture 的 `free_roam_autonomy_runtime.state=avoiding` 只是 `artifact_only=true/cmd_vel_publish_enabled=false` 的只读记录，不应触发“自动扫图运行中”文案。
  - 已修正为只有本轮 start 已转发，或 `free_roam_autonomy=ready + cmd_vel_publish_enabled=true + artifact_only=false` 的 runtime，才切换草图运行态。
- 通过：`cd pc-tools/workstation && npx vitest run test/App.test.ts -t "renders Robot Control V1 by default|draws radar pulse on the robot marker|starts free-roam autonomy through the fixed proxy"`
  - 1 个 test file passed，3 个测试通过，89 个跳过。
- 通过：`cd pc-tools/workstation && npm run lint`
  - `eslint .` 完成。
- 通过：`cd pc-tools/workstation && npm run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- 通过：`cd pc-tools/workstation && npm test`
  - 2 个 test files passed，186 个测试通过。
- 通过：`git diff --check`
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`
  - `node ... TCP *:7001 (LISTEN)`

## 剩余风险

- 该轮只覆盖 PC mock 和前端 WYSIWYG 文案，没有启动真实自动扫图，也没有发送真实运动控制。
- 草图仍是覆盖监看参考，不等于真实 SLAM 覆盖优化路径、Nav2 路线或避障轨迹。
