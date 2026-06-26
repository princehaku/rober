# PC 送达失败地图所见即所得

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏在本页最终 `delivery/complete` 返回失败时，将地图终点 marker 从普通 `已到达` 切到 `送达确认失败`。
  - 地图 caption 同步显示失败短原因，例如 `delivery_gate_rejected`，避免用户误判为已送达或普通到达。
  - 失败态只读取本次 complete 响应，不让 latest 的旧失败记录污染当前地图。
- `pc-tools/workstation/src/styles.css`
  - 新增 `送达确认失败` 终点 marker 样式，和已送达/确认中区分。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 delivery gate 拒绝用例，锁定地图 marker、caption、送达区未通过文案，以及不触发 manual、keyboard、stop 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`
  - 补充 2026-06-26 11:30 的 PC 端送达失败 WYSIWYG 行为契约。

## 验证结果

- `npm test -- -t "shows delivery confirmation failure on the map after final completion is rejected|shows delivery confirmation pending on the map while final completion is in flight"`：通过，2 passed。
- `npm run lint`：通过。
- `npm run build`：通过。
- `npm test`：通过，2 test files passed，196 tests passed。
- 完整测试会刷新两个历史 DOM smoke artifact 的 `checked_at`，本轮已恢复为原始时间戳，避免无关 diff。

## 剩余风险

- 本轮只做 PC 前端 mock 验证，不触发真实机器人运动，不证明真实上位机 delivery gate 的现场数据质量。
