# Final - 板载 evidence 到 O6 archive / O7 consumer detail

## sprint_type

`sprint_type: epic`

## 迭代结论

- 本轮已把 `trashbot.field_evidence_manifest.v1` 真正接入 O7 `consumer detail` 主路径，并补齐 O7/PC 对 `manifest_gate`、`artifact_status`、`not_proven`、`delivery_success`、`safe_to_control`、`primary_actions_enabled` 的可读展示。
- `consumer detail` 现在强制要求上游 detail 提供 field evidence manifest 或既有 ingest contract；缺字段、schema mismatch、unsafe success/control claim、无 contract 时统一 fail-closed。
- SSH 不可达不再阻断本轮软件闭环：preflight 可留存 `blocked_ssh_unreachable` JSON，本地完整 fixture 仍可驱动 manifest->consumer detail 的 mock 证据链。

## 本轮功能点完整性判断

判定：**功能点完整性已具备（实现 + 本地验证完成）**，满足以下条款：

1. 读取 `trashbot.field_evidence_manifest.v1` 的入口和异常态定义齐全；
2. manifest -> O7 consumer detail 映射已实际落地，并兼容既有 ingest contract；
3. O7/PC 可观察 manifest gate、artifact status、not_proven、delivery_success、safe_to_control、primary_actions_enabled；
4. 失败态固定 fail-closed，不允许误导为真实控制或真实交付成功；
5. SSH 不可达时保留本地/mock 兜底路径；
6. 验收命令已覆盖 Python 脚本、单元测试、PC build/test/lint、local/mock smoke、`rg` 和 `git diff --check`。

## 验收命令清单（留痕）

- `python3 onboard/scripts/field_route_evidence_preflight.py --help`：通过
- `python3 onboard/scripts/field_route_evidence_manifest.py --help`：通过
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile ...`：通过
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest ...`：通过，`Ran 10 tests`
- `cd pc-tools/workstation && npm run build && npm run test && npm run lint`：通过，`48 passed (48)`
- `timeout 8s ssh ...`：当前 macOS 主机失败，原因是 `timeout` 命令不存在，不是 target 返回
- `python3 onboard/scripts/field_route_evidence_preflight.py --mode ssh ...`：通过，输出 `status=blocked_ssh_unreachable`
- `python3 onboard/scripts/field_route_evidence_manifest.py --mode local ...`：通过，输出 `gate_pass=true`、`status=field_evidence_manifest_ready_not_delivery_proof`
- `rg -n "field_evidence_manifest.v1|manifest_gate|artifact_status|not_proven|delivery_success|primary_actions_enabled|safe_to_control" ...`：通过
- `git diff --check`：通过

## 风险与剩余证据缺口

- 仍未补齐真实 SSH / 真实 `map.yaml/route.csv/keyframes/rosbag/replay.jsonl` 现场证据。
- 真实 O6 archive/consumer production 链路、真实隧道、真实机器人数据仍未验证。
- `delivery_success=true` 仍不在本轮证据范围内；真实 deliver 与真实 robot control 在后续 sprint 验收。
- 当前开发机缺少 `timeout` 命令；若后续必须逐字复跑 SSH 有界命令，需要安装 coreutils 或切到带 `timeout` 的 shell 环境。

## 责任与下一位执行

- 下游 owner：`full-stack-software-engineer`
- 下一步优先把真实 SSH/board 路线材料挂进同一 contract，再让 O6 archive 生产链读同一份 evidence。
