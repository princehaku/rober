# PC free-roam 建图雷达 fresh 交叉校验

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - free-roam runtime gate 若声明 `lidar_fresh=ready`，PC summary 仍会用同轮 `/api/radar/status` 和 `/api/radar/scan-proof/latest` 的 `latest_scan_proof_fresh` 复核。
  - 如果雷达 readback 没证明 fresh，则把 `lidar_fresh` gate 降为 `not_proven`，并写入 `mapping_missing`。
  - 自由移动启动 readiness 不受影响；只影响建图验收口径。
- `pc-tools/workstation/test/catalog.test.ts`
  - 增加 runtime 旧 gate 与雷达 stale readback 冲突的合同测试。
- `docs/product/pc_tools_workstation.md`
  - 同步记录建图 gate 的雷达 fresh 交叉校验和安全边界。

## 验证结果

- `npm test -- --run catalog.test.ts -t "keeps stale radar readback in free-roam mapping gaps even when runtime gate is old-ready"`
  - 结果：通过，`1 passed | 123 skipped`。
- `npm test`
  - 结果：通过，`2 passed`，`288 passed`。
- `npm run build`
  - 结果：通过，生成 `dist/`；Vite 仍提示单个 chunk 超过 500 kB，这是既有打包体积 warning，不影响本轮 summary 交叉校验。
- PC API 重启和 live 只读复核
  - `npm run api:public` 已重新启动，`lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node` 监听 `*:7001`。
  - live summary 返回 `mapping_missing=camera_first_frame,lidar_fresh,mapping_active,fresh_map_preview`，`lidar_fresh` gate 为 `not_proven`，证据为“雷达最新扫描未刷新”。

## 剩余风险

- 本轮不触发真实雷达刷新或 free-roam start，不发送 manual/keyboard/Nav2/delivery/stop 或 `/cmd_vel`。
- live 当前雷达仍是 `latest_proof_stale_while_lifecycle_running`；修正后 PC 会把它作为建图缺口展示，但真实 fresh scan 仍需现场刷新雷达证明。
