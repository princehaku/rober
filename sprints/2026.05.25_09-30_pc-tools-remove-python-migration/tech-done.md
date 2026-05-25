# PC Tools Remove Python Migration Tech Done

## sprint_type

epic

## 实际改动

- 删除 `pc-tools` 下旧 Python 文件 270 个，删除 `pc-tools/route/__pycache__` 1 个。
- 保留非 Python 资产：`pc-tools/evidence/fixtures/**`、`pc-tools/evidence/README.md`、`pc-tools/route/README.md`、`pc-tools/workstation/**`、`pc-tools/training/`、`pc-tools/labeling/`。
- 更新 `pc-tools/workstation/src/server/catalog.ts`：Evidence Tools 改为递归索引 `pc-tools/evidence/fixtures/**/*.json`，Route Debug 改为 `node_route_json_loader` 能力描述，不再把旧 route Python 文件作为 gate。
- 更新 `pc-tools/workstation/src/shared/contracts.ts`：Evidence/Route/Proof Boundary schema 升级到 Node/Vue 主入口语义，继续固定 `delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
- 更新 `pc-tools/workstation/src/App.vue`：Route Debug 页面展示 Node Route JSON Loader；Evidence Tools 页面展示 JSON fixture 分组；UI 不展示旧 Python gate 执行入口。
- 更新 `pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/App.test.ts`：覆盖无 Python 文件时 Evidence/Route 可用、JSON fixture 索引可读、Route JSON loader fail-closed、API/UI 不暴露旧 Python gate 执行语义、不出现控制 topic 或串口设备路径、fail-closed flags 固定为 false。
- 更新 `pc-tools/README.md`、`pc-tools/route/README.md`、`pc-tools/evidence/README.md`、`docs/product/pc_tools_workstation.md`：说明旧 Python 已移除，Node.js + Vue 工作站为主入口。

## 验证结果

```text
cd pc-tools/workstation && npm run build
> tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json
✓ built in 410ms
exit 0
```

```text
cd pc-tools/workstation && npm run test
Test Files  2 passed (2)
Tests  8 passed (8)
exit 0
```

```text
cd pc-tools/workstation && npm run lint
> eslint .
exit 0
```

```powershell
Get-ChildItem -Path pc-tools -Recurse -File -Include *.py | Where-Object { $_.FullName -notmatch '\\workstation\\node_modules\\' }
```

结果为空，`pc-tools` 范围内除 `workstation/node_modules` 外没有 `.py` 文件。

## 失败定位与修复

第一轮 `npm run build` 失败于 TypeScript 类型收窄：

- `readableJsonCount()` 的 `0 | 1` literal reduce 推断导致返回类型不匹配。
- `groupFromFixture()` 的一级目录可能被推断为 `undefined`。
- `routeDebugLoader` 返回的 `delivery_success=false`、`primary_actions_enabled=false` 未被推断为 literal false。

已通过显式 `reduce<number>`、目录 fallback 和 `false as const` 修复后重新验证通过。

第一轮 `npm run test` 失败于测试断言假设 `wave_rover_feedback_replay` 下存在 JSON fixture。实际该目录保留的是 `.jsonl` 和 `.log` 非 Python资产，不属于 JSON fixture 索引。已改为断言真实存在的 `wave_rover_hil_packet_intake` JSON fixture 分组，重新验证通过。

## 剩余风险

- 本轮只验证 PC 工作站 Node/Vue 软件链路，不证明真实 ROS2、Nav2、硬件、串口、WAVE ROVER、手机、云端或 delivery success。
- 删除旧 Python 会移除历史 Python gate 的直接可运行入口；有价值的历史材料只以非 Python fixture/README/Node 测试继续保留。
