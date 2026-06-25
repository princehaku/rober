# 2026-06-26 03:05 PC 扫图保存后覆盖提示对齐

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏“扫图覆盖”在地图已保存且保存后的只读 preview 已成功刷新时，显示“地图已保存，地图画面已自动刷新；现在检查覆盖效果”。
  - 如果保存后 preview 未成功转发，继续保留“刷新后检查覆盖效果”的保守提示。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展 free-roam keyboard / save 流程组件测试，覆盖保存成功后覆盖 guidance 与其他保存后 WYSIWYG 状态一致。
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录保存后自动刷新状态同步到覆盖提示。
- `docs/product/pc_tools_workstation.md`
  - 记录 PC 普通首屏扫图覆盖 guidance 的保存后刷新口径。

## 验证结果

- 通过：`npm test -- -t "keeps free-roam keyboard locked until map recording starts"`
  - `Test Files 1 passed | 1 skipped (2)`
  - `Tests 1 passed | 177 skipped (178)`
- 通过：`npm run lint`
- 通过：`npm run build`
  - `vite v7.3.3 building client environment for production`
  - `dist/assets/index-Cb1WfkNI.js 473.08 kB`
- 通过：`npm test`
  - `Test Files 2 passed (2)`
  - `Tests 178 passed (178)`
- 通过：`git diff --check`
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`
  - `node 90259 ... TCP *:7001 (LISTEN)`

## 剩余风险

- 本轮只覆盖 PC 前端状态和 mock 组件测试，不触发真实上位机建图、保存地图、manual、keyboard pulse、Nav2、delivery、stop 或 `/cmd_vel`。
- 真实机器人现场仍需要 operator 在 `0.0.0.0:7001` 访问 PC 工作站后复核地图画面和覆盖效果。
