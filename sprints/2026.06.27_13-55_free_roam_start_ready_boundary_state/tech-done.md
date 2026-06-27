# Free-roam start-ready boundary state

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `safe_command_boundary.free_roam_autonomy` 从二态改为三态：`locked`、`start_ready`、`ready`。
  - `start_ready` 专门表示上车 runtime 已加载且停止兜底 ready，勾现场安全确认即可发起低速自由移动；`ready` 仍只表示上车端已经打开运动发布。
- `pc-tools/workstation/test/catalog.test.ts`
  - 更新 free-roam summary 回归断言，覆盖 runtime artifact-only 但可发起 start 的场景。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 free-roam boundary 三态语义。

## 验证结果

- `npm test -- --run catalog.test.ts -t "free-roam"`
  - 结果：通过，`8 passed | 117 skipped`。
- `npm test`
  - 结果：通过，`2 passed`，`290 passed`。
- `npm run build`
  - 结果：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成；Vite 仍提示单个 chunk 超过 500 kB，这是既有打包体积 warning。
- 重启 `npm run api:public` 后验证 7001：
  - `lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 Node 监听 `*:7001`。
  - `curl http://127.0.0.1:7001/api/robot-control/summary?...` 显示 live `free_roam_autonomy=start_ready`、`free_roam_autonomy_start_ready=true`、`free_roam_autonomy_label=自由移动（勾确认后可启动）`，runtime 仍为 `artifact_only=true/cmd_vel_publish_enabled=false`。

## 剩余风险

- 本轮只修正 PC summary 状态口径，不发送 free-roam start、manual、keyboard、Nav2、delivery、stop 或 `/cmd_vel`。
- 真实自由移动仍需要现场勾选安全确认并点击开始；相机和雷达 ready 只决定能否按建图验收。
