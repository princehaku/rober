# 2026.06.02 11-12 O7 Long Stability Real Material

## Sprint Type

- `sprint_type: micro`
- Owner: `full-stack-software-engineer`
- Objective: O7 PC 端运营调试平台
- Scope: 实际运行 O7 180s+ browser long-stability collector，读取 artifact，按真实材料队列语义收口；失败时只补 operator 可理解的失败解释。

## 实际运行证据

- 命令：`cd pc-tools/workstation && npm run o7:browser-long-stability`
- 默认 URL：`http://192.168.1.11:8088/`
- artifact：`pc-tools/workstation/.workstation-runtime/o7-browser-playback-smoke.json`
- 结果分类：`blocked`
- 关键字段：
  - `status=failed`
  - `failure_category=browser_smoke_failed`
  - `remote_health_status=remote_health_unreachable`
  - `blocked_reason=page.goto: net::ERR_CONNECTION_REFUSED`
  - `start_clicked=false`
  - `offer_executed_by_browser=false`
  - `first_frame_received=false`
  - `stability_summary.status=not_observed`
  - `stability_summary.observation_window_ms=0`
  - `server_peer_close_status=not_attempted`
  - `post_smoke_remote_health.status=remote_health_unreachable`
  - `safe_to_control=false`
  - `sends_commands=false`
  - `robot_control_executed=false`

## 实际改动

- 更新 `pc-tools/workstation/src/server/realMaterialAcceptance.ts`：
  - O7 browser artifact 已经 `failed` / `fail_closed` / `degraded` 时，`blocking_reason` 优先暴露脱敏后的 `failure_category`、关键失败 token 和 `remote_health_status`。
  - 本轮真实失败会归类为 `browser_smoke_failed__net_err_connection_refused__remote_health_unreachable`。
  - 响应不泄露原始 LAN URL、Playwright 调用栈或 artifact 绝对路径。
  - lint 首次发现 ANSI escape regex literal 触发 `no-control-regex`，已改为运行时构造 `RegExp`，保持脱敏行为不变。
- 更新 `pc-tools/workstation/test/catalog.test.ts`：
  - 新增失败 artifact 回归测试，证明 acceptance queue 不会把连接拒绝退化成泛泛的 `first_frame_not_received`。
  - 验证 queue 仍保持 `network_probe_executed=false` 和 no-control flags。
- 更新 `docs/interfaces/real_material_acceptance_queue.md`：
  - 补充 O7 blocked 失败解释语义和本轮真实 `ERR_CONNECTION_REFUSED` 采集边界。
- 更新 `docs/product/pc_tools_workstation.md`：
  - 同步 O7 real-material queue 的失败原因展示边界。

## 用户旅程变化和触点收益

- Operator 现在能从 `GET /api/real-material/acceptance` 的 O7 item 直接看出下一步不是“重跑 180s 等待”，而是先恢复或确认板端 HTTP/WebRTC camera 服务监听。
- UI/API 仍然只读 artifact，不自动 POST `/offer`，不创建 WebRTC session，不发送控制。
- 失败原因以机器 token 呈现，便于 sprint 和 OKR owner 复核真实材料缺口。

## 接口影响

- `GET /api/real-material/acceptance` schema 不变。
- O7 item 的 `blocking_reason` 在失败 artifact 场景下更具体：
  - 旧：可能退化为 `first_frame_not_received`
  - 新：例如 `browser_smoke_failed__net_err_connection_refused__remote_health_unreachable`
- ROS2 / O1 / WAVE ROVER / LiDAR / hardware 相关接口无变更。

## 验证结果

- `cd pc-tools/workstation && npm run o7:browser-long-stability`
  - 已运行并结束；生成 `.workstation-runtime/o7-browser-playback-smoke.json`。
  - 结果 blocked：板端 `http://192.168.1.11:8088/` 连接被拒绝，未点击 start，未 POST `/offer`，未创建 WebRTC session，未拿到首帧，未进入 180s stability window。
- `cd pc-tools/workstation && npm run test -- catalog.test.ts`
  - 通过；1 file / 54 tests passed。

## 验收命令结果

- `cd pc-tools/workstation && npm run o7:browser-long-stability -- --dry-run`
  - 通过；输出 `status=dry_run`、`artifact_written=false`、`network_probe_executed=false`、`post_executed=false`、`webrtc_session_created=false`、`offer_executed_by_browser=false`。
  - dry-run 未联网、未 POST `/offer`、未创建 WebRTC session、未覆盖真实 runtime artifact。
- `cd pc-tools/workstation && npm run test`
  - 通过；`2` 个 test file / `60` 个 tests passed。
- `cd pc-tools/workstation && npm run build`
  - 通过；`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成，Vite 输出 `35 modules transformed`。
- `cd pc-tools/workstation && npm run lint`
  - 首次失败：`pc-tools/workstation/src/server/realMaterialAcceptance.ts` 的 ANSI escape regex literal 触发 `no-control-regex`。
  - 已最小修复：改为 `String.fromCharCode(27)` 运行时构造 `RegExp` 后重跑通过。

## Product / OKR 建议口径

- O7 建议保持约 `96%`，不因本轮真实 collector blocked 上调为完成。
- 真实 `180s` / `3-5min` browser long-stability artifact 仍为 `not_proven`，不能表述为 production done。
- 本轮新增价值是把 O7 blocker 从泛化的 `first_frame_not_received` 收敛为 `browser_smoke_failed__net_err_connection_refused__remote_health_unreachable`，下一步应先确认板端 HTTP/WebRTC camera 服务是否监听、端口是否正确、板端网络是否可达。
- O1 / WAVE ROVER / LiDAR / ROS2 / hardware 本轮未消费，OKR Owner 若更新进度，应只计入 O7 operator evidence quality 提升，不计入真实长稳态通过或真实上车闭环。

## Product Closeout

- Product / OKR Owner 收口：Objective 7 保持约 `96%`，口径更新为 `software collector entry + blocked real-material failure classification`。
- 本轮证据证明 collector 入口已真实运行并落盘 artifact，但 artifact 为 blocked：`ERR_CONNECTION_REFUSED`、`remote_health_unreachable`、未点击 start、未执行 `/offer`、未创建 WebRTC session、未收到首帧、`observation_window_ms=0`。
- 本轮不消费 O1 SSH blocker，未 SSH `root@192.168.1.11 -p 37878`，未改 WAVE ROVER / LiDAR / ROS2 / hardware；OKR 只计入 O7 失败分类和 operator 下一步可理解性提升。
- `OKR.md` 与 `docs/process/okr_progress_log.md` 已同步记录 `2026.06.02_11-12_o7-long-stability-real-material`，并明确真实 `180s` / `3-5min` artifact 仍为 `not_proven`。

## 剩余风险

- 真实 180s/3-5min browser artifact 仍未完成，O7 不应被表述为 production done。
- 当前 blocker 是板端 HTTP/WebRTC camera 服务连接拒绝或未监听；需要现场确认服务进程、端口、板端网络和 camera server 日志。
- 弱网、TURN、公网云 relay、鉴权、真实用户浏览器/手机、ASR/TTS、手控/Nav2、真实 robot ACK 和完整上车任务闭环仍为 `not_proven`。
- O1 SSH / `T=1001` blocker 本轮未消费；OKR 进度和 O7 口径需要 Product / OKR Owner 后续基于本 sprint 证据收口。
