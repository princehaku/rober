# Board Field Evidence Preflight Sprint Tech Done

## sprint_type: epic

## 实际完成

本轮已实现 `board_field_evidence_preflight_cli`，并把上一阶段“设计已完成但未实现”的状态推进为可运行软件证据入口：

- 新增 `onboard/scripts/field_route_evidence_preflight.py`，支持 `--mode local|ssh`、`--dry-run`、`--ssh-target`、`--ssh-port`、`--timeout-s`、`--output`。
- 输出 `trashbot.board_field_evidence_preflight.v1` JSON packet，包含 `status`、`source`、`mode`、`dry_run`、`generated_at`、`target`、`checks`、`commands`、`next_required_evidence`、`blocked_reason`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- dry-run 不执行 SSH、不要求 ROS2、不要求 topic 存在，只生成模板和 `dry_run_template_only_not_proven` 证据。
- SSH 不可达时仍写出 JSON，状态为 `blocked_ssh_unreachable`，不把本轮收口成纯口头 SSH blocker。
- 真实模式按 fail closed 分层检查 setup、ROS2 CLI、trashbot packages、required topics、topic smoke。
- 新增单元测试覆盖 dry-run contract、SSH argv 构造、SSH 不可达仍落盘、安全脱敏、local setup 缺失 fail closed。
- 新增 `docs/navigation/field_route_evidence_preflight.md`，说明该工具是 preflight，不是 map/route/送达成功证据。

## 实际改动文件

- `onboard/scripts/field_route_evidence_preflight.py`
- `onboard/tests/test_field_route_evidence_preflight.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `sprints/2026.06.09_15-04_board-field-evidence-preflight/tech-done.md`
- `sprints/2026.06.09_15-04_board-field-evidence-preflight/side2side_check.md`
- `sprints/2026.06.09_15-04_board-field-evidence-preflight/final.md`

## 验证结果

执行时间：2026-06-09 16:11:21 CST 附近。

```bash
git status --short
```

关键输出摘要：

```text
 M docs/navigation/fixed_route_workflow.md
 M onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py
 M pc-tools/evidence/README.md
 M sprints/2026.06.09_14-15_board-live-route-preflight-and-capture/tech-plan.md
?? docs/navigation/field_route_evidence_preflight.md
?? onboard/scripts/field_route_evidence_preflight.py
?? onboard/tests/
...
```

上述已存在未提交项多数不在本轮允许范围内；本轮只 stage 允许路径。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/scripts/field_route_evidence_preflight.py
```

结果：exit 0，无输出。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/tests/test_field_route_evidence_preflight.py
```

关键输出：

```text
.....
----------------------------------------------------------------------
Ran 5 tests in 0.014s

OK
```

```bash
python3 onboard/scripts/field_route_evidence_preflight.py --mode local --dry-run --output /tmp/trashbot_field_preflight.json
python3 -m json.tool /tmp/trashbot_field_preflight.json >/tmp/trashbot_field_preflight.pretty.json
```

关键输出：

```text
{"output": "/tmp/trashbot_field_preflight.json", "schema": "trashbot.board_field_evidence_preflight.v1", "status": "dry_run_template_only_not_proven"}
```

JSON 摘要：

```text
status= dry_run_template_only_not_proven
blocked_reason= dry_run_template_only_not_proven
not_proven= True delivery_success= False primary_actions_enabled= False
first_topic_cmd= ros2 topic hz /scan --window 2
```

建议追加 SSH 预检也已运行：

```bash
python3 onboard/scripts/field_route_evidence_preflight.py --mode ssh --ssh-target root@192.168.1.11 --ssh-port 37878 --timeout-s 5 --output /tmp/trashbot_field_preflight_ssh.json
python3 -m json.tool /tmp/trashbot_field_preflight_ssh.json >/tmp/trashbot_field_preflight_ssh.pretty.json
```

关键输出：

```text
{"output": "/tmp/trashbot_field_preflight_ssh.json", "schema": "trashbot.board_field_evidence_preflight.v1", "status": "blocked_ssh_unreachable"}
```

JSON 摘要：

```text
status= blocked_ssh_unreachable
blocked_reason= blocked_ssh_unreachable
not_proven= True delivery_success= False primary_actions_enabled= False
first_topic_cmd= ssh -p 37878 root@192.168.1.11 ros2 topic hz /scan --window 2
```

## 失败定位

第一轮单元测试失败原因是测试代码在 `TemporaryDirectory` 关闭后读取 JSON 文件，导致 `FileNotFoundError`。已把读取移动到临时目录生命周期内并重跑通过。

真实 SSH 预检返回 `blocked_ssh_unreachable`，这是当前网络/上位机可达性状态；工具已按设计产出 JSON evidence packet，不阻塞本轮软件交付。

## 剩余风险

- 本轮验证边界是 macOS 本地 dry-run、单元测试和 SSH 不可达分层；没有证明真实上位机 ROS2 topic、map、route、keyframe、rosbag 或 replay 已产生。
- 本轮不涉及 WAVE ROVER、ESP32、UART、串口、底盘协议、launch 默认硬件参数或 HIL。
- 真实现场恢复后仍需在上位机或 SSH 模式下跑非 dry-run，并补齐 route/map/keyframe/rosbag/replay 材料。
