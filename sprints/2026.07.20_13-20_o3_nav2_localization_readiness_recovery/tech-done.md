# O3 Nav2 Localization Readiness Recovery - Tech Done

- `sprint_type: epic`
- 状态：`implemented_live_planner_only_no_go_owned_stop_clean`
- proof boundary：`strict_no_motion_persistent_lifecycle_fresh_pose_planner_only_path_readiness`
- `READINESS_GO=false`
- `PLANNER_ONLY_NO_GO`
- `OWNED_STOP_CLEAN=yes`
- `OKR_CREDIT=false`
- `RACE_RECONCILIATION_COMPLETE=yes`

## 实际改动

Robot Software 交付：

- `onboard/scripts/upper_robot_api.py`：`POST /api/nav2/start` 必须消费完整 strict-no-motion JSON；bodyless、旧 `{}`、auto/true、未知字段和非法 timeout 在 subprocess 前 fail closed。
- o11 start 有效 argv 固定 `--base-enabled false --lidar-enabled false`；response 显式提供 `command_result/effective_contract/root_causes/cleanup/nav2_lifecycle_status/new-open`，HTTP 200 不作为成功条件。
- `POST /api/nav2/stop` 只验收 o11 owned PID/process group cleanup 与 stopped readback，不发底盘 stop、不打开 UART。
- `onboard/tests/test_upper_robot_api.py` 和 `docs/navigation/field_route_evidence_preflight.md` 同步 strict lifecycle 合同、兼容迁移和 no-motion 边界。

Algorithm 交付：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py` 新增 persisted-pose planner-only gate；只有 current fresh `/amcl_pose`、fresh dynamic `map->odom`、unique AMCL attribution、`map->base_link` 和所需 lifecycle active 同时成立才可尝试 `ComputePathToPose`。
- `initialpose_opt_in=false` 时 publish attempts 固定为 0；missing/stale/ambiguous 在 planner action 前 NO-GO。
- `onboard/tests/test_nav2_runtime_proof_helper.py` 与 `docs/navigation/fixed_route_workflow.md` 覆盖并记录 fresh/missing/stale/ambiguous、零发布与 planner-only 合同。

## 本地验证

- Robot：`python3 -m py_compile onboard/scripts/upper_robot_api.py` exit 0；`python3 -m unittest onboard/tests/test_upper_robot_api.py` 为 `Ran 114 tests ... OK (skipped=1)`，skip 为缺 `aiohttp`；中文注释比例 `20.2%`。
- Algorithm：`python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py` exit 0；`python3 -m unittest onboard/tests/test_nav2_runtime_proof_helper.py` 为 `Ran 167 tests ... OK`；中文注释比例 `20.946%`。
- 双方 diff、静态断言及文档验收均为绿；本 Product 收口不重跑工程 tests、SSH、ROS2 或 live。

## Final live 序列与安全边界

- 远端 API 与 helper 均和本地 SHA 对齐；远端 `py_compile` 通过。
- 首窗口外部调用为 start/proof/latest/owned-stop=`1/1/1/1`；helper `81243ms`，roots 为 `amcl_pose_probe_interrupted_before_observation`、`sigint_before_final_artifact`、`helper_process_timeout_after_partial_artifact`。这些已发布事实继续有效。
- 第二窗口内部调用同样为 `1/1/1/1` 且窗口内 retry=`0`；全 sprint 累计 start/proof/latest/owned-stop=`2/2/2/2`。第二窗口是发布后非预期后台/编排竞态，违反 no-retry 边界，不能表述为正常 exactly-once，也不产生第二次 OKR credit。
- strict start 为 `status=started_strict_no_motion`、`semantic_success=true`、effective `base_enabled=false/lidar_enabled=false`；既存 base/LiDAR holder 未变化，new-open=`0/0`。
- `initialpose/goal/cmd_vel/UART=0/0/0/0`；base manual/base stop、T1/T11/T13 均为 0；WAVE ROVER command log delta=`0`，无物理运动。
- 最终 stop 为 `status=stopped_owned_process_group`、`semantic_success=true`、`cleanup.ok=true`、scope=`o11_owned_pid_process_group_only`；owned PID `684474` 已移除、PID 文件已移除，最终 lifecycle stopped。结论：`OWNED_STOP_CLEAN=yes`。
- `readiness_assertion.json` 是 stop 前 snapshot，其中 `owned_lifecycle_stop_pending=true` 属于当时事实；最终 cleanup 必须以 `lifecycle_safety_manifest.json.final_stop` 与 `api_nav2_stop_response.json` 为准，不能把 pre-stop 字段误当最终状态。

## post_publish_race_window

commit `3fe3c053ceada54c10dd8414098863a66e5f08e1` 发布后，第二窗口以 lifecycle PID/PG `684474` 和 proof PG `685333` 运行；artifact 只能证明 endpoint、PID/PG 与时间，不能判定 invoking agent、session 或 operator 身份。该窗口 helper `80444ms`，是未计划的编排竞态与禁止重试偏差，不是第二份产品进展。

第二窗口 partial artifact 证明 `map_server_active=true`、`amcl_active=true`，dynamic `map->odom` observed、timestamp parsed、publisher attribution=`attributed_unique_amcl`，并且 `map->base_link=true`。但 formal TF freshness gate 未成立，current AMCL pose sample/timestamp/freshness 未证明，persisted pose audit 未完成，planner/controller active 未证明，path requested=true 但 attempted/succeeded/generated=false、count=0；因此 `READINESS_GO=false`。

第二 owned stop 在 16:54 完成；16:55 `post_publish_race_cleanup` 审计没有再发 stop（新增 stop invocation=`0`），因为 lifecycle 已 stopped、PID null、无 owned lifecycle/proof 残留。Upper API healthy，tty holders 与 command log 不变，`physical_motion=false`。禁止第三个 proof/window。

## Algorithm 结果：PLANNER_ONLY_NO_GO

第二窗口 helper 在 `80444ms` 超出 API `80s` process budget；partial artifact 保留，最后成功 phase=`tf_probe`，中断时 command=`ros2 pkg list`，根因包含：

- `helper_process_timeout_after_partial_artifact`
- `sigint_before_final_artifact`
- `current_amcl_pose_sample_timestamp_and_freshness_not_proven`
- `persisted_pose_audit_and_final_tf_freshness_gate_not_reached`
- `planner_and_controller_lifecycle_active_not_proven_before_timeout`
- `path_generation_not_attempted`

Partial current evidence 已证明：

- `map_server_active=true`、`amcl_active=true`；
- `map->odom` observed、dynamic、timestamp parsed，publisher attribution=`attributed_unique_amcl`；
- `map->base_link=true`；
- `initialpose_publish_attempts=0`。

但 partial evidence 不证明 fresh `/amcl_pose`、persisted pose final gate、`map->odom` formal freshness、planner/controller active 或 path。最终 `path_generation_requested=true`，但 attempted/succeeded/generated=`false/false/false`、count=`0`。因此 `PLANNER_ONLY_NO_GO`，不得用 partial lifecycle/TF 事实升级为 readiness GO。

## OKR 与证据增量

- `current_run_artifact_delta=true`：只表示 fresh no-motion current artifact、strict contract 与 clean owned stop。
- `external_artifact_delta=false`、`live_control_delta=false`、`user_action_delta=false`。
- `robot_control_executed=false`、`route_execution_success=false`、`hil_pass=false`、`delivery_success=false`、`safe_to_control=false`、`okr_credit=false`。
- O5 保持约 `85%`（provider/runtime blocker `2/2`），O6/O7 各保持约 `93%`，O1 保持约 `94%`；O3 不新增 Mission credit，主百分比 flat，KR `不归档`。

## 完整文件清单

Robot Software：

- `onboard/scripts/upper_robot_api.py`
- `onboard/tests/test_upper_robot_api.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `artifacts/api_nav2_start_response.json`
- `artifacts/api_nav2_start_status.json`
- `artifacts/api_nav2_stop_response.json`
- `artifacts/lifecycle_safety_manifest.json`

Algorithm：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/fixed_route_workflow.md`
- `artifacts/nav2_proof_refresh_response.json`
- `artifacts/nav2_proof_latest_response.json`
- `artifacts/current_localization_source_audit.json`
- `artifacts/readiness_assertion.json`

Sprint：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`
- `tech-done.md`
- `side2side_check.md`
- `final.md`

## 剩余风险与下一轮

- O10 helper 在 `ros2 pkg list` / TF probe 之后仍会超出 API 80s runtime budget；current fresh `/amcl_pose`、persisted final gate、planner/controller 和 path 仍未证明。
- Upper API graceful shutdown 的既有 `stop-sigterm` 风险不因本轮 unit-scoped cleanup 消失。
- 暂停重复 strict-start wrapper/live refresh；不得重跑本窗口或用旧 pose、文档、wrapper 补齐 readiness。
- `next_offline_runtime_budget_fix`：下一轮由 `robot-software-engineer` + `robot-algorithm-engineer` 先在本地/离线剖析并修复 O10 helper 的 runtime path、probe order 与 budget 分配；只有新测试证明能在 80s 内完成 final artifact，才开一个新的 no-motion current proof。
- 旧运动授权的 current context 已经过两个窗口，后续动作不得直接复用；任何新动作都必须重新确认 current operator、route、obstacle 与 readiness。
