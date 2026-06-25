# PC Minimal Safety Precheck Contract

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：把 `safe_command_boundary.manual_motion_entry_status` 从旧的 operator-report/HIL 多材料口径改为 `controlled_jog_requires_safety_confirmation_only`，首屏标签改为 `低速手控（勾安全确认即可）`，并把 `operator_report_preflight_required_fields` 固定为空数组。
- `pc-tools/workstation/src/shared/contracts.ts`、`pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/catalog.test.ts`：同步更新类型和测试 fixture，锁定普通低速手控/键盘手控只要求本地安全确认，不再要求 operator report 材料。
- `docs/product/pc_tools_workstation.md`：修正历史段落，明确普通 manual/keyboard pulse 不再要求 operator report preflight 或 wheel/LiDAR/视频材料完整；这些材料继续作为证据/验收项，不作为普通低速手控放行条件。

## 验证结果

- `cd pc-tools/workstation && npm test`：通过，155 tests。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过。
- 本机 PC Node 已重启到 `0.0.0.0:7001`，PID `69094`。
- 真实 PC summary 只读 smoke：`GET http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回：
  - `manual_motion_entry_status=controlled_jog_requires_safety_confirmation_only`
  - `manual_motion_entry_label=低速手控（勾安全确认即可）`
  - `non_stop_requires_confirm_hil_checklist=true`
  - `non_stop_requires_operator_report_preflight=false`
  - `operator_report_preflight_required_fields=[]`
  - `safe_to_control=false`
  - `delivery_success=false`

## 剩余风险

- 本轮只收敛普通低速手控/键盘手控的预检合同；未执行真实发车、Nav2 route execution、delivery success、wheel raw L/R 非零或自由建图。
- first-jog 专用入口仍保留视觉材料 gate，用于首次运动证据闭环；本轮没有改 first-jog 的门禁。
