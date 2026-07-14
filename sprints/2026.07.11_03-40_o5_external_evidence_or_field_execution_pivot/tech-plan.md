# O5 External Evidence Or Field Execution Pivot Tech Plan

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的活跃 Objective 是 O5：云中转控制面，约 `85%`。
2. 本 sprint 不直接针对 O5 做 support-only 实现增量。
3. 理由：`sprints/2026.07.10_17-22_o5_production_cutover_readiness_packet/final.md` 已明确当前无真实公网 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic 或真实 phone/browser evidence 时，O5 readiness packet 固定 `okr_credit_allowed=false`。继续 O5 readiness/support packet 会连续消费同一 blocker，不能计主 OKR 增量。
4. 本 sprint 选择可推进的最低路线：O6/O7 + 现场 O3 验证 lane 的新材料消费/现场执行 pack。若实现阶段拿到真实 O5 external production evidence，允许切回 O5；否则默认禁止 O5 support-only 加分。

## Owner 分工

主责 owner：`robot-algorithm-engineer`。

主责原因：

- 目标是产出或消费新的路线/现场执行材料，不是云 relay readiness、PC UI surface 或硬件参数。
- 当前最合适入口是 Algorithm 侧 `field_route_evidence_manifest`，后续 O6/O7 可消费其输出。
- 单 owner 文件范围集中，避免多 owner 并发写共享 sprint 文档或接口合同。

咨询 owner：

- `robot-software-engineer`：仅在真实 O5 external production evidence 突然可用时，补 O5 relay/cutover 事实；本计划不默认派发。
- `full-stack-software-engineer`：仅在后续 O7 消费 pack 时介入；本 sprint 不以 UI 展示作为主交付。
- `rober-hardware-engineer`：仅在实现触及 WAVE ROVER current live HIL、UART、T1001 或轮速反馈时介入，并必须重新读取 `docs/vendor/VENDOR_INDEX.md`。

## 文件范围

计划阶段已允许改动：

- `sprints/2026.07.11_03-40_o5_external_evidence_or_field_execution_pivot/pre_start.md`
- `sprints/2026.07.11_03-40_o5_external_evidence_or_field_execution_pivot/prd.md`
- `sprints/2026.07.11_03-40_o5_external_evidence_or_field_execution_pivot/tech-plan.md`

下一步 implementation 建议允许 `robot-algorithm-engineer` 改动：

- `onboard/scripts/field_route_evidence_manifest.py`
- `onboard/tests/test_field_route_evidence_manifest.py`
- `docs/navigation/field_route_evidence_manifest.md`
- `sprints/2026.07.11_03-40_o5_external_evidence_or_field_execution_pivot/tech-done.md`
- `sprints/2026.07.11_03-40_o5_external_evidence_or_field_execution_pivot/artifacts/algorithm_worker_report.md`

下一步 implementation 默认禁止改动：

- O5 relay production cutover readiness packet 相关代码，除非真实 external production evidence 到位并由 Product 明确切回 O5。
- O7 UI/consumer 文件，避免把 display surface 当成本轮主交付。
- O1 hardware bundle 文件，避免继续 historical same-session 包装。
- `OKR.md` 和 `docs/process/okr_progress_log.md`，直到 Product closeout 有真实材料 delta 和验证证据。

## 接口边界

建议新增或扩展 Algorithm 输出合同：`trashbot.field_execution_pack.v1`。

最低字段：

- `schema`
- `task_id`
- `source_run_id`
- `source_sprint`
- `material_freshness`
- `present_materials`
- `missing_materials`
- `new_materials_consumed`
- `historical_comparators`
- `live_or_field_command_executed`
- `route_execution_material_present`
- `nav2_result_material_present`
- `delivery_or_operator_material_present`
- `production_readback_material_present`
- `okr_credit_allowed`
- `support_only_reason`
- `next_required_evidence`
- `proof_boundary`

安全规则：

- `okr_credit_allowed=true` 只能在存在新的 external 或 field execution material delta 时输出。
- 缺新材料时必须输出 `okr_credit_allowed=false` 和 `support_only_reason=blocked_missing_new_field_execution_material`。
- historical comparator 可作为对照，但不得计入 `new_materials_consumed`。
- 不得回显 URL、token、连接串、raw frame、base64、大段日志、绝对私密路径或 traceback。
- 所有 success/safety 字段默认 fail-closed；没有真实证据时不得输出 delivery success、safe-to-control、HIL pass、production ready 或 route execution success。

## 实施步骤

1. Inventory：只读盘点候选材料，优先找未被最近 sprint 消费的新 `task_id`、`map.yaml`、`route.csv`、keyframe、rosbag、replay JSONL、Nav2 result、delivery record、operator confirmation 或 production readback。
2. Gate：若没有新材料，直接在 `tech-done.md` 写 `blocked_missing_new_field_execution_material`，不改实现代码。
3. Contract：若有新材料，在 `field_route_evidence_manifest.py` 增加 pack 归一化、脱敏和 fail-closed 输出。
4. Tests：补 targeted tests，覆盖 positive、缺材料、task mismatch、dangerous true、unsafe payload、historical comparator 不计分。
5. Docs：同步 `docs/navigation/field_route_evidence_manifest.md`，明确该 pack 的输入、输出、证明边界和后续 O6/O7 消费条件。
6. Closeout：写 `tech-done.md`，记录实际改动、验证命令、失败定位、剩余风险和下一步建议。

## 验收命令

计划阶段只运行文档存在与关键词检查：

```bash
test -f sprints/2026.07.11_03-40_o5_external_evidence_or_field_execution_pivot/pre_start.md && test -f sprints/2026.07.11_03-40_o5_external_evidence_or_field_execution_pivot/prd.md && test -f sprints/2026.07.11_03-40_o5_external_evidence_or_field_execution_pivot/tech-plan.md
```

```bash
rg -n "OKR 最低优先级核对|O5|okr_credit_allowed|验收命令|文件范围|接口边界" sprints/2026.07.11_03-40_o5_external_evidence_or_field_execution_pivot/tech-plan.md
```

实现阶段建议 `robot-algorithm-engineer` 运行：

```bash
python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py
```

```bash
python3 -m unittest onboard.tests.test_field_route_evidence_manifest
```

```bash
rg -n "field_execution_pack|okr_credit_allowed|blocked_missing_new_field_execution_material|new_materials_consumed|historical_comparators" onboard/scripts/field_route_evidence_manifest.py onboard/tests/test_field_route_evidence_manifest.py docs/navigation/field_route_evidence_manifest.md sprints/2026.07.11_03-40_o5_external_evidence_or_field_execution_pivot/tech-done.md
```

```bash
git diff --check -- onboard/scripts/field_route_evidence_manifest.py onboard/tests/test_field_route_evidence_manifest.py docs/navigation/field_route_evidence_manifest.md sprints/2026.07.11_03-40_o5_external_evidence_or_field_execution_pivot
```

## 风险边界

- 本计划阶段不运行实现/测试命令，不修改产品代码，不修改 `OKR.md`。
- 本 sprint 不证明真实公网 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic 或真实 phone/browser。
- 本 sprint 不证明 current live HIL pass、safe-to-control、delivery success、wheel direction、IMU/battery calibration 或 current live route execution success。
- 若 implementation 仅新增 schema/readback/display 但没有新 material delta，Product closeout 必须保持 OKR flat。
- 若 implementation 发现已有工作树改动影响同文件，owner 必须保留他人改动并最小化 patch，不得回滚。

## 子 Agent 派发建议

使用单线闭环，派发 1 个 `worker`，prompt 角色为 `robot-algorithm-engineer`。

文件范围使用本 `tech-plan.md` 的 implementation 文件范围。输出必须包含：

1. 实际改动的文件列表。
2. 验证命令输出结果。
3. 失败定位。
4. 剩余风险。

如果 inventory 阶段没有新材料，worker 仍应返回 `tech-done.md`，说明 blocked 原因和下一条需要 CEO/现场提供的材料，不得为了交付而新增 wrapper。
