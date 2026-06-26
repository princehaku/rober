# PC 雷达启动中 marker 所见即所得修正

## Sprint 类型

sprint_type: micro

## 实际改动

- 普通首屏点击 `启动雷达` 后，在 radar lifecycle POST 未返回前，地图雷达 marker 改为 `雷达启动中，位置未读到`，不再回显上一轮 `最近障碍` 读数。
- 同步更新 marker 的可访问说明为 `等待刷新确认`，让现场明确这是启动请求飞行中，不是新的实时雷达点。
- 保留 `雷达待刷新 / 刷新中 / 雷达已运行` 对待确认或实时局部距离、点数的展示口径，避免影响已有雷达 proof 回读路径。
- 更新 PC 端产品文档，记录 2026-06-27 起启动中 marker 不使用旧 scan artifact 的口径。

## 验证结果

- 已通过：`npm test -- --testNamePattern "radar-starting marker|auto-refreshes radar proof|radar start"`；1 个 test file 通过，5 个相关用例通过。
- 已通过：`npm test`；2 个 test files 通过，260 个用例通过。
- 已通过：`npm run lint`
- 已通过：`npm run build`；Vite 仍提示单个 chunk 超过 500 kB，这是既有体积提醒，不影响构建成功。
- 已通过：`git diff --check`

## 剩余风险

- 本轮只修正 PC 可视化语义，不宣称真实雷达生命周期、定位或 Nav2 已恢复；真实运行仍要看上位机 radar refresh proof 和现场 readback。
