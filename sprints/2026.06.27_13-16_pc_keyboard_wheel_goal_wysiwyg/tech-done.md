# PC 键盘 wheel raw 目标可视化

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏键盘区新增 `键盘轮速目标` 行。
  - 当键盘入口已满足但当前 wheel raw L/R 仍为 `0/0` 时，明确提示启用后/启用中应按住方向键读取非零 L/R。
  - 该行只消费只读 base feedback 和本地键盘 armed 状态；不改变键盘 pulse、stop、Nav2、free-roam 或任何控制 gate。
- `pc-tools/workstation/test/App.test.ts`
  - 增加当前 L/R=`0/0` 的键盘可用场景断言，覆盖启用前和启用后的提示。
- `docs/product/pc_tools_workstation.md`
  - 同步记录普通首屏键盘 wheel raw 目标提示和安全边界。

## 验证结果

- `npm test -- --run App.test.ts -t "keeps keyboard wheel readback unproven when manual pulse returns only zero L/R"`
  - 结果：通过，`1 passed | 163 skipped`。
- `npm test`
  - 结果：通过，`2 passed`，`287 passed`。
- `npm run build`
  - 结果：通过，生成 `dist/`；Vite 仍提示单个 chunk 超过 500 kB，这是既有打包体积 warning，不影响本轮键盘提示。
- PC API 重启和 live 只读复核
  - `npm run api:public` 已重新启动，`lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node` 监听 `*:7001`。
  - live summary 返回 `keyboard_control_start_ready=true`、base wheel L/R=`0/0`、camera=`source_first_frame_failed`、lidar=`latest_proof_stale_while_lifecycle_running`、free-roam `start_ready=true`；该状态会触发本轮新增的键盘 wheel raw 目标提示。

## 剩余风险

- 本轮不触发真实键盘手控、不发送 manual/stop/Nav2/free-roam/`/cmd_vel`；真实 wheel raw L/R 是否非零仍需要现场勾安全确认后按住方向键验证。
- live 上位机当前 base feedback 仍为 L/R=`0/0`；该改动只让 PC 首屏把下一手动作说清楚，不修复底盘电机使能、供电或模式问题。
