# Minimal Precheck Safety Confirm Alias

- sprint_type: micro
- 时间：2026-07-02 15:05 CST
- Owner：User Touchpoint Full-Stack Engineer

## 实际改动

- `RobotControlSummaryResponse` 新增 `current_minimal_precheck_pack_safety_confirm_required`，与 `current_minimal_precheck_pack_requires_safety_confirm` 同源，避免现场脚本读取同义字段时得到 `null`。
- 普通 PC `plain-current-minimal-precheck-pack` 新增 DOM 属性 `data-safety-confirm-required`。
- 补充 `robotControlSummary` 和 `App` 测试断言。
- 更新 `docs/product/pc_tools_workstation.md` 和 `pc-tools/README.md`。

## 验证结果

- `npm test -- test/robotControlSummary.test.ts`：通过，10 tests。
- `npm test -- test/App.test.ts`：通过，237 tests。
- `npm run build`：通过，Vite chunk size warning 为既有体积提醒。
- `git diff --check`：通过。
- 重启 PC API 后，`GET /api/robot-control/summary` 返回 `current_minimal_precheck_pack_status=safety_confirm_only`、`current_minimal_precheck_pack_safety_confirm_required=true`、`current_minimal_precheck_pack_minimal_precheck_safety_only=true`，相机/雷达/现场报告/路线 WYSIWYG 发车前置均为 `false`，点击展示包仍不发车。

## 剩余风险

- 目标仍未完成：Nav2 完整行程、键盘连续手控、自由移动仍需要现场安全确认后的真实运动读回。
- 相机仍缺首帧，建图仍被 `camera_first_frame` 阻塞。
- 本轮只改 summary/DOM 合同，未发送任何运动、Nav2、manual、keyboard、free-roam、建图、delivery 或 stop 请求。
