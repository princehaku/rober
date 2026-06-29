# PC 总览建图前缀去重

sprint_type: micro

## 实际改动

- 在 `pc-tools/workstation/src/server/robotControlSummary.ts` 中清理 `current_fact_plain` 的建图分组拼接：外层已经显示 `建图启动` / `建图验收` 时，去掉内层同名前缀。
- 在 `pc-tools/workstation/test/catalog.test.ts` 中新增断言，锁定总览不再出现 `建图启动：建图启动` 或 `建图验收：建图验收`。
- 在 `docs/product/pc_tools_workstation.md` 中记录该只读总览文案清理。

## 验证结果

- 已通过定向 summary 验证：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "free-roam|current_fact"`，结果 `12 passed | 148 skipped`。
- 已通过全量 PC 测试：`npm --prefix pc-tools/workstation test`，结果 `375 passed`。
- 已通过 PC build：`npm --prefix pc-tools/workstation run build`，`tsc` 与 `vite build` 通过；仅保留既有 Vite chunk size 提示。
- 已重启本地 PC API 到 `0.0.0.0:7001`，新 PID 为 `44406`。
- 已通过 7001 只读 summary live 验证：`current_fact_plain` 显示 `建图启动：未 ready` 和 `建图验收：未 ready`，不再出现 `建图启动：建图启动` 或 `建图验收：建图验收`。

## 剩余风险

- 本轮只改只读 summary 文案，不调用 free-roam、建图、manual、keyboard、Nav2、delivery、stop 或 `/cmd_vel`。
- 真实车相机首帧和雷达 fresh 缺口仍需现场硬件恢复后复验；本轮只让总览表达更清楚。
