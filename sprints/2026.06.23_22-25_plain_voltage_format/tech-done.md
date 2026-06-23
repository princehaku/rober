# 2026.06.23 22:25 Plain Voltage Format

sprint_type: micro

## 实际改动

- PC 普通首屏新增 `formatPlainVoltage`，把真实上位机 `feedback_voltage_v` 的长小数格式化为最多两位小数。
- `本轮进度` 和 `轮速记录` 普通提示继续显示当前 `L/R=0/0`、T1001 帧数和供电读数，但不再把 `12.43049049V` 这类工程长小数暴露给普通用户。
- 高级诊断和 PC proxy contract 保持原始值，不把电压外推成 wheel raw L/R 非零、运动、Nav2 或 delivery success 证明。
- 更新 `docs/product/pc_tools_workstation.md` 记录普通首屏电压展示口径。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- -t "wheel L/R"`，3 个目标测试通过。
- 通过：`cd pc-tools/workstation && npm test`，2 个 test files、145 个测试通过。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只改善普通 PC 界面读数展示；真实上位机当前仍读到 wheel L/R=0/0，wheel raw L/R 非零、完整 Nav2 路线执行、delivery success 和 PC 键盘连续手控仍需要后续 operator 显式执行与验证。
