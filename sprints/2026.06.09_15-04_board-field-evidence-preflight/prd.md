# Board Field Evidence Preflight Sprint PRD

## 用户价值

普通用户最终关心小车能不能沿真实路线送垃圾；工程侧当前最大缺口是现场证据采集反复被 SSH、ROS2 环境和 topic 状态阻塞。`board_field_evidence_preflight_cli` 的价值是把现场执行前的检查变成一次命令和一个 JSON 证据包，减少下一轮真实上位机恢复后的人肉排错。

## 功能点定义

功能点：`board_field_evidence_preflight_cli`。

新增 CLI 建议路径：

```text
onboard/scripts/field_route_evidence_preflight.py
```

建议测试路径：

```text
onboard/tests/test_field_route_evidence_preflight.py
```

## 必须支持的使用方式

本地 dry-run：

```bash
python3 onboard/scripts/field_route_evidence_preflight.py \
  --mode local \
  --dry-run \
  --output /tmp/trashbot_field_preflight.json
```

真实本机 ROS2 预检：

```bash
python3 onboard/scripts/field_route_evidence_preflight.py \
  --mode local \
  --output "$HOME/.ros/trashbot_runs/field_preflight.json"
```

SSH 预检：

```bash
python3 onboard/scripts/field_route_evidence_preflight.py \
  --mode ssh \
  --ssh-target root@192.168.1.11 \
  --ssh-port 37878 \
  --output /tmp/trashbot_field_preflight_ssh.json
```

## Evidence Packet 要求

输出 JSON 必须包含：

- `schema=trashbot.board_field_evidence_preflight.v1`
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

## 检查项要求

最小检查项：

1. `environment`: hostname、时间、运行平台、当前工作目录。
2. `ssh_reachability`: SSH 目标、端口、dry-run 下的命令模板、真实模式下的返回码和安全摘要。
3. `ros2_cli`: `command -v ros2`。
4. `setup_candidates`: `/opt/ros/humble/setup.bash`、`/ws/install/setup.bash`、`~/rober/onboard/install/setup.bash`、`~/apps/rober/onboard/install/setup.bash`。
5. `trashbot_packages`: `ros2 pkg list` 中的 `ros2_trashbot_bringup`、`ros2_trashbot_nav`、`ros2_trashbot_hardware`、`ros2_trashbot_behavior`。
6. `topics`: `/scan`、`/camera/image_raw`、`/odom`、`/tf`、`/map`。
7. `topic_smoke_commands`: `/scan`、`/odom`、`/camera/image_raw` 的 `ros2 topic hz` 和 `/tf` 的 `ros2 topic echo --once`。
8. `learning_commands`: `learn.launch.py`、`/trashbot/save_map`、`route_csv_to_yaml`、`fixed_route_autonomy dry_run`、可选 rosbag record。
9. `output_contract`: 推荐 `RUN_ID` 和 `OUT_DIR`，避免覆盖旧材料。

## 失败分层

工具必须 fail closed，至少区分：

- `blocked_ssh_unreachable`
- `blocked_ros2_cli_missing`
- `blocked_setup_missing`
- `blocked_trashbot_packages_missing`
- `blocked_required_topics_missing`
- `blocked_topic_smoke_failed`
- `ready_for_live_route_capture_not_proven`
- `dry_run_template_only_not_proven`

## 安全和边界

- 不输出 SSH 私钥、token、bearer、完整环境变量、完整 home 目录文件列表或凭证路径。
- 不把 dry-run 包装成真实现场通过。
- 不暴露 `/cmd_vel` 控制能力。
- 不启用任何真实移动命令。
- 默认只做探测、模板和证据路径标准化。

## 验收口径

完成标准：

- dry-run 在没有 ROS2、没有真实 SSH 的 macOS 开发机上可稳定输出合法 JSON。
- JSON 中包含下一次现场采集需要执行的命令模板。
- 单元测试覆盖 dry-run、SSH 命令构造、失败分层、安全字段和 schema。
- 文档同步说明该工具是 preflight，不是 route/map 成功证据。
- sprint `tech-done.md` 记录实际验证输出。

