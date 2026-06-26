# PC Free Move Label / Mapping Split

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 当上车端 `free_roam_autonomy_start_ready=true` 但完整自动扫图未 ready 时，summary label 从“自动扫图（勾确认后可启动）”改为“自由移动（勾确认后可启动）”。
  - fallback gate 的下一步从“开始自动扫图”改为“开始自由移动”，避免把低速自由移动误说成可验收建图。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏自动扫图准备区按 `plainFreeRoamMappingQualityReady` 分层显示：相机/雷达未 ready 时按钮为“开始自由移动（低速）”，相机和雷达 ready 后才显示“开始自动扫图（低速）”。
  - runtime、下一步和 readiness 提示同步使用“自由移动/自动扫图”两套文案，但不改变后端 gate，不新增任何 PC 侧运动 endpoint。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 更新 `free_roam_autonomy_label` 字面量合同。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/catalog.test.ts`
  - 回归覆盖 radar stale、camera no first frame、start-ready artifact-only 和完整 ready 自动扫图路径。
- `docs/product/pc_tools_workstation.md`
  - 记录普通 PC 界面自由移动和建图验收的命名边界。

## 验证结果

- 已通过：`cd pc-tools/workstation && npm test -- --testNamePattern "free-roam|free movement|free-roam autonomy|free-roam recording|low-speed free-roam|start-ready free-roam|mapping acceptance"`，`Tests 25 passed | 235 skipped (260)`。
- 已通过：`cd pc-tools/workstation && npm test`，`Tests 260 passed (260)`。
- 已通过：`cd pc-tools/workstation && npm run lint`。
- 已通过：`cd pc-tools/workstation && npm run build`。
  - 保留既有 Vite chunk size warning：`Some chunks are larger than 500 kB after minification`。
- 已通过：`git diff --check`。

## 剩余风险

- 本轮只修普通 PC 界面和 summary 命名，不执行真实低速移动，不证明相机/雷达硬件已 ready。
- 当前 live 上位机仍显示相机首帧失败、雷达 stopped；因此页面应显示可自由移动但不可按可验收建图收口。
