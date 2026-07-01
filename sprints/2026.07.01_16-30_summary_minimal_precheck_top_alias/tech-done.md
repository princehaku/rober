# Summary Minimal Precheck Top Alias

## Sprint 类型

sprint_type: micro

## 实际改动

- `GET /api/robot-control/summary` 顶层新增发车前最小预检 alias：`minimal_precheck_safety_only`、`safety_confirm_required_for_motion`、`live_motion_runbook_minimal_precheck_safety_only`、`live_motion_runbook_safety_confirm_required` 和 `live_motion_runbook_minimal_precheck_plain`。
- 这些字段直接镜像 `live_closure_summary`，让现场脚本无需展开嵌套字段即可确认“执行运动只需勾现场安全确认；相机、雷达和现场报告不作为额外发车前置”。
- 更新 summary 合同、服务端返回、定向测试、catalog live-summary 合同测试和 PC 工作站产品文档。

## 验证结果

- 通过：`git diff --check`
- 通过：`npm test -- --run test/robotControlSummary.test.ts`，结果 `1 passed / 9 passed`。
- 通过：`npm test -- --run test/catalog.test.ts -t "live-summary"`，结果 `1 passed / 1 passed / 180 skipped`。
- 通过：`npm test`，结果 `3 passed / 421 passed`。
- 通过：`npm run lint`。
- 通过：`npm run build`；仅保留 Vite 既有 chunk size warning。
- 通过：重启 `0.0.0.0:7001` 后，用只读 `GET /api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787` 确认顶层最小预检 alias 非空：`minimal_precheck_safety_only=true`、`safety_confirm_required_for_motion=true`、`live_motion_runbook_minimal_precheck_safety_only=true`、`live_motion_runbook_safety_confirm_required=true`，且 `live_motion_runbook_minimal_precheck_plain=发车前预检已精简：执行运动只需勾现场安全确认；相机、雷达和现场报告不作为额外发车前置。`

## 剩余风险

- 本轮只增加只读 summary alias，不自动勾选安全确认，不执行 Nav2、manual、keyboard、free-roam、建图、delivery、stop 或 `/cmd_vel`。
- 完整 motion 目标仍需现场在安全确认后复验同窗口 wheel L/R 非零、delivery success、键盘按住窗口轮速和自由移动启动读回。
