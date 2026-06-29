# 2026.06.30 05:38 PC Radar Panel Map Marker Contract

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `plainRadarMapDomEvidence`，雷达卡复用地图卡的贴图事实，避免雷达卡和地图卡出现不同口径。
  - 普通首屏雷达卡直接暴露地图 marker WYSIWYG 合同：
    - `data-radar-map-points-visible`
    - `data-radar-map-point-count`
    - `data-radar-map-source-point-count`
    - `data-radar-map-frame-id`
    - `data-radar-map-source`
    - `data-radar-map-overlay-status`
    - `data-radar-start-map-refresh-required`
    - `data-radar-start-map-refresh-pending`
    - `data-radar-start-map-refresh-failed`
    - `data-radar-start-map-refresh-complete`
    - `data-radar-old-points-suppressed`
    - `data-radar-map-marker-wysiwyg-endpoint=/api/robot-control/map/preview`
- `pc-tools/workstation/test/App.test.ts`
  - 扩展雷达启动后自动刷新测试，覆盖雷达卡自己能证明地图点已显示、同轮地图刷新已 complete。
  - 扩展 not-current 旧点测试，覆盖雷达卡自己能证明旧雷达来源点已被抑制、未冒充当前地图点。
- `pc-tools/README.md`
  - 记录雷达卡地图 marker WYSIWYG DOM 合同。
- `docs/product/pc_tools_workstation.md`
  - 同步普通用户雷达卡验收口径。

## 验证结果

- `npm test -- test/App.test.ts -t "auto-refreshes radar proof after plain radar start reports ok"`：通过，1 passed / 218 skipped。
- `npm test -- test/App.test.ts -t "honors not-current map radar overlay summary instead of redrawing old proof points"`：通过，1 passed / 218 skipped。
- `npm test -- --run`：通过，2 个 test files、389 个 tests 全部通过。
- `npm run build`：通过，Vite 仍有既有 bundle size warning。
- `git diff --check`：通过，无 whitespace 错误。
- PC Node `0.0.0.0:7001`：已重启，`lsof` 显示 `node` PID `38958` 监听 `TCP *:7001`。
- `curl -fsS http://127.0.0.1:7001/`：通过，返回当前构建入口 `/assets/index-BPUOX0MM.js` 和 `/assets/index-Qsyb8IAr.css`。
- `curl -fsS http://127.0.0.1:7001/assets/index-BPUOX0MM.js | rg -q "data-radar-start-map-refresh-complete"`：通过，JS bundle 包含启动后地图刷新完成合同。
- `curl -fsS http://127.0.0.1:7001/assets/index-BPUOX0MM.js | rg -q "data-radar-old-points-suppressed"`：通过，JS bundle 包含旧点抑制合同。
- `curl -fsS http://127.0.0.1:7001/assets/index-BPUOX0MM.js | rg -q "data-radar-map-marker-wysiwyg-endpoint"`：通过，JS bundle 包含固定地图 marker 验收入口。

## 剩余风险

- 本轮只补 PC Web 侧只读 DOM 合同和 mock 测试，没有真实启动雷达、没有刷新真实地图、没有执行 Nav2、没有发送 manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。
- 真机上雷达点能否贴到地图仍取决于上位机 `/api/robot-control/map/preview` 同轮返回 map-frame 位姿和 radar overlay 点。
