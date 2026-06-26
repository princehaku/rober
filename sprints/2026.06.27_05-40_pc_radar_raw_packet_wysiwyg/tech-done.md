# PC 雷达 raw packet 所见即所得

- sprint_type: micro
- owner: full-stack-software-engineer
- 时间：2026-06-27 05:40

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：Robot Control summary 的 LiDAR 摘要新增 `latest_scan_proof_result_status` 与 `raw_packet_once_observed`，把上位机 `latest_proof_status=raw_packets_parsed` 这类现场状态透给普通首屏。
- `pc-tools/workstation/src/shared/contracts.ts`：同步补充 summary 合约字段。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：当雷达 lifecycle 在跑、raw packet 已观察到但地图雷达点仍为 0 时，普通事实、地图 marker、aria 和 freshness 文案明确显示“原始包已收到，暂无地图点”，不再让用户只按“刷新地图/雷达”理解。
- `pc-tools/workstation/test/App.test.ts`：把“running lidar zero fresh points”回归升级为 raw packet 已到但无 scan 点的现场口径。
- `docs/product/pc_tools_workstation.md`：记录 PC 端 raw packet WYSIWYG 边界；该状态不解锁自动驾驶，不把 raw packet 当成可用避障点。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts`（150 passed）
- 通过：`npm test -- --run test/catalog.test.ts`（112 passed）
- 通过：`npm run lint`
- 通过：`npm run build`（Vite 仅提示现有 chunk size warning）
- 通过：`git diff --check`

## 剩余风险

- 本轮是 PC summary/UI/fixture 层验证，不等于真实雷达 scan 点恢复。
- 自动驾驶无法动的剩余根因仍需要用真实上位机的 Nav2、定位、雷达点和底盘反馈窗口继续拆；本轮只把 raw packet 与 scan 点的现场状态显示清楚，避免误判。
