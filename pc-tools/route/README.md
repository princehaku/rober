# pc-tools/route

`pc-tools/route/` 现在只保留 fixed-route 调试说明和非 Python 资产。旧 route Python 调试脚本已移除，PC 路线调试入口由 Node/Vue 工作站承接：

```text
pc-tools/workstation/src/server/routeDebugLoader.ts
```

## Node Route JSON Loader

工作站的 Route Debug 页面通过 `/api/route/debug-summary` 读取本地 JSON 路径参数：

- `statusJson`
- `taskRecord`
- `taskRecordDir`
- `elevatorRouteReconciliation`

loader 只读取 JSON 并生成 safe summary。缺文件、坏 JSON、unsupported schema/boundary、unsafe copy、success/control claim、evidence_ref mismatch 都会 fail closed，且响应继续固定：

- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- `console_controls=read_only`

## 证明边界

Route Debug 只能证明 Node 工作站可以把本地 route/status/task/reconciliation JSON 压缩成软件证明摘要。它不证明真实 ROS2、真实 Nav2/fixed-route、真实路线采集、真实电梯、真实 WAVE ROVER 运动、真实串口反馈、真实 HIL、dropoff/cancel completion 或 delivery success。

## 验证

Route Debug 的验证入口是工作站 Node 测试：

```bash
cd pc-tools/workstation && npm run test
```

不再运行 Python unittest 或 Python route 脚本。
