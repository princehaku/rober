# Technical Plan

- `sprint_type: epic`
- 状态：计划完成；按用户要求创建后停止，尚未实施。
- 唯一 owner：`robot-algorithm-engineer`
- 目标：`root@192.168.1.11:37878`

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 最低 Objective：O5（85%）。
- 本 sprint 不直接针对 O5，切换到 O1（94%）支撑下的 O3 live localization lane。
- 理由：O5 production/cloud success 依赖外部 success-class 证据，support wrapper 已重复消费；本轮 CEO 已重新提供真实上位机并授权推进 persisted pose audit 与最多一次 controlled `/initialpose`。
- O5 保持、不归档；本轮 clean localization 仍不等于 route/delivery/HIL credit。

## Engineer 精确文件范围

`robot-algorithm-engineer` 只允许修改：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `sprints/2026.07.15_04-55_o3_controlled_initialpose_localization_proof/artifacts/algorithm/**`
- `sprints/2026.07.15_04-55_o3_controlled_initialpose_localization_proof/tech-done.md`

明确禁止修改 launch/config、其他业务代码或其他 sprint 文档。实现、测试、SSH capture、修复复验与 `tech-done.md` 由该 owner 单线闭环。

## 实现步骤

1. 在 helper 增加结构化 `persisted_pose_audit`，区分静态 config、helper effective `set_initial_pose: false` 与发布前 live consumption；静态 `set_initial_pose: true` 不得直接置为 consumed。
2. 增加 canonical map free-cell/world pose audit：记录 map/YAML/PGM hash、尺寸、resolution/origin、free pixel 与坐标换算，产出确定性 `map` world pose。
3. 把 read-only pre-initialpose gate 移到发布前：fresh `/scan`、AMCL subscriber active、TF authority clear、无竞争/static `map->odom`。
4. 把实际 `/initialpose` publish 总 attempt 限制为 `<=1`：rclpy 已发布后严禁 CLI fallback；rclpy 在发布前失败且 attempt=0 时才允许单次 CLI `--once`。
5. 发布后只读采集 fresh `/amcl_pose` 与唯一 AMCL dynamic `map->odom` endpoint/publisher/header timestamp/freshness；不触发 planner/controller/path。
6. 所有失败保留 exact blocker，并用 helper 自有 PGID cleanup；禁止 `pkill`/`killall`。

## 本地测试与静态验收

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
python3 -m unittest onboard/tests/test_nav2_runtime_proof_helper.py
rg -n 'persisted_pose_audit|canonical.*free.*cell|world.*pose|initialpose.*attempt|/amcl_pose|map.?to.?odom|process_group|cleanup' \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/field_route_evidence_preflight.md
git diff --check -- \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/field_route_evidence_preflight.md \
  sprints/2026.07.15_04-55_o3_controlled_initialpose_localization_proof
```

单测必须覆盖：config `set_initial_pose: true` 不等于 live consumed、上一轮 effective false、persisted live consumption 跳过 publish、non-free/越界 pose fail-closed、subscriber/TF authority gate、rclpy/CLI 总 attempt `<=1`、一次已发布后绝不重试、fresh pose/TF clean gate 与 exact PGID cleanup。

## SSH deploy 与 live capture

```bash
set -euo pipefail
SPRINT=sprints/2026.07.15_04-55_o3_controlled_initialpose_localization_proof
ART="$SPRINT/artifacts/algorithm"
TARGET=root@192.168.1.11
PORT=37878
REMOTE=/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
MAP=/root/rober/onboard/runtime/maps/trashbot_map.yaml
RAW=/tmp/o3_controlled_initialpose_localization_proof.json
mkdir -p "$ART"
shasum -a 256 onboard/scripts/o10_amcl_nav2_runtime_proof.py | tee "$ART/helper_local_sha256.txt"
scp -P "$PORT" onboard/scripts/o10_amcl_nav2_runtime_proof.py "$TARGET:$REMOTE"
ssh -p "$PORT" "$TARGET" "sha256sum '$REMOTE'; test -r '$MAP'" | tee "$ART/deploy_and_map_readback.txt"
ssh -p "$PORT" "$TARGET" "ros2 node list; ros2 topic list" >"$ART/graph_before.txt" 2>"$ART/graph_before.stderr"
date -u +%Y-%m-%dT%H:%M:%SZ | tee "$ART/run_started_at.txt"
set +e
ssh -p "$PORT" "$TARGET" \
  "timeout --signal=INT --kill-after=12s 180s python3 '$REMOTE' --strict-no-motion --no-base-uart --managed-runtime-opt-in --reuse-existing-lidar-lifecycle --managed-map-yaml '$MAP' --managed-timeout-s 70 --timeout-s 4 --initialpose-opt-in --initialpose-canonical-free-cell-opt-in --initialpose-yaw 0.0 --output '$RAW'" \
  >"$ART/runtime.stdout" 2>"$ART/runtime.stderr"
RUN_EXIT=$?
set -e
printf '%s\n' "$RUN_EXIT" | tee "$ART/runtime.exit"
scp -P "$PORT" "$TARGET:$RAW" "$ART/runtime-proof.json"
ssh -p "$PORT" "$TARGET" "ros2 node list; ros2 topic list" >"$ART/graph_after.txt" 2>"$ART/graph_after.stderr"
date -u +%Y-%m-%dT%H:%M:%SZ | tee "$ART/run_finished_at.txt"
```

该 live command 必须在实现中新增并验证 `--initialpose-canonical-free-cell-opt-in`；命令不得包含 path/planner/controller/NavigateToPose/cmd_vel/base manual/UART/运动。若 pre-write gate 不通过，helper 必须自然 fail-closed 且不发布。

## JSON assertions 与 clean gate

```bash
python3 -m json.tool "$ART/runtime-proof.json" >"$ART/runtime-proof.pretty.json"
python3 - "$ART/runtime-proof.json" <<'PY'
import json, sys

d = json.load(open(sys.argv[1], encoding="utf-8"))
p = d.get("proof", d)
assert p["persisted_pose_audit"]["config_presence_is_live_consumption"] is False
assert p["canonical_initialpose_map_audit"]["free_cell_verified"] is True
assert p["canonical_initialpose_map_audit"]["world_pose_auditable"] is True
assert p["pre_initialpose_gate"]["clean"] is True
assert int(p["initialpose_publish_attempts"]) <= 1
assert p["localization_signal_freshness"]["/scan"]["freshness"]["status"] == "fresh"
assert p["localization_signal_freshness"]["/amcl_pose"]["freshness"]["status"] == "fresh"
edge = p["tf_source_freshness"]["edges"]["map_to_odom"]
assert edge["source_class"] == "dynamic"
assert edge["publisher_attribution_status"] == "attributed_unique_amcl"
assert edge["timestamp"]["parsed"] is True
assert edge["freshness"]["status"] == "fresh"
assert p["managed_runtime_cleanup_ok"] is True
for key in ("safe_to_control", "route_execution_success", "delivery_success", "hil_pass", "robot_control_executed"):
    assert p[key] is False
print("controlled_initialpose_localization_clean_gate_ok")
PY
```

结构字段名如在实现中已有等价字段，Engineer 必须统一到上述合同或同步更新 assertion 与文档；不能弱化含义。若 persisted pose 已 live 消费，允许 `initialpose_publish_attempts=0`，但其余 fresh pose/TF clean gate 仍必须满足。

## Forbidden command scan、cleanup 与失败修复复验

```bash
! rg -n -- '--path-generation-opt-in|planner_server|controller_server|NavigateToPose|navigate_to_pose|cmd_vel|/api/base/manual|/dev/ttyS5|pkill|killall' \
  "$ART/runtime.stdout" "$ART/runtime.stderr"
rg -n 'safe_to_control.*false|route_execution_success.*false|delivery_success.*false|hil_pass.*false|robot_control_executed.*false' \
  "$ART/runtime-proof.pretty.json"
diff -u "$ART/graph_before.txt" "$ART/graph_after.txt" | tee "$ART/graph_cleanup.diff" || true
git diff --check -- \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/field_route_evidence_preflight.md \
  "$SPRINT"
```

- cleanup 只允许 helper 对自有 PGID 执行，必须记录 PGID identity、attempt、residual `0`；不得清理既有进程。
- 任一 local test、SSH deploy、map audit、subscriber、TF authority、attempt、freshness、JSON assertion、forbidden scan 或 cleanup 失败，由 `robot-algorithm-engineer` 在精确文件范围内定位、修复、重部署并完整复验后再写 `tech-done.md`。
- 不允许因失败改 launch/config，不允许第二次 `/initialpose`；一次已发布后的失败只能读取并收口 exact blocker。

## Proof boundary

即使 clean gate 全通过，本轮边界仍为 `robot_runtime_o3_strict_no_motion_controlled_initialpose_localization_proof_only`。固定不证明机器人真实物理位置准确、planner/path、route execution、delivery/operator acceptance、HIL、safe-to-control、production cloud 或任何底盘控制。
