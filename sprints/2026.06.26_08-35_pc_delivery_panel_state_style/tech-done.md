# PC 送达面板状态样式

sprint_type: micro

## 实际改动

- PC 普通首屏 `任务收口` 面板新增 `data-state=已送达/确认中/检查中/需复验/...`，让送达状态不只存在于内部 chip 文案里。
- `最终确认` 面板新增 `data-state=已完成/确认中/待确认/...`，提交中和已完成态有独立外框样式。
- 测试覆盖送达成功时 `任务收口=已送达`、`最终确认=已完成`，以及最终确认提交中 `任务收口/最终确认=确认中`。
- 产品文档同步记录该展示边界：只影响 PC 前端 WYSIWYG，不自动提交送达、不执行 Nav2、不发送 manual/keyboard pulse、stop，也不调用 `/cmd_vel`。

## 验证结果

- 通过：`npm test -- -t "marks the map goal as delivered only when delivery success matches the current Nav2 route|shows delivery confirmation pending on the map while final completion is in flight"`，`2 passed | 190 skipped`。
- 通过：`npm run lint`。
- 通过：`npm run build`，Vite 产物生成成功。
- 通过：`npm test`，`192 passed`。
- 通过：全量测试改写的两个旧 smoke artifact `checked_at` 已恢复到原值，未纳入本轮改动。
- 通过：`git diff --check`。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN || true`，`node ... TCP *:7001 (LISTEN)`。

## 剩余风险

- 当前仍是 PC 前端/mock 合同验证；未触发真实 Nav2 行程、真实送达确认或真实小车运动。
