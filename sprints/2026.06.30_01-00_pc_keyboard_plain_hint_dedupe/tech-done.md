# PC 键盘 summary 顶层文案去重

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：将 `readback_summary.keyboard.plain_hint` 从两个细字段直接拼接，改成一条面向普通用户的完整白话提示，避免重复表达“按住才动”。
- `pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/App.test.ts`：同步锁定新的顶层键盘提示文案。
- `docs/product/pc_tools_workstation.md`：记录该 summary 字段的只读语义和不触发运动接口的边界。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "Robot Control summary proxies"`，结果 `1 passed | 159 skipped`。
- 通过：`npm --prefix pc-tools/workstation run build`，结果 `tsc` 与 `vite build` 成功；Vite 仍提示既有 chunk 超过 500 kB。
- 通过：`npm --prefix pc-tools/workstation test`，结果 `2 passed`、`375 passed`。
- 通过：重启 PC API 到 `0.0.0.0:7001` 后只读请求 `GET /api/robot-control/summary`，确认 `readback_summary.keyboard.plain_hint` 返回 `可启用键盘；启用本身不发车，必须按住 W/A/S/D 或方向键才会连续低速移动，松开/失焦/切页/换方向或点停止都会停。`。

## 剩余风险

- 当前改动仅收口 PC summary 可读文案，不改变键盘启用、manual pulse、stop、Nav2、free-roam 或 `/cmd_vel` 控制链路。
