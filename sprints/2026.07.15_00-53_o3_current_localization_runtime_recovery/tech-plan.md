# Technical Plan

- sprint_type: epic
- 状态：计划完成，下一阶段由 Engineer 实施与验证。
- 主责 owner：`robot-algorithm-engineer`。
- 并行咨询：`robot-software-engineer`，严格只读，不改文件。

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 最低 Objective：O5（85%）。
- 本 sprint 不直接针对 O5，改为推进 O1（94%）中的 O3 localization runtime。
- 理由：O5 缺真实 production endpoint/凭证，且 support-only 已连续重复消费。
- 本轮选择有真实上位机、可 strict-no-motion 推进的最低可行动 live 项。

## Algorithm 唯一可写范围

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `sprints/2026.07.15_00-53_o3_current_localization_runtime_recovery/artifacts/algorithm/**`
- `sprints/2026.07.15_00-53_o3_current_localization_runtime_recovery/tech-done.md`
- launch/config 本轮不在可写范围；只有出现精确失败证据后，回报主节点再获授权。

## Robot Software 只读范围

- 可只读核对上述 helper、相关 launch/source、远端 graph、topic、lifecycle 与进程来源。
- 只返回 `/map_server`、`/amcl`、`/scan`、`/amcl_pose`、TF 及启动依赖事实。
- 禁止修改任何仓库或远端文件，禁止启动/停止节点，禁止发布 topic。

## 本地验收命令

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
python3 -m unittest onboard/tests/test_nav2_runtime_proof_helper.py
rg -n 'strict-no-motion|managed-runtime-opt-in|managed-map-yaml|reuse-existing-lidar-lifecycle|no-base-uart' onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/tests/test_nav2_runtime_proof_helper.py docs/navigation/field_route_evidence_preflight.md
git diff --check -- onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/tests/test_nav2_runtime_proof_helper.py docs/navigation/field_route_evidence_preflight.md sprints/2026.07.15_00-53_o3_current_localization_runtime_recovery
```

## 部署、只读 discovery 与证据目录

```bash
set -euo pipefail
SPRINT=sprints/2026.07.15_00-53_o3_current_localization_runtime_recovery
ART="$SPRINT/artifacts/algorithm"
TARGET=root@192.168.1.11
PORT=37878
REMOTE=/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
RAW=/tmp/o3_current_localization_runtime_recovery.json
mkdir -p "$ART"
date -u +%Y-%m-%dT%H:%M:%SZ | tee "$ART/deploy_started_at.txt"
shasum -a 256 onboard/scripts/o10_amcl_nav2_runtime_proof.py | tee "$ART/helper_local_sha256.txt"
scp -P "$PORT" onboard/scripts/o10_amcl_nav2_runtime_proof.py "$TARGET:$REMOTE"
ssh -p "$PORT" "$TARGET" "sha256sum '$REMOTE'" | tee "$ART/helper_remote_sha256.txt"
ssh -p "$PORT" "$TARGET" "find /root/rober/onboard -type f -name '*.yaml' -print | sort" | tee "$ART/map_yaml_candidates.txt"
rg -n 'managed.map|map.yaml|resolve.*map|yaml' onboard/scripts/o10_amcl_nav2_runtime_proof.py | tee "$ART/helper_map_resolution_rules.txt"
```

- Algorithm 仅按 helper 已有 map resolution 规则核对 `map_yaml_candidates.txt`。
- 只有规则唯一命中时，才把该绝对路径单行写入 `$ART/managed_map_yaml.txt`。
- 无命中、多命中或无法证明唯一时立即 fail-closed；不得按文件名、时间或经验猜测。

```bash
test "$(sed '/^[[:space:]]*$/d' "$ART/managed_map_yaml.txt" | wc -l | tr -d ' ')" -eq 1
MAP="$(sed -n '1p' "$ART/managed_map_yaml.txt")"
case "$MAP" in /root/rober/onboard/*.yaml) ;; *) exit 64 ;; esac
ssh -p "$PORT" "$TARGET" "test -f '$MAP' && test -r '$MAP'"
```

## Strict-No-Motion 现场命令

```bash
ssh -p "$PORT" "$TARGET" "ros2 node list; ros2 topic list" >"$ART/graph_before.txt" 2>"$ART/graph_before.stderr"
date -u +%Y-%m-%dT%H:%M:%SZ | tee "$ART/run_started_at.txt"
set +e
ssh -p "$PORT" "$TARGET" "timeout --signal=INT --kill-after=8s 150s python3 '$REMOTE' --strict-no-motion --no-base-uart --managed-runtime-opt-in --reuse-existing-lidar-lifecycle --managed-map-yaml '$MAP' --managed-timeout-s 70 --timeout-s 4 --output '$RAW'" >"$ART/runtime.stdout" 2>"$ART/runtime.stderr"
RUN_EXIT=$?
set -e
printf '%s\n' "$RUN_EXIT" | tee "$ART/runtime.exit"
date -u +%Y-%m-%dT%H:%M:%SZ | tee "$ART/run_finished_at.txt"
set +e
scp -P "$PORT" "$TARGET:$RAW" "$ART/runtime-proof.json" >"$ART/pull.stdout" 2>"$ART/pull.stderr"
PULL_EXIT=$?
set -e
printf '%s\n' "$PULL_EXIT" | tee "$ART/pull.exit"
ssh -p "$PORT" "$TARGET" "ros2 node list; ros2 topic list" >"$ART/graph_after.txt" 2>"$ART/graph_after.stderr"
```

- 命令固定不含 initialpose、`--path-generation-opt-in`、planner/controller、NavigateToPose、`cmd_vel`、base/manual 或 motion。
- `timeout` 只能向本轮 helper 自有 process group 发送 INT/KILL；禁止 `pkill`、`killall` 或清理既有节点。

## JSON、结构、cleanup 与 false flags 验收

```bash
test "$(cat "$ART/runtime.exit")" -eq 0
test "$(cat "$ART/pull.exit")" -eq 0
python3 -m json.tool "$ART/runtime-proof.json" >"$ART/runtime-proof.pretty.json"
python3 -c 'import json,sys; p=sys.argv[1]; d=json.load(open(p)); assert isinstance(d,dict) and d' "$ART/runtime-proof.json"
rg -n '/scan|/amcl_pose|map.?to.?odom|amcl|endpoint|timestamp|fresh|process_group|cleanup' "$ART/runtime-proof.pretty.json" "$ART/runtime.stdout" "$ART/runtime.stderr"
rg -n 'safe_to_control.*false|route_execution_success.*false|delivery_success.*false|hil_pass.*false' "$ART/runtime-proof.pretty.json"
! rg -n -- '--path-generation-opt-in|initialpose|NavigateToPose|cmd_vel|base/manual|motion command|planner_server|controller_server' "$ART/runtime.stdout" "$ART/runtime.stderr"
diff -u "$ART/graph_before.txt" "$ART/graph_after.txt" | tee "$ART/graph_cleanup.diff" || true
git diff --check -- onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/tests/test_nav2_runtime_proof_helper.py docs/navigation/field_route_evidence_preflight.md "$SPRINT"
```

- 结构验收必须证明 `/scan`、`/amcl_pose` 与 dynamic `map->odom` 属于同一窗口，并记录 AMCL endpoint/timestamp/freshness。
- cleanup 必须由 helper 自有 process group 完成；`graph_cleanup.diff` 中不得出现本轮遗留节点。
- 任一 guard、唯一 map、节点来源、freshness、dynamic TF、退出码或 cleanup 失败即 fail-closed。
- 验收记录固定：`safe_to_control=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`。
- 静态 `map->odom`、旧窗口、local fix 或仅启动成功均不能替代 live AMCL 证据。
- 验证失败由 Algorithm 在唯一可写范围内定位、修复、重部署并复验，再更新 `tech-done.md`。
