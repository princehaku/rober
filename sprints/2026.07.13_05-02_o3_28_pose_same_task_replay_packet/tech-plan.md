# Tech Plan - O3 28-Pose Same-Task Replay Packet

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_05-02_o3_28_pose_same_task_replay_packet/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-algorithm-engineer`
- Plan status: ready for single-owner implementation
- Proof boundary target: `software_proof_o3_o1_strict_no_motion_same_task_route_replay_packet_only`

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节完成度最低的 Objective 是 **Objective 5：云中转控制面**，约 `85%`。
2. 本 sprint 不直接针对 Objective 5 / O5。
3. 不针对 O5 的理由：O5 当前只有接入真实 external production evidence 才可继续计进度，包括 HTTPS/TLS、公网入口、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser。当前环境没有这些材料，继续做 readiness、checklist、wrapper、handoff 或 cutover packet 会重复消费同一 blocker。
4. 本 sprint 选择 O3/O1 strict no-motion 的理由：04:02 sprint 已 accepted，且已经产出 28-pose fixed-route consumer summary、`route_csv` 和 `replay_jsonl`；本轮可以把它推进为 same-task route replay / material packet，比继续 O5 support-only 包装更接近后续 route execution 证据链。
5. OKR 决策边界：本轮即使验收通过，也只接受为 O3/O1 strict no-motion same-task replay/material packet；O5 继续约 `85%`，O1 继续约 `94%`，KR `不归档`，除非后续另有 route execution、delivery/operator acceptance、current live HIL、safe-to-control 或 production external evidence。

## 不重复包装的理由

本轮不得重复 helper/export/readiness/route-intent 包装，理由如下：

- 02:00 已补 future CLI fallback structured export contract。
- 03:00 已产出 fresh same-run `28-pose` structured path material。
- 04:02 已把 03:00 material 消费为 fixed-route consumer summary、route replay JSONL 和 route CSV。
- 再写 helper、export、readiness、handoff、safe summary 或 route-intent 文案，不会新增同一任务可消费证据。
- 本轮必须直接消费 04:02 `route_csv` 与 `replay_jsonl`，产出 same-task replay/material packet 或等价 consumer integration artifact。

## 技术目标

让 Algorithm offline consumer 读取 04:02 accepted material，输出同一 `task_id` / `route_intent_id` 下的 strict no-motion replay packet。

输入：

- Summary: `sprints/2026.07.13_04-02_o3_28_pose_fixed_route_consumer/artifacts/algorithm/fixed_route_28_pose_consumer_summary.json`
- `route_csv`: `sprints/2026.07.13_04-02_o3_28_pose_fixed_route_consumer/artifacts/algorithm/fixed_route_28_pose_route.csv`
- `replay_jsonl`: `sprints/2026.07.13_04-02_o3_28_pose_fixed_route_consumer/artifacts/algorithm/fixed_route_28_pose_replay.jsonl`

输出建议：

- `sprints/2026.07.13_05-02_o3_28_pose_same_task_replay_packet/artifacts/algorithm/same_task_replay_packet_summary.json`
- `sprints/2026.07.13_05-02_o3_28_pose_same_task_replay_packet/artifacts/algorithm/same_task_route_replay_packet.jsonl`
- 可选：`same_task_route_replay_packet.csv` 或 consumer readback JSON

Summary 至少包含：

- `schema=trashbot.o3.same_task_route_replay_packet.v1`
- `packet_id`
- `task_id=task_o3_28_pose_fixed_route_consumer_20260713_0402`
- `route_intent_id=route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path`
- `route_csv_ref`
- `replay_jsonl_ref`
- `route_csv_row_count=28`
- `replay_jsonl_event_count=28`
- `path_structured_pose_count=28`
- `same_task_identity_verified=true`
- `same_task_replay_packet_ready=true`
- `consumer_integration_status=pass_strict_no_motion_same_task_replay_packet`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `safe_to_control=false`
- `robot_control_executed=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`

## Algorithm Worker 实现范围

Owner：`robot-algorithm-engineer`

允许改动范围建议限定为：

- `onboard/scripts/o3_28_pose_same_task_replay_packet.py` 或现有 fixed-route/replay consumer 脚本的最小扩展
- `onboard/tests/test_o3_28_pose_same_task_replay_packet.py` 或对应 Algorithm 单元测试
- `docs/navigation/fixed_route_workflow.md` 的 05:02 最小同步段落
- `sprints/2026.07.13_05-02_o3_28_pose_same_task_replay_packet/artifacts/algorithm/`
- `sprints/2026.07.13_05-02_o3_28_pose_same_task_replay_packet/tech-done.md`

不得改动：

- 硬件配置、WAVE ROVER UART、launch safety 参数、controller/BT、Nav2 runtime action 或真实控制路径
- `OKR.md`
- 既有 sprint 文档
- 与本轮无关的 O5/O6/O7 代码或 UI

## 实现步骤

1. 读取 04:02 summary，校验 `fresh_28_pose_structured_material_consumed=true`、`historic_21_57_artifact_primary_source=false`、`path_structured_pose_count=28` 和 safety fields false。
2. 读取 04:02 `route_csv`，校验 header、28 row、order/source_index 连续、frame/position/orientation 字段完整。
3. 读取 04:02 `replay_jsonl`，校验 28 个 replay events、event 类型、同一 task/route identity 或可从 summary 反查。
4. 对 summary、CSV、JSONL 计算 sha256 或等价 fingerprint，并写入 packet summary。
5. 生成 same-task replay/material packet，逐 pose 输出可被 consumer 顺序读取的 no-motion replay record。
6. 写 `tech-done.md`，记录实际改动、验证结果、失败定位、剩余风险和下一步证据链。

## 接口和安全边界

本轮只做 artifact/offline consumer integration。

禁止项：

- 不触发 route execution。
- 不运行 NavigateToPose。
- 不运行 controller/BT。
- 不发布 `/cmd_vel`。
- 不调用 `/api/base/manual`。
- 不打开 WAVE ROVER UART。
- 不声明 delivery/operator acceptance、current live HIL、safe-to-control 或 O5 production/external evidence。

必须保持：

- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `safe_to_control=false`
- `robot_control_executed=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`

## 验收命令

Product planning 文档验收命令：

```bash
test -f sprints/2026.07.13_05-02_o3_28_pose_same_task_replay_packet/pre_start.md && test -f sprints/2026.07.13_05-02_o3_28_pose_same_task_replay_packet/prd.md && test -f sprints/2026.07.13_05-02_o3_28_pose_same_task_replay_packet/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|O5|28-pose|same-task|route replay|route_csv|replay_jsonl|route_execution_success=false|delivery_success=false|hil_pass=false|safe_to_control=false|robot-algorithm-engineer" sprints/2026.07.13_05-02_o3_28_pose_same_task_replay_packet
```

Algorithm implementation worker 必须在实际实现后至少运行：

```bash
python3 -m py_compile onboard/scripts/o3_28_pose_same_task_replay_packet.py
python3 -m unittest onboard.tests.test_o3_28_pose_same_task_replay_packet
python3 onboard/scripts/o3_28_pose_same_task_replay_packet.py \
  --summary sprints/2026.07.13_04-02_o3_28_pose_fixed_route_consumer/artifacts/algorithm/fixed_route_28_pose_consumer_summary.json \
  --route-csv sprints/2026.07.13_04-02_o3_28_pose_fixed_route_consumer/artifacts/algorithm/fixed_route_28_pose_route.csv \
  --replay-jsonl sprints/2026.07.13_04-02_o3_28_pose_fixed_route_consumer/artifacts/algorithm/fixed_route_28_pose_replay.jsonl \
  --output-dir sprints/2026.07.13_05-02_o3_28_pose_same_task_replay_packet/artifacts/algorithm
python3 -m json.tool sprints/2026.07.13_05-02_o3_28_pose_same_task_replay_packet/artifacts/algorithm/same_task_replay_packet_summary.json >/tmp/o3_28_pose_same_task_replay_packet_summary.pretty.json
python3 - <<'PY'
import json
from pathlib import Path

base = Path("sprints/2026.07.13_05-02_o3_28_pose_same_task_replay_packet/artifacts/algorithm")
summary = json.loads((base / "same_task_replay_packet_summary.json").read_text())
assert summary["task_id"] == "task_o3_28_pose_fixed_route_consumer_20260713_0402"
assert summary["route_intent_id"] == "route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path"
assert summary["route_csv_row_count"] == 28
assert summary["replay_jsonl_event_count"] == 28
assert summary["path_structured_pose_count"] == 28
assert summary["same_task_identity_verified"] is True
assert summary["same_task_replay_packet_ready"] is True
for key in ("route_execution_success", "delivery_success", "hil_pass", "safe_to_control", "robot_control_executed", "publishes_cmd_vel", "calls_base_manual", "uses_base_uart"):
    assert summary[key] is False, key
print("o3_28_pose_same_task_replay_packet_ok")
PY
rg -n "same-task|28-pose|route_csv|replay_jsonl|route_execution_success=false|delivery_success=false|hil_pass=false|safe_to_control=false|robot-algorithm-engineer" sprints/2026.07.13_05-02_o3_28_pose_same_task_replay_packet docs/navigation/fixed_route_workflow.md
git diff --check -- onboard/scripts/o3_28_pose_same_task_replay_packet.py onboard/tests/test_o3_28_pose_same_task_replay_packet.py docs/navigation/fixed_route_workflow.md sprints/2026.07.13_05-02_o3_28_pose_same_task_replay_packet
```

如果 worker 复用现有脚本名，必须把 `py_compile`、unittest 和 `git diff --check` 的路径替换为实际改动文件；但 JSON validation、structured assertions、anchor `rg` 和 safety false invariant 不得删除。

## 收口边界

Product 可接受：

- packet 同时消费 04:02 summary、`route_csv`、`replay_jsonl`。
- packet 证明 same-task identity 和 28-pose order/readback。
- artifact 中有 source refs、fingerprints、row/event counts、first/last pose 或等价摘要。
- safety fields 全部 false。

Product 不接受：

- 只新增 review、handoff、safe summary、readiness 或 route-intent 文案。
- 只复制 04:02 summary，不读取 `route_csv` 和 `replay_jsonl`。
- 把本轮写成 route execution、fixed-route movement、NavigateToPose、controller/BT、`/cmd_vel`、`/api/base/manual`、WAVE ROVER UART、delivery/operator acceptance、HIL、safe-to-control 或 O5 production evidence。
- 把 28-pose 硬改成 21-pose，或补造历史 stdout-tail 缺失点。

## 风险和回滚

- 如果 CSV 或 JSONL 读取失败，应 fail closed，输出 `same_task_replay_packet_ready=false` 或直接非零退出，不得生成可接受 packet。
- 如果 identity 不一致，应标记 `same_task_identity_verified=false` 并阻断验收。
- 如果后续消费者需要 O6/O7 archive/readback，应另开跨 owner sprint；本轮只做 Algorithm material packet。
- 本轮不需要回滚其他 worktree 改动；范围外修改保持不动。
