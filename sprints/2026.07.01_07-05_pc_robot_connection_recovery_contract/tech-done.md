# PC 上车连接恢复合同

## sprint_type

micro

## 实际改动

- `live_closure_summary` 新增上车连接总诊断字段：
  - `robot_api_connection_status`
  - `robot_api_connection_plain`
  - `robot_api_connection_next_action_plain`
  - loaded/failed/blocked 计数
  - `robot_api_connection_failed_endpoint_ids`
  - `robot_api_connection_blocked_reasons`
  - `robot_api_connection_recovery_endpoints`
  - `robot_api_connection_sends_motion_when_clicked=false`
- 当所有 Robot API 只读端点均失败时，当前卡点优先提示先恢复上车连接，下一步明确检查小车电源、网络、`8787` Robot API 服务和 SSH 登录状态。
- 普通首屏新增 `plain-live-robot-connection` 行，展示小车连接状态和下一步恢复动作，并暴露同名 data 属性；该行只读，不触发任何运动控制。
- 同步更新产品文档，明确连接恢复合同属于 no-motion 诊断。

## 验证结果

- 通过：`git diff --check`。
- 通过：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts -t "7071|Robot Control summary proxies Robot API"`，`1 passed`，`2 passed | 176 skipped`。
- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "Robot Control V1"`，`1 passed`，`1 passed | 229 skipped`。
- 通过：`cd pc-tools/workstation && npm run build`，`tsc` 与 `vite build` 通过；Vite 仍提示单 chunk 超过 500 kB，这是既有体积提示。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：PC Node 重启到 `0.0.0.0:7001`，实际监听进程 `node` PID `39722`；`GET /api/health` 返回 `safe_to_control=false`、`delivery_success=false`；只读 `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `robot_api_connection.status=degraded`、`loaded_count=0`、`failed_count=15`、`live_closure_summary.robot_api_connection_status=degraded`、`robot_api_connection_plain=小车连接不可用...`、`robot_api_connection_next_action_plain=先确认小车电源、网络、8787 Robot API 服务和 SSH 登录状态，再刷新 PC 状态。`、`robot_api_connection_sends_motion_when_clicked=false`。

## 剩余风险

- 本轮没有恢复真实上车网络或 `8787` 服务，也没有发送 Nav2、manual、keyboard、free-roam、map start、delivery、stop 或 `/cmd_vel`。
- 当前真实环境仍需要先恢复 `192.168.1.11` 的 Robot API/SSH 可读性，才能继续完整路线执行、同窗口轮速 L/R、delivery success、键盘连续手控和建图 HIL 验证。
