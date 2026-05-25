# PC Tools Route JSON Loader Tech Done

## sprint_type

micro

## 实际改动

- 在 `pc-tools/workstation/src/server/routeDebugLoader.ts` 新增 Route Debug 本地 JSON 只读 loader，支持 `statusJson`、`taskRecord`、`taskRecordDir`、`elevatorRouteReconciliation`，并复用旧 `route_debug_web.py` 的 fail-closed 语义：缺文件、坏 JSON、unsupported schema/boundary、unsafe copy、success/control claim、`evidence_ref` mismatch 均返回 blocked/not_proven 摘要。
- 在 `pc-tools/workstation/src/server/index.ts` 和 `catalog.ts` 接入 `GET /api/route/debug-summary` query 参数；API 仍固定 `source=software_proof`、`proof_status=not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`pc_only=true`、`console_controls=read_only`。
- 在 `pc-tools/workstation/src/App.vue` 与 `styles.css` 增加 Route Debug 路径输入区和 safe summary 展示，只显示加载状态、blocked reason、route/task/reconciliation 摘要，不展示完整本机路径或控制入口。
- 在 `pc-tools/workstation/test/catalog.test.ts` 与 `App.test.ts` 增加 Vitest 覆盖：正常读取 sample status/task/reconciliation、坏 JSON fail-closed、unsafe copy/success/control claim 拒绝、页面/API 不包含 `/cmd_vel` 或 `/dev/tty`，且成功与主动作字段固定为 false。
- 同步更新 `docs/product/pc_tools_workstation.md`，说明 Route Debug JSON loader 的 query 契约、展示边界和不可声明事项。

## 验证结果

```text
cd pc-tools/workstation && npm run build
✓ built in 507ms
tsc -p tsconfig.server.json passed
```

```text
cd pc-tools/workstation && npm run test
Test Files  2 passed (2)
Tests  8 passed (8)
```

```text
cd pc-tools/workstation && npm run lint
eslint . passed
```

```text
python -m unittest discover pc-tools/route -p "test_*.py"
Ran 7 tests in 0.065s
OK
```

## 剩余风险

- 本轮仍是 PC-only software proof，没有 ROS2、Nav2、真实串口、WAVE ROVER feedback、HIL 或真实投放验证。
- Node API 只读取和脱敏本地 JSON，不替代 `pc-tools/route/route_debug_web.py` 的旧 gate 权威。
- UI 路径输入框会显示操作者正在输入的本机路径；API 返回和摘要展示只保留 `file:<basename>` 或加载状态，不回显完整本机路径。
