# sprint_type: micro

## 背景

本轮目标是修复 PC Robot Control Console V1 在真实上位机只读 readback 中把 `status/camera` 误判为 `fetch_failed` 的问题。  
上一轮真实 evidence 已证明远端 `http://192.168.1.11:8787` 的 `/api/status`、`/api/camera/health`、`/api/camera/devices` 都可读；误判根因是 `pc-tools/workstation/src/server/robotControlSummary.ts` 对全部 endpoint 统一使用 `1500ms` 超时。

## 实际改动

1. 更新 [`/Users/m1/apps/rober/pc-tools/workstation/src/server/robotControlSummary.ts`](/Users/m1/apps/rober/pc-tools/workstation/src/server/robotControlSummary.ts)
   - 把 Robot API 白名单从“id + endpoint”升级成“id + endpoint + timeout_ms”配置。
   - 为 `/api/status`、`/api/camera/health`、`/api/camera/devices` 提供更宽的只读超时窗口。
   - 保持其余 proof/latest/readback endpoint 的短超时不变。
   - 保持 GET-only、private LAN only、危险 true 字段 fail-closed、safe command boundary 全部 disabled。
   - `fetch_failed` 现在会把超时原因带成 `fetch_timeout_<n>ms`，方便区分慢端点与其他 fetch 异常。
2. 更新 [`/Users/m1/apps/rober/pc-tools/workstation/test/catalog.test.ts`](/Users/m1/apps/rober/pc-tools/workstation/test/catalog.test.ts)
   - 新增按路径 + 延迟返回的 Robot API fixture server。
   - 新增慢 `/api/status`、`/api/camera/health`、`/api/camera/devices` 仍应 `loaded` 的测试。
   - 保留 `/api/base/status`、`/api/base/feedback-samples/latest` 因危险字段被 `blocked` 的断言，确保没有放松安全边界。
3. 更新 [`/Users/m1/apps/rober/docs/product/pc_tools_workstation.md`](/Users/m1/apps/rober/docs/product/pc_tools_workstation.md)
   - 补充 Robot Control V1 的端点级只读超时策略说明。
   - 明确该策略只减少误报，不放松 URL、方法或危险字段安全边界。
4. 更新 [`/Users/m1/apps/rober/pc-tools/README.md`](/Users/m1/apps/rober/pc-tools/README.md)
   - 同步说明 `status/camera` 采用更宽只读超时窗口，其余 endpoint 继续短超时。

## 用户旅程 / 触点收益

1. 操作员在 Robot Control tab 填入真实上位机 `baseUrl` 后，不会再因为 `status/camera` 稍慢就看到三连 `fetch_failed`。
2. 页面可以更准确地区分：
   - `readback loaded but control blocked`：例如 base/status 因 `sends_commands=true` 被安全边界阻断；
   - `endpoint blocked/not_proven`：例如 `404` 的 localize/operator；
   - `fetch_failed`：真正的网络/超时异常。
3. 控制按钮仍全部 disabled，用户不会因为 readback 变准而误以为已经开放手控或 Nav2 下发。

## 接口影响和安全边界

1. 对外 API 路径与响应 schema 不变，未改 `contracts.ts`。
2. 仅服务端内部读取策略变化：
   - `status/camera` 使用更宽只读超时；
   - 其余 endpoint 维持短超时。
3. 未启用 `/api/base/manual`、`/cmd_vel`、Nav2 goal、radar start、map start、keyboard control、map click goal。
4. `base` 相关 endpoint 仍因危险真值字段而 `blocked`，这是当前安全设计，未放松。
5. `status` endpoint 如果嵌入 `base.sends_commands=true` 之类危险字段，也仍会被 `blocked`，不会因为超时放宽而变成可控。

## 验证结果

### 验收命令

- `cd pc-tools/workstation && npm run build`
  - 通过。
- `cd pc-tools/workstation && npm run test`
  - 通过，`2` 个 test files、`55` 个 tests 全绿。
- `cd pc-tools/workstation && npm run lint`
  - 通过。
- `git diff --check`
  - 通过。

### 真实上位机 summary 复验

先对当前本机已运行的 `http://127.0.0.1:8787` 执行：

```bash
curl --max-time 20 -sS 'http://127.0.0.1:8787/api/robot-control/summary?baseUrl=http://192.168.1.11:8787'
```

结果仍返回旧行为，`status/camera` 继续超时，且超时文案还是旧的 `The operation was aborted due to timeout`。  
这说明该 8787 workstation API 进程没有加载本轮代码，不应作为本轮复验结论。

随后使用当前代码在新端口启动只读 API：

```bash
cd pc-tools/workstation
PORT=8788 npm run api
curl --max-time 20 -sS 'http://127.0.0.1:8788/api/robot-control/summary?baseUrl=http://192.168.1.11:8787'
```

关键字段：

- `robot_api_connection.loaded_count=8`
- `robot_api_connection.blocked_count=5`
- `robot_api_connection.failed_count=0`
- `readback_summary.camera.status=ready`
- `readback_summary.camera.devices_status=loaded`
- `o3_proof_summary.path_generated=true`
- `o3_proof_summary.path_point_count=31`
- `base_status` / `base_feedback_samples_latest` 仍因 `dangerous_true_field:*sends_commands` 被 `blocked`
- `localize_proof_latest`、`operator_report_latest` 仍为 `http_status_404`

结论：本轮修复已经把真实慢 `status/camera` 从误报 `fetch_failed` 修正为可读，同时安全阻断仍然生效。

主会话随后停止旧的 `127.0.0.1:8787` workstation API 进程，并用当前代码重新启动同一端口：

```bash
PORT=8787 npm run api
curl --max-time 20 -sS 'http://127.0.0.1:8787/api/robot-control/summary?baseUrl=http://192.168.1.11:8787'
```

原始返回已保存到：

- `artifacts/workstation_robot_control_summary_8787.json`

关键字段：

- `robot_api_connection.loaded_count=8`
- `robot_api_connection.blocked_count=5`
- `robot_api_connection.failed_count=0`
- `readback_summary.camera.status=ready`
- `readback_summary.camera.devices_status=loaded`
- `readback_summary.lidar.status=scan_once_hz_raw_packet_tf_observed`
- `readback_summary.base.status=loaded`
- `o3_proof_summary.path_generated=true`
- `o3_proof_summary.path_point_count=31`
- `safe_command_boundary.command_dispatch_enabled=false`
- `safe_command_boundary.manual_control_enabled=false`
- `safe_command_boundary.navigate_goal_enabled=false`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`

## 剩余风险

1. 真实上位机的 `/api/status` 现在可在更宽窗口内返回，但其内部如果继续聚合 `base.sends_commands=true`，summary 顶层仍会显示 `blocked`；这是符合当前 fail-closed 设计的，不是回归。
2. `localize_proof_latest` 和 `operator_report_latest` 当前仍是 `404`，所以整页不会进入完全 `readable` 状态。
3. 本轮没有改前端文案去单独区分“status 自身已读到，但因嵌套 base 危险字段被 blocked”；如果下一轮要优化 operator 可读性，可以继续在不放松危险字段扫描的前提下补 UI copy。
4. 本轮验证范围仅覆盖 Node summary 代理、测试和真实 GET 复验；不包含 HIL、运动控制、`/api/base/manual`、`/cmd_vel`、Nav2 goal 或真实交付成功。

## 是否需要其他角色协同

当前不需要其他角色介入即可交付本轮 micro 修复。  
若后续要把 `status` 中嵌套的 base blocked reason 做成更清晰的 UI 文案，继续由 `full-stack-software-engineer` 单线处理即可；如需改变上位机 `/api/status` 聚合内容，再和 `robot-software-engineer` 协同。
