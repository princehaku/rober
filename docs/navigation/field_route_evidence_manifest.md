# Field Route Evidence Manifest

`onboard/scripts/field_route_evidence_manifest.py` 生成 `trashbot.field_evidence_manifest.v1`。它是现场路线材料的 artifact gate，只读扫描材料目录，不发布 `/cmd_vel`，不启动导航，不修改 WAVE ROVER、ESP32、UART、串口、波特率、速度映射、底盘反馈协议或 launch 默认硬件参数。

## 输入和输出

必需输入：

- `--mode local|ssh`
- `--artifact-root <dir>` 或 `--input <dir>`
- `--output <manifest.json>`

`--input` 是离线 evidence packet intake 的别名，语义等同于 `--artifact-root`。保留 `--artifact-root` 是为了兼容前序 SSH/manifest 脚本；新增 `--input` 是为了让现场人工导出的本地目录可以直接进入 sprint P0 验收命令，不需要再连 `root@192.168.1.11 -p 37878`。

可选输入：

- `--preflight-json <field_route_evidence_preflight.py 输出>`

没有 `--preflight-json` 时仍会生成 manifest，但 `preflight.status=missing_preflight_json`、`not_proven=true`，只证明离线 artifact intake 软件路径，不证明现场 ready 或 delivery。

可选 SSH 参数：

- `--ssh-target root@192.168.1.11`
- `--ssh-port 37878`
- `--timeout-s 5`

真实上位机入口仍是：

```bash
ssh root@192.168.1.11 -p 37878
```

SSH 模式只运行远端只读 Python 扫描，不启动 `ros2 launch`、Nav2、fixed route 或运动命令。SSH 不可达时状态记录为 `blocked_ssh_unreachable`。

## 必需 artifact

manifest 会检查以下材料：

- `map.yaml`
- `route.csv`
- `keyframes/` 下至少一个 `.jpg`、`.jpeg`、`.png` 或 `.json`
- `rosbag` / `route_bag` 目录或 rosbag 文件
- `replay.jsonl` 或 `fixed_route_replay.jsonl`

每项 artifact 记录：

- `required`
- `present`
- `path`
- `size_bytes`
- `mtime_utc`
- `sha256`
- `reason`

目录 artifact 使用稳定排序后的目录摘要：对子文件的相对路径、大小和 sha256 做二次 sha256，因此可复跑比较，但不会把图片或 bag 内容写进 manifest。

## 离线 evidence packet intake

本地目录可以来自现场人工 USB 拷贝、压缩包解压、后续 SSH 成功后的 run 目录，或已有 `trashbot.field_evidence_manifest.v1` 的材料包。推荐命令：

```bash
python3 onboard/scripts/field_route_evidence_manifest.py \
  --mode local \
  --input /tmp/trashbot_field_evidence_fixture \
  --output /tmp/trashbot_field_evidence_manifest.json
```

离线 intake 会在 artifact 扫描前检查目录内已有 manifest 候选：

- `field_evidence_manifest.json`
- `trashbot_field_evidence_manifest.json`
- `trashbot.field_evidence_manifest.v1.json`
- `manifest.json`
- `route_data/field_evidence_manifest.json`
- `route_data/trashbot_field_evidence_manifest.json`

已有 manifest 的 `schema` 必须是 `trashbot.field_evidence_manifest.v1`。如果 schema 不匹配、JSON 无法解析，或已有 manifest 自带以下危险成功声明，输出必须 fail closed，返回非零，并把 `input_manifest.blocked_reason` 写入新 manifest：

- `delivery_success=true`
- `safe_to_control=true`
- `primary_actions_enabled=true`

这条规则的原因是：离线 packet 是材料入口，不是现场控制或送达验收单。即使同一目录的 `map.yaml`、`route.csv`、keyframes、rosbag 和 replay 都齐全，也不能用 artifact 完整性把旧 manifest 的危险成功声明“洗白”。

## gate 语义

`gate_pass=true` 只表示必需 artifact 都存在且非空。它不等于真实路线成功、不等于 Nav2 实跑成功、不等于送达成功。

manifest 顶层始终保留安全边界：

- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`

同时保留面向 O6/O7 消费的显式 gate 字段：

- `artifact_status`：`gated | missing | blocked`
- `artifact_health`：artifact 计数、present/missing 列表和摘要
- `manifest_gate.status`：`gated | blocked_not_proven`
- `manifest_gate.gate_pass`
- `manifest_gate.blocked_reason`

当 preflight 是 dry-run、SSH 不可达、preflight JSON 缺失或不是 `ready_for_live_route_capture_not_proven` 时，即使本地 fixture 完整，也必须保持：

- `not_proven=true`
- `blocked_reason=<preflight 状态或 SSH blocker>`

这条规则用于“不再次只消费同一 SSH blocker”：SSH 仍不可达时，研发可以用本地完整 fixture 验证 manifest 功能；但输出不会伪装成真实现场路线材料。

`pc-tools/workstation` 的 O7 Field Evidence Consumer Ingest 会继续消费这份 manifest，并把它和 route replay / labeling fixture 合成统一只读摘要。入口说明见 [O7 Field Evidence Consumer Ingest](o7_field_evidence_consumer_ingest.md)。本地/mock 与 future SSH 读取都必须保持 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`，以及明确的 `blocked_reason` / `next_required_evidence`。

## 本地 fixture 复跑

完整 fixture 示例：

```bash
rm -rf /tmp/trashbot_field_manifest_fixture_complete
mkdir -p /tmp/trashbot_field_manifest_fixture_complete/keyframes
mkdir -p /tmp/trashbot_field_manifest_fixture_complete/route_bag
printf 'image: map.pgm\nresolution: 0.05\n' >/tmp/trashbot_field_manifest_fixture_complete/map.yaml
printf 'x,y,yaw\n0,0,0\n1,0,0\n' >/tmp/trashbot_field_manifest_fixture_complete/route.csv
printf '{"x":0,"y":0}\n' >/tmp/trashbot_field_manifest_fixture_complete/keyframes/0001.json
printf 'rosbag2_bagfile_information:\n' >/tmp/trashbot_field_manifest_fixture_complete/route_bag/metadata.yaml
printf '{"event":"start"}\n{"event":"done"}\n' >/tmp/trashbot_field_manifest_fixture_complete/fixed_route_replay.jsonl

python3 onboard/scripts/field_route_evidence_manifest.py \
  --mode local \
  --artifact-root /tmp/trashbot_field_manifest_fixture_complete \
  --preflight-json /tmp/trashbot_field_preflight_ssh.json \
  --output /tmp/trashbot_field_manifest_complete.json
```

如果 `/tmp/trashbot_field_preflight_ssh.json` 仍是 `blocked_ssh_unreachable`，完整 fixture 的 `gate_pass` 可以为 `true`，但 `not_proven=true`、`delivery_success=false`、`primary_actions_enabled=false` 必须保持。

使用离线 intake alias 复跑同一个 fixture：

```bash
python3 onboard/scripts/field_route_evidence_manifest.py \
  --mode local \
  --input /tmp/trashbot_field_manifest_fixture_complete \
  --output /tmp/trashbot_field_manifest_complete_from_input.json
```

缺失 fixture 示例：

```bash
rm -rf /tmp/trashbot_field_manifest_fixture_missing
mkdir -p /tmp/trashbot_field_manifest_fixture_missing/keyframes
printf 'image: map.pgm\n' >/tmp/trashbot_field_manifest_fixture_missing/map.yaml

python3 onboard/scripts/field_route_evidence_manifest.py \
  --mode local \
  --artifact-root /tmp/trashbot_field_manifest_fixture_missing \
  --preflight-json /tmp/trashbot_field_preflight_ssh.json \
  --output /tmp/trashbot_field_manifest_missing.json || true
```

缺失 fixture 必须输出 `gate_pass=false`，并通过 `blocked_artifacts_missing` 或 `blocked_artifacts_empty` fail closed。

## 真实 SSH 复跑

先运行 preflight：

```bash
python3 onboard/scripts/field_route_evidence_preflight.py \
  --mode ssh \
  --ssh-target root@192.168.1.11 \
  --ssh-port 37878 \
  --timeout-s 5 \
  --output /tmp/trashbot_field_preflight_ssh.json
```

如果现场已经采集到材料，例如远端目录为 `$HOME/.ros/trashbot_runs/<RUN_ID>`，运行：

```bash
python3 onboard/scripts/field_route_evidence_manifest.py \
  --mode ssh \
  --artifact-root '$HOME/.ros/trashbot_runs/<RUN_ID>' \
  --preflight-json /tmp/trashbot_field_preflight_ssh.json \
  --ssh-target root@192.168.1.11 \
  --ssh-port 37878 \
  --timeout-s 5 \
  --output /tmp/trashbot_field_manifest_ssh.json
```

只有真实 SSH 可达、preflight 非 dry-run 且 artifact 完整时，manifest 才能作为 O3 现场路线材料完整性证据；它仍不证明 `delivery_success=true`。
