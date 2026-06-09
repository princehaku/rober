# Board Field Evidence Preflight Sprint Final

## 收口状态

状态：software_preflight_ready。

本轮已实现并验证 `board_field_evidence_preflight_cli`。该工具提供 local/dry-run 和 SSH 两类 evidence packet 入口，能在没有 ROS2、没有真实 SSH 的 macOS 开发机上稳定产出 JSON，并在 SSH 不可达时分层记录 `blocked_ssh_unreachable`。

## OKR 影响

本轮支撑临时激活 O3 现场验证 lane：下一次上位机网络恢复后，可以先用标准 JSON 预检定位 SSH、ROS2、setup、package、topic、topic smoke，再进入 map/route/keyframe/rosbag/replay 采集。

本轮也为 O6 evidence archive 和 O7 PC route replay 准备了可被消费的标准 preflight contract，但不直接提升真实现场材料完成度。

## 已完成事项

- 新增 `onboard/scripts/field_route_evidence_preflight.py`。
- 新增 `onboard/tests/test_field_route_evidence_preflight.py`。
- 新增 `docs/navigation/field_route_evidence_preflight.md`。
- 更新 `tech-done.md` 和 `side2side_check.md` 的实现与验证证据。
- dry-run JSON 证明模板入口可用，且明确 `not_proven=true`、`delivery_success=false`、`primary_actions_enabled=false`。
- SSH 建议预检已运行并输出 `blocked_ssh_unreachable` JSON，不再把本轮收口成纯 SSH blocker。

## 验证结果

已通过：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/scripts/field_route_evidence_preflight.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/tests/test_field_route_evidence_preflight.py
python3 onboard/scripts/field_route_evidence_preflight.py --mode local --dry-run --output /tmp/trashbot_field_preflight.json
python3 -m json.tool /tmp/trashbot_field_preflight.json >/tmp/trashbot_field_preflight.pretty.json
python3 onboard/scripts/field_route_evidence_preflight.py --mode ssh --ssh-target root@192.168.1.11 --ssh-port 37878 --timeout-s 5 --output /tmp/trashbot_field_preflight_ssh.json
python3 -m json.tool /tmp/trashbot_field_preflight_ssh.json >/tmp/trashbot_field_preflight_ssh.pretty.json
```

单元测试结果：

```text
Ran 5 tests in 0.014s
OK
```

dry-run 状态：

```text
dry_run_template_only_not_proven
```

SSH 状态：

```text
blocked_ssh_unreachable
```

## 未完成事项与风险

- 未证明真实上位机 SSH、ROS2 topic、map、route、keyframe、rosbag 或 replay 已成功；本轮只交付 preflight 软件入口。
- 未执行 Docker/Humble `colcon build`，因为本轮是独立 Python CLI 和 unittest，验收命令未要求全工作区构建。
- 未改动 WAVE ROVER、ESP32、UART、串口、底盘协议、launch 默认硬件参数或 OKR 百分比。

## 完成前反思

- 没有 revert 或覆盖工作区中已有的无关改动。
- 没有扩大文件范围到无关 PC/mobile/cloud surface。
- 代码注释采用中文，核心复杂逻辑解释了 fail closed、dry-run 不等于实证和 SSH 不可达仍落盘的原因。
- 测试首轮失败已定位并修复，最终验收链路全部通过。
