# O3 AMCL Map TF Recovery Probe Tech Done

## sprint_type

sprint_type: epic

## 自主能力目标和本轮抓手

- 目标：在真实上位机 no-motion 场景下，把 `/amcl_pose`、`/map`、`map->odom`、`map->base_link` 和 `/api/nav2/proof/refresh` 的阻塞从“现象未就绪”下钻到可复核 root cause。
- 抓手：扩展 [`/Users/m1/apps/rober/onboard/scripts/field_route_evidence_preflight.py`](/Users/m1/apps/rober/onboard/scripts/field_route_evidence_preflight.py) 的 AMCL/map/TF 预检面，新增 topic type/publisher、managed map yaml、lifecycle 和 TF 失败摘要，同时保留 no-motion refresh readback 与所有危险字段固定 false。

## 改动文件和接口影响

- 修改 [`/Users/m1/apps/rober/onboard/scripts/field_route_evidence_preflight.py`](/Users/m1/apps/rober/onboard/scripts/field_route_evidence_preflight.py)
- 修改 [`/Users/m1/apps/rober/onboard/tests/test_field_route_evidence_preflight.py`](/Users/m1/apps/rober/onboard/tests/test_field_route_evidence_preflight.py)
- 修改 [`/Users/m1/apps/rober/docs/navigation/field_route_evidence_preflight.md`](/Users/m1/apps/rober/docs/navigation/field_route_evidence_preflight.md)
- 修改 [`/Users/m1/apps/rober/docs/navigation/fixed_route_workflow.md`](/Users/m1/apps/rober/docs/navigation/fixed_route_workflow.md)
- 新增 [`/Users/m1/apps/rober/sprints/2026.07.11_06-37_o3_amcl_map_tf_recovery_probe/artifacts/local_preflight.raw.json`](/Users/m1/apps/rober/sprints/2026.07.11_06-37_o3_amcl_map_tf_recovery_probe/artifacts/local_preflight.raw.json)
- 新增 [`/Users/m1/apps/rober/sprints/2026.07.11_06-37_o3_amcl_map_tf_recovery_probe/artifacts/local_preflight.pretty.json`](/Users/m1/apps/rober/sprints/2026.07.11_06-37_o3_amcl_map_tf_recovery_probe/artifacts/local_preflight.pretty.json)
- 新增 [`/Users/m1/apps/rober/sprints/2026.07.11_06-37_o3_amcl_map_tf_recovery_probe/artifacts/local_preflight.summary.json`](/Users/m1/apps/rober/sprints/2026.07.11_06-37_o3_amcl_map_tf_recovery_probe/artifacts/local_preflight.summary.json)
- 新增 [`/Users/m1/apps/rober/sprints/2026.07.11_06-37_o3_amcl_map_tf_recovery_probe/artifacts/live_amcl_map_tf_preflight.raw.json`](/Users/m1/apps/rober/sprints/2026.07.11_06-37_o3_amcl_map_tf_recovery_probe/artifacts/live_amcl_map_tf_preflight.raw.json)
- 新增 [`/Users/m1/apps/rober/sprints/2026.07.11_06-37_o3_amcl_map_tf_recovery_probe/artifacts/live_amcl_map_tf_preflight.pretty.json`](/Users/m1/apps/rober/sprints/2026.07.11_06-37_o3_amcl_map_tf_recovery_probe/artifacts/live_amcl_map_tf_preflight.pretty.json)
- 新增 [`/Users/m1/apps/rober/sprints/2026.07.11_06-37_o3_amcl_map_tf_recovery_probe/artifacts/live_amcl_map_tf_preflight.summary.json`](/Users/m1/apps/rober/sprints/2026.07.11_06-37_o3_amcl_map_tf_recovery_probe/artifacts/live_amcl_map_tf_preflight.summary.json)

接口影响：

- 仍保持 `schema=trashbot.board_field_evidence_preflight.v1` 不变。
- 顶层新增 `root_cause_summary`，以安全摘要暴露 `/map`、`/amcl_pose`、lifecycle、managed map yaml、TF 和 refresh readback 关键根因字段。
- 新增 `--managed-map-yaml` 参数；summary-facing 输出只记录默认 managed map yaml basename `trashbot_map.yaml`，不回显板上完整路径。

## 实现内容

1. 在预检脚本中新增 AMCL/map/TF root-cause probe：
   - `/map` 与 `/amcl_pose` 的 `ros2 topic type` 和 `ros2 topic info -v`；
   - `/map_server`、`/amcl`、`/planner_server` 的 `ros2 lifecycle get`；
   - managed map yaml 的存在性、basename、size 和 `sha256` 前缀摘要；
   - `map->odom`、`map->base_link` 的 TF 失败短句。
2. 把上述探测压缩成 `root_cause_summary`，供 sprint 和后续消费者直接读取，不需要重新解析完整 raw 输出。
3. 单测覆盖新增 root-cause probe、managed map yaml 摘要、topic metadata fail-closed，以及顶层摘要字段。
4. 文档同步说明新的 no-motion AMCL/map/TF root-cause 采集范围和收口方式。

## 测试、dry-run 或上车验证结果

### 1. `python3 -m py_compile onboard/scripts/field_route_evidence_preflight.py`

- 结果：通过

### 2. `python3 -m unittest onboard.tests.test_field_route_evidence_preflight`

- 结果：通过
- 关键输出：

```text
Ran 16 tests in 0.019s
OK
```

### 3. `python3 onboard/scripts/field_route_evidence_preflight.py --mode local --dry-run --output sprints/2026.07.11_06-37_o3_amcl_map_tf_recovery_probe/artifacts/local_preflight.raw.json`

- 结果：通过
- 关键摘要见 [`/Users/m1/apps/rober/sprints/2026.07.11_06-37_o3_amcl_map_tf_recovery_probe/artifacts/local_preflight.summary.json`](/Users/m1/apps/rober/sprints/2026.07.11_06-37_o3_amcl_map_tf_recovery_probe/artifacts/local_preflight.summary.json)

```text
status=dry_run_template_only_not_proven
safe_to_control=false
delivery_success=false
route_execution_success=false
hil_pass=false
```

### 4. `python3 onboard/scripts/field_route_evidence_preflight.py --mode ssh --ssh-target root@192.168.1.11 --ssh-port 37878 --timeout-s 8 --output sprints/2026.07.11_06-37_o3_amcl_map_tf_recovery_probe/artifacts/live_amcl_map_tf_preflight.raw.json`

- 结果：真实上位机可达，脚本完成；最终状态 `blocked_refresh_readback_failed`
- 关键摘要见 [`/Users/m1/apps/rober/sprints/2026.07.11_06-37_o3_amcl_map_tf_recovery_probe/artifacts/live_amcl_map_tf_preflight.summary.json`](/Users/m1/apps/rober/sprints/2026.07.11_06-37_o3_amcl_map_tf_recovery_probe/artifacts/live_amcl_map_tf_preflight.summary.json)

```text
status=blocked_refresh_readback_failed
localization_blocked_reasons=[
  blocked_amcl_pose_not_observed,
  blocked_map_to_odom_not_observed,
  blocked_map_to_base_link_not_observed
]
map_topic.blocked_reasons=[blocked_map_topic_type_missing]
amcl_pose_topic.blocked_reasons=[blocked_amcl_pose_topic_type_missing]
managed_map_yaml.blocked_reasons=[]
managed_map_yaml.configured_basename=trashbot_map.yaml
managed_map_yaml.summary.exists=true
map_server/amcl/planner_server lifecycle=Node not found
refresh.status=refresh_command_failed
safe_to_control=false
delivery_success=false
route_execution_success=false
hil_pass=false
```

### 5. `git diff --check -- onboard/scripts/field_route_evidence_preflight.py onboard/tests/test_field_route_evidence_preflight.py docs/navigation/field_route_evidence_preflight.md docs/navigation/fixed_route_workflow.md sprints/2026.07.11_06-37_o3_amcl_map_tf_recovery_probe`

- 结果：通过

### 6. 返工：`starts_nav2` no-motion readback 误判修复

- 背景：验收指出 `DANGEROUS_TRUE_FIELDS` 把 `starts_nav2` 也当成 hard-fail，但本轮 refresh body 明确允许 `managed_runtime_opt_in=true`，因此 lifecycle/runtime start 本身不应等价于运动或 goal execution。
- 修复：
  - 从危险 true hard-fail 集合中移除 `starts_nav2`；
  - 保留 `safe_to_control`、`delivery_success`、`robot_control_executed`、`publishes_cmd_vel`、`calls_base_manual`、`navigate_goal_enabled` 等真实越界字段为 fail-closed；
  - 新增单测证明 `starts_nav2=true`、其余 no-motion 安全字段保持 false 时，不会返回 `blocked_refresh_invokes_motion_or_goal_execution`。
- 返工后验证：

```text
python3 -m py_compile onboard/scripts/field_route_evidence_preflight.py
通过

python3 -m unittest onboard.tests.test_field_route_evidence_preflight
Ran 16 tests in 0.019s
OK

git diff --check -- onboard/scripts/field_route_evidence_preflight.py onboard/tests/test_field_route_evidence_preflight.py docs/navigation/field_route_evidence_preflight.md docs/navigation/fixed_route_workflow.md sprints/2026.07.11_06-37_o3_amcl_map_tf_recovery_probe
通过
```

### 7. 返工：managed map yaml summary 去路径化

- 背景：验收指出 `root_cause_summary.managed_map_yaml` 和 sprint 文案不应回显板上完整路径。
- 修复：
  - summary-facing 字段从 `configured_path` 改为 `configured_basename`；
  - 单测新增断言，确保 summary 渲染结果不包含 `/root/` 或完整 managed map yaml 路径；
  - 文档和本文件改为使用“configured managed map basename”表述。
- 返工后 artifact 变化：
  - `live_amcl_map_tf_preflight.summary.json` 中 `managed_map_yaml` 只保留 `configured_basename=trashbot_map.yaml` 和 `basename/exists/size_bytes/sha256_prefix`；
  - summary 渲染结果确认不包含 `/root/`。
- 本次返工不改变安全结论：仍然 fail-closed，OKR 百分比不变。

## 数据、样本或调试输出变化

- live root-cause summary 首次明确给出：
  - `/map` topic type 不可解析，publisher count 也拿不到；
  - `/amcl_pose` topic type 不可解析；
  - `/map_server`、`/amcl`、`/planner_server` 三个 lifecycle probe 都返回 `Node not found`；
  - configured managed map basename `trashbot_map.yaml` 当前可读，summary 记录 `exists=true`、`size_bytes=148`、`sha256_prefix=1b54312162c6`；
  - `tf2_echo` 对 `map->odom` 与 `map->base_link` 都返回 `Invalid frame ID "map"`；
  - `/api/nav2/proof/refresh` 仍是 `refresh_command_failed`。
- 这说明 blocker 已从“AMCL/TF 没观测到”进一步收敛为“map/nav runtime 本身未起、map frame 未建立”，而不是 LiDAR 当前窗口缺样本或 managed map yaml basename 缺失。

## 失败定位

- 当前 root cause 更接近 bringup/runtime 缺口，而不是单纯 localization echo 超时：
  - `map` frame 未建立，所以 `map->odom`、`map->base_link` 都在 `Invalid frame ID "map"` 上等待；
  - `/map_server`、`/amcl`、`/planner_server` probe 都是 `Node not found`，说明这轮 no-motion 板上没有对应 Nav2 lifecycle node 存活证据；
  - configured managed map basename `trashbot_map.yaml` 当前可读，因此 blocker 不再是 map yaml 文件缺失，而是 runtime 没把 `map` frame 和相关 lifecycle 节点拉起；
  - `/map` 与 `/amcl_pose` 连 topic type 都无法读取，和上面的 lifecycle 缺失相互印证；
  - `/api/nav2/proof/refresh` 因 refresh command 本身失败，没有产生新的 path/material 成功证据。

## OKR 结论

- 本轮没有 same-run `path_generated=true`，也没有新的 `map.yaml`、`route.csv`、keyframe、rosbag、replay JSONL 成功材料。
- 因此主 OKR 百分比保持不变，必须 fail-closed；本轮价值是新增真实板 root-cause evidence，而不是恢复路线成功。

## 剩余风险和下一步能力建设建议

- 风险：
  - 目前只能证明真实板上的 Nav2/map/AMCL runtime 未 ready，尚未在本轮修复到可发布 `map` frame 的状态；
  - refresh 仍失败，所以还不能确认 path generation blocker 是否在修复后会继续下钻到新层级；
  - 本轮严格 no-motion，没有发送任何 `/cmd_vel`、`/api/base/manual` 或 NavigateToPose，也因此不产生路线成功证据。
- 下一步建议：
  - 先排查为什么 `map_server`、`/amcl`、`/planner_server` 在板上是 `Node not found`；
  - 对齐 `managed_map_yaml` 的实际路径或生成链，恢复 map runtime 的最小启动前提；
  - 仅在确认以上三点都仍然 no-motion 且安全字段保持 false 后，重跑 refresh readback；
  - 只有当 `map` frame 恢复并产出 same-run path/material success，才允许后续 O6/O7 消费链重新计主进度。
