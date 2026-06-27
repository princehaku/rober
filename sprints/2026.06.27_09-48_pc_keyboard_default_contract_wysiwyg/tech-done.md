# PC 键盘默认合同当前事实对齐

sprint_type: micro

## 实际改动

- `pc-tools/workstation/test/App.test.ts`
  - 默认 Robot Control summary fixture 补齐真实后端已有的键盘 bounded pulse 合同：
    `keyboard_control_mode=bounded_repeating_manual_pulse`、`keyboard_reuses_manual_gate=true`、
    `keyboard_control_start_ready=true`、键盘 manual/stop 代理和 pulse 时间边界。
  - 默认普通首屏断言从“还差：键盘入口、安全确认”改为“还差：安全确认”。
  - 默认“当前事实”断言从“键盘：先复查手控条件”改为“键盘：勾安全确认后可启用”。
  - 缺键盘合同专项测试显式删除合同字段，继续覆盖 fail-closed 行为。
- `docs/product/pc_tools_workstation.md`
  - 同步记录默认 fixture 与真实 summary 的键盘口径：键盘入口已存在时，只剩安全确认，不误报入口缺失。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- App.test.ts --testNamePattern "Robot Control V1|键盘|keyboard|安全确认"`
  - `Test Files 1 passed`
  - `Tests 18 passed | 143 skipped`
- 通过：`cd pc-tools/workstation && npm run lint`
- 通过：`cd pc-tools/workstation && npm run build`
  - Vite 仍提示单 chunk 超过 500 kB，这是既有打包体积 warning，不影响本轮功能。
- 通过：`cd pc-tools/workstation && npm test`
  - `Test Files 2 passed`
  - `Tests 282 passed`
- 通过：`git diff --check`
- 通过：确认 `0.0.0.0:7001` 仍监听。
  - `node ... TCP *:7001 (LISTEN)`
- live 只读确认：`GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787`
  - `keyboard_control_start_ready=true`
  - `keyboard_control_mode=bounded_repeating_manual_pulse`
  - `keyboard_jog_duration_ms=240`
  - `keyboard_jog_interval_ms=260`
  - `keyboard_reuses_manual_gate=true`
  - `manual_motion_entry_status=controlled_jog_requires_safety_confirmation_only`
  - `hil_checklist` 只有 `operator_safety_confirmed`

## 剩余风险

- 本轮不执行真实键盘手控，不产生 wheel raw L/R 新证据。
- PC 键盘连续手控的真实完成仍需要现场勾安全确认后按住方向键，看到连续 pulse、非零 L/R 和 release stop 成功。
