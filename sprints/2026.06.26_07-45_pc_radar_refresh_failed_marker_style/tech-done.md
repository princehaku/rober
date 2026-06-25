# 2026.06.26 07:45 PC 雷达刷新失败地图样式

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/styles.css`：将地图雷达 marker 的 `雷达刷新失败` 纳入失败视觉态，并把旧 `刷新失败` marker 选择器也归入失败态。
- `pc-tools/workstation/test/App.test.ts`：在雷达 refresh 失败用例中增加 `data-state="雷达刷新失败"` 对应 CSS 选择器断言，锁住地图标记所见即所得。
- `docs/product/pc_tools_workstation.md`：同步记录雷达刷新失败 marker 的失败视觉态契约。

## 验证结果

- `npm test -- -t "shows plain radar refresh failure reason on the map"`：通过，1 passed / 191 skipped。
- `npm run lint`：通过。
- `npm run build`：通过。
- `npm test`：通过，2 files passed，192 tests passed。
- 全量测试产生的两个旧 smoke artifact `checked_at` 副作用已恢复到既有值。

## 剩余风险

- 本轮只做 PC 前端 mock 验证，没有启动真实雷达，也没有触发真实小车运动或 HIL 上车验证。
