# PC Nav2 轮速窗口诊断增强

## Sprint 类型

sprint_type: micro

## 实际改动

- 普通首屏行程证据新增 Nav2 轮速窗口诊断：当 Nav2 本次执行窗口内 `L/R=0/0` 待复验，但底盘全局只读样本已经证明过非零轮速时，文案会提示“底盘只读样本已出现非零轮速，Nav2 仍需同窗口复验”。
- 保持完整 Nav2 route proof 判定不变：全局/历史底盘非零样本不能替代 Nav2 执行窗口内的同帧 `T1001 L/R` 非零，也不会自动确认 delivery success。
- 更新 PC 端产品文档，记录“底盘轮速链路可读”和“Nav2 本次执行窗口缺同帧非零 L/R”分开展示的口径。

## 验证结果

- 已通过：`npm test -- --testNamePattern "IMU-only route arrival"`；1 个相关用例通过。
- 已通过：`npm test`；2 个 test files 通过，260 个用例通过。
- 已通过：`npm run lint`
- 已通过：`npm run build`；Vite 仍提示单个 chunk 超过 500 kB，这是既有体积提醒，不影响构建成功。
- 已通过：`git diff --check`

## 剩余风险

- 本轮只增强 PC 诊断文案，不修复真实 Nav2 执行窗口内 L/R 采样为 `0/0` 的底层问题；真实完整路线仍需要现场重新执行并读到同窗口非零 L/R 或其它受认可运动证明。
