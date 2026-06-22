# Delivery Preserve Motion Claims

sprint_type: micro

## 实际改动

- PC 送达草稿和最终送达 operator report 会继承已有 motion evidence 材料。
- 只有 Robot Control summary 中 `operator_hil_material_summary.wheel_feedback` / `lidar_delta` 已明确为 `true; ref=...` 时，才把 `wheel_feedback_lr_nonzero_proven + wheel_feedback_ref`、`physical_motion_lidar_delta_proven + scan_delta_ref` 带入送达 report。
- 没有已有 ref 时仍保持 false/缺 ref，不伪造 wheel raw L/R、LiDAR delta 或 delivery success。
- 补充 Vue 测试，覆盖送达草稿和最终送达确认都不会把已有 wheel/LiDAR motion claims 覆盖成 false。
- 更新 `docs/product/pc_tools_workstation.md` 记录继承边界。

## 验证结果

- 通过：`npm test`，Vitest `2 passed (2)`，`112 passed (112)`。
- 通过：`npm run lint`，ESLint 无报错。
- 通过：`npm run build`，`tsc` 与 Vite production build 通过。
- 通过：`git diff --check`。

## 当前真实证据

- 当前真实上位机 operator report 仍是 delivery draft，`wheel_feedback_lr_nonzero_proven=false`、`physical_motion_lidar_delta_proven=false`、`delivery_success=false`。
- 当前真实只读底盘反馈样本仍为 L/R=`0/0`，`wheel_feedback_lr_nonzero_proven=false`。

## 剩余风险

- 本轮只修复 PC report 继承逻辑；没有执行真实 first-jog、键盘手控或送达确认。
- 真实 wheel raw L/R 非零仍需要后续现场 first-jog/manual motion readback 产生 `true; ref=...`，之后本逻辑才能防止送达草稿覆盖该材料。
