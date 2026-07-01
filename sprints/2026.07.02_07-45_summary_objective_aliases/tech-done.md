# tech-done

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：在 `GET /api/robot-control/summary` 顶层新增四项目标短 alias：`objective_missing_ids`、`objective_next_id`、`motion_objective_complete`、`wysiwyg_objective_complete`、`precheck_objective_complete`、`mapping_objective_complete`。
- `pc-tools/workstation/src/shared/contracts.ts`：补齐上述 summary alias 类型，保证脚本读顶层字段不会变成隐式 `any` 或未声明字段。
- `pc-tools/workstation/test/robotControlSummary.test.ts`、`pc-tools/workstation/test/catalog.test.ts`：验证顶层 alias 与 `live_closure_summary.objective_audit_*` 同源，且当前状态下 motion/wysiwyg/mapping 未完成、precheck 已完成。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：记录这些字段只读、不重算、不触发任何运动。

## 验证结果

- `git diff --check`：通过。
- `npm test -- robotControlSummary.test.ts catalog.test.ts`：2 files / 191 tests passed。
- `npm run lint`：通过。
- `npm run build`：通过；仅保留 Vite chunk size warning。

## 剩余风险

- 本切片只提升 summary 顶层可读性，不执行实车 Nav2、键盘、自由移动或建图验收。
