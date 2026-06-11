# 技术完成记录

- `sprint_type: micro`
- 目标：增强 `pc-tools/workstation` 默认关闭的 `高级诊断 -> 现场点动设置 / 控制边界`，让非 stop 方向按钮在材料不齐时明确展示缺项并保持禁用，材料齐时才可点击；`停止` 继续只受 `baseUrl` 和 `pending` 约束。
- 边界：不改后端安全门禁，不开放 `/cmd_vel`、NavigateToPose 或任何真实机器人控制入口；不把 `safe_to_control`、`delivery_success`、`robot_control_executed` 置真；不改 `onboard/**` 和 `docs/vendor/**`。

## 实际改动

- 调整 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue` 的非 stop 点动门禁：新增现场材料缺项判断，要求 `robotApiBaseUrl`、本地 HIL checklist、`operator_hil_material_summary` 已加载且 `operator_present/physical_clearance/emergency_stop` 与四项材料引用均满足，才允许方向按钮可点。
- 在高级诊断中补充材料缺项展示与明确提示文案，缺项时显示“材料未满足，本机不会发送点动”。
- 保持 `停止` 只受 `baseUrl` 和 `pending` 约束，不受材料缺失影响。
- 更新单测 `pc-tools/workstation/test/App.test.ts`，覆盖材料不齐禁用、缺项展示、stop 仍可用、材料齐时方向按钮可点击并继续通过固定 workstation proxy。
- 同步更新 `docs/product/pc_tools_workstation.md`，把 manual/stop 门禁说明收紧到当前实现。
- 将测试生成的 DOM smoke artifact 落盘目录切到本轮 sprint：`sprints/2026.06.11_16-45_pc_manual_motion_readiness_ui/artifacts/`，避免继续写旧 sprint artifact。

## 验证结果

- `cd pc-tools/workstation && npm run build` 通过。
- `cd pc-tools/workstation && npm run test -- --run` 通过，`2` 个 test files、`92` 个 tests 全部通过。
- `cd pc-tools/workstation && npm run lint` 通过。
- `git diff --check` 通过。
- 本轮测试产物只写入 `sprints/2026.06.11_16-45_pc_manual_motion_readiness_ui/artifacts/`，未再写旧 sprint artifact。

## 剩余风险

- 这次只验证了前端构建、单测、lint 和 diff 格式，没有覆盖真实上位机、串口、ROS 或 HIL。
- 当前门禁仍依赖 `operator_hil_material_summary` 的回传质量；如果上位机材料摘要格式漂移，需要再补对应前端测试。
