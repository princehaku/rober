# 2026-06-26 03:20 PC 扫图保存后步骤条收口

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 保存地图后，普通首屏“扫地式建图”步骤条不再继续提示低速扫图可手控。
  - `低速扫图` 在保存后显示已完成，并提示“扫图已收口，检查地图效果”。
  - `停止收口` 在保存后显示已完成，并提示“扫图已停止并保存”。
  - `保存地图` 在保存后 preview 已自动刷新时提示“已保存，地图画面已自动刷新，可以检查效果”。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展 free-roam 保存流程断言，覆盖保存后的步骤条收口文案。
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录保存后步骤条收口的用户流程口径。
- `docs/product/pc_tools_workstation.md`
  - 记录 PC 普通首屏保存后步骤条 WYSIWYG 状态。

## 验证结果

- 通过：`npm test -- -t "keeps free-roam keyboard locked until map recording starts"`
  - `Test Files 1 passed | 1 skipped (2)`
  - `Tests 1 passed | 177 skipped (178)`
- 通过：`npm run lint`
- 通过：`npm run build`
  - `vite v7.3.3 building client environment for production`
  - `dist/assets/index-DgONWvSB.js 473.24 kB`
- 通过：`npm test`
  - `Test Files 2 passed (2)`
  - `Tests 178 passed (178)`
- 通过：`git diff --check`
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`
  - `node 90259 ... TCP *:7001 (LISTEN)`

## 剩余风险

- 本轮只覆盖 PC 前端步骤条和 mock 组件测试，不触发真实上位机建图、保存地图、manual、keyboard pulse、Nav2、delivery、stop 或 `/cmd_vel`。
- 真实现场仍需要 operator 在 `0.0.0.0:7001` 页面上复核保存后的地图画面、覆盖效果和可导航状态。
