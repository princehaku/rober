# Tech Done - Field Evidence Artifact Gate

## Sprint 类型

sprint_type: epic

收口时间：2026-06-09 17:20 CST。

## 实际改动

- 新增 `onboard/scripts/field_route_evidence_manifest.py`，实现 `trashbot.field_evidence_manifest.v1` manifest CLI。
- 新增 `onboard/tests/test_field_route_evidence_manifest.py`，覆盖完整 fixture、缺失 artifact、空 keyframe、dry-run preflight 和 SSH 只读命令构造。
- 更新 `docs/navigation/field_route_evidence_preflight.md`，补充下游 manifest gate 复跑入口。
- 新增 `docs/navigation/field_route_evidence_manifest.md`，记录 manifest contract、真实 SSH 用法、本地 fixture 用法和证据边界。

本轮未修改 WAVE ROVER、ESP32、UART、串口、波特率、速度映射、底盘反馈协议、ROS2 launch 默认硬件参数、PC/mobile/cloud UI/API。

## 实现说明

- `gate_pass` 表示 artifact 清单完整性：`map.yaml`、`route.csv`、`keyframes/`、rosbag、fixed-route replay JSONL 均存在且非空。
- `not_proven` 表示现场证明边界：只要 preflight 不是非 dry-run 的 `ready_for_live_route_capture_not_proven`，即使本地 fixture 完整，也保持 `not_proven=true`。
- `delivery_success=false` 和 `primary_actions_enabled=false` 始终保留；manifest gate 不是送达成功证明，也不放行真实控制动作。
- SSH 模式只执行远端只读 Python 扫描，不启动导航、不发布运动命令。

## 验证结果

完整验收命令已运行，结果通过：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/scripts/field_route_evidence_preflight.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py
```

单元测试：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/tests/test_field_route_evidence_preflight.py
Ran 5 tests in 0.018s
OK

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/tests/test_field_route_evidence_manifest.py
Ran 5 tests in 0.011s
OK
```

真实 SSH preflight 尝试：

```text
python3 onboard/scripts/field_route_evidence_preflight.py --mode ssh --ssh-target root@192.168.1.11 --ssh-port 37878 --timeout-s 5 --output /tmp/trashbot_field_preflight_ssh.json
{"output": "/tmp/trashbot_field_preflight_ssh.json", "schema": "trashbot.board_field_evidence_preflight.v1", "status": "blocked_ssh_unreachable"}
```

SSH 失败定位：

```text
ssh: connect to host 192.168.1.11 port 37878: No route to host
```

本地完整 fixture manifest：

```text
python3 onboard/scripts/field_route_evidence_manifest.py --mode local --artifact-root /tmp/trashbot_field_manifest_fixture_complete --preflight-json /tmp/trashbot_field_preflight_ssh.json --output /tmp/trashbot_field_manifest_complete.json
{"gate_pass": true, "output": "/tmp/trashbot_field_manifest_complete.json", "schema": "trashbot.field_evidence_manifest.v1", "status": "field_evidence_manifest_ready_not_delivery_proof"}
```

关键字段：

```text
status=field_evidence_manifest_ready_not_delivery_proof
gate_pass=true
blocked_reason=blocked_ssh_unreachable
not_proven=true
delivery_success=false
primary_actions_enabled=false
preflight_status=blocked_ssh_unreachable
```

本地缺失 fixture manifest：

```text
python3 onboard/scripts/field_route_evidence_manifest.py --mode local --artifact-root /tmp/trashbot_field_manifest_fixture_missing --preflight-json /tmp/trashbot_field_preflight_ssh.json --output /tmp/trashbot_field_manifest_missing.json || true
{"gate_pass": false, "output": "/tmp/trashbot_field_manifest_missing.json", "schema": "trashbot.field_evidence_manifest.v1", "status": "blocked_artifacts_missing"}
```

关键字段：

```text
status=blocked_artifacts_missing
gate_pass=false
blocked_reason=missing_required_artifact
not_proven=true
delivery_success=false
primary_actions_enabled=false
missing: route_csv, rosbag, replay_jsonl
empty/no valid keyframe: keyframes
```

关键词和格式检查：

```text
rg -n "field_evidence_manifest|ssh root@192.168.1.11 -p 37878|not_proven|delivery_success=false|不再次只消费同一 SSH blocker" docs/navigation sprints/2026.06.09_17-03_field-evidence-artifact-gate
passed

git diff --check
passed
```

## 偏差

- 真实 SSH 仍不可达，因此没有远端 `map.yaml`、`route.csv`、keyframe、rosbag 或 replay JSONL 可校验。
- 本轮按设计切换到本地完整 fixture 和缺失 fixture，完成 manifest 功能验证，确保不再次只消费同一 SSH blocker。

## 剩余风险

- 未证明真实上位机 SSH、ROS2 topic smoke、Nav2/fixed-route 实跑或真实路线采集。
- 未证明真实 artifact 目录结构是否与本地 fixture 完全一致；CLI 已通过 `--artifact-root` 和常见候选路径兼容。
- 未执行 Docker/Humble `colcon build`，因为本轮验收范围是独立 Python CLI、unittest、fixture 和文档。

## Commit / Push

未执行 commit / push。原因：当前工作区已有上一轮未提交且范围外的改动；本轮只应由主节点选择性提交允许范围文件，避免混入无关改动。

推荐 commit message：

```text
Add field evidence artifact manifest gate
```
