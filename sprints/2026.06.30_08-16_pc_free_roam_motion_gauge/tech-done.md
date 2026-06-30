# PC free-roam motion gauge

sprint_type: micro

## 实际改动

- 在 PC 普通首屏自由移动 / 建图卡新增 `plain-free-roam-motion-gauge`，把低速自由移动是否可启动、是否只差安全确认、相机/雷达是否阻止自由移动、相机/雷达是否满足建图、建图记录是否 ready 和主按钮语义合成一行。
- 仪表 DOM 暴露 `data-safety-confirmed`、`data-free-move-start-ready`、`data-can-free-move-now`、`data-camera-blocks-free-motion=false`、`data-radar-blocks-free-motion=false`、`data-camera-ready-for-mapping`、`data-radar-ready-for-mapping`、`data-mapping-start-ready`、主按钮动作和固定自由移动/停止/建图 endpoint。
- 更新 PC 文档，明确该仪表只作为只读验收合同，固定 `data-sends-motion-when-clicked=false`，不会自动启动自由移动或建图。

## 验证结果

- `npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default"`：通过，1 passed / 218 skipped。
- `npm test -- --run test/App.test.ts -t "allows free-roam recording when camera source is selected but not yet frame-proven"`：通过，1 passed / 218 skipped。
- `npm test -- --run`：通过，2 test files passed，389 tests passed。
- `npm run lint`：通过，0 errors；保留 4 个既有 Vue 换行 warning。
- `npm run build`：通过，Vite 输出 `dist/assets/index-IGk476SI.js` 和 `dist/assets/index-CJ6C5-CF.css`；保留现有 chunk size warning。
- `git diff --check`：通过。

## 剩余风险

- 本轮只验证 PC Web fixture 和 DOM 合同，不触发真实自由移动、建图记录或小车运动。
- 两份历史 smoke artifact 在本轮开始前已是 dirty，本轮不纳入提交。
