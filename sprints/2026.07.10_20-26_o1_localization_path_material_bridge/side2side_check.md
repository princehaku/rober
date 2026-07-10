# O1 Localization Path Material Bridge Side2Side Check

## sprint_type

sprint_type: epic

## Product 验收结论

Product closeout 判定：本 sprint 满足 O1 `localization_path_material_bridge` 的保守验收口径，可以作为 O1 从约 `89%` 上调到约 `90%` 的证据，但不能作为 HIL、控制安全、送达成功或同 run 路径生成成功证据。

本轮价值不是把历史材料包装成成功路线，而是把 `38_pc_summary_after_map_fix.json` 中同 run localization/path readback 接入现有 O1 material bundle，并把 same-run path 当前仍失败的事实固定到 fail-closed 输出里。这样下一轮 current live HIL / Nav2 path proof 可以直接对照缺口。

## Side2Side 对照

| 验收项 | 计划要求 | tech-done 证据 | Product 判断 |
| --- | --- | --- | --- |
| 用户价值 | 把 free-cell map material 接到 localization/path readiness proof | `localization_path_material_bridge_present=true` | 通过 |
| 同 run localization | 消费 `38_pc_summary_after_map_fix.json` 的 map/localize readback | `same_run_map_once_observed=true`、`same_run_amcl_pose_observed=true`、TF map-to-odom / map-to-base-link true | 通过 |
| 同 run path 边界 | 不把 path attempt 误写成成功 | `same_run_path_generation_requested=true`、`same_run_path_generation_succeeded=false`、`same_run_path_generated=false`、`same_run_path_point_count=0`、`same_run_path_proven=false` | 通过 |
| cross-run comparator | June 11 clean-baseline 只能作为对照 | `cross_run_clean_baseline_path_summary.path_point_count=31` | 通过，不能替代 same-run proof |
| fail-closed | 覆盖 missing endpoint / TF / path success tamper / unsafe / dangerous true | `Ran 24 tests in 0.104s OK`，主会话退回后的 dangerous optional fields 已补测 | 通过 |
| 安全字段 | 全部安全、控制、送达、route execution 字段固定 false | `hil_pass=false`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`nav2_route_execution_success=false` | 通过 |
| 文档同步 | 硬件合同和 sprint 记录同步 | `docs/hardware/wave_rover_motion_map_hil_material_bundle.md` 与 `tech-done.md` 已记录 | 通过 |

## OKR 映射和方向判断

- O1：继续，保守上调到约 `90%`。理由是本轮确实消费了新的 historical same-run localization/path material delta，并用 fail-closed 明确 same-run path still false。
- O5：暂停计分，保持约 `85%`。O5 仍是最低 Objective，但上一轮 cutover readiness packet 已明确 `okr_credit_allowed=false`，且本轮没有真实 external production evidence。
- O6/O7：保持约 `91%`。本轮没有 archive/readback/UI 消费范围，不调整。

方向判断：继续推进 O1，但下一轮必须转 current live HIL / current same-run Nav2 path generation / route execution evidence。若继续 O5，只有真实 external production evidence 才允许计分。

## KR 拆解和历史归档

- O1 KR1/KR3：获得 material-level 支撑，说明 historical same-run motion/map/localization readback 已能被安全消费。
- O1 KR4：fail-closed 单测覆盖扩大到 localization/path bridge、dangerous optional true 和 comparator dangerous true。
- O1 KR5：未调整 launch、串口、波特率、速度映射或控制参数。
- 已完成 KR：本轮不归档任何 KR。
- 历史记录位置：仅追加到 `OKR.md` 当前 O1 段、`OKR.md` 4.1 快照和 `docs/process/okr_progress_log.md`；不移动 KR 到历史区。

## 证据边界

proof boundary：`software_proof_o1_motion_map_hil_material_bundle_only` / historical same-run software proof only。

本轮证明：

- `38_pc_summary_after_map_fix.json` 的 same-run localization/path readback 已被安全 intake。
- same-run localization readiness material 存在。
- same-run path 仍未生成：`same_run_path_point_count=0`、`same_run_path_proven=false`。
- June 11 clean-baseline path `path_point_count=31` 只是 cross-run comparator。

本轮不证明：

- current live HIL
- safe-to-control
- delivery success
- same-run path generation success
- Nav2 route execution success
- wheel direction
- IMU/battery calibration
- production cloud

## 剩余风险和下一步

剩余风险是当前仍没有 live WAVE ROVER 同 run HIL acceptance、轮向确认、IMU/battery 标定、current same-run Nav2 path success、route execution 或 delivery result。

下一步优先级：由 `rober-hardware-engineer` 或 `robot-algorithm-engineer` 在真实/准现场条件下采集 current same-run `feedback_T1001.log`、motion command record、operator/external observation、HIL acceptance record，以及 Nav2 path generation / route execution readback；O5 只有拿到真实公网 HTTPS/TLS、4G/SIM、production DB/queue、worker/cutover、OSS/CDN 或真实 phone/browser 证据时才继续计分。
