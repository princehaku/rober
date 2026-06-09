# 技术执行单 - 板载 evidence 到 O6 archive / O7 consumer detail

## sprint_type

`sprint_type: epic`

## 实际改动（实施完成）

- `onboard/scripts/field_route_evidence_manifest.py`
  - 顶层补 `safe_to_control=false`
  - 输出 `artifact_status`、`artifact_health`、`manifest_gate`
  - 保持 preflight/SSH blocker 下的 fail-closed 语义
- `onboard/tests/test_field_route_evidence_manifest.py`
  - 新增 `safe_to_control`、`artifact_status`、`manifest_gate.status` 断言
- `pc-tools/workstation/src/shared/contracts.ts`
  - 扩展 manifest summary 与 consumer detail contract
  - `consumer detail` 新增 `field_evidence` 可读区块
- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
  - `consumer detail` 强制读取上游 `trashbot.field_evidence_manifest.v1` 或既有 `trashbot.pc_tools_workstation.o7_field_evidence_consumer_ingest.v1`
  - 缺字段、schema mismatch、unsafe success/control claim、无 contract 时全部 fail-closed
  - 将 `manifest_gate`、`artifact_status`、`not_proven`、`safe_to_control`、`delivery_success`、`primary_actions_enabled` 映射为 O7 detail 可读字段
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
  - O7 `Field evidence consumer ingest` 区块展示 `manifest_gate`、`artifact_status`、`primary_actions_enabled`
  - O7 `consumer detail` 区块展示 `field evidence contract/input status/manifest_gate/artifact_status/blocked_reason/not_proven`
- `pc-tools/workstation/test/catalog.test.ts`
  - 扩展 manifest fixture
  - 新增 consumer detail 直接消费 manifest、消费既有 ingest contract、缺少 field evidence contract fail-closed 用例
  - 放宽 test helper，使 detail mock 不再硬编码单一 task id
- `pc-tools/workstation/test/App.test.ts`
  - 补齐 O7 ingest / consumer detail fixture 中的 field evidence 字段，覆盖 UI 展示路径
- 文档同步：
  - `docs/navigation/field_route_evidence_manifest.md`
  - `docs/navigation/o7_field_evidence_consumer_ingest.md`
  - `docs/product/pc_tools_workstation.md`
  - 明确 manifest gate / artifact status / consumer detail fail-closed 边界

## 验收命令与结果

- `python3 onboard/scripts/field_route_evidence_preflight.py --help`
  - 通过
- `python3 onboard/scripts/field_route_evidence_manifest.py --help`
  - 通过
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/scripts/field_route_evidence_preflight.py onboard/scripts/field_route_evidence_manifest.py`
  - 通过
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/tests/test_field_route_evidence_preflight.py onboard/tests/test_field_route_evidence_manifest.py`
  - 通过，`Ran 10 tests`
- `cd pc-tools/workstation && npm run build && npm run test && npm run lint`
  - 通过，`2 passed (2)` / `48 passed (48)`
- `timeout 8s ssh -o BatchMode=yes -o ConnectTimeout=5 root@192.168.1.11 -p 37878 "echo preflight_probe"`
  - 在当前 macOS 主机失败：`zsh:1: command not found: timeout`
  - 该失败来自本机缺少 `timeout` 命令，不是 target 侧结果
- `python3 onboard/scripts/field_route_evidence_preflight.py --mode ssh --ssh-target root@192.168.1.11 --ssh-port 37878 --timeout-s 5 --output /tmp/trashbot_field_preflight_ssh.json`
  - 通过，输出 `status=blocked_ssh_unreachable`
- `python3 onboard/scripts/field_route_evidence_manifest.py --mode local --artifact-root /tmp/trashbot_field_manifest_fixture_complete --preflight-json /tmp/trashbot_field_preflight_ssh.json --output /tmp/trashbot_field_manifest_complete.json || true`
  - 通过，输出 `gate_pass=true`、`status=field_evidence_manifest_ready_not_delivery_proof`
- `rg -n "field_evidence_manifest.v1|manifest_gate|artifact_status|not_proven|delivery_success|primary_actions_enabled|safe_to_control" ...`
  - 通过，命中脚本、workstation、文档和 sprint 留痕
- `git diff --check`
  - 通过
- `git status --short --branch`
  - 仅本轮允许范围内文件为 modified，待 commit/push

## 失败定位与偏差

- 首轮 Vitest 失败根因是 `listenConsumerRead()` test helper 把 detail 路径硬编码为 `task-consumer-001`，导致新用例命中 404 后误报 schema mismatch。
- 修复方式：放宽 helper，对任意 `/api/o6/consumer/tasks/<task_id>?view=default&include=...` detail 请求返回 detail fixture。
- 当前唯一未闭环项是 commit/push 尚未执行。

## 剩余风险

- `timeout` 命令在当前 macOS 环境缺失，若后续需要严格复跑同一命令，应安装 coreutils 或在其他有 `timeout` 的 shell 环境执行。
- SSH 预检 JSON 当前仍是 `blocked_ssh_unreachable`，所以本轮证据边界仍是 local/mock software proof，不是 live SSH/board success。
