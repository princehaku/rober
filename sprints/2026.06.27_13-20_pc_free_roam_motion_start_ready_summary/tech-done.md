# PC free-roam 启动 readiness 语义修正

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - `readback_summary.free_roam` 新增 `motion_start_ready` 字段。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `motion_start_ready` 跟随上车 runtime loaded 与 stop 兜底 readiness，表示“可以发起自由移动”。
  - 保留 `motion_ready` 的原语义：当前上车端是否已经打开运动发布。
  - fail-closed summary 也补齐 `motion_start_ready=false`。
- `pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/App.test.ts`
  - 更新 summary 合同期望，锁定 `motion_start_ready=true` 且 `motion_ready=false` 的未启动但可启动语义。
- `docs/product/pc_tools_workstation.md`
  - 同步记录字段语义和安全边界。

## 验证结果

- `npm test -- --run catalog.test.ts -t "surfaces free-roam autonomy runtime state from latest artifact readback"`
  - 结果：通过，`1 passed | 122 skipped`。
- `npm test`
  - 结果：通过，`2 passed`，`287 passed`。
- `npm run build`
  - 结果：通过，生成 `dist/`；Vite 仍提示单个 chunk 超过 500 kB，这是既有打包体积 warning，不影响本轮 summary 字段。
- PC API 重启和 live 只读复核
  - `npm run api:public` 已重新启动，`lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node` 监听 `*:7001`。
  - live summary 返回 `readback_summary.free_roam.start_ready=true`、`motion_start_ready=true`、`motion_ready=false`、`artifact_only=true`、`cmd_vel_publish_enabled=false`，对应“可启动自由移动，但当前没有运动发布”。

## 剩余风险

- 本轮不触发真实 free-roam start，不发送 manual/keyboard/Nav2/delivery/stop 或 `/cmd_vel`；只是修正只读 summary 的 readiness 语义。
- live 当前仍是 `artifact_only=true`、`cmd_vel_publish_enabled=false`，说明小车没有在自己跑；需要现场勾安全确认后显式点击开始自由移动，才能验证真实运动。
