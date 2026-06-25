# 2026.06.26 07:50 PC 实时画面框状态样式

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/styles.css`：实时画面 16:9 frame 根据 `data-state` 显示可见、等待/处理中、偏暗/失败三类视觉态；等待类 overlay 也使用独立遮罩，避免普通用户把连接中/等待第一帧误读为普通黑屏。
- `pc-tools/workstation/test/App.test.ts`：在既有画面等待/关闭、画面偏暗、首帧失败用例中增加 CSS selector 断言，锁住画面框所见即所得。
- `docs/product/pc_tools_workstation.md`：同步记录实时画面 frame 的状态视觉契约和安全边界。

## 验证结果

- `npm test -- -t "shows camera closing state while peer cleanup is still pending"`：通过，1 passed / 191 skipped。
- `npm test -- -t "marks near-black preview as 画面偏暗 instead of optimistic 已打开|keeps camera source first-frame failure visible while streaming waits for a drawable frame"`：通过，2 passed / 190 skipped。
- `npm run lint`：通过。
- `npm run build`：通过。
- `npm test`：通过，2 files passed，192 tests passed。
- 全量测试产生的两个旧 smoke artifact `checked_at` 副作用已恢复到既有值。

## 剩余风险

- 本轮只做 PC 前端 mock 验证，不打开真实 WebRTC，不触发真实小车运动，也不覆盖 HIL 上车验证。
