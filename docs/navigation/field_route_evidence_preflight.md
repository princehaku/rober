# Field Route Evidence Preflight

`onboard/scripts/field_route_evidence_preflight.py` 是现场路线证据采集前的预检入口。它只生成 JSON evidence packet、只读探测 ROS2/SSH/topic 状态，并输出下一步 map、route、keyframe、rosbag、replay 采集命令模板；它不是路线成功、送达成功或 Nav2 实跑通过证明。

## 本地 dry-run

在 macOS 开发机、无 ROS2、无真实 SSH 时也应稳定运行：

```bash
python3 onboard/scripts/field_route_evidence_preflight.py \
  --mode local \
  --dry-run \
  --output /tmp/trashbot_field_preflight.json
```

dry-run 输出状态固定为 `dry_run_template_only_not_proven`，并保持：

- `not_proven=true`
- `delivery_success=false`
- `primary_actions_enabled=false`

## 上位机或本机真实预检

在已经 source ROS2 工作区的上位机上运行：

```bash
python3 onboard/scripts/field_route_evidence_preflight.py \
  --mode local \
  --output "$HOME/.ros/trashbot_runs/field_preflight.json"
```

通过 SSH 从开发机探测上位机：

```bash
python3 onboard/scripts/field_route_evidence_preflight.py \
  --mode ssh \
  --ssh-target root@192.168.1.11 \
  --ssh-port 37878 \
  --timeout-s 5 \
  --output /tmp/trashbot_field_preflight_ssh.json
```

SSH 不可达时，工具仍会写出 JSON，状态为 `blocked_ssh_unreachable`。这份 JSON 只能证明预检入口可用和网络 blocker 已分层，不能证明现场路线材料已经产生。

## JSON contract

输出 schema 为 `trashbot.board_field_evidence_preflight.v1`，关键字段包括：

- `status`
- `source`
- `mode`
- `dry_run`
- `generated_at`
- `target`
- `checks`
- `commands`
- `next_required_evidence`
- `blocked_reason`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

失败状态采用 fail closed 分层：

- `blocked_ssh_unreachable`
- `blocked_ros2_cli_missing`
- `blocked_setup_missing`
- `blocked_trashbot_packages_missing`
- `blocked_required_topics_missing`
- `blocked_topic_smoke_failed`
- `ready_for_live_route_capture_not_proven`
- `dry_run_template_only_not_proven`

## 安全边界

工具不发布 `/cmd_vel`，不启动运动任务，不修改 WAVE ROVER、ESP32、UART、串口、底盘协议或 launch 默认硬件参数。命令输出进入 JSON 前会做长度裁剪和常见凭证脱敏，避免把 token、password、private key 片段带入证据包。

真实路线验收仍需要补齐上位机 SSH 可达、ROS2 topic smoke、`map.yaml`、`route.csv`、`keyframes/`、`route_bag/` 或 fixed-route replay JSONL。

## 下游 artifact gate

预检 JSON 生成后，使用 `onboard/scripts/field_route_evidence_manifest.py` 继续生成 `trashbot.field_evidence_manifest.v1`。manifest gate 会校验 `map.yaml`、`route.csv`、`keyframes/`、rosbag 和 fixed-route replay JSONL 是否存在且非空，并记录 sha256 或目录摘要。

示例：

```bash
python3 onboard/scripts/field_route_evidence_manifest.py \
  --mode local \
  --artifact-root /tmp/trashbot_field_manifest_fixture_complete \
  --preflight-json /tmp/trashbot_field_preflight_ssh.json \
  --output /tmp/trashbot_field_manifest_complete.json
```

如果 SSH 仍不可达，必须保留 `blocked_ssh_unreachable` 与 `not_proven=true`，但可以用本地完整 fixture 和缺失 fixture 验证 manifest 功能，确保不再次只消费同一 SSH blocker。无论 artifact gate 是否通过，manifest 仍保持 `delivery_success=false` 和 `primary_actions_enabled=false`，直到真实现场路线和送达验收另行证明。
