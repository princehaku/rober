# 技术执行单 - 板载 evidence 到 O6 archive / O7 consumer detail

## sprint_type

`sprint_type: epic`

## 实际改动（阶段状态）

**本轮为设计与验收准备阶段，尚未执行代码实现。**

- 已补齐本轮完整文档链：
  - `pre_start.md`
  - `prd.md`
  - `tech-plan.md`
  - `side2side_check.md`（待验收）
  - `final.md`（待收口）
- 明确了跨 O6/O7 的消费主线与边界：
  - `trashbot.field_evidence_manifest.v1` 读取要求
  - manifest -> archive/consumer detail 注入方向
  - O7 consumer detail 可见字段（manifest gate + artifact status + not_proven + delivery_success）
  - SSH 不可达也可继续 local/mock 验证的降级策略
- 明确 `full-stack-software-engineer` 交付范围与功能完整性验收命令

## 验收命令（本轮设计可用性）

- `python3` 脚本帮助页/预检与 manifest 能跑通（仅设计阶段可执行清单）：
  - `python3 onboard/scripts/field_route_evidence_preflight.py --help`
  - `python3 onboard/scripts/field_route_evidence_manifest.py --help`
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/scripts/field_route_evidence_preflight.py onboard/scripts/field_route_evidence_manifest.py`
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/tests/test_field_route_evidence_preflight.py onboard/tests/test_field_route_evidence_manifest.py`
- `git diff --check`：
  - `git diff --check -- sprints/2026.06.09_18-19_board-evidence-to-archive-consumer`
- PC 端链路后续验收命令（工程阶段）：
  - `cd pc-tools/workstation && npm run build && npm run test && npm run lint`
- SSH 有界预检命令（仅有界失败，保持可回退）：
  - `timeout 8s ssh -o BatchMode=yes -o ConnectTimeout=5 root@192.168.1.11 -p 37878 "echo preflight_probe"`
- 本轮命令模板（工程阶段）：
  - `python3 onboard/scripts/field_route_evidence_preflight.py --mode ssh --ssh-target root@192.168.1.11 --ssh-port 37878 --timeout-s 5 --output /tmp/trashbot_field_preflight_ssh.json`
  - `python3 onboard/scripts/field_route_evidence_manifest.py --mode local --artifact-root /tmp/trashbot_field_manifest_fixture_complete --preflight-json /tmp/trashbot_field_preflight_ssh.json --output /tmp/trashbot_field_manifest_complete.json`

## 失败定位与偏差

- 目前无实现运行偏差；仅完成设计文档。
- 本轮不执行代码实现，因此未形成本地实现日志或新增缺陷关闭记录。

## 下一步

- 进入 `full-stack-software-engineer` 实现与验收阶段。

