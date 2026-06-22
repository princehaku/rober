# Plain First-Jog Wheel Summary Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `plainFirstJogEvidenceSummary`。
  - 普通 `移动/导航` 卡片在 `试动一下` 返回后显示轮速证据短摘要：
    - 非零证明为 true 时显示 `轮速证据已拿到：L/R=...，运动帧=...`。
    - 已试动但非零未证明时显示当前 L/R 和运动帧数量。
    - 试动未进入时显示未采集轮速证据。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 first-jog forwarded fixture，验证普通首屏显示 wheel raw L/R 非零证据摘要。
- `docs/product/pc_tools_workstation.md`
  - 同步记录普通首屏试动后轮速摘要边界。

## 验证结果

- `npm test`
  - 通过：`Test Files 2 passed (2)`，`Tests 112 passed (112)`。
- `npm run lint`
  - 通过：`eslint .` 无报错。
- `npm run build`
  - 通过：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`。

## 剩余风险

- 本轮是 UI 摘要与测试 fixture，没有执行真实 first-jog/manual。
- wheel raw L/R 非零仍需现场运行真实 during-motion `T=1001 L/R` 采集。
- delivery success 仍不能宣称完成。
