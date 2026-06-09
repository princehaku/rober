# Tech Plan - 板载 evidence 到 O6 archive / O7 consumer detail

## 计划状态

本轮为设计优先阶段。先补齐可执行规范：输入 schema、字段映射、fail-closed、命令清单与验收口径。工程实现交给 `full-stack-software-engineer`。

## 目标与设计边界

### 功能完整性（本轮验收门槛）

1. **Manifest 读取**
   - 输入必须优先解析 `trashbot.field_evidence_manifest.v1`。
   - 同时支持 local fixture 输入，不因 SSH 阶段失败而阻断本地验收。
2. **O6 接入**
   - manifest 可映射为 O6 archive 或 consumer detail 可读模型的输入：`task_id/task_ref/evidence_ref`、`artifact_status/gate_pass`、`not_proven`、`delivery_success`、`blocked_reason` 必须可追溯。
   - 任一缺失字段时保持 blocked，不返回 fake 成功。
3. **O7 级联可见**
   - 通过 O7/PC 的 consumer detail 能看到 manifest 来源与 artifact 状态，不需要再读取 raw fixture 才形成“有依据”展示。
4. **边界可读**
   - API/UI 同步展示：
     - `manifest_gate`
     - `artifact_status`
     - `not_proven`
     - `delivery_success`
     - `safe_to_control`
     - `primary_actions_enabled`
5. **SSH 与本地双通道**
   - SSH 预检存在但不是唯一成功条件；SSH 不可达时仍可产出 local/mock 软件证据链。

## OKR 最低优先级核对

- 当前 `OKR.md` 最低对象为 **O7**（约 12%）。
- 本 sprint 针对最低对象：是。  
- 说明：O7 当前缺少可持续消费链路；若不先把 manifest 转入 O6 archive / consumer detail，后续 O7-KR3/KR4/后续 KR 的交付会反复围绕“输入源不一致”返工。  
- 同时该实现对 O6 也是直接可用的接续动作，补齐 O6-KR2/KR6 与 O6 archive 的消费入口一致性，不与 O7 冲突。

## 设计实现任务（功能点级）

### FP1: manifest 入口统一

- 读取路径：`manifestJson`（required）。
- 输出摘要：`schema`, `status`, `gate_pass`, `artifact_count`, `artifact_health`, `next_required_evidence`, `blocked_reason`.
- 失败状态：`blocked_not_proven` / `blocked_artifacts_missing` / `blocked_schema_mismatch`。

### FP2: 构建 O6 archive / consumer 入库输入

- 保留 `task_id`、`robot_id`、`route_evidence` 指纹与 `evidence_refs`。
- 若存在 `route.csv/map.yaml/keyframes/replay`，将可见性写入到 mock archive/consumer 统一读模型（不新建未知 task）。
- 限制：不创建 orphan inference/event；失败返回 `not_proven=true` 且给 `artifact_status=blocked`。

### FP3: consumer detail 可读映射

- O7 读取顺序：
  1. `consumer list/detail`（首选）
  2. 仅当 consumer 不可用再给出本地替代解释，不允许回退到未标记的 raw join。
- detail 字段要求：
  - manifest 产出信息（schema/status/blocked）
  - 轨迹/事件/标注/推理/隧道摘要的可读样本
  - proof boundary（`proof_status`, `safe_to_control`, `connects_cloud_production`, `robot_control_executed`）

### FP4: Fail-closed 与控制边界

- 统一字段包含：
  - `proof_status=not_proven`
  - `safe_to_control=false`
  - `connects_cloud_production=false`
  - `robot_control_executed=false`
  - `delivery_success=false`
  - `primary_actions_enabled=false`
- 任何出现控制成功迹象或成功文案字段时必须降级为 blocked。

## 责任人和文件范围

- 主责 owner：`full-stack-software-engineer`
- 预期可改文件（实施阶段）：
  - `onboard/scripts/field_route_evidence_manifest.py`
  - `onboard/scripts/field_route_evidence_preflight.py`
  - `onboard/tests/test_field_route_evidence_manifest.py`
  - `pc-tools/workstation/src/shared/contracts.ts`
  - `pc-tools/workstation/src/server/index.ts`
  - `pc-tools/workstation/src/server/catalog.ts`
  - `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`（如需新增接口映射）
  - `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
  - `pc-tools/workstation/test/**`
  - 视需要更新：`docs/product/pc_tools_workstation.md`、`docs/navigation/field_route_evidence_manifest.md`、`docs/navigation/o7_field_evidence_consumer_ingest.md`

## 验收命令（工程阶段必须满足）

```bash
python3 onboard/scripts/field_route_evidence_preflight.py --help
python3 onboard/scripts/field_route_evidence_manifest.py --help
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/scripts/field_route_evidence_preflight.py onboard/scripts/field_route_evidence_manifest.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/tests/test_field_route_evidence_preflight.py onboard/tests/test_field_route_evidence_manifest.py
```

```bash
cd pc-tools/workstation && npm run build && npm run test && npm run lint
```

```bash
git diff --check -- sprints/2026.06.09_18-19_board-evidence-to-archive-consumer
```

```bash
timeout 8s ssh -o BatchMode=yes -o ConnectTimeout=5 root@192.168.1.11 -p 37878 "echo preflight_probe"
```

```bash
python3 onboard/scripts/field_route_evidence_preflight.py \
  --mode ssh --ssh-target root@192.168.1.11 --ssh-port 37878 --timeout-s 5 --output /tmp/trashbot_field_preflight_ssh.json
python3 onboard/scripts/field_route_evidence_manifest.py \
  --mode local --artifact-root /tmp/trashbot_field_manifest_fixture_complete \
  --preflight-json /tmp/trashbot_field_preflight_ssh.json --output /tmp/trashbot_field_manifest_complete.json || true
```

```bash
rg -n "field_evidence_manifest.v1|manifest_gate|artifact_status|not_proven|delivery_success|primary_actions_enabled|safe_to_control" onboard/scripts pc-tools/workstation/docs sprints/2026.06.09_18-19_board-evidence-to-archive-consumer
```

## 风险与失败重试

- 风险 1：若 manifest 与现有 `o7_field_evidence_consumer_ingest` 预览 schema 不对齐，需先冻结字段差异再实现。  
- 风险 2：consumer read 与 archive detail 字段重复拼接导致语义不一致。  
  - 缓解：本 sprint 只允许 consumer detail 为主，archive detail 为兼容/次路径。
- 风险 3：SSH 又恢复后出现 live 与 mock 分叉。  
  - 缓解：以 manifest contract 为单一入口，UI 只展示 `source` 差异，不把两种来源路径语义分裂。

## 成功退出条件

- 下列项在实施后可被 `full-stack-software-engineer` 直接验收通过：
  - manifest->O6 archive/consumer detail 映射有字段化定义；
  - 本地/mock 与 live（若可达）路径都能得到同结构 fail-closed / success-notion；
  - O7 consumer detail 页面可见 manifest gate 与 artifact 状态；
  - `not_proven` 和 `delivery_success` 不再能被 UI 覆盖为真实成功。

