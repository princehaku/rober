# Tech Plan - O3 28-Pose Fixed Route Consumer

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_04-02_o3_28_pose_fixed_route_consumer/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-algorithm-engineer`
- Plan status: ready for single-owner implementation

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节完成度最低的 Objective 是 **Objective 5：云中转控制面**，约 `85%`。
2. 本 sprint 不直接针对 Objective 5。
3. 不针对 O5 的理由：最近 O5 sprint 已明确缺真实公网 HTTPS/TLS、4G/SIM、production DB/queue、production worker/cutover、OSS/CDN live traffic、真实手机/browser 证据；`cloud_production_cutover_readiness_packet` 等 readiness/checklist/wrapper 均为 support-only，继续包装会重复消费同一 external production evidence blocker。
4. 本 sprint 选择 O3/O1 strict no-motion 的理由：03:00 sprint 已产出 fresh same-run `28-pose` structured path artifact，且 fixed-route / route-intent consumer 是不触发 motion 的相邻低位链路；消费该 material 能产出 `task_id` / `route_intent_id` / route material，比继续 O5 support-only wrapper 更接近 route execution 证据链。
5. OKR 决策边界：本轮即使验收通过，也只接受为 O3/O1 strict no-motion fixed-route consumer material；O5 继续约 `85%`，O1 继续约 `94%`，KR `不归档`，除非后续另有 route execution、delivery/operator acceptance、current live HIL、safe-to-control 或 production external evidence。

## 技术目标

让 fixed-route / route-intent consumer 优先消费 03:00 fresh `28-pose` structured path material，输出可复核 no-motion consumer artifact，替代 01:00 对旧 21:57 partial stdout-tail 的 primary 依赖。

目标结果：

- primary source 为 `sprints/2026.07.13_03-00_o3_live_full_structured_path_capture/artifacts/algorithm/live_full_structured_path_capture_summary.json`
- consumer 读取 `path_structured_pose_count=28` 或等价 28 pose material
- 输出 summary JSON，记录 `route_intent_id`、`task_id`、source artifact ref、validation status、blocked/not-proven boundary
- 输出 route replay JSONL/CSV 或等价 dry-run check material，覆盖 28 个 structured poses 的 order/frame/pose 字段
- 固定 safety fields：`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`safe_to_control=false`

## 单 Owner 实现范围

Owner：`robot-algorithm-engineer`

允许改动范围由实现 worker 在实际任务中细化，建议限定为：

- `onboard/scripts/` 下 fixed-route / route-intent / path material consumer 相关脚本
- `onboard/tests/` 下对应 Algorithm 单元测试
- `docs/navigation/fixed_route_workflow.md` 的最小同步段落
- `sprints/2026.07.13_04-02_o3_28_pose_fixed_route_consumer/artifacts/algorithm/`
- `sprints/2026.07.13_04-02_o3_28_pose_fixed_route_consumer/tech-done.md`

本 planning worker 仅创建 `pre_start.md`、`prd.md`、`tech-plan.md`，不直接修改产品代码。

## 实现步骤

1. 读取 03:00 summary artifact，校验 `path_generated=true`、`path_structured_pose_count=28`、`historic_21_57_artifact_reused_as_live_proof=false`。
2. 在 fixed-route / route-intent consumer 中新增或调整 input selection：优先读取 fresh structured poses；只有缺少 structured poses 时才允许降级到 stdout-tail material。
3. 生成本轮 consumer summary，字段至少包含：
   - `schema`
   - `route_intent_id`
   - `task_id`
   - `primary_source_artifact`
   - `historic_21_57_artifact_primary_source=false`
   - `path_structured_pose_count=28`
   - `validation_status`
   - `dry_run_status`
   - `route_execution_success=false`
   - `delivery_success=false`
   - `hil_pass=false`
   - `safe_to_control=false`
4. 生成 route replay JSONL/CSV 或等价检查材料，确保 28 个 pose 的顺序、frame、position、orientation 可复核。
5. 写 `tech-done.md`，记录实际改动、验证结果、失败定位、剩余风险和下一步证据链。

## 接口和安全边界

本轮只做 no-motion software/artifact consumer。

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
test -f sprints/2026.07.13_04-02_o3_28_pose_fixed_route_consumer/pre_start.md && test -f sprints/2026.07.13_04-02_o3_28_pose_fixed_route_consumer/prd.md && test -f sprints/2026.07.13_04-02_o3_28_pose_fixed_route_consumer/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|28-pose|fixed-route|route_execution_success=false|delivery_success=false|hil_pass=false|robot-algorithm-engineer" sprints/2026.07.13_04-02_o3_28_pose_fixed_route_consumer
```

Algorithm implementation worker 必须在实际实现后至少运行：

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
python3 -m json.tool sprints/2026.07.13_04-02_o3_28_pose_fixed_route_consumer/artifacts/algorithm/*summary*.json >/tmp/o3_28_pose_fixed_route_consumer_summary.pretty.json
rg -n "28|path_structured_pose_count|fixed-route|route_intent_id|task_id|route_execution_success|delivery_success|hil_pass|safe_to_control|historic_21_57" sprints/2026.07.13_04-02_o3_28_pose_fixed_route_consumer
git diff --check -- onboard/scripts onboard/tests docs/navigation/fixed_route_workflow.md sprints/2026.07.13_04-02_o3_28_pose_fixed_route_consumer
```

如果实现未触及 helper，则可以把 `py_compile` / unittest 范围替换为实际 fixed-route / route-intent consumer 脚本和测试，但 `json.tool`、anchor `rg`、`git diff --check` 和 safety invariant 检查必须保留。

## 收口边界

Product 可接受：

- fresh 28-pose structured material 被 consumer 成功读取。
- 新 artifact 能证明 fixed-route / route-intent consumer 不再依赖旧 21:57 partial stdout-tail 作为 primary source。
- 输出同一任务材料，包含 `route_intent_id` / `task_id` / route check evidence。
- no-motion safety fields 全部固定 false。

Product 不接受：

- 把本轮写成 route execution、fixed-route movement、NavigateToPose、controller/BT、`/cmd_vel`、`/api/base/manual`、WAVE ROVER UART、delivery/operator acceptance、HIL、safe-to-control 或 O5 production evidence。
- 把 28-pose 硬改成 21-pose，或补造历史 stdout-tail 缺失点。
- 只新增 review/handoff/readiness 文案而不产出 `task_id`、`route_intent_id`、summary JSON 或 route material。

## 风险和回滚

- 如果 consumer 仍只能读取旧 partial material，应 fail closed，写明 `fresh_28_pose_structured_material_not_consumed`，并保留 safety false。
- 如果 28-pose route material 与既有 schema 不兼容，应优先扩展 schema 兼容可变 pose count，不能硬编码 21。
- 如果验证失败，`robot-algorithm-engineer` 必须先定位失败字段、修复并重跑；不能把首轮失败作为最终收口。
- 本轮不需要回滚其他 worktree 改动；范围外修改应保持不动。
