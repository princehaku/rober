# Field Route Evidence Manifest

`onboard/scripts/field_route_evidence_manifest.py` 生成 `trashbot.field_evidence_manifest.v1`。它是现场路线材料的 artifact gate，只读扫描材料目录，不发布 `/cmd_vel`，不启动导航，不修改 WAVE ROVER、ESP32、UART、串口、波特率、速度映射、底盘反馈协议或 launch 默认硬件参数。

## 输入和输出

必需输入：

- `--mode local|ssh`
- `--artifact-root <dir>`
- `--preflight-json <field_route_evidence_preflight.py 输出>`
- `--output <manifest.json>`

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

## gate 语义

`gate_pass=true` 只表示必需 artifact 都存在且非空。它不等于真实路线成功、不等于 Nav2 实跑成功、不等于送达成功。

manifest 顶层始终保留安全边界：

- `delivery_success=false`
- `primary_actions_enabled=false`

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
