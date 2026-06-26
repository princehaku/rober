# 2026.06.26 23:59 PC 自动扫图 latest 只读代理

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`
  - 新增 `GET /api/robot-control/free-roam/autonomy/latest` 固定只读代理，缺省 `baseUrl` 时默认读取固定小车 `http://192.168.1.11:8787`。
  - 代理只转发到上位机 `/api/free-roam/autonomy/latest`，返回 `decision_state/reason/stop_required/artifact_only/cmd_vel_publish_enabled/gate_count` 短摘要。
  - 该代理不调用 start/stop、manual、Nav2、delivery 或 `/cmd_vel`；PC 顶层仍固定 `safe_to_control=false`、`delivery_success=false`、`robot_control_executed=false`。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 增加 `RobotControlFreeRoamAutonomyLatestResponse` 合同。
- `pc-tools/workstation/test/catalog.test.ts`
  - 默认只读地址测试覆盖 free-roam latest。
  - 新增固定 latest 代理测试，确认只 GET `/api/free-roam/autonomy/latest`，不调用 start/stop/manual。
- `docs/product/pc_tools_workstation.md`
  - 同步记录自动扫图 latest 只读代理和安全边界。

## 验证结果

- `npm test -- test/catalog.test.ts -t "free-roam autonomy latest|defaults Robot Control read-only"`：1 file passed，2 passed，95 skipped。
- `npm test -- test/catalog.test.ts`：1 file passed，97 passed。
- `npm test`：2 files passed，217 passed。
- `npm run build`：通过；Vite 仍提示单 chunk 大于 500 kB，这是既有打包提示。
- `npm run lint`：通过。
- `git diff --check`：通过。
- Live 7001 重启验证：
  - `npm run api` 输出 `pc-tools workstation API listening on http://0.0.0.0:7001`。
  - `lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node` 监听 `TCP *:7001`。
- Live 上位机 latest 验证：
  - `GET /api/robot-control/free-roam/autonomy/latest?baseUrl=http://192.168.1.11:8787` 返回 JSON schema `trashbot.pc_tools_workstation.robot_control_free_roam_autonomy_latest_proxy.v1`，`proxy_status=latest_loaded`、`remote_http_status=200`。
  - `latest_key_values.decision_state=locked`、`decision_reason=还未勾选现场安全确认`、`stop_required=true`、`artifact_only=true`、`cmd_vel_publish_enabled=false`、`gate_count=5`。
  - 顶层仍为 `safe_to_control=false`、`delivery_success=false`、`robot_control_executed=false`，`hard_dangerous_true_fields=[]`。
  - 缺省 `baseUrl` 的 `GET /api/robot-control/free-roam/autonomy/latest` 默认读取 `source_base_url=http://192.168.1.11:8787`，不再落到前端 HTML。

## 剩余风险

- 本轮只补 PC 只读 runtime 代理，不开放自动扫图运动发布。
- 当前 live 自动扫图 runtime 仍为 locked/artifact-only；真车自由跑动建图仍需要上车端 runtime 解锁、雷达/停止兜底和 HIL 验证。
- wheel raw L/R 非零、完整 Nav2 路线执行、delivery success 和 PC 键盘连续手控仍需要继续 live HIL 收口。
