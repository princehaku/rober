# PC Localize Reset Real Proxy Smoke

sprint_type: micro

## 实际改动

- 本轮未修改 PC 产品代码、测试代码、普通首屏组件、样式、`onboard/` 产品代码或硬件配置。
- 新增本 sprint 证据目录：
  - `artifacts/pc_proxy/run_context.json`
  - `artifacts/pc_proxy/summary_before_reset.json`
  - `artifacts/pc_proxy/direct_localize_latest_before_reset.json`
  - `artifacts/pc_proxy/localize_reset_malicious_browser_body_request.json`
  - `artifacts/pc_proxy/localize_reset_proxy_response.json`
  - `artifacts/pc_proxy/summary_after_reset.json`
  - `artifacts/pc_proxy/direct_localize_latest_after_reset.json`
  - `artifacts/pc_proxy/localize_reset_smoke_summary.json`
  - `artifacts/pc_proxy/localize_reset_smoke_corrected_summary.json`
  - `artifacts/dom_smoke/pc_plain_user_home_dom_smoke.json`
  - `artifacts/cleanup_summary.json`
  - `artifacts/cleanup_upper_status_after.json`
  - `artifacts/cleanup_ssh_process_device_check.txt`
- 同步更新文档：
  - `pc-tools/README.md`
  - `docs/product/pc_tools_workstation.md`
  - `docs/hardware/board_sensor_stack_smoke.md`
  - `docs/navigation/fixed_route_workflow.md`

## 真实 PC Proxy Smoke

临时 workstation API：`http://127.0.0.1:18791`。
真实上位机 Robot API：`http://192.168.1.11:8787`。

执行链路：

- 前置 `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787`
- 前置直接只读 `GET http://192.168.1.11:8787/api/localize/proof/latest`
- `POST /api/robot-control/localize/reset?baseUrl=http://192.168.1.11:8787`
- 后置 `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787`
- 后置直接只读 `GET http://192.168.1.11:8787/api/localize/proof/latest`

本轮 POST 故意携带恶意/无关 body：`endpoint=/api/base/manual`、
`path_generation_opt_in=true`、`sends_motion_commands=true`、
`publishes_cmd_vel=true`、`calls_base_manual=true` 和伪造 `cmd_vel`。PC route 忽略
`req.body`，实际仍只调用固定上位机 endpoint `/api/localize/reset`。

结果摘要：

- Workstation proxy HTTP `200`。
- `proxy_status=refresh_forwarded`
- `remote_endpoint=/api/localize/reset`
- `remote_http_status=200`
- `refresh_kind=localization_reset`
- `last_result_status=refreshed`
- `evidence_ref=o10-amcl-nav2-runtime-1781157704384`
- `initialpose_published=true`
- `amcl_pose_observed=true`
- `amcl_pose_frame_id=map`
- `amcl_frame_params={base_frame_id: base_link, global_frame_id: map, odom_frame_id: odom}`
- `root_causes=[]`
- `managed_runtime_cleanup_ok=true`
- `managed_runtime_remaining_processes=[]`

No-motion 合同保持：

- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `robot_control_executed=false`
- `sends_motion_commands=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`

没有执行：

- `NavigateToPose`
- `compute_path_to_pose`
- `/cmd_vel`
- `/api/base/manual`
- fixed-route execution
- WAVE ROVER UART

## 首屏边界验证

执行命令：

```bash
cd pc-tools/workstation && npm run test -- test/App.test.ts -t "renders Robot Control V1"
```

结果：通过，`1 passed | 12 skipped`。

本轮 `artifacts/dom_smoke/pc_plain_user_home_dom_smoke.json` 记录：

- `.simple-user-console` 仍存在。
- 标题仍是 `Rober 小车控制台`。
- 首屏五卡片仍是 `小车连接`、`实时画面`、`雷达`、`地图`、`移动/导航`。
- 默认可见首屏未出现 `定位重置`、`initialpose`、`AMCL`、`HIL`、`proof`、`Nav2`、
  `/cmd_vel`、`/api/base/manual`、`task_id`、`Mock`、`检查路径`。
- `定位重置（高级）`、`/api/localize/reset`、`initialpose_published`、
  `amcl_pose_observed` 只保留在默认关闭的高级诊断。

## Cleanup

- 已停止临时 workstation API。
- `lsof -nP -iTCP:18791 -sTCP:LISTEN` 无监听。
- 上位机 `trashbot-upper-robot-api.service=active`。
- SSH 只读 `ps` grep 未发现长期 `localize/Nav2/AMCL/map_server/planner_server/helper`
  残留。
- SSH 只读 `lsof /dev/ttyS5 /dev/ttyACM0` 无输出。
- SSH 只读 `fuser -v /dev/ttyS5 /dev/ttyACM0` 无输出。

## 验证结果

- `git diff --check`：通过。
- PC 产品代码未改，因此未执行完整 `npm run build`、`npm run test -- --run`、
  `npm run lint`。
- 首屏 DOM smoke：通过，见上方现有 App.test targeted run。
- 真实 PC proxy localize reset smoke：通过，见
  `artifacts/pc_proxy/localize_reset_smoke_corrected_summary.json`。
- Cleanup：通过，见 `artifacts/cleanup_summary.json` 和
  `artifacts/cleanup_ssh_process_device_check.txt`。

## 剩余风险

- 本轮证明 PC 可以通过固定代理触发上位机 no-motion `/initialpose + AMCL` 定位材料，
  不证明真实导航执行、路径跟随、固定路线行驶、HIL 或 delivery success。
- 上位机 `/api/status` 的 status 字段在 cleanup 摘要中没有顶层 `status` 短值，但 HTTP
  200、schema 和安全 false 字段可读；不影响本轮 localize reset 结论。
- 本轮不提升 `safe_to_control`，不放开普通首屏定位重置，也不允许非 stop 运动。
