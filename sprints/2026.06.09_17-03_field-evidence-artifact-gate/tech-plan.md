# Tech Plan - Field Evidence Artifact Gate

## 执行结论

本 sprint 为 `sprint_type: epic`，计划已完成后可进入实现阶段。  
主责 engineer：`robot-algorithm-engineer`。  
执行模式：单 owner 闭环，由 Algorithm Engineer 负责实现、测试、修复、文档同步、`tech-done.md` / `side2side_check.md` / `final.md` 留档，以及按 CEO 要求完成 git commit / push。

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：O7：PC 端运营调试平台（约 12%）。
- 本 sprint 是否针对该 Objective：否，直接针对 `OKR.md` 当前最高优先级里的“现场 O3 验证 lane（归档 Objective 临时激活）”。
- 不针对 O7 的理由：CEO 已再次给出真实上位机 SSH 入口 `ssh root@192.168.1.11 -p 37878`，且 `OKR.md` 第 5 节明确要求优先产出 `map.yaml`、`route.csv`、keyframe、rosbag 或 replay JSONL。O7 的真实路线回放缺口依赖这些现场材料，本 sprint 产出的 evidence manifest 会成为 O7 后续消费的输入。
- final.md 收口时需复核：如果本轮已经产生真实 replay JSONL / keyframe 清单，下一轮可切回 O7 PC 回放或 O6 archive 消费；如果没有真实材料，也必须证明本地 artifact gate 可用，不再次只消费同一 SSH blocker。

## 方案概览

在已有 `onboard/scripts/field_route_evidence_preflight.py` 基础上，新增现场 artifact gate：

1. 先运行或读取 field preflight JSON，保留 `blocked_ssh_unreachable`、`dry_run_template_only_not_proven`、`ready_for_live_route_capture_not_proven` 等状态。
2. 对 artifact 根目录进行只读扫描，生成 manifest。
3. 对每个必需 artifact 做存在性、非空、mtime、大小、sha256 或目录摘要校验。
4. 顶层合成 `gate_pass` 和 fail-closed 状态。
5. SSH 可达时通过 `ssh root@192.168.1.11 -p 37878` 在远端只读列举和摘要 artifact；SSH 不通时仍用本地 fixture 完成测试。

核心原则：

- 模板或 dry-run 只能证明入口可用，不能让 `delivery_success=true`。
- 缺任意必需 artifact 必须 fail closed。
- 本地 fixture 可以证明软件功能，不得伪装成真实上位机材料。
- 本轮不改硬件协议、不发布运动命令、不启动真实导航。

## 文件范围

Algorithm Engineer 允许改动：

- `onboard/scripts/field_route_evidence_preflight.py`
- `onboard/scripts/field_route_evidence_manifest.py`（如选择新增独立 CLI）
- `onboard/tests/test_field_route_evidence_preflight.py`
- `onboard/tests/test_field_route_evidence_manifest.py`（如选择新增测试文件）
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/field_route_evidence_manifest.md`（如选择新增独立文档）
- `sprints/2026.06.09_17-03_field-evidence-artifact-gate/tech-done.md`
- `sprints/2026.06.09_17-03_field-evidence-artifact-gate/side2side_check.md`
- `sprints/2026.06.09_17-03_field-evidence-artifact-gate/final.md`

禁止改动：

- WAVE ROVER、ESP32、UART、串口、波特率、速度映射、底盘反馈协议相关代码或配置。
- ROS2 launch 默认硬件参数。
- PC/mobile/cloud UI 或 API。
- 本 sprint 设计文件之外的产品计划文档，除非实现中确实需要同步导航文档。

## Manifest contract

建议 schema：

```json
{
  "schema": "trashbot.field_evidence_manifest.v1",
  "run_id": "20260609T170300Z",
  "generated_at": "2026-06-09T09:03:00+00:00",
  "source": "local_fixture|ssh_remote",
  "mode": "local|ssh",
  "preflight_status": "ready_for_live_route_capture_not_proven",
  "gate_pass": false,
  "status": "blocked_artifacts_missing",
  "blocked_reason": "missing_route_csv",
  "not_proven": true,
  "delivery_success": false,
  "primary_actions_enabled": false,
  "artifacts": {
    "map_yaml": {
      "required": true,
      "present": false,
      "path": "...",
      "size_bytes": 0,
      "mtime_utc": null,
      "sha256": null,
      "reason": "missing"
    }
  }
}
```

状态建议：

- `field_evidence_manifest_ready_not_delivery_proof`
- `blocked_ssh_unreachable`
- `blocked_preflight_not_ready`
- `blocked_artifacts_missing`
- `blocked_artifacts_empty`
- `blocked_artifact_digest_failed`
- `dry_run_template_only_not_proven`

## 实现步骤

1. 读取 `AGENTS.md`、`OKR.md`、本 sprint 三份设计文档，以及现有 preflight CLI / 测试 / 文档。
2. 设计 manifest 数据结构和 artifact 判定规则，优先保持纯 Python 标准库实现。
3. 实现本地 artifact 扫描：文件 sha256、目录文件列表摘要、缺失/空文件原因。
4. 实现 SSH 只读路径：优先复用现有 SSH 参数、timeout、脱敏和命令摘要策略；不可达时写入 `blocked_ssh_unreachable`。
5. 实现 CLI 参数：至少支持 `--mode local|ssh`、`--artifact-root`、`--preflight-json`、`--output`、`--ssh-target root@192.168.1.11`、`--ssh-port 37878`、`--timeout-s`。
6. 添加单元测试：完整 fixture、缺失 artifact、dry-run/preflight 未证明、SSH command 构造或 SSH 不可达分层。
7. 更新 `docs/navigation/` 文档：本地 fixture 复跑、真实 SSH 复跑、manifest 字段含义和证据边界。
8. 运行验收命令；失败先定位并修复，不把第一轮失败作为最终结果。
9. 更新 `tech-done.md`、`side2side_check.md`、`final.md`，最后按 CEO 要求 commit / push。

## 验收命令

Engineer 必须运行并在 `tech-done.md` 贴出关键日志片段：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/scripts/field_route_evidence_preflight.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/tests/test_field_route_evidence_preflight.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/tests/test_field_route_evidence_manifest.py
python3 onboard/scripts/field_route_evidence_preflight.py --mode ssh --ssh-target root@192.168.1.11 --ssh-port 37878 --timeout-s 5 --output /tmp/trashbot_field_preflight_ssh.json
python3 -m json.tool /tmp/trashbot_field_preflight_ssh.json >/tmp/trashbot_field_preflight_ssh.pretty.json
python3 onboard/scripts/field_route_evidence_manifest.py --mode local --artifact-root /tmp/trashbot_field_manifest_fixture_complete --preflight-json /tmp/trashbot_field_preflight_ssh.json --output /tmp/trashbot_field_manifest_complete.json
python3 -m json.tool /tmp/trashbot_field_manifest_complete.json >/tmp/trashbot_field_manifest_complete.pretty.json
python3 onboard/scripts/field_route_evidence_manifest.py --mode local --artifact-root /tmp/trashbot_field_manifest_fixture_missing --preflight-json /tmp/trashbot_field_preflight_ssh.json --output /tmp/trashbot_field_manifest_missing.json || true
python3 -m json.tool /tmp/trashbot_field_manifest_missing.json >/tmp/trashbot_field_manifest_missing.pretty.json
rg -n "field_evidence_manifest|ssh root@192.168.1.11 -p 37878|not_proven|delivery_success=false|不再次只消费同一 SSH blocker" docs/navigation sprints/2026.06.09_17-03_field-evidence-artifact-gate
git diff --check
```

如实现选择在现有 preflight CLI 内增加 manifest 子命令，而不是新增 `field_route_evidence_manifest.py`，必须在 `tech-done.md` 解释偏差，并把上述命令等价替换为实际 CLI。

## 接口影响

- 新增或扩展 CLI，不改变 ROS2 topic、action、service 契约。
- 新增 manifest JSON contract，供后续 O6 archive / O7 PC route replay 消费。
- 不影响硬件协议、不影响 launch 默认值、不影响真实底盘安全边界。

## 风险与处理

- SSH 仍不通：必须记录 `blocked_ssh_unreachable`，但用本地 fixture 完成 manifest 测试和文档，不再次只消费同一 SSH blocker。
- 真实 artifact 路径不确定：CLI 必须允许 `--artifact-root` 参数，不硬编码路径；文档可列推荐路径。
- preflight JSON 是 dry-run：manifest 必须保持 `not_proven=true`，不能因为 fixture 完整就宣称真实现场材料通过。
- 目录 digest 规则不一致：实现中固定排序和相对路径，保证测试可复现。

## 下一步子 Agent 派发

应派发给：`robot-algorithm-engineer`。

### 文件范围

```text
onboard/scripts/field_route_evidence_preflight.py
onboard/scripts/field_route_evidence_manifest.py
onboard/tests/test_field_route_evidence_preflight.py
onboard/tests/test_field_route_evidence_manifest.py
docs/navigation/field_route_evidence_preflight.md
docs/navigation/field_route_evidence_manifest.md
sprints/2026.06.09_17-03_field-evidence-artifact-gate/tech-done.md
sprints/2026.06.09_17-03_field-evidence-artifact-gate/side2side_check.md
sprints/2026.06.09_17-03_field-evidence-artifact-gate/final.md
```

### 验收命令

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/scripts/field_route_evidence_preflight.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/tests/test_field_route_evidence_preflight.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/tests/test_field_route_evidence_manifest.py
python3 onboard/scripts/field_route_evidence_preflight.py --mode ssh --ssh-target root@192.168.1.11 --ssh-port 37878 --timeout-s 5 --output /tmp/trashbot_field_preflight_ssh.json
python3 -m json.tool /tmp/trashbot_field_preflight_ssh.json >/tmp/trashbot_field_preflight_ssh.pretty.json
python3 onboard/scripts/field_route_evidence_manifest.py --mode local --artifact-root /tmp/trashbot_field_manifest_fixture_complete --preflight-json /tmp/trashbot_field_preflight_ssh.json --output /tmp/trashbot_field_manifest_complete.json
python3 -m json.tool /tmp/trashbot_field_manifest_complete.json >/tmp/trashbot_field_manifest_complete.pretty.json
python3 onboard/scripts/field_route_evidence_manifest.py --mode local --artifact-root /tmp/trashbot_field_manifest_fixture_missing --preflight-json /tmp/trashbot_field_preflight_ssh.json --output /tmp/trashbot_field_manifest_missing.json || true
python3 -m json.tool /tmp/trashbot_field_manifest_missing.json >/tmp/trashbot_field_manifest_missing.pretty.json
rg -n "field_evidence_manifest|ssh root@192.168.1.11 -p 37878|not_proven|delivery_success=false|不再次只消费同一 SSH blocker" docs/navigation sprints/2026.06.09_17-03_field-evidence-artifact-gate
git diff --check
```

### 输出要求

Engineer 必须返回：

1. 实际改动的文件列表。
2. 验证命令输出结果，包括 SSH 尝试、本地完整 fixture、本地缺失 fixture、单元测试和 `git diff --check`。
3. 失败定位，如 SSH 不通、artifact 缺失或 preflight 未 ready。
4. 剩余风险。
5. git commit hash 和 push 结果；如无法 push，说明原因和远端状态。

