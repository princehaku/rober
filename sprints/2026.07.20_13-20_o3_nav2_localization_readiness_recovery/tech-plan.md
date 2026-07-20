# O3 Nav2 Localization Readiness Recovery - Tech Plan

## 状态与合同修订

- `sprint_type: epic`
- 状态：`plan_contract_correction_implementation_ready`
- `IMPLEMENTATION_READY=yes`
- Robot Software owner：`robot-software-engineer`
- Algorithm owner：`robot-algorithm-engineer`
- proof boundary：`strict_no_motion_persistent_lifecycle_fresh_pose_planner_only_path_readiness`

原计划误把 `/api/nav2/start` body 当成已消费合同，误写了 `/api/nav2/proof/refresh` 字段，引用了不存在的 helper test，并设定了禁止 initialpose 时不可达的 path GO。本修订以代码事实建立可实现的两 owner 合同；HTTP 200 不再作为成功条件。

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5（约 85%）。
- 本 sprint 是否针对该最低 Objective：否。
- 理由：Objective 5 external provider/runtime blocker 已连续消费 `2/2`。本轮切换到 Objective 3 current readiness，并直接解锁 Objective 1（约 94%）的 current-run HIL 前置；Objective 6 / Objective 7（均约 93%）在 readiness 前暂停 action 重跑。
- `final.md` 收口复核：若没有 current safe lifecycle + fresh persisted localization + planner-only path artifact，OKR 保持 flat；本轮不归档 KR。

## 只读可行性结论与 o11 边界

- `upper_robot_api.py` 当前 start handler 不读 body，必须修；default `--base-enabled auto --lidar-enabled auto` 不满足本轮零串口 new-open 合同。
- `o11_nav2_lifecycle.sh` 已接受并透传 `--base-enabled false --lidar-enabled false`，stop 只终止 PID 文件归属的自身进程组。因此本 sprint 不修改该脚本。
- O10 helper 已有 persisted pose source audit 与 zero-publish 基础，但 path precondition 当前硬绑 initialpose request enabled，Algorithm 需拆开该 gate。
- 真实 helper test 路径是 `onboard/tests/test_nav2_runtime_proof_helper.py`。

## 两 owner 精确文件范围

### Robot Software owner（范围互斥 A）

1. `onboard/scripts/upper_robot_api.py`
2. `onboard/tests/test_upper_robot_api.py`
3. `docs/navigation/field_route_evidence_preflight.md`
4. `sprints/2026.07.20_13-20_o3_nav2_localization_readiness_recovery/artifacts/api_nav2_start_response.json`
5. `sprints/2026.07.20_13-20_o3_nav2_localization_readiness_recovery/artifacts/api_nav2_start_status.json`
6. `sprints/2026.07.20_13-20_o3_nav2_localization_readiness_recovery/artifacts/api_nav2_stop_response.json`
7. `sprints/2026.07.20_13-20_o3_nav2_localization_readiness_recovery/artifacts/lifecycle_safety_manifest.json`
8. `sprints/2026.07.20_13-20_o3_nav2_localization_readiness_recovery/tech-done.md`

### Algorithm owner（范围互斥 B）

1. `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
2. `onboard/tests/test_nav2_runtime_proof_helper.py`
3. `docs/navigation/fixed_route_workflow.md`
4. `sprints/2026.07.20_13-20_o3_nav2_localization_readiness_recovery/artifacts/nav2_proof_refresh_response.json`
5. `sprints/2026.07.20_13-20_o3_nav2_localization_readiness_recovery/artifacts/nav2_proof_latest_response.json`
6. `sprints/2026.07.20_13-20_o3_nav2_localization_readiness_recovery/artifacts/current_localization_source_audit.json`
7. `sprints/2026.07.20_13-20_o3_nav2_localization_readiness_recovery/artifacts/readiness_assertion.json`

禁止修改 launch、hardware/vendor config、`OKR.md`、progress log 或 `o11_nav2_lifecycle.sh`。若安全合同不能在上述范围兑现，停止实现并返回 Product 修订，不得扩域。

## 并行实现与集成顺序

1. 并行 A：Robot Software 实现 start body parsing/validation、false/false command 构造、semantic response、timeout 与 fixed stop 验证。
2. 并行 B：Algorithm 将 path precondition 改为“initialpose opt-in 成功，或 current fresh persisted pose source audit clean”二选一；本轮请求只能走后者，publish attempts 必须为 0。
3. 两 owner 各自完成本地 tests、修复、复验和 docs，不共享文件。
4. Live integration 严格串行：Robot Software safe start → Algorithm no-motion proof → Robot Software status capture → Robot Software fixed stop/cleanup → 双方结构验收 → Robot Software 汇总 `tech-done.md`。

## Robot Software API 合同

Start request：

```json
{
  "strict_no_motion": true,
  "base_enabled": false,
  "lidar_enabled": false,
  "reuse_existing_scan": true,
  "timeout_s": 20
}
```

实现要求：route handler 读取 JSON 并传给 lifecycle control；只接受上述安全组合。构造的现有 `o11_nav2_lifecycle.sh start` argv 必须固定 `--base-enabled false --lidar-enabled false`。bodyless、auto、true、未知 mode、invalid timeout 均不得执行。

Start response 必须包含：`status`、`command_result`、`evidence.effective_contract`、`evidence.base_uart_new_open_count`、`evidence.lidar_serial_new_open_count`、`root_causes`、`cleanup`、`nav2_lifecycle_status`。HTTP 200 下只要 command timeout/nonzero/not-executed、status not running、effective flags 不符或 new-open 非 0，均为 NO-GO。

Stop 沿用 `POST /api/nav2/stop` 无 body；必须解析 owned process group cleanup 和 stopped status，不调用底盘 stop、不发送 UART。

## Algorithm proof 合同

Proof request：

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

Path precondition 必须要求：map/amcl/planner/controller active；`persisted_pose_audit.persisted_pose_live_consumed=true`；`/amcl_pose` timestamp parsed + fresh；`map_to_odom` dynamic + timestamp parsed + fresh + `attributed_unique_amcl`；`map_to_base_link=true`；无 localization root cause。满足后才允许 planner-only `ComputePathToPose`。

任一 fresh/source/lifecycle 条件不满足：`path_generation_attempted=false`、root cause 精确、`initialpose_publish_attempts=0`。Helper 不启动 managed runtime，不持有/cleanup persistent lifecycle，不新开 LiDAR；response 必须区分 cleanup `not_required` 与失败。

## Owner 本地验收命令

Robot Software 执行：

```bash
python3 -m py_compile onboard/scripts/upper_robot_api.py
python3 -m unittest onboard/tests/test_upper_robot_api.py
git diff --check -- onboard/scripts/upper_robot_api.py onboard/tests/test_upper_robot_api.py docs/navigation/field_route_evidence_preflight.md sprints/2026.07.20_13-20_o3_nav2_localization_readiness_recovery
```

Algorithm 执行：

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
python3 -m unittest onboard/tests/test_nav2_runtime_proof_helper.py
git diff --check -- onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/tests/test_nav2_runtime_proof_helper.py docs/navigation/fixed_route_workflow.md sprints/2026.07.20_13-20_o3_nav2_localization_readiness_recovery
```

Robot Software tests 必须覆盖 body consumed/legacy blocked/false-false argv/semantic failure/timeout/owned stop。Algorithm tests 必须覆盖 current fresh persisted success、missing/stale/ambiguous attribution no-go、path opt-in、publish attempts 0、planner-only forbidden token absence。

## 真机 strict-no-motion 集成命令

实现和本地 tests 全绿后由对应 owner 执行，主节点不得代跑：

```bash
ssh -p 37878 root@192.168.1.11 "curl -fsS -X POST http://127.0.0.1:8787/api/nav2/start -H 'Content-Type: application/json' --data-binary @-" <<'JSON'
{"strict_no_motion":true,"base_enabled":false,"lidar_enabled":false,"reuse_existing_scan":true,"timeout_s":20}
JSON
ssh -p 37878 root@192.168.1.11 "curl -fsS -X POST http://127.0.0.1:8787/api/nav2/proof/refresh -H 'Content-Type: application/json' --data-binary @-" <<'JSON'
{"timeout_s":30,"managed_runtime_opt_in":false,"managed_timeout_s":30,"managed_map_yaml":"","initialpose_opt_in":false,"path_generation_opt_in":true,"path_generation_timeout_s":30,"path_goal_frame_id":"map","path_goal_x":0.8,"path_goal_y":0.0,"path_goal_yaw":0.0}
JSON
ssh -p 37878 root@192.168.1.11 "curl -fsS http://127.0.0.1:8787/api/nav2/status && curl -fsS http://127.0.0.1:8787/api/nav2/proof/latest"
ssh -p 37878 root@192.168.1.11 "curl -fsS -X POST http://127.0.0.1:8787/api/nav2/stop"
ssh -p 37878 root@192.168.1.11 "curl -fsS http://127.0.0.1:8787/api/nav2/status"
```

每步先落原始 artifact 并解析 JSON 语义再继续。Start semantic failure 不进入 proof；proof semantic failure仍必须执行 owned stop；stop failure记录 cleanup blocker，但不得扫杀其它 runtime。

## Artifact / JSON 结构断言

`readiness_assertion.json` 至少包含：

- `schema_version="trashbot.o3_nav2_current_readiness.v2"`
- `proof_boundary="strict_no_motion_persistent_lifecycle_fresh_pose_planner_only_path_readiness"`
- `current_for_this_capture_window=true`
- `strict_no_motion_contract_effective=true`
- `base_uart_new_open_count=0`、`lidar_serial_new_open_count=0`
- lifecycle map/amcl/planner/controller active
- persisted pose/TF freshness 与 source attribution clean
- `initialpose_publish_attempts=0`
- path requested/attempted/succeeded，point count > 0
- helper cleanup=`not_required`，owned lifecycle stop cleanup ok
- `obstacle_clear` 只进入 `next_motion_gate_blockers[]`
- 全部固定安全假字段为 false。

结构验收命令由双方在 artifacts 齐备后执行：

```bash
python3 -m json.tool sprints/2026.07.20_13-20_o3_nav2_localization_readiness_recovery/artifacts/api_nav2_start_response.json >/dev/null
python3 -m json.tool sprints/2026.07.20_13-20_o3_nav2_localization_readiness_recovery/artifacts/nav2_proof_refresh_response.json >/dev/null
python3 -m json.tool sprints/2026.07.20_13-20_o3_nav2_localization_readiness_recovery/artifacts/api_nav2_stop_response.json >/dev/null
python3 -m json.tool sprints/2026.07.20_13-20_o3_nav2_localization_readiness_recovery/artifacts/readiness_assertion.json >/dev/null
```

随后用 Python 断言上述字段，并额外检查 response 的 `command_result/status/evidence/root_causes/cleanup`、timeout、generated time；禁止仅检查 HTTP 200。

## GO / NO-GO 与失败修复循环

GO：strict start semantic success、new-open=`0/0`、persistent 四 lifecycle active、fresh persisted localization/TF source clean、zero initialpose publish、planner-only path success、owned stop cleanup success。Helper managed runtime 是否 persist 不参与 GO，因为本请求明确不启动 helper managed runtime。

NO-GO：任一字段 missing/stale/conflict/timeout/nonzero/cleanup failure。`obstacle_clear=false/not_proven` 不降低 planner-only GO，但必须保留为下一 motion gate blocker。任何 NO-GO 都不得触发 goal/cmd_vel/manual/initialpose/UART。

失败先由所属 owner 定位并在自己的文件范围修复，重跑该 owner 全部本地命令；接口单测均通过后才能重新开始一个新的 current live window。跨 owner schema 不一致由 Robot Software 在不改 Algorithm 文件的前提下调整 consumer/assertion，若必须改双方合同则返回 Product 修订计划。

## 工程与留档约束

- 新增/修改代码技术注释必须全部为中文，有意义中文注释比例超过 20%。
- 两份 navigation 文档分别由对应 owner 同步，不能用 `tech-done.md` 替代业务文档。
- Robot Software 汇总的 `tech-done.md` 必须记录实际改动、逐条命令 exit/log、失败修复、artifact、proof boundary 和剩余风险。
- 不创建 `side2side_check.md` / `final.md`，不修改 OKR/progress，不宣称 route/HIL/safe/delivery/mission 完成。
