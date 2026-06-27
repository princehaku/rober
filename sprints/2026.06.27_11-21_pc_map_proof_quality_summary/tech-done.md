# PC Map Proof Quality Summary

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `readback_summary.map` 继续优先使用扁平 readback key。
  - 当扁平 key 缺失时，只读消费 `/api/map/proof/latest` payload 内的嵌套 proof 字段，提取 `map_quality_status`、`free_cells/map_free_cell_count` 和 `map_usable_for_navigation`。
  - 该逻辑不触发建图刷新、Nav2 goal、`/cmd_vel`、`/api/base/manual` 或任何运动控制。
- `pc-tools/workstation/test/catalog.test.ts`
  - 增加嵌套 `latest_result.proof` 地图质量 fixture，覆盖 PC summary 的兜底提取。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 PC summary 对嵌套 map proof 质量字段的只读消费边界。

## 验证结果

- `npm test -- catalog.test.ts --testNamePattern "map proof quality"`：通过，1 passed / 121 skipped。
- `npm run lint`：通过。
- `npm run build`：通过；Vite 仍有既有 chunk size warning。
- `npm test`：通过，2 test files / 286 tests passed。
- `git diff --check`：通过，无 whitespace error。
- 7001 live summary：`http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `robot_api_connection.status=readable`、`loaded_count=15`、`failed_count=0`，`readback_summary.map.status=map_once_artifact_metadata_observed`、`map_quality_status=has_free_cells`、`map_free_cell_count=421`、`map_usable_for_navigation=true`。
- 本机运行态：创建并启动用户 LaunchAgent `/Users/m1/Library/LaunchAgents/com.rober.pc.api.7001.plist`，只运行 PC API，监听 `0.0.0.0:7001`；未修改 Clash 或系统代理。

## 剩余风险

- 该 sprint 只修正 PC summary 的地图质量事实展示，不证明真实地图可导航、Nav2 已可执行、底盘轮速已非零或 delivery success。
- 若上位机未来改名质量字段，PC 仍会保守显示 `not_loaded`，不会伪造可导航状态。
