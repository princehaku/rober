# PC 雷达状态源冲突所见即所得

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏从 `read_endpoints` 同时读取 `radar_status` 与 `radar_scan_proof_latest` 的 lifecycle/freshness。
  - 当两个只读端点对雷达 lifecycle 给出相反结果时，将雷达状态降级为 `雷达待刷新`，并显示“雷达状态源不一致；先刷新雷达确认”。
  - 地图 `雷达点口径` 同步说明当前点位只作待刷新材料，不能当成实时贴图雷达点。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 `/api/radar/status=stopped` 与 `/api/radar/scan-proof/latest=running` 的回归测试，确认不会触发 radar start、manual、Nav2 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录雷达状态源冲突的普通用户口径和控制边界。

## 验证结果

- `npm test -- --testNamePattern "conflicting radar status sources|stale running lidar proof|updates the map radar marker"`：通过，3 passed。
- `npm test`：通过，2 test files / 257 tests passed。
- `npm run lint`：通过。
- `npm run build`：通过；保留既有 Vite chunk size warning。
- `git diff --check`：通过。

## 剩余风险

- 该 sprint 只修 PC 所见即所得显示，不改变上位机雷达 lifecycle、雷达驱动、Nav2、底盘或摄像头状态。
- 真实现场仍需要点击 `刷新雷达` 或检查上车服务，确认哪个只读端点代表最新状态。
