# PC 发车前单一安全确认

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 删除高级点动区旧的四项 HIL checklist 状态。
  - 高级点动区改为复用 `plainUnifiedSafetyConfirmed`，与普通首屏、扫图、行程、键盘手控共用同一个“人在旁边、周围安全、停止手段就绪”安全确认。
  - 点动说明从“同时满足 checklist/现场材料”改为“默认地址、一个安全确认、当前无 pending；stop 可在安全确认缺失时单独发送”，避免 UI 继续暗示额外发车预检。
- `pc-tools/workstation/test/App.test.ts`
  - 更新普通/高级诊断 smoke 断言：高级区只出现单一安全确认，不再出现“现场有人扶控并准备急停”等旧四项 checklist。
  - 扩展“一个安全确认复用”用例，确认高级点动区 checkbox 与普通移动、扫图确认同步。
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录 PC 端发车前预检已收敛为单一安全确认，底层字段名保持兼容但 UI 不再展示四项 HIL checklist。

## 验证结果

- `cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "reuses one plain safety confirmation|plain motion precheck|plain trip preflight"`
  - 通过：4 个相关用例通过。
- `cd pc-tools/workstation && npm test`
  - 通过：2 个测试文件，255 个用例通过。
- `cd pc-tools/workstation && npm run build`
  - 通过：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 成功。
  - 仍有 Vite 既有 chunk 大小提示：`dist/assets/index-*.js` 超过 500 kB；不影响本轮改动。

## 剩余风险

- 送达最终确认仍保留多项现场确认，这是送达收口 gate，不属于发车前预检。
- 代码里的请求字段仍叫 `confirm_hil_checklist`，这是为了兼容上位机 API；PC UI 已不再把它展示成多项 checklist。
