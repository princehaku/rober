# O3 Nav2 Localization Readiness Recovery - Tech Done

- `sprint_type: epic`
- 状态：`implemented_live_no_go_owned_cleanup_complete`
- proof boundary：`strict_no_motion_persistent_lifecycle_fresh_pose_planner_only_path_readiness`
- `READINESS_GO=false`
- `OWNED_STOP_CLEANUP_OK=yes`
- `OKR_CREDIT=false`

## 实际改动

Robot Software 交付：

- `onboard/scripts/upper_robot_api.py`：`POST /api/nav2/start` 改为必须消费完整 strict-no-motion JSON；bodyless、旧 `{}`、auto/true、未知字段和非法 timeout 在 subprocess 前 fail closed。
- 受管 o11 start 有效 argv 固定 `--base-enabled false --lidar-enabled false`；response 显式提供 `command_result/effective_contract/root_causes/cleanup/nav2_lifecycle_status/new-open`，HTTP 200 不作为成功条件。
- `POST /api/nav2/stop` 只验收 o11 owned PID/process group cleanup 与 stopped readback，不发底盘 stop、不打开 UART。
- `onboard/tests/test_upper_robot_api.py` 新增 strict body、legacy zero invocation、false/false argv、semantic failure cleanup、timeout 与 owned stop 回归。
- `docs/navigation/field_route_evidence_preflight.md` 记录新合同、旧 PC `{}` 代理的兼容迁移和 no-motion 边界。

Algorithm 交付：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py` 新增 persisted-pose planner-only gate；只有 current fresh `/amcl_pose`、dynamic fresh `map->odom`、unique AMCL attribution、`map->base_link` 和四 lifecycle active 同时成立才可尝试 ComputePathToPose。
- `initialpose_opt_in=false` 时 publish attempts 固定为 0；missing/stale/ambiguous 在 planner action 前 NO-GO。
- `onboard/tests/test_nav2_runtime_proof_helper.py` 覆盖 fresh success gate、missing/stale/ambiguous no-go、四 lifecycle、zero publish 与 forbidden motion token。
- `docs/navigation/fixed_route_workflow.md` 同步 current persisted localization 与 planner-only 合同。

## 真机集成与失败修复

1. 远端旧 `upper_robot_api.py` SHA 为 `e3cdae050bff8539c7312db4032cf414ee92afdd96b82a8ca08ec252d0a8271f`。staged SCP、远端 `py_compile`、原子覆盖均 exit 0；最终本地/远端 SHA 均为 `944fe3ba43201c8363b175959e0efc5b440369f4005a1ca0a03dec40328f6bd8`。
2. 首次 bounded `systemctl restart trashbot-upper-robot-api.service` exit 124；根因为旧 PID `553724` 长时停在 `stop-sigterm`。仅对该 unit cgroup 执行 `systemctl kill -s SIGKILL`，再受管 start；新 API PID `679127`，health poll exit 0、`status=ready`。未扫杀 ROS/串口进程。
3. exactly-one strict start POST exit 0；`status=started_strict_no_motion`、`semantic_success=true`、effective false/false、owned lifecycle PID/PG `679928`。
4. Algorithm exactly-one proof refresh 保留 partial artifact 后 helper timeout；wrapper cleanup 成功，managed-runtime cleanup 为 `not_required`，未重试 proof。
5. pre-stop status 仍确认 PID `679928` running 且 false/false。exactly-one stop POST exit 0；`status=stopped_owned_process_group`、`semantic_success=true`、`command_result.executed/ok=true`、`cleanup.ok=true`、scope=`o11_owned_pid_process_group_only`、`root_causes=[]`。
6. final status 为 stopped/PID null；Nav2/AMCL/planner/controller 节点已清空，Upper API PID `679127` 仍 active/ready。

## 唯一 Proof 结果

`READINESS_GO=false`，且 `path_generation_attempted=false`、`path_generated=false`、`initialpose_publish_attempts=0`。精确 blockers：

- `helper_process_timeout_after_partial_artifact`
- `amcl_pose_probe_interrupted_before_observation`
- `lifecycle_active_fields_not_proven_in_current_proof`
- `persisted_pose_audit_not_reached_before_timeout`
- `current_amcl_pose_stamp_and_freshness_not_proven`
- `dynamic_map_to_odom_stamp_freshness_and_unique_amcl_attribution_not_proven`
- `map_to_base_link_not_observed`
- `path_generation_not_attempted`

本轮保持 `safe_to_control=false`、`route_execution_success=false`、`hil_pass=false`、`delivery_success=false`、`mission_objective_0_satisfied=false`和 `okr_credit=false`。

## 串口、节点与调用边界

- `/dev/ttyS5` 全窗口仍由既存 `esp32_bridge` PID `13543` 持有；`/dev/ttyACM0` 仍由既存 `lidar_driver` PID `550922` 持有。start/stop 前后 holder PID 不变，new-open=`0/0`。
- WAVE ROVER command debug 在全窗口始终为 `3570` 行、`1245562` bytes、mtime `1783532582`，UART motion delta=0。
- invocation counts：start=1、proof refresh=1、proof latest GET=1、stop=1；goal/manual/base-stop/cmd_vel publish/initialpose/UART motion/T1/T11/T13 均为 0。
- 物理运动未发生。

## 验证结果

- Robot `python3 -m py_compile onboard/scripts/upper_robot_api.py`：exit 0。
- Robot `python3 -m unittest onboard/tests/test_upper_robot_api.py`：最终 `Ran 114 tests ... OK (skipped=1)`；五项 targeted strict lifecycle tests `Ran 5 ... OK`。
- Algorithm `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py`：exit 0。
- Algorithm `python3 -m unittest onboard/tests/test_nav2_runtime_proof_helper.py`：`Ran 167 tests ... OK`。
- 8 份 JSON 全部 `python3 -m json.tool`：exit 0，`JSON_TOOL_COUNT=8`。
- 跨 artifact 结构断言：`INTEGRATION_ASSERTION=O3_STRICT_NO_MOTION_FINAL_NO_GO_CLEANUP_OK`。
- combined scoped `git diff --check`：exit 0。
- Robot source+test 中文注释 owner 验收为 `20.63%`，集成时当前 diff 复核为 `25.24%`；Algorithm 产品源文件中文注释 `32/143=22.38%`。

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

## 剩余风险

- start transport 原始 bytes 在中断前未落盘；start artifact 明确保留该边界并恢复了合同关键字段，status 与 stop 为完整 raw JSON。
- Upper API graceful shutdown 仍可卡在 `stop-sigterm`，本轮仅使用 unit-scoped recovery，未修复该既有问题。
- current fresh persisted pose、dynamic fresh uniquely-attributed `map->odom`、`map->base_link` 与 planner-only path 未在同一 proof 窗口成立；下轮必须从这些 root cause 修复，不得用新 wrapper 重复消费 timeout。
- 本 sprint 不创建 `side2side_check.md` / `final.md`，不修改 OKR/progress，不归档 KR。
