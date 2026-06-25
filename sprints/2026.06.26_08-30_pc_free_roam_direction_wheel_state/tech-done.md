# PC 扫图方向轮速状态

sprint_type: micro

## 实际改动

- PC 普通首屏地图里的扫图方向 marker 新增 `data-wheel-state=非零已读到/等待非零/未读取`，把按住键盘扫图时的 wheel raw L/R 证据从短文案提升为可测试 DOM 状态。
- 样式新增 `非零已读到` 和 `等待非零` 两种轮速证据视觉态，避免 operator 只靠阅读 marker 文案判断轮速材料。
- 测试覆盖按住前进扫图时 `data-wheel-state=非零已读到`、aria 和 CSS 选择器。
- 产品文档同步记录该展示边界：只消费既有 keyboard manual pulse 摘要，不额外发送 manual/stop，不执行 Nav2/delivery，也不调用 `/cmd_vel`。

## 验证结果

- 通过：`npm test -- -t "keeps free-roam keyboard locked until map recording starts"`，`1 passed | 191 skipped`。
- 通过：`npm run lint`。
- 通过：`npm run build`，Vite 产物生成成功。
- 通过：`npm test`，`192 passed`。
- 通过：全量测试改写的两个旧 smoke artifact `checked_at` 已恢复到原值，未纳入本轮改动。
- 通过：`git diff --check`。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN || true`，`node ... TCP *:7001 (LISTEN)`。

## 剩余风险

- 当前仍是 PC 前端/mock 合同验证；未触发真实小车运动，未做真实 WAVE ROVER wheel raw L/R HIL。
