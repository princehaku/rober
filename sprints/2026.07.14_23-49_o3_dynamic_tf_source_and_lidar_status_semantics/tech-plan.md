# Tech Plan - O3 Dynamic TF Source and LiDAR Status Semantics

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_23-49_o3_dynamic_tf_source_and_lidar_status_semantics/`
- Parallel owner A: `robot-algorithm-engineer`
- Parallel owner B / integration owner: `robot-software-engineer`
- Target: `root@192.168.1.11:37878`
- Boundary: strict no-motion, read-only live probes, no planner

## 并行与集成顺序

主节点必须同轮并行派两个 owner。初始阶段两者各自实现、测试、部署限定脚本、采只读 artifact，
且分别写 owner report；都不得创建 `tech-done.md`。主节点核对两份证据，失败则派回原 owner 修复
复验。两条 lane 最终返回后，才 follow-up `robot-software-engineer` 创建 `tech-done.md` 汇总。

## Owner A - Robot Algorithm Engineer

### 唯一可写范围

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `sprints/2026.07.14_23-49_o3_dynamic_tf_source_and_lidar_status_semantics/artifacts/algorithm/**`

不得写 `tech-done.md`，不得改 planner/route、launch/Nav2/AMCL 参数、地图、LiDAR 配置、
Robot Software 范围、`OKR.md` 或 progress log。

### 实现合同

在现有 `tf_source_freshness.edges.map_to_odom` / `tf_readiness_summary.map_to_odom_dynamic`
中关联 `/tf` endpoint inventory 与 `/amcl` node publisher inventory，输出：

- `publisher_attribution_status`；
- `publisher_endpoint`（node name、namespace、topic type、QoS）或候选列表；
- `source_topic=/tf`、dynamic/static 分类、transform timestamp、freshness status/reason；
- 不能唯一归因时的 exact reason，不得把所有 `/tf` publisher 当 AMCL 已确认来源。

新增技术注释必须为中文且注释比例超过 20%。不得新增或重跑 path/planner wrapper。

### Algorithm 验收命令

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
rg -n 'publisher_attribution|publisher_endpoint|source_topic|timestamp|freshness|map_to_odom|/tf' \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/field_route_evidence_preflight.md
git diff --check -- onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/tests/test_nav2_runtime_proof_helper.py docs/navigation/field_route_evidence_preflight.md \
  sprints/2026.07.14_23-49_o3_dynamic_tf_source_and_lidar_status_semantics/artifacts/algorithm
```

Regression 必须覆盖：dynamic `map->odom` + `/amcl` endpoint 可归因；多 publisher ambiguity；
timestamp/freshness stale/missing；static `map->odom` 不得冒充 dynamic。

真实板仅部署 helper 并读现有 graph；严禁带 `--managed-runtime-opt-in`、
`--initialpose-opt-in`、`--path-generation-opt-in`：

```bash
SPRINT='sprints/2026.07.14_23-49_o3_dynamic_tf_source_and_lidar_status_semantics'
ART="$SPRINT/artifacts/algorithm"; TARGET='root@192.168.1.11'; PORT=37878
REMOTE='/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py'
RAW='/root/rober/onboard/runtime/o3_dynamic_tf_source_inventory.raw.json'
mkdir -p "$ART"; date -u +%Y-%m-%dT%H:%M:%SZ > "$ART/capture_started_at_utc.txt"
shasum -a 256 onboard/scripts/o10_amcl_nav2_runtime_proof.py > "$ART/local_helper.sha256"
scp -P "$PORT" -o BatchMode=yes -o ConnectTimeout=8 \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py "$TARGET:/tmp/o10_amcl_nav2_runtime_proof.py.codex"
ssh -p "$PORT" -o BatchMode=yes -o ConnectTimeout=8 "$TARGET" \
  "install -m 0755 /tmp/o10_amcl_nav2_runtime_proof.py.codex '$REMOTE'; rm -f /tmp/o10_amcl_nav2_runtime_proof.py.codex; sha256sum '$REMOTE'" \
  > "$ART/remote_helper.sha256" 2> "$ART/deploy.stderr.log"
set +e
ssh -p "$PORT" -o BatchMode=yes -o ConnectTimeout=8 "$TARGET" \
  "hostname; date -Ins; timeout --signal=INT --kill-after=8s 90s python3 '$REMOTE' \
   --strict-no-motion --no-base-uart --timeout-s 4 --output '$RAW'" \
  > "$ART/dynamic_tf_source_inventory.stdout.log" 2> "$ART/dynamic_tf_source_inventory.stderr.log"
printf '%s\n' "$?" > "$ART/dynamic_tf_source_inventory.exit_code.txt"
scp -P "$PORT" -o BatchMode=yes -o ConnectTimeout=8 "$TARGET:$RAW" \
  "$ART/dynamic_tf_source_inventory.raw.json"
printf '%s\n' "$?" > "$ART/dynamic_tf_source_inventory.scp_exit_code.txt"; set -e
date -u +%Y-%m-%dT%H:%M:%SZ > "$ART/capture_finished_at_utc.txt"
```

Artifact 必须满足 `collector_mode=read_only_existing_ros_graph_no_motion`、path requested/attempted
均 false、全部 safety fields false。Clean 时 dynamic edge 必须为 `/tf`、publisher attribution 为
AMCL graph endpoint、timestamp parsed 且 freshness `fresh`；否则须有 attribution status/root cause。
执行 `python3 -m json.tool "$ART/dynamic_tf_source_inventory.raw.json" >/dev/null`，并将字段断言、
exit/SHA、失败定位和风险写入 `artifacts/algorithm/owner-report.md`。

## Owner B - Robot Software Engineer

### 唯一可写范围

- `onboard/scripts/o1_lidar_lifecycle.sh`
- `onboard/tests/test_lidar_lifecycle_script.py`
- `docs/hardware/board_sensor_stack_smoke.md`
- `sprints/2026.07.14_23-49_o3_dynamic_tf_source_and_lidar_status_semantics/artifacts/robot_software/**`
- 当前 sprint `tech-done.md`，但仅限 integration follow-up 阶段创建

不得修改 Algorithm 范围、`upper_robot_api.py`/tests、systemd、launch/baudrate 配置、`OKR.md`
或 progress log；API semantics 通过 lifecycle status source 修正完成。

### 实现合同

Bare `status` 不得把默认 `230400` 写成 current。优先级为：running holder `/proc/<pid>/cmdline`
显式参数；PID-matched persisted status；loaded driver diagnostics；当前 `start/__run` explicit
command。候选带 source/status；冲突须 fail closed 或以 holder 为 current 并显式标 conflict。
无 current evidence 时 `baudrate=null`、status=`unknown_no_current_readback`。Vendor truth 独立为
`vendor_reference_baudrate=230400` / `reference_only_not_current`；`150000` 不得称 vendor confirmed。
新增技术注释必须为中文且注释比例超过 20%。

### Robot Software 验收命令

```bash
bash -n onboard/scripts/o1_lidar_lifecycle.sh
python3 -m unittest onboard.tests.test_lidar_lifecycle_script
python3 -m unittest \
  onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_radar_status_prefers_driver_diagnostics_baudrate_over_stale_lifecycle_reference \
  onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_radar_status_does_not_promote_reference_baudrate_without_current_readback
rg -n 'baudrate_readback|holder|diagnostics|current|reference|230400|150000' \
  onboard/scripts/o1_lidar_lifecycle.sh onboard/tests/test_lidar_lifecycle_script.py \
  docs/hardware/board_sensor_stack_smoke.md
git diff --check -- onboard/scripts/o1_lidar_lifecycle.sh onboard/tests/test_lidar_lifecycle_script.py \
  docs/hardware/board_sensor_stack_smoke.md \
  sprints/2026.07.14_23-49_o3_dynamic_tf_source_and_lidar_status_semantics/artifacts/robot_software
```

Tests 覆盖 running PID+150000、holder 优先、PID mismatch stale、diagnostics fallback、无 running
evidence 时不把 230400 当 current、vendor reference 独立、安全字段 false。

真实板只部署 status 脚本；不得 `start`/`stop`、不得重启 LiDAR 或 upper API：

```bash
SPRINT='sprints/2026.07.14_23-49_o3_dynamic_tf_source_and_lidar_status_semantics'
ART="$SPRINT/artifacts/robot_software"; TARGET='root@192.168.1.11'; PORT=37878
REMOTE='/root/rober/onboard/scripts/o1_lidar_lifecycle.sh'; mkdir -p "$ART"
shasum -a 256 onboard/scripts/o1_lidar_lifecycle.sh > "$ART/local_script.sha256"
scp -P "$PORT" -o BatchMode=yes -o ConnectTimeout=8 \
  onboard/scripts/o1_lidar_lifecycle.sh "$TARGET:/tmp/o1_lidar_lifecycle.sh.codex"
ssh -p "$PORT" -o BatchMode=yes -o ConnectTimeout=8 "$TARGET" \
  "install -m 0755 /tmp/o1_lidar_lifecycle.sh.codex '$REMOTE'; rm -f /tmp/o1_lidar_lifecycle.sh.codex; sha256sum '$REMOTE'" \
  > "$ART/remote_script.sha256" 2> "$ART/deploy.stderr.log"
set +e
ssh -p "$PORT" -o BatchMode=yes -o ConnectTimeout=8 "$TARGET" \
  "timeout 8s bash '$REMOTE' status" > "$ART/lidar_lifecycle_status.current.json" \
  2> "$ART/lidar_lifecycle_status.stderr.log"; printf '%s\n' "$?" > "$ART/lidar_lifecycle_status.exit_code.txt"
ssh -p "$PORT" -o BatchMode=yes -o ConnectTimeout=8 "$TARGET" \
  'curl -fsS --max-time 8 http://127.0.0.1:8787/api/radar/status' \
  > "$ART/radar_status.current.json" 2> "$ART/radar_status.stderr.log"
printf '%s\n' "$?" > "$ART/radar_status.exit_code.txt"; set -e
```

两 JSON 均须通过 `python3 -m json.tool`。Clean 要求 lifecycle running、current baudrate `150000`
来自 holder/PID-matched status/diagnostics，API 同为 `150000`；两者 vendor reference 都为
`230400`，全部 safety fields false。字段断言、exit/SHA、失败和风险写入
`artifacts/robot_software/owner-report.md`。

## 失败继续定位

- SSH `255`：保留 stderr，只重试一次 identity/read-only command。
- `/tf` publisher 不唯一：保留 candidates/QoS 并 fail closed，不用 tf2 buffer 补成 attributed。
- timestamp 缺失、clock domain 不可比或 stale：分别记录原因，不用 wall clock 冒充 ROS stamp。
- holder/status/diagnostics 冲突：holder 优先并标 conflict；PID mismatch status 只能是 stale。
- status/API 仍报 synthetic `230400` current：派回 Robot Software；不得修改/重启实际 150000 lifecycle。
- 任一 test/JSON/assertion/diff-check 失败，必须派回原 owner 修复复验后才能验收。

## OKR 最低优先级核对

1. `OKR.md` 4.1 最低是 Objective 5，约 `85%`；O6/O7 约 `93%`，O1 约 `94%`。
2. 本 sprint 不直接针对 Objective 5，转向 O3 dynamic TF source 与 LiDAR current status semantics。
3. 14:38 export、15:38 relay HTTP、16:40 headless browser 已连续消费 production/cloud blocker；
   继续 relay/browser/export 违反 no-repeat/WIP。CEO 已提供 `192.168.1.11:37878`，本轮两个 exact
   runtime gap 可推进且不重复 planner wrapper。`final.md` 必须复核该理由。

## 计划阶段验收命令

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|85%|map_to_odom_dynamic_source_not_observed_in_tf_source_inventory|192.168.1.11|37878|strict no-motion|robot-algorithm-engineer|robot-software-engineer|/tf|150000|230400|reference|dynamic" sprints/2026.07.14_23-49_o3_dynamic_tf_source_and_lidar_status_semantics
git diff --check -- sprints/2026.07.14_23-49_o3_dynamic_tf_source_and_lidar_status_semantics
test ! -e sprints/2026.07.14_23-49_o3_dynamic_tf_source_and_lidar_status_semantics/tech-done.md && test ! -e sprints/2026.07.14_23-49_o3_dynamic_tf_source_and_lidar_status_semantics/side2side_check.md && test ! -e sprints/2026.07.14_23-49_o3_dynamic_tf_source_and_lidar_status_semantics/final.md
```

成功只接受为 O3/O1 dynamic TF attribution 与 LiDAR status semantics evidence，不证明 planner、
route execution、delivery/operator acceptance、HIL、safe-to-control 或 O5 production cloud。
