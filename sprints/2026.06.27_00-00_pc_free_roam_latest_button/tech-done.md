sprint_type: micro

# PC 自动扫图 latest 只读按钮

## 实际改动

- `pc-tools/workstation/src/client/workstationApi.ts` 新增 `GET /api/robot-control/free-roam/autonomy/latest` client 封装，沿用默认小车地址参数。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue` 在普通首屏“自动扫图准备”里新增“刷新自动扫图状态（只读）”按钮；点击后只读取 latest artifact 并刷新 summary，页面显示 `decision_state/reason/stop_required/artifact_only/cmd_vel_publish_enabled` 摘要。
- `pc-tools/workstation/test/App.test.ts` 增加 latest fixture 和首屏只读按钮测试，明确断言不触发 start、stop、manual 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md` 同步记录首屏 latest 只读刷新入口和安全边界。

## 验证结果

- `npm test -- test/App.test.ts -t "refreshes free-roam autonomy latest"`：通过，1 passed / 120 skipped。
- `npm test -- test/App.test.ts`：通过，121 passed。
- `npm test`：通过，2 files / 218 passed。
- `npm run build`：通过；Vite 仍有既有 chunk size warning。
- `npm run lint`：通过。
- `git diff --check`：通过。
- PC Node 已重启在 `0.0.0.0:7001`，`lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `TCP *:7001 (LISTEN)`。
- 现场只读代理验证：`GET http://127.0.0.1:7001/api/robot-control/free-roam/autonomy/latest` 默认读取 `http://192.168.1.11:8787`，返回 `proxy_status=latest_loaded`、`decision_state=locked`、`decision_reason=还未勾选现场安全确认`、`artifact_only=true`、`cmd_vel_publish_enabled=false`、`safe_to_control=false`、`robot_control_executed=false`。
- 现场 summary 验证：`GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `free_roam_autonomy=locked`，runtime 为 `locked/还未勾选现场安全确认/artifact_only=true/cmd_vel_publish_enabled=false`。

## 剩余风险

- 真实上车端 `/api/free-roam/autonomy/latest` 当前只证明可读 latest artifact；是否开放自动扫图运动发布仍依赖后续真车 HIL 与安全门禁，不由本按钮改变。
