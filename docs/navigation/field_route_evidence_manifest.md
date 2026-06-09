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
- `--map-yaml <map.yaml>`：当 `--artifact-root` 指向 `artifacts/route/` 而 map 位于相邻 `artifacts/map/` 时必须显式传入。
- `--map-pgm <map.pgm>`：同上，必须显式传入相邻 map 图像，脚本不会隐式猜测任意父目录。
- `--derive-replay-jsonl <output.jsonl>`

没有 `--preflight-json` 时仍会生成 manifest，但 `preflight.status=missing_preflight_json`、`not_proven=true`，只证明离线 artifact intake 软件路径，不证明现场 ready 或 delivery。

`--derive-replay-jsonl` 只在本地 intake 时生效：脚本会只读解析 `route.csv`，派生 deterministic replay JSONL，补给 O7/PC consumer 与 manifest gate。它不会生成 rosbag，不会发布 `/cmd_vel`，也不会把 `safe_to_control`、`delivery_success`、`primary_actions_enabled` 置为 `true`。

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

manifest 必需检查以下材料：

- `map.yaml`，或真实 bundle 下的 `map/*.yaml`
- `map.pgm`，或真实 bundle 下的 `map/*.pgm`
- `route.csv`，或真实 bundle 下的 `route/route.csv`
- `manifest.json`，或真实 bundle 下的 `route/manifest.json`
- `keyframes/`，或真实 bundle 下的 `route/keyframes/`，目录下至少一个 `.jpg`、`.jpeg`、`.png` 或 `.json`

完整 bundle / 旧 field packet intake 还会把以下运行材料纳入 gate：

- `rosbag` / `route_bag` 目录或 rosbag 文件
- `replay.jsonl` 或 `fixed_route_replay.jsonl`

当 `--artifact-root` 明确指向 `artifacts/route/` 或 `route_data/`，并且同时提供 `--map-yaml` 与 `--map-pgm` 时，脚本进入真实 route-root material intake：`rosbag` 和 `replay_jsonl` 缺失会记录为 optional 缺口，不阻断 `gate_pass`。这条路径用于先把真实 route/map/source refs 交给 O6/O7 消费，不宣称 Nav2 实跑或 delivery success。

兼容顺序保持向后兼容：同层路径、`route/` 分层路径、`route_data/` 旧路径都会被扫描。真实 2026-06-10 现场 bundle 使用 `map/` 与 `route/` 分层结构时，可以直接传 bundle root；如果只传 `artifacts/route/`，必须用 `--map-yaml` 和 `--map-pgm` 显式引用相邻 map 文件。

每项 artifact 记录：

- `required`
- `present`
- `path`
- `size_bytes`
- `mtime_utc`
- `sha256`
- `reason`

目录 artifact 使用稳定排序后的目录摘要：对子文件的相对路径、大小和 sha256 做二次 sha256，因此可复跑比较，但不会把图片或 bag 内容写进 manifest。

`manifest.json` 是上游 route/source manifest。例如 `route_data_recorder` 写出的 `trashbot.vision_samples.v1` 会作为 `source_manifest` 记录 schema、路径和样本数量，不会因为 schema 不是 `trashbot.field_evidence_manifest.v1` 而阻断生成。只有 `field_evidence_manifest.json`、`trashbot_field_evidence_manifest.json` 或 `trashbot.field_evidence_manifest.v1.json` 这类旧 field-evidence 输出才进入 `input_manifest` 安全复用检查。

## 离线 evidence packet intake

本地目录可以来自现场人工 USB 拷贝、压缩包解压、后续 SSH 成功后的 run 目录，或已有 `trashbot.field_evidence_manifest.v1` 的材料包。推荐命令：

```bash
python3 onboard/scripts/field_route_evidence_manifest.py \
  --mode local \
  --input /tmp/trashbot_field_evidence_fixture \
  --output /tmp/trashbot_field_evidence_manifest.json
```

离线 intake 会在 artifact 扫描前检查目录内已有 field-evidence manifest 候选：

- `field_evidence_manifest.json`
- `trashbot_field_evidence_manifest.json`
- `trashbot.field_evidence_manifest.v1.json`
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
- `derived_replay.generated | frame_count | output | source_route_csv | blocked_reason`

`derived_replay` 只描述 replay JSONL 是否由 `route.csv` 派生成功：

- `generated=true` 说明派生文件已写出，并且 `replay_jsonl` artifact 会扫描到该输出。
- `frame_count` 是 JSONL 行数；例如 2026-06-10 的 01-15 真实 route bundle 期望值是 `17`。
- `blocked_reason=missing_route_csv` 表示请求了 derive，但输入 bundle 中没有可读 `route.csv`。
- `blocked_reason=not_requested` 表示本次没有启用 derive；如果 bundle 本身也没有 replay 文件，manifest 会继续因为缺 `replay_jsonl` 而 fail closed。

即使 `derived_replay.generated=true`，manifest 仍不会把这份材料升级成 Nav2 实跑、固定路线成功或 delivery proof。derive replay 只补 O7-safe 回放材料，不补 O3 现场 rosbag 证据。

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

真实 bundle 或只有 `route.csv` 的 packet 可以直接派生 replay：

```bash
python3 onboard/scripts/field_route_evidence_manifest.py \
  --mode local \
  --input sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf/artifacts \
  --derive-replay-jsonl sprints/2026.06.10_02-05_field-run-bundle-replay-intake/artifacts/derived_replay.jsonl \
  --output sprints/2026.06.10_02-05_field-run-bundle-replay-intake/artifacts/field_run_manifest.json \
  --run-id field_run_bundle_replay_intake_20260610
```

派生得到的每一行 JSONL 至少包含：

- `schema`
- `event`
- `frame_index`
- `timestamp_ms`
- `frame_id`
- `x_m`
- `y_m`
- `yaw_rad`
- `state`
- `evidence_ref`
- `source_route_csv`

其中 `evidence_ref` 与 `source_route_csv` 使用 `field_route://...` 安全引用，不写开发机绝对路径，便于后续 archive、解压和 O7 消费者复用。

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

## 真实 01-15 route artifact 复跑

`sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf/artifacts/route/` 是真实上位机路线材料目录，map 文件在相邻 `artifacts/map/`。生成 O6/O7 可消费的 fail-closed manifest：

```bash
python3 onboard/scripts/field_route_evidence_manifest.py \
  --mode local \
  --artifact-root sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf/artifacts/route \
  --map-yaml sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf/artifacts/map/trashbot_dynamic_odom_tf_map.yaml \
  --map-pgm sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf/artifacts/map/trashbot_dynamic_odom_tf_map.pgm \
  --output /tmp/trashbot_real_route_field_manifest.json
```

该输出应显式引用真实 `route.csv`、`manifest.json`、`keyframes/`、`map.yaml` 和 `map.pgm`。因为没有本轮真实 delivery/result 验收，它仍必须保持 `not_proven=true`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。如果 `route_bag` 或 replay 缺失，manifest 会记录到 optional 缺口，不阻断 O6/O7 route/material intake。

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
