# O3 No-Motion Nav2 Runtime Repair Tech Plan

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节完成度最低的主 Objective 是 O5，约 `~85%`。
2. 本 sprint 不直接推进 O5。
3. 转向理由：最近 O5 external evidence lane 已因缺真实 production external evidence fail-closed；继续 readiness/probe/checklist 会重复消费 `no_real_production_external_evidence` blocker，且 `okr_credit_allowed=false`。现场 O3 lane 已连续两轮完成诊断，本轮改做 no-motion Nav2/map/AMCL runtime repair，目标是产出可被 O1/O6/O7 后续消费的同轮 path/material 前置证据。

## Owner 与分工

- `robot-software-engineer` 单线闭环：修复或确认 `/api/nav2/start -> o11_nav2_lifecycle.sh -> autonomous.launch.py nav2_stack_only:=true -> /api/nav2/proof/refresh` 链路，运行本地测试和真实板 no-motion 验证，更新 `tech-done.md`。
- 主节点：只做派单、验收、`side2side_check.md` / `final.md` 汇总。

## 文件范围

允许修改：

- `onboard/scripts/o11_nav2_lifecycle.sh`
- `onboard/scripts/upper_robot_api.py`
- `onboard/tests/test_upper_robot_api.py`
- `onboard/src/ros2_trashbot_bringup/launch/autonomous.launch.py`
- `onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py`
- `onboard/scripts/field_route_evidence_preflight.py`
- `onboard/tests/test_field_route_evidence_preflight.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.11_07-38_o3_no_motion_nav2_runtime_repair/tech-done.md`
- `sprints/2026.07.11_07-38_o3_no_motion_nav2_runtime_repair/artifacts/**`

不得修改：

- O5/O6/O7 relay、archive、PC workstation 或 cloud production readiness packet 文件。
- WAVE ROVER 底盘协议解析、速度映射、默认运动控制策略。
- 其他 sprint 目录。

## 接口边界

- `/api/nav2/start` 可以启动受管 Nav2 runtime，但不能发送 goal、不能发布 `/cmd_vel`、不能调用 `/api/base/manual`。
- `/api/nav2/proof/refresh` 在 `managed_runtime_opt_in=true` 下允许 `starts_nav2=true`，但仍必须对运动相关 true 字段 fail-closed。
- `autonomous.launch.py nav2_stack_only:=true` 必须继续跳过 `waypoint_manager`、`nav_to_goal`、`task_orchestrator`、`fixed_route_autonomy`、operator gateway 和 remote bridge。
- summary-facing artifact 不得回显 token、密钥、完整板上敏感路径、完整 raw stdout、traceback 或连接串。

## 验收命令

子 agent 必须运行并汇报结果：

```bash
python3 -m py_compile onboard/scripts/o11_nav2_lifecycle.sh onboard/scripts/upper_robot_api.py onboard/scripts/field_route_evidence_preflight.py
```

如果 `py_compile` 不能编译 shell 脚本，必须改为：

```bash
bash -n onboard/scripts/o11_nav2_lifecycle.sh
python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/field_route_evidence_preflight.py
```

```bash
python3 -m unittest onboard.tests.test_upper_robot_api onboard.tests.test_field_route_evidence_preflight
```

```bash
python3 -m unittest discover -s onboard/src/ros2_trashbot_bringup/test
```

```bash
python3 onboard/scripts/field_route_evidence_preflight.py --mode local --dry-run --output sprints/2026.07.11_07-38_o3_no_motion_nav2_runtime_repair/artifacts/local_preflight.raw.json
```

若真实上位机可达，先执行 no-motion runtime start/status/refresh 验证，再运行：

```bash
python3 onboard/scripts/field_route_evidence_preflight.py --mode ssh --ssh-target root@192.168.1.11 --ssh-port 37878 --timeout-s 12 --output sprints/2026.07.11_07-38_o3_no_motion_nav2_runtime_repair/artifacts/live_nav2_runtime_repair.raw.json
```

最后运行：

```bash
git diff --check -- onboard/scripts/o11_nav2_lifecycle.sh onboard/scripts/upper_robot_api.py onboard/tests/test_upper_robot_api.py onboard/src/ros2_trashbot_bringup/launch/autonomous.launch.py onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py onboard/scripts/field_route_evidence_preflight.py onboard/tests/test_field_route_evidence_preflight.py docs/navigation/field_route_evidence_preflight.md docs/navigation/fixed_route_workflow.md sprints/2026.07.11_07-38_o3_no_motion_nav2_runtime_repair
```

## 风险与回滚

- 若真实板不可达，本轮只能保留 local dry-run 和不可达原因，不宣称 runtime repair 现场有效。
- 若 repair 后仍没有 `/map` / `/amcl_pose` / TF / path，本轮 OKR 百分比不变，但必须把新根因写入 `tech-done.md`。
- 若验证发现启动链会发运动命令，必须立即 fail-closed 并修复；不得以风险说明替代修复。
