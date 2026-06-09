# Tech Done - Board Live Evidence Capture

## sprint_type

`sprint_type: epic`

## 自主能力目标和本轮抓手

本轮目标是执行 `board_live_evidence_capture` 的实现/验证阶段，把 CEO 提供的真实上位机入口：

```bash
ssh root@192.168.1.11 -p 37878
```

转成 O3 现场证据，优先获取 `map.yaml`、`route.csv`、keyframe、rosbag 或 replay JSONL。实际执行结果是 live SSH 失败在网络路由层，因此未进入 ROS2 topic smoke、learn.launch、地图保存、路线采集或 rosbag capture；随后按 tech-plan 执行 fallback evidence，产出标准 SSH preflight JSON、local dry-run JSON、manifest fixture JSON 和 CEO 决策点。

本轮只涉及 SSH/network/ROS2 preflight 与离线 fixture，不涉及摄像头安装、物理尺寸、底盘运动、UART、WAVE ROVER 指令、电压或机械安全假设，因此未引用 `docs/vendor/VENDOR_INDEX.md` 做硬件结论。

## 实际改动文件和接口影响

实际改动文件：

- `sprints/2026.06.09_20-21_board-live-evidence-capture/tech-done.md`
- `sprints/2026.06.09_20-21_board-live-evidence-capture/side2side_check.md`
- `sprints/2026.06.09_20-21_board-live-evidence-capture/final.md`

接口影响：

- 未修改产品代码、测试代码、launch、硬件配置、`OKR.md` 或 `docs/` 业务文档。
- 未改变 `delivery_success`、`safe_to_control`、`primary_actions_enabled`、`not_proven` 等 fail-closed 语义。
- 仅生成 `/tmp` 下执行证据和本 sprint 收口文档。

## 验证命令与关键输出

### 本机工作区状态

```bash
git status --short --branch
```

关键输出：

```text
## master...origin/master
?? sprints/2026.06.09_20-21_board-live-evidence-capture/
```

### 真实 SSH preflight

```bash
ssh -o BatchMode=yes -o ConnectTimeout=5 root@192.168.1.11 -p 37878 "echo board_live_ssh_ok && hostname && date"
```

结果：失败，退出码 `255`。

关键输出：

```text
ssh: connect to host 192.168.1.11 port 37878: No route to host
```

分层定位：失败发生在本机到 `192.168.1.11:37878` 的网络路由/可达性层，尚未进入 SSH 鉴权、上位机 shell、ROS2 setup、topic 或 capture 阶段。

### SSH 模式 preflight JSON

```bash
python3 onboard/scripts/field_route_evidence_preflight.py --mode ssh --ssh-target root@192.168.1.11 --ssh-port 37878 --timeout-s 5 --output /tmp/trashbot_field_preflight_ssh.json
python3 -m json.tool /tmp/trashbot_field_preflight_ssh.json >/tmp/trashbot_field_preflight_ssh.pretty.json
```

关键输出：

```json
{"output": "/tmp/trashbot_field_preflight_ssh.json", "schema": "trashbot.board_field_evidence_preflight.v1", "status": "blocked_ssh_unreachable"}
```

关键 JSON 字段：

```json
{
  "status": "blocked_ssh_unreachable",
  "blocked_reason": "blocked_ssh_unreachable",
  "target": {
    "mode": "ssh",
    "ssh_port": 37878,
    "ssh_target": "root@192.168.1.11",
    "timeout_s": 5
  },
  "delivery_success": false,
  "not_proven": true,
  "primary_actions_enabled": false,
  "safe_to_control": false
}
```

### Board evidence CLI

```bash
bash -n onboard/scripts/board_live_route_preflight.sh
bash onboard/scripts/board_live_route_preflight.sh --help
bash onboard/scripts/board_live_route_preflight.sh --dry-run --local-only
bash onboard/scripts/board_live_route_preflight.sh --skip-capture
```

结果：

- `bash -n`：通过。
- `--help`：通过，展示默认 `host=192.168.1.11`、`port=37878`，以及 `--dry-run`、`--local-only`、`--skip-capture` 等入口。
- `--dry-run --local-only`：通过，输出 capture/replay 模板，log 路径为 `/Users/m1/.ros/trashbot_live_preflight/20260609_201142_28152.log`。
- `--skip-capture`：退出码 `2`，按设计暴露 SSH/network blocker，log 路径为 `/Users/m1/.ros/trashbot_live_preflight/20260609_201149_28282.log`。

`--dry-run --local-only` 关键输出：

```text
default_gateway=192.168.1.1
ping 192.168.1.1 exit=2
ping 192.168.1.11 exit=2
nc 192.168.1.11:37878 exit=1
local-only mode: skip ssh and remote checks.
dry-run mode: capture commands are emitted for manual execution only.
capture_plan_dir=/Users/m1/.ros/trashbot_live_runs/20260609_201142_28152
```

`--skip-capture` 关键输出：

```text
ping 192.168.1.11 exit=2
nc 192.168.1.11:37878 exit=1
ssh 192.168.1.11:37878 exit=255
ssh handshake failed; continue with failure log.
ssh unavailable; exiting non-zero by design to expose network blocker clearly.
```

### Local fallback preflight JSON

```bash
python3 onboard/scripts/field_route_evidence_preflight.py --mode local --dry-run --output /tmp/trashbot_field_preflight_local.json
python3 -m json.tool /tmp/trashbot_field_preflight_local.json >/tmp/trashbot_field_preflight_local.pretty.json
```

关键输出：

```json
{"output": "/tmp/trashbot_field_preflight_local.json", "schema": "trashbot.board_field_evidence_preflight.v1", "status": "dry_run_template_only_not_proven"}
```

关键 JSON 字段：

```json
{
  "status": "dry_run_template_only_not_proven",
  "blocked_reason": "dry_run_template_only_not_proven",
  "delivery_success": false,
  "dry_run": true,
  "not_proven": true,
  "primary_actions_enabled": false,
  "safe_to_control": false
}
```

### Manifest fixture

按 tech-plan 原 fallback fixture 命令执行时，fixture 目录包含 `map.yaml`、`route.csv`、`keyframes/0001.json`、`route_bag/metadata.yaml`，但未创建 `replay.jsonl`。当前 manifest 脚本把 `replay_jsonl` 也列为 required artifact，因此第一次 gate 失败：

```json
{
  "status": "blocked_artifacts_missing",
  "artifact_status": "missing",
  "missing_artifacts": ["replay_jsonl"],
  "present_artifacts": ["map_yaml", "route_csv", "keyframes", "rosbag"],
  "gate_pass": false,
  "delivery_success": false,
  "not_proven": true,
  "safe_to_control": false
}
```

为区分计划 fixture 偏差和 manifest CLI 能力，保留失败文件：

- `/tmp/trashbot_field_manifest_missing_replay.json`
- `/tmp/trashbot_field_manifest_missing_replay.pretty.json`

随后追加 dry-run fixture `replay.jsonl` 并复跑：

```bash
printf '{"t":0,"x":0,"y":0,"yaw":0,"state":"dry_run_fixture"}\n' >/tmp/trashbot_field_manifest_fixture_complete/replay.jsonl
python3 onboard/scripts/field_route_evidence_manifest.py --mode local --artifact-root /tmp/trashbot_field_manifest_fixture_complete --preflight-json /tmp/trashbot_field_preflight_local.json --output /tmp/trashbot_field_manifest_complete.json
python3 -m json.tool /tmp/trashbot_field_manifest_complete.json >/tmp/trashbot_field_manifest_complete.pretty.json
```

关键输出：

```json
{"gate_pass": true, "output": "/tmp/trashbot_field_manifest_complete.json", "schema": "trashbot.field_evidence_manifest.v1", "status": "field_evidence_manifest_ready_not_delivery_proof"}
```

关键 JSON 字段：

```json
{
  "status": "field_evidence_manifest_ready_not_delivery_proof",
  "artifact_status": "gated",
  "present_artifacts": ["map_yaml", "route_csv", "keyframes", "rosbag", "replay_jsonl"],
  "gate_pass": true,
  "blocked_reason": "dry_run_template_only_not_proven",
  "delivery_success": false,
  "not_proven": true,
  "primary_actions_enabled": false,
  "safe_to_control": false
}
```

结论：manifest gate 可以消费完整材料目录；但本次材料是 local fixture，不是 live O3 现场证据，不能提升为真实送达或真实路线完成。

### 单元测试和静态检查

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/scripts/field_route_evidence_preflight.py onboard/scripts/field_route_evidence_manifest.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/tests/test_field_route_evidence_preflight.py onboard/tests/test_field_route_evidence_manifest.py
```

关键输出：

```text
Ran 10 tests in 0.042s
OK
```

### 文档搜索检查

```bash
rg -n "board_live_evidence_capture|功能点完整性|ssh root@192.168.1.11 -p 37878|map.yaml|route.csv|keyframe|rosbag|replay JSONL|blocked_ssh_unreachable|CEO 决策点" sprints/2026.06.09_20-21_board-live-evidence-capture
```

结果：通过，匹配到 `pre_start.md`、`prd.md`、`tech-plan.md` 中的功能点、入口、产物门槛、`blocked_ssh_unreachable` 和 CEO 决策点。

## 失败定位

本轮 live 失败根因不是 ROS2、Nav2、route recorder、manifest 或 replay，而是网络可达性：

- `ssh root@192.168.1.11 -p 37878` 返回 `No route to host`。
- `board_live_route_preflight.sh --skip-capture` 中 `ping 192.168.1.11` 失败、`nc 192.168.1.11:37878` 失败、SSH handshake 失败。
- 因 SSH 不可达，无法安全进入上位机 `hostname/date`、`command -v ros2`、workspace setup、`ros2 topic list`、`/scan`、`/camera/image_raw`、`/odom`、`/tf`、`/map` smoke。
- 未执行任何运动命令，未启动 live capture，未声称 `safe_to_control=true`。

## 数据、样本或调试输出变化

本轮新增或刷新以下本地执行证据：

- `/tmp/trashbot_field_preflight_ssh.json`
- `/tmp/trashbot_field_preflight_ssh.pretty.json`
- `/tmp/trashbot_field_preflight_local.json`
- `/tmp/trashbot_field_preflight_local.pretty.json`
- `/tmp/trashbot_field_manifest_missing_replay.json`
- `/tmp/trashbot_field_manifest_missing_replay.pretty.json`
- `/tmp/trashbot_field_manifest_complete.json`
- `/tmp/trashbot_field_manifest_complete.pretty.json`
- `/tmp/trashbot_field_manifest_fixture_complete/`
- `/Users/m1/.ros/trashbot_live_preflight/20260609_201142_28152.log`
- `/Users/m1/.ros/trashbot_live_preflight/20260609_201149_28282.log`

这些材料是 fallback/debug evidence，不是 live route/map evidence。

## 剩余风险与下一步建议

剩余风险：

- 真实上位机 `192.168.1.11:37878` 对当前开发机不可路由，O3 live evidence 未产出。
- 因 SSH 不通，尚未验证上位机 ROS2 Humble、trashbot package、`/scan`、`/camera/image_raw`、`/odom`、`/tf`、`/map` topic。
- 执行中发现 tech-plan 原 fixture 命令缺少 `replay.jsonl`，与当前 manifest required artifact 集合存在轻微偏差；验收后已补正本 sprint `tech-plan.md` 的 fallback fixture 命令。后续若调整 manifest required 集合，仍需同步计划和脚本帮助文本。

CEO 决策点：

1. 确认上位机是否开机、是否连接到与开发机同一局域网，且 IP 仍为 `192.168.1.11`。
2. 确认端口 `37878` 是否仍映射到上位机 SSH 服务，或提供新的 host/port。
3. 若开发机不在现场同网段，请切到现场网络、VPN/WireGuard/frp，或由现场人员从上位机导出 `map.yaml`、`route.csv`、keyframes、route_bag、replay.jsonl` 后交给 manifest gate。
4. 下一轮若入口可达，优先执行 board runtime/topic smoke，再做非运动的静态 rosbag/topic capture；只有现场安全条件明确时才运行 learn.launch route recorder。
