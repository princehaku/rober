# O3 Nav2 Localization Readiness Recovery - PRD

## 状态与产品方向

- `sprint_type: epic`
- 状态：`plan_contract_correction_requirements_ready`
- proof boundary：`strict_no_motion_persistent_lifecycle_fresh_pose_planner_only_path_readiness`
- Owner：`robot-software-engineer` + `robot-algorithm-engineer`
- 产品方向：`调整`。从不可达的 managed no-initialpose proof 改为 persistent safe lifecycle + current fresh pose planner-only path。

## 用户问题与核心抓手

当前上位机可访问，但 Nav2 lifecycle、定位/TF 与 path 未 ready。用户需要的是下一次受控路线 action 的可信前置，而不是 HTTP 200、旧 success 或 cleanup 后消失的临时 graph。

核心抓手有两个：

1. Robot Software 让 `/api/nav2/start` 真正消费显式 strict-no-motion body，强制 `base_enabled=false`、`lidar_enabled=false`，复用 current scan，persistent 启动 map/amcl/planner/controller。
2. Algorithm 让 `/api/nav2/proof/refresh` 在 `initialpose_opt_in=false`、`initialpose_publish_attempts=0` 时，仅凭同窗 fresh `/amcl_pose` 与唯一 AMCL dynamic TF 进入 planner-only `ComputePathToPose`；缺失即 fail closed。

## FR-1 安全 lifecycle start API

`POST /api/nav2/start` 的精确 request body：

```json
{
  "strict_no_motion": true,
  "base_enabled": false,
  "lidar_enabled": false,
  "reuse_existing_scan": true,
  "timeout_s": 20
}
```

合同要求：

- handler 必须读取并验证 body，不能忽略字段；body missing、`strict_no_motion!=true`、任一 enabled 非 false 或 reuse 非 true 时 fail closed，`command_result.executed=false`。
- accepted request 只能调用现有 `o11_nav2_lifecycle.sh start`，effective argv 必须含 `--base-enabled false --lidar-enabled false`；不得回退到 `auto` 或 `true`。
- response 必须暴露 `status`、`command_result`、`evidence.effective_contract`、`root_causes`、`cleanup`、`nav2_lifecycle_status`；`evidence.base_uart_new_open_count=0`、`evidence.lidar_serial_new_open_count=0` 必须有 current readback 支撑。
- HTTP 200 不是成功；只有 command executed/ok、effective flags、new-open counts 和 lifecycle status 一起满足才算 start accepted。

兼容性：route 与 HTTP method 不变；legacy bodyless/auto start 从“隐式执行”改为显式 blocked，是有意的 fail-closed 语义收紧。`POST /api/nav2/stop` 保持 bodyless owned-process-group stop，不发送底盘命令。

## FR-2 current persisted localization planner-only proof

安全 start active 后，`POST /api/nav2/proof/refresh` 的精确 body：

```json
{
  "timeout_s": 30,
  "managed_runtime_opt_in": false,
  "managed_timeout_s": 30,
  "managed_map_yaml": "",
  "initialpose_opt_in": false,
  "path_generation_opt_in": true,
  "path_generation_timeout_s": 30,
  "path_goal_frame_id": "map",
  "path_goal_x": 0.8,
  "path_goal_y": 0.0,
  "path_goal_yaw": 0.0
}
```

合同要求：

- helper 不启动 managed runtime、不新开 LiDAR、不 cleanup persistent lifecycle；`managed_runtime_requested=false`、`managed_runtime_started=false`。
- path gate 在 initialpose opt-out 时，只有 `persisted_pose_audit.persisted_pose_live_consumed=true`、current fresh pose timestamp、fresh dynamic `map_to_odom`、唯一 AMCL publisher attribution、`map_to_base_link=true`、map/amcl/planner/controller active 时才允许 planner-only path。
- `initialpose_publish_attempts=0`、`initialpose_published=false`；missing/stale/ambiguous source 时 `path_generation_attempted=false`、精确 root cause、NO-GO。
- `ComputePathToPose` 只允许规划，不允许 `NavigateToPose`、FollowPath、controller action、`/cmd_vel` 或 base/manual。

## FR-3 JSON 语义与 timeout

每个 response 即使 HTTP 200，也必须解析：

- `command_result.executed`、`command_result.ok`、returncode/timeout/error；
- 顶层 `status`、`evidence_type`、`root_causes[]`；
- `latest_result.proof` 内 lifecycle、freshness、source attribution、path、publish attempts；
- `cleanup.required` / `cleanup.ok` / owned process group；
- response 与 artifact 的 generated/captured time 属于同一 current window。

Start timeout 上限 20 秒，proof timeout/path timeout 各 30 秒；timeout 一律 fail closed。Robot Software stop 后必须确认 owned lifecycle stopped；helper cleanup 在 `managed_runtime_opt_in=false` 时应明确 `not_required`，不能把 persistent lifecycle 的后续 stop 误记为 helper cleanup。

## FR-4 readiness GO

同窗 GO 需要：

- start strict contract accepted 且 effective；base UART/LiDAR new-open count=`0/0`；
- map/amcl/planner/controller active；
- current fresh persisted pose/TF source audit clean；
- `initialpose_publish_attempts=0`；
- `path_generation_opt_in=true`、attempted/succeeded=true、path point count > 0；
- Robot Software 最终 stop/cleanup 成功且无范围外进程被终止。

`obstacle_clear` 仅写为 `next_motion_gate_blocker`，不阻断 planner-only readiness。固定安全假字段：`safe_to_control=false`、`route_execution_success=false`、`nav2_goal_execution_proven=false`、`wheel_feedback_lr_nonzero_proven=false`、`hil_pass=false`、`delivery_success=false`、`mission_objective_0_satisfied=false`、`okr_credit=false`。

## 验收口径

1. Robot Software targeted tests 覆盖 body consumed、legacy blocked、false/false argv、HTTP 200 semantic failure、timeout、status parse、owned stop。
2. Algorithm targeted tests 覆盖 fresh persisted pose success、missing/stale/ambiguous fail closed、zero publish、planner-only path，以及真实测试路径 `onboard/tests/test_nav2_runtime_proof_helper.py`。
3. 真机集成按 start → proof → status/latest → stop 串行，artifact/结构断言通过；任何 motion/control/serial new-open 计数均为 0。
4. 两 owner 各自修复并复验自身失败，Robot Software 最后汇总 `tech-done.md`；新增/修改代码技术注释全部为中文且有意义注释比例超过 20%。
5. 同步 `docs/navigation/field_route_evidence_preflight.md` 与 `docs/navigation/fixed_route_workflow.md`；不创建后三份 closeout，不改 OKR/progress。

## KR 与历史归档

本轮不归档 KR，历史区无新增。只有 current artifact 通过、Product 在后续 `side2side_check.md` / `final.md` 接受且证据边界不被夸大，才讨论 OKR 进度；本 sprint 不是 route/HIL/delivery 结果。
