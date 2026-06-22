# Delivery Closure Checklist

sprint_type: micro

## 实际改动

- PC 高级诊断送达确认区新增 `送达收口检查`，把 delivery latest/check/complete 的缺项与当前表单状态合并显示。
- 收口摘要按六项展示 `已满足/未满足`：Nav2 路线执行成功、现场报告 ready_for_review、现场观察到运动/到达、现场观察到停止、确认已投放/送达、视频与 route/map ref。
- 摘要只做 operator 提示，不自动勾选最终 checklist，不提交 operator report，不调用 delivery complete，也不把 `delivery_success` 提升为 true。
- 补充 Vue 测试，覆盖复算送达缺口后收口摘要能把 `operator_report_ready_for_review`、`operator_observed_motion`、`operator_observed_stop`、`structured_hil_claims.delivery_success` 翻译成未满足项。
- 更新 `docs/product/pc_tools_workstation.md` 记录送达收口检查边界。

## 验证结果

- 通过：`npm test`，Vitest `2 passed (2)`，`112 passed (112)`。
- 通过：`npm run lint`，ESLint 无报错。
- 通过：`npm run build`，`tsc` 与 Vite production build 通过。
- 通过：`git diff --check`。

## 当前真实证据

- 真实上位机 `GET /api/nav2/goal/execution/latest` 返回 `status=goal_succeeded`、`evidence_ref=o11-nav2-goal-execution-1782099547218`、`feedback_sample_count=8`。
- 真实上位机 `GET /api/delivery/latest` 返回 `delivery_success=false`，缺 `confirm_delivery_completion`、`operator_report_ready_for_review`、`operator_observed_motion`、`operator_observed_stop`、`structured_hil_claims.delivery_success`。

## 剩余风险

- 本轮没有执行真实送达确认；delivery success 仍依赖现场 operator 完成最终确认并由上位机 delivery gate 接受。
- UI 收口摘要只降低误操作成本，不能替代视频、route/map、观察运动/停止和投放/送达确认。
