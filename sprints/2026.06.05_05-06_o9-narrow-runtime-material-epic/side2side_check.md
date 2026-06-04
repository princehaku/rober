# Side2Side Check: O9 Narrow Runtime Material Epic

## sprint_type

sprint_type: epic

## PRD 对照

| PRD 项 | 结果 | 证据 | 判断 |
| --- | --- | --- | --- |
| PC 同源 refresh 复验 | 部分完成 | `pc-tools/workstation/test/App.test.ts` 新增 same-origin + not_proven 护栏，28 tests pass | 不涨 O7；缺 PC live API smoke、hz/TF/fallback 全字段展示 |
| 远端 8787 status/runtime 复验 | 完成最小闭环 | 远端 restart/curl 返回 `fresh_scan_proof_observed=true`、hz `257.987`、TF observed、latest loaded | 关闭 02-03 remote restart/curl 缺口；不证明 continuous radar |
| continuous radar 或 SLAM `/map` | blocked | `continuous_scan_status=not_proven`，`scan_continuity_not_observed`；`/api/map/proof/latest` 404 | 不涨 O3/O9 |
| 真实/受控电梯图片 | blocked | 本地/远端未发现真实/受控 manifest，只存在 template/fixture/blocker | 不涨 O2/O9 |
| stop-first HIL 决策门 | blocked | `hil_safety_preconditions_not_met`，没有现场看护/净空/急停/授权 | 不涨 O1/O9 |

## 越界检查

- 未声明 `safe_to_control=true`。
- 未运行 `/api/base/manual`、`/cmd_vel` 或 WAVE ROVER 运动命令。
- 未声明 HIL pass、PC WASD 控车、Nav2 可用、SLAM map 完成或真实送达。
- 未把 fixture/checker/template 写成真实/受控电梯材料。
- 未因 PC App 测试护栏上调 O7。

## 结论

本轮符合“窄 Epic 不再 Micro-only readback”的流程要求，并关闭了 02-03 远端未 restart/curl 缺口。产品能力进展仍保守：只有 O8 治理可小涨；O1/O2/O3/O7/O9 不因本轮 status/readback、测试护栏或 blocker 记录上调。
