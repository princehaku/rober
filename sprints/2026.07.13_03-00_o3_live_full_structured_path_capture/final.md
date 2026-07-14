# Final - O3 Live Full Structured Path Capture

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_03-00_o3_live_full_structured_path_capture/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-algorithm-engineer`
- Product status: accepted with conservative no-motion boundary

## 用户价值和产品北极星

北极星是让普通手机用户最终可以发起一条可验证、可复盘、可送达的固定路线送垃圾任务。本轮没有进入送达执行，但把上一轮
“旧 21:57 artifact 只有 partial stdout-tail poses”推进成 fresh same-run 28-pose structured path material，减少后续 fixed-route / route-intent consumer 对历史材料的依赖。

## Product Acceptance Verdict

Product 接受本轮为 O3/O1 strict no-motion fresh structured planner path material。

接受事实：

- `fresh_live_artifact_used=true`
- `historic_21_57_artifact_reused_as_live_proof=false`
- `path_generated=true`
- `path_point_count=28`
- `path_structured_pose_count=28`

保守拒绝：

- 不接受为 original `path_structured_pose_count=21` target achieved。
- 不接受为 route execution、fixed-route movement、NavigateToPose、controller/BT、`/cmd_vel`、`/api/base/manual`、WAVE ROVER UART、delivery/operator acceptance、HIL、safe-to-control 或 O5 production/external evidence。

Exact blocker:

```text
expected_21_structured_pose_count_not_reproduced_current_live_returned_28_after_map_bounds_adaptation
```

## OKR 映射和 KR 决策

- O5：继续约 `85%`。本轮没有真实 external production evidence，不调整。
- O1：继续约 `94%`。本轮是 additive planner-only no-motion material，不新增 HIL、safe-to-control、route execution 或 delivery evidence。
- O6/O7：继续约 `93%`。本轮没有 archive/readback 或 PC consumer 的新接入。
- KR archive：`不归档`。本轮没有完成、替换、取消或过期 KR。
- 方向判断：继续 O3/O1 no-motion live material lane，但下一轮必须消费 28-pose artifact 或重跑当前 AMCL/map state，不再重复 route-intent/readiness packaging。

## 本轮核心抓手和实际改动

Algorithm worker 产出 fresh same-run strict no-motion runtime material，并写入：

- `sprints/2026.07.13_03-00_o3_live_full_structured_path_capture/artifacts/algorithm/live_full_structured_path_capture_summary.json`
- `sprints/2026.07.13_03-00_o3_live_full_structured_path_capture/tech-done.md`

Product closeout 写入：

- `sprints/2026.07.13_03-00_o3_live_full_structured_path_capture/side2side_check.md`
- `sprints/2026.07.13_03-00_o3_live_full_structured_path_capture/final.md`
- `sprints/2026.07.13_03-00_o3_live_full_structured_path_capture/artifacts/product/product_acceptance_live_full_structured_path_capture.json`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## Product 验证结果

- `python3 -m json.tool .../live_full_structured_path_capture_summary.json >/tmp/product_live_full_structured_path_capture_summary.pretty.json`：通过，无输出。
- Product 结构断言：通过，输出 `product_live_full_structured_path_capture_acceptance_ok`。
- Anchor `rg`：通过，命中 `2026-07-13 03:00`、`live_full_structured_path_capture`、`path_structured_pose_count=28`、exact blocker、`不归档` 和 `O5`。
- Scoped `git diff --check`：通过，无输出。

Algorithm worker 验证来自 `tech-done.md`：

- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py`：通过。
- `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper`：`Ran 140 tests in 2.292s` / `OK`。
- summary `json.tool`：通过。
- safety invariant：`live_full_structured_path_capture_safety_ok`。
- scoped `git diff --check`：通过。

## 需要做什么和责任 Engineer

下一轮 owner：`robot-algorithm-engineer`。

验收口径：

1. 首选消费本轮 28-pose structured artifact，接入 fixed-route / route-intent consumer，并证明 consumer 不再依赖旧 21:57 partial stdout-tail。
2. 若仍坚持 21-pose target，则先用当前 live AMCL/map state 复跑，避免 `map_bounds_adapted_no_motion_planner_probe`。
3. 只有出现 route execution、delivery/operator acceptance、current live HIL、safe-to-control 或 O5 production evidence，才考虑 OKR 百分比上调或 KR 归档。

## 剩余风险

- 28-pose material 与原始 21-pose expectation 不一致，可能需要 consumer 兼容可变 path shape。
- 该 artifact 是 planner-only no-motion proof，不证明机器人可以执行路线或安全运动。
- safety/control/delivery/HIL flags 全部为 false，仍不能启用任何运动或交付声明。
- O5 仍被真实 external production evidence blocker 锁住，本轮没有 O5 增量。
