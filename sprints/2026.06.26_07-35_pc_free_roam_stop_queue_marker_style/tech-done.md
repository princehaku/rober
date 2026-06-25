# 2026.06.26 07:35 PC 自由扫图停止排队地图样式

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/styles.css`：将自由扫图地图 marker 的 `auto_stop_queued` 状态纳入等待/警示视觉态，避免 operator 点击自动扫图停止并排队后退回默认灰色 marker。
- `pc-tools/workstation/test/App.test.ts`：在“start pending 时点击停止自动扫图”用例中增加 `data-state="auto_stop_queued"` 和 CSS 选择器断言，锁定地图所见即所得状态。
- `docs/product/pc_tools_workstation.md`：同步记录 `停止已排队` 地图 marker 的视觉态与测试契约。

## 验证结果

- `npm test -- -t "queues free-roam autonomy stop while the start request is still pending"`：通过，1 passed / 191 skipped。
- `npm run lint`：通过。
- `npm run build`：通过。
- `npm test`：通过，2 files passed，192 tests passed。
- 全量测试产生的两个旧 smoke artifact `checked_at` 副作用已恢复到既有值。

## 剩余风险

- 本轮只做 PC 前端 mock 验证，没有触发真实小车运动，也没有做 HIL 上车验证。
- `auto_stop_queued` 仅保证排队停止期间地图 marker 有明确等待/警示视觉态；真实上车端 stop 响应链路沿用上一轮已实现逻辑。
