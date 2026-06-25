# PC 当前 Nav2 路线折线状态样式

sprint_type: micro

## 实际改动

- PC 普通首屏地图里的当前可执行 Nav2 路线显式锁定 `data-state=当前路线` 的蓝色实线样式，和 `最近路线` 的黄系虚线形成稳定区别。
- 在“执行图上路线”相关测试中断言当前路线折线 DOM 状态、aria 和 CSS 选择器，避免普通用户把当前可执行路线与最近旧路线看成同一种线。
- 产品文档同步记录该展示边界：只影响 PC 前端地图 WYSIWYG，不自动执行 Nav2、不调用 manual/keyboard/delivery/stop，也不调用 `/cmd_vel`。

## 验证结果

- 通过：`npm test -- -t "draws no-motion route start and end markers when no executed goal is available"`，`1 passed | 191 skipped`。
- 通过：`npm run lint`。
- 通过：`npm run build`，Vite 产物生成成功。
- 通过：`npm test`，`192 passed`。
- 通过：全量测试改写的两个旧 smoke artifact `checked_at` 已恢复到原值，未纳入本轮改动。
- 通过：`git diff --check`。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN || true`，`node ... TCP *:7001 (LISTEN)`。

## 剩余风险

- 当前仍是 PC 前端/mock 合同验证；未触发真实 Nav2 行程，未做真实小车 HIL。
