# PC Free Roam Start-Ready Label

sprint_type: micro

## 实际改动

- Robot Control summary 的 `safe_command_boundary.free_roam_autonomy_label` 从二态改为三态：
  - `自动扫图`：上车端 runtime 已 `cmd_vel_publish_enabled=true` 且 gates ready；
  - `自动扫图（勾确认后可启动）`：基础 start gate 已满足，但 runtime 仍是 artifact-only/stopped；
  - `自动扫图（未开放）`：基础 start gate 也未满足。
- 更新 shared contract 和 catalog 测试，锁定 `free_roam_autonomy_start_ready=true`、但雷达 freshness 不满足时的 label 仍提示可勾确认后启动，而不是误报未开放。
- 更新 PC 工作站产品文档，记录该 label 只修正 WYSIWYG 文案，不自动发车。

## 验证结果

- `cd pc-tools/workstation && npm test -- catalog.test.ts`：通过，106 tests passed。
- `cd pc-tools/workstation && npm test -- App.test.ts`：通过，139 tests passed。
- `cd pc-tools/workstation && npm run build`：通过；Vite 仍提示单个 chunk 超过 500 kB 的既有体积 warning。
- `git diff --check`：通过。
- 真实 PC 7001 只读 smoke：`HOST=0.0.0.0 PORT=7001 ./node_modules/.bin/tsx src/server/index.ts` 已监听 `*:7001`；
  `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `robot_api_connection.status=readable`、
  `safe_to_control=false`、`safe_command_boundary.robot_control_executed=false`、`dangerous_true_fields=[]`、
  `free_roam_autonomy=locked`、`free_roam_autonomy_start_ready=true`、
  `free_roam_autonomy_label=自动扫图（勾确认后可启动）`、runtime 为 `artifact_only=true/cmd_vel_publish_enabled=false/stopping`。

## 剩余风险

- 本轮不触发真实 `/api/free-roam/autonomy/start`，避免在没有当前现场安全确认的情况下让车移动。
- 真实 smoke 已确认 live label 修正；本轮仍不触发真实 `/api/free-roam/autonomy/start`，因此不证明小车本轮已经自助移动。
