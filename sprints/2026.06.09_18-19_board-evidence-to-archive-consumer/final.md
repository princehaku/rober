# Final - 板载 evidence 到 O6 archive / O7 consumer detail

## sprint_type

`sprint_type: epic`

## 迭代结论（设计阶段）

- 本轮按用户要求已完成完整 6 文件设计链条，聚焦“manifest 到 O6 archive / O7 consumer detail”可执行设计。
- 目标是把上一轮 `field_evidence_manifest.v1` 的现场材料产物，升级为可被 O6/O7 统一消费的主入口。
- 本轮尚未进入代码实现，属于“先验收设计再执行”的产品入口轮。

## 本轮功能点完整性判断

判定：**功能点完整性已具备（设计可执行）**，满足以下条款：

1. 读取 `trashbot.field_evidence_manifest.v1` 的入口和异常态定义齐全；
2. manifest -> O6 archive/consumer detail 转换或注入方向明确；
3. O7/PC 可观察 manifest gate、artifact status、not_proven、delivery_success、primary_actions_enabled；
4. 失败态固定 fail-closed，不允许误导为真实控制或真实交付成功；
5. SSH 不可达时保留本地/mock 兜底路径；
6. 验收命令包含 Python 脚本单元/构建、PC build/test/lint、git diff 检查及有界 SSH 命令。

## 验收命令清单（留痕）

- `python3` 预检与 manifest 脚本帮助页：
  - `python3 onboard/scripts/field_route_evidence_preflight.py --help`
  - `python3 onboard/scripts/field_route_evidence_manifest.py --help`
- `python3` 基础验证：
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/scripts/field_route_evidence_preflight.py onboard/scripts/field_route_evidence_manifest.py`
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/tests/test_field_route_evidence_preflight.py onboard/tests/test_field_route_evidence_manifest.py`
- PC 工程链：
  - `cd pc-tools/workstation && npm run build && npm run test && npm run lint`
- 空白差异检查：
  - `git diff --check -- sprints/2026.06.09_18-19_board-evidence-to-archive-consumer`
- SSH 有界预检：
  - `timeout 8s ssh -o BatchMode=yes -o ConnectTimeout=5 root@192.168.1.11 -p 37878 "echo preflight_probe"`
- manifest 与 SSH 联动 smoke 模板：
  - `python3 onboard/scripts/field_route_evidence_preflight.py --mode ssh --ssh-target root@192.168.1.11 --ssh-port 37878 --timeout-s 5 --output /tmp/trashbot_field_preflight_ssh.json`
  - `python3 onboard/scripts/field_route_evidence_manifest.py --mode local --artifact-root /tmp/trashbot_field_manifest_fixture_complete --preflight-json /tmp/trashbot_field_preflight_ssh.json --output /tmp/trashbot_field_manifest_complete.json`

## 风险与剩余证据缺口

- 仍未补齐实时现场证据落库（真实 SSH、真实 `map.yaml/route.csv/keyframes/rosbag/replay.jsonl`）。
- 未验证 O7 consumer detail 与 O6 archive/consumer 的最终生产级联通（本轮为设计）。
- `delivery_success=true` 仍不在本轮证据范围内；真实 deliver 与真实 robot control 在后续 sprint 验收。

## 责任与下一位执行

- 下游 owner：`full-stack-software-engineer`
- 本 sprint 文档可直接转入实现，建议首轮只实现 manifest->O6 archive 与 consumer detail 的最小闭环，其他真实现场项按新 blocker 出现后按 sprint 追加。

