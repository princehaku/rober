# 2026.06.30 05:46 PC Mapping Sensor DOM Contract

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 扩展 `PlainFreeRoamDomEvidence`，让自由移动 / 建图主面板直接暴露建图传感器事实。
  - `plain-free-roam-mapping` 新增 DOM 合同：
    - `data-camera-current-frame-visible`
    - `data-camera-current-mjpeg-frame-visible`
    - `data-camera-current-video-frame-visible`
    - `data-camera-source-first-frame-ready`
    - `data-camera-source-readiness`
    - `data-camera-shared-preview-single-upstream`
    - `data-camera-shared-preview-client-count`
    - `data-radar-fresh-for-mapping`
    - `data-radar-map-points-visible`
    - `data-radar-map-point-count`
  - 建图入口现在能直接证明“相机源首帧 + 雷达新鲜后可建图”，同时区分“源首帧 ready”和“本页当前已显示画面”。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展默认普通首屏测试，覆盖建图主面板上相机/雷达未 ready 的 DOM 证据。
  - 扩展相机和雷达 ready 后的建图启动测试，覆盖建图主面板上 ready DOM 证据。
- `pc-tools/README.md`
  - 记录建图主面板传感器 DOM 合同。
- `docs/product/pc_tools_workstation.md`
  - 同步普通用户建图验收口径。

## 验证结果

- `npm test -- test/App.test.ts -t "Robot Control V1 by default"`：通过，1 passed / 218 skipped。
- `npm test -- test/App.test.ts -t "starts free-roam autonomy through the fixed proxy only after ready readback and safety confirmation"`：通过，1 passed / 218 skipped。
- `npm test -- --run`：通过，2 个 test files、389 个 tests 全部通过。
- `npm run build`：通过，Vite 仍有既有 bundle size warning。
- `git diff --check`：通过，无 whitespace 错误。
- PC Node `0.0.0.0:7001`：已重启，`lsof` 显示 `node` PID `55258` 监听 `TCP *:7001`。
- `curl -fsS http://127.0.0.1:7001/`：通过，返回当前构建入口 `/assets/index-DXZtNgT4.js` 和 `/assets/index-Qsyb8IAr.css`。
- `curl -fsS http://127.0.0.1:7001/assets/index-DXZtNgT4.js | rg -q "data-camera-source-first-frame-ready"`：通过，JS bundle 包含建图相机源首帧合同。
- `curl -fsS http://127.0.0.1:7001/assets/index-DXZtNgT4.js | rg -q "data-radar-fresh-for-mapping"`：通过，JS bundle 包含建图雷达 fresh 合同。
- `curl -fsS http://127.0.0.1:7001/assets/index-DXZtNgT4.js | rg -q "data-camera-shared-preview-single-upstream"`：通过，JS bundle 包含共享预览单上游合同。

## 剩余风险

- 本轮只补 PC Web 侧只读 DOM 合同和 mock 测试，没有真实启动建图、自由移动、Nav2、manual、keyboard、delivery、stop 或 `/cmd_vel`。
- 真机建图是否可验收仍取决于上位机相机首帧、雷达新鲜扫描、地图记录状态和同轮地图预览。
