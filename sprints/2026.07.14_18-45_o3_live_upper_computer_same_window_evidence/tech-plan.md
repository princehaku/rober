# Tech Plan - O3 Live Upper-Computer Same-Window Evidence

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_18-45_o3_live_upper_computer_same_window_evidence/`
- Single implementation/integration owner: `robot-algorithm-engineer`
- Target: `root@192.168.1.11:37878`
- Boundary: strict `no-motion`

## Owner 和执行顺序

`robot-algorithm-engineer` 单线闭环完成 SSH preflight、fresh live capture、artifact 拉回、结构验收、
失败定位、必要修复、复验和 `tech-done.md`。不并行派其他 owner，不创建共享文件并行。

执行顺序固定为：

1. 记录 target、local/remote 时间、hostname、helper SHA、ROS source/map/helper 存在性。
2. 只读 `http://127.0.0.1:8787/api/radar/status`；只有 current readback 证明现有 lifecycle 为
   `/dev/ttyACM0 @ 150000` 时才进入 helper run，否则以 exact root cause 收口，不改硬件配置。
3. 运行一次有界 `o10_amcl_nav2_runtime_proof.py` strict no-motion capture。
4. 无论 exit `0/2/124` 都尝试拉回 remote raw/partial JSON；exit `255` 保留 SSH stderr。
5. 生成 current-window capture envelope并验证。只有 artifact 证明 helper 自身有明确 bug，才允许
   修改 helper/tests/docs，随后复跑 targeted tests 和同一 live command 一次。
6. 更新 `tech-done.md`，记录实际改动、完整 exit code、关键输出、失败定位和剩余风险。

## 文件范围

Algorithm owner 必改/可生成：

- `sprints/2026.07.14_18-45_o3_live_upper_computer_same_window_evidence/artifacts/algorithm/**`
- `sprints/2026.07.14_18-45_o3_live_upper_computer_same_window_evidence/tech-done.md`

仅当 fresh live artifact 明确证明 helper bug 时才允许修改：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`

禁止修改 `OKR.md`、O5/O6/O7/PC 代码、launch/hardware 配置、地图、AMCL/Nav2 参数、LiDAR
baudrate/port、WAVE ROVER driver/firmware，以及范围外文件。

## 接口和安全边界

本轮不新增产品接口，不执行路线，不驱动底盘。允许的 ROS 行为只有只读 topic/lifecycle/TF/
AMCL/map probes、no-motion localization 初始化和 planner-only `ComputePathToPose`。

严禁发布 `/cmd_vel`、调用 `/api/base/manual`、运行 `NavigateToPose`、controller/BT、打开
WAVE ROVER UART 或发送任何非零底盘命令。LiDAR 只复用 current readback 已确认的 existing
lifecycle，helper 必须带 `--reuse-existing-lidar-lifecycle`，不得启动第二个 LiDAR driver。

Artifact 顶层和 `proof` 中的以下值必须固定为 false：

```text
safe_to_control
publishes_cmd_vel
calls_base_manual
uses_base_uart
robot_control_executed
route_execution_success
delivery_success
hil_pass
```

## SSH 和 Fresh Live Capture 命令

以下命令由 Algorithm owner 在实现阶段执行；Product 计划阶段不得运行 SSH。外层预算为
480 秒，remote helper budget 为 450 秒，planner action budget 为 30 秒，SSH connect timeout
为 8 秒。所有 exit code 必须原样记录，禁止用无条件 `|| true` 抹平失败。

```bash
set -u
SPRINT="sprints/2026.07.14_18-45_o3_live_upper_computer_same_window_evidence"
ART="$SPRINT/artifacts/algorithm"
TARGET_HOST="192.168.1.11"
TARGET_PORT="37878"
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
REMOTE_HELPER="/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py"
REMOTE_RAW="/root/rober/onboard/runtime/o3_live_upper_computer_same_window_${RUN_ID}.raw.json"
LOCAL_REMOTE_RAW="$ART/live_upper_computer_same_window_evidence.remote.raw.json"
mkdir -p "$ART"

date -u +%Y-%m-%dT%H:%M:%SZ > "$ART/capture_started_at_utc.txt"
sha256sum onboard/scripts/o10_amcl_nav2_runtime_proof.py > "$ART/local_helper.sha256"

set +e
timeout 30s ssh -p "$TARGET_PORT" \
  -o BatchMode=yes -o ConnectTimeout=8 -o ServerAliveInterval=10 -o ServerAliveCountMax=2 \
  "root@$TARGET_HOST" \
  'set -u; printf "remote_hostname="; hostname; printf "remote_time="; date -Ins; \
   test -s /root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py; \
   sha256sum /root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py; \
   test -s /root/rober/onboard/runtime/maps/trashbot_map.yaml; \
   curl -fsS --max-time 8 http://127.0.0.1:8787/api/radar/status' \
  > "$ART/preflight.stdout.log" 2> "$ART/preflight.stderr.log"
PREFLIGHT_RC=$?
printf '%s\n' "$PREFLIGHT_RC" > "$ART/preflight.exit_code.txt"
set -e
```

Preflight exit 非 0，或 current radar JSON 不是 `baudrate=150000` / existing lifecycle 时，停止
helper run：保留 target、timestamps、stdout/stderr/exit，exact root cause 分别写为 SSH/source/map/
radar readback 层，不猜参数、不重启服务、不抢串口。

Preflight clean 后运行：

```bash
set +e
timeout --signal=INT --kill-after=20s 480s ssh -p "$TARGET_PORT" \
  -o BatchMode=yes -o ConnectTimeout=8 -o ServerAliveInterval=10 -o ServerAliveCountMax=2 \
  "root@$TARGET_HOST" \
  "timeout --signal=INT --kill-after=15s 450s python3 '$REMOTE_HELPER' \
    --strict-no-motion \
    --no-base-uart \
    --managed-runtime-opt-in \
    --reuse-existing-lidar-lifecycle \
    --managed-lidar-serial-port /dev/ttyACM0 \
    --managed-lidar-serial-baudrate 150000 \
    --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml \
    --initialpose-opt-in \
    --path-generation-opt-in \
    --path-generation-timeout-s 30 \
    --timeout-s 18 \
    --output '$REMOTE_RAW'" \
  > "$ART/live_upper_computer_same_window_evidence.stdout.log" \
  2> "$ART/live_upper_computer_same_window_evidence.stderr.log"
CAPTURE_RC=$?
printf '%s\n' "$CAPTURE_RC" > "$ART/live_upper_computer_same_window_evidence.exit_code.txt"

timeout 35s scp -P "$TARGET_PORT" \
  -o BatchMode=yes -o ConnectTimeout=8 \
  "root@$TARGET_HOST:$REMOTE_RAW" "$LOCAL_REMOTE_RAW"
SCP_RC=$?
printf '%s\n' "$SCP_RC" > "$ART/live_upper_computer_same_window_evidence.scp_exit_code.txt"
date -u +%Y-%m-%dT%H:%M:%SZ > "$ART/capture_finished_at_utc.txt"
set -e
```

Owner 随后从上述原始文件生成
`artifacts/algorithm/live_upper_computer_same_window_evidence.raw.json` capture envelope。该 envelope
必须保留原始 proof，不得把历史 artifact 拼成 current result；同时写入：

- `schema=trashbot.o3.live_upper_computer_same_window_evidence.v1`
- `target_host=192.168.1.11`、`target_port=37878`、remote hostname
- local/remote started/finished timestamps、local/remote helper SHA
- `preflight_exit_code`、`capture_exit_code`、`scp_exit_code`、remote raw path
- `fresh_live_attempted=true`、`historic_artifact_used_as_current_live_proof=false`
- `proof_boundary=robot_runtime_o3_strict_no_motion_localization_planner_evidence_only`
- remote proof 和固定 false safety fields

## 失败继续定位和修复规则

- `PREFLIGHT_RC=255`：只允许再跑一次同样的 identity SSH，增加 `-v` 保存 transport stderr；
  收敛为 connect timeout、auth、host key 或 server disconnect，不做代码修复。
- radar status exit/non-JSON/baudrate/lifecycle 不一致：记录 current readback exact root cause；不改
  port/baudrate、不启动第二个 driver，交后续 hardware/robot-software 事实任务。
- `CAPTURE_RC=124`：优先拉 partial raw JSON，读取 `last_phase/current_command/root_causes`；不能
  只写 generic timeout。
- `CAPTURE_RC=2`：这是 helper fail-closed 结果；按 artifact 的 ROS source、lifecycle、topic、TF
  或 planner layer 收口，不自动修改 helper。
- `CAPTURE_RC=0` 但关键字段缺失/自相矛盾，或 helper 没有持久化已观察到的 CLI result：才认定
  helper bug。由同一 owner在限定文件内修复，补 targeted regression，运行本地验证，部署并核对
  SHA 后只复跑一次同一 live command。
- `/scan`、`/amcl_pose`、dynamic `map_to_odom`、map/AMCL lifecycle 或 planner unavailable 属于
  runtime root cause，不得为了变绿而伪造字段或回填旧 artifact。

## 实现验收命令

Algorithm owner 必须运行并把输出写入 `tech-done.md`：

```bash
python3 -m json.tool \
  sprints/2026.07.14_18-45_o3_live_upper_computer_same_window_evidence/artifacts/algorithm/live_upper_computer_same_window_evidence.raw.json \
  >/dev/null

python3 - <<'PY'
import json
from pathlib import Path

p = Path("sprints/2026.07.14_18-45_o3_live_upper_computer_same_window_evidence/artifacts/algorithm/live_upper_computer_same_window_evidence.raw.json")
d = json.loads(p.read_text(encoding="utf-8"))
assert d["schema"] == "trashbot.o3.live_upper_computer_same_window_evidence.v1"
assert d["target_host"] == "192.168.1.11"
assert d["target_port"] == 37878
assert d["fresh_live_attempted"] is True
assert d["historic_artifact_used_as_current_live_proof"] is False
assert d["proof_boundary"] == "robot_runtime_o3_strict_no_motion_localization_planner_evidence_only"
assert d.get("capture_started_at_utc") and d.get("capture_finished_at_utc")
assert d.get("remote_hostname") and d.get("local_helper_sha256") and d.get("remote_helper_sha256")
proof = d["proof"]
for key in ("safe_to_control", "publishes_cmd_vel", "calls_base_manual", "uses_base_uart",
            "robot_control_executed", "route_execution_success", "delivery_success", "hil_pass"):
    assert d.get(key) is False and proof.get(key) is False, key

facts = {
    "scan": bool(proof.get("scan_once_observed")),
    "amcl_pose": bool(proof.get("amcl_pose_observed")),
    "map_server_active": bool(proof.get("map_server_active")),
    "amcl_active": bool(proof.get("amcl_active")),
    "map_to_odom_dynamic": bool(((proof.get("tf_readiness_summary") or {}).get("map_to_odom_dynamic") or {}).get("dynamic_source_observed")),
    "path_attempted": bool(proof.get("path_generation_attempted")),
    "path_generated": bool(proof.get("path_generated")),
    "path_point_count": int(proof.get("path_point_count") or 0),
}
clean = all((facts["scan"], facts["amcl_pose"], facts["map_server_active"], facts["amcl_active"],
             facts["map_to_odom_dynamic"], facts["path_attempted"], facts["path_generated"],
             facts["path_point_count"] > 0))
if not clean:
    causes = proof.get("root_causes") or d.get("exact_root_causes") or []
    assert causes, facts
print("live_upper_computer_same_window_evidence_acceptance_ok", facts)
PY

rg -n '192\.168\.1\.11|37878|/scan|/amcl_pose|map_server_active|amcl_active|map_to_odom|ComputePathToPose|path_generation_attempted|path_generated|path_point_count|root_causes|safe_to_control|publishes_cmd_vel|calls_base_manual|uses_base_uart|route_execution_success|delivery_success|hil_pass' \
  sprints/2026.07.14_18-45_o3_live_upper_computer_same_window_evidence/artifacts/algorithm \
  sprints/2026.07.14_18-45_o3_live_upper_computer_same_window_evidence/tech-done.md

git diff --check -- \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/field_route_evidence_preflight.md \
  docs/navigation/fixed_route_workflow.md \
  sprints/2026.07.14_18-45_o3_live_upper_computer_same_window_evidence
```

只有 helper 被修改时额外运行：

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
sha256sum onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

## 计划阶段验收命令

Product owner 只运行以下本地文档验收命令，不运行 SSH、helper 或 live capture：

```bash
test -s sprints/2026.07.14_18-45_o3_live_upper_computer_same_window_evidence/pre_start.md && test -s sprints/2026.07.14_18-45_o3_live_upper_computer_same_window_evidence/prd.md && test -s sprints/2026.07.14_18-45_o3_live_upper_computer_same_window_evidence/tech-plan.md
rg -n 'sprint_type: epic|OKR 最低优先级核对|robot-algorithm-engineer|192\.168\.1\.11|37878|no-motion|/cmd_vel|/api/base/manual|NavigateToPose|WAVE ROVER UART|o10_amcl_nav2_runtime_proof.py|验收命令' sprints/2026.07.14_18-45_o3_live_upper_computer_same_window_evidence/{pre_start.md,prd.md,tech-plan.md}
git diff --check -- sprints/2026.07.14_18-45_o3_live_upper_computer_same_window_evidence
```

## OKR 最低优先级核对

1. `OKR.md` 4.1 当前最低 Objective 是 O5，约 `85%`；O6/O7 约 `93%`，O1 约 `94%`。
2. 本 sprint 不直接针对 O5，改走 O3 navigation lane，为 O1 采 current same-window live evidence。
3. 不针对 O5 的原因：CLI export、live relay HTTP、headless browser 已连续消费同一 production/
   cloud external-evidence blocker，且仍是 support-only；再做 wrapper 会触发重复消费和 WIP 红线。
   CEO 已提供 `192.168.1.11:37878` 真实上位机，fresh no-motion localization/planner artifact 是
   当前环境可直接推进的更强证据类。本理由在 final closeout 时必须复核。

## 验收结果边界

成功仅接受为 current-window true-board strict no-motion localization/planner evidence。它不证明
`NavigateToPose`、route execution、delivery/operator acceptance、current live HIL、
safe-to-control、WAVE ROVER UART 或 O5 production cloud。失败只有在 current-run raw evidence、
target/timestamp/exit code 和 exact root cause 完整时才可收口；否则必须由同一 owner继续定位。
