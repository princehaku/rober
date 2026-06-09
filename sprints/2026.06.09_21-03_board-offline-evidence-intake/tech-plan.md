# Board Offline Evidence Intake Tech Plan

## 责任 Engineer

- 主责 owner：`robot-software-engineer`
- 协作 owner：`full-stack-software-engineer`
- 只读咨询：`robot-algorithm-engineer`

本 plan 是下一轮实现 sprint 的可派发设计，不在当前只读设计轮直接修改工程代码。

## 文件范围

下一轮实现阶段建议允许改动：

- `onboard/scripts/field_route_evidence_manifest.py`
- `onboard/scripts/field_route_evidence_preflight.py`（仅当需要复用现有 packet/status 结构时）
- `onboard/scripts/field_route_evidence_offline_intake.py`（如现有入口不足，可新增）
- `onboard/tests/test_field_route_evidence_manifest.py`
- `onboard/tests/test_field_route_evidence_offline_intake.py`（如新增入口）
- `pc-tools/workstation/src/**`（仅限 manifest/consumer detail 已有字段展示或 fixture 消费必要变更）
- `pc-tools/workstation/tests/**`
- `docs/product/pc_tools_workstation.md` 或相关 `docs/` 文档（记录 offline evidence intake 的产品边界）
- `sprints/2026.06.09_21-03_board-offline-evidence-intake/tech-done.md`
- `sprints/2026.06.09_21-03_board-offline-evidence-intake/side2side_check.md`
- `sprints/2026.06.09_21-03_board-offline-evidence-intake/final.md`

当前只读设计轮实际允许并已使用的范围仅为：

- `sprints/2026.06.09_21-03_board-offline-evidence-intake/pre_start.md`
- `sprints/2026.06.09_21-03_board-offline-evidence-intake/prd.md`
- `sprints/2026.06.09_21-03_board-offline-evidence-intake/tech-plan.md`

## 接口边界

- 输入：本地 evidence packet 目录，不要求 SSH 可达。
- 可选输入：`map.yaml`、`route.csv`、keyframes、`route_bag/`、`replay.jsonl`、既有 manifest JSON。
- 输出：`trashbot.field_evidence_manifest.v1` 或等价 consumer detail 可读结构。
- 安全边界：没有真实送达和真实控制证据时，必须保持 fail-closed：
  - `delivery_success=false`
  - `safe_to_control=false`
  - `primary_actions_enabled=false`
- 真实 SSH 边界：`ssh root@192.168.1.11 -p 37878` 只能作为 P1 附加检查，不能作为 P0 阻塞项。

## 设计步骤

### A. Robot Software Engineer 主线

1. 读取现有 manifest/preflight 脚本与测试，确认 `trashbot.field_evidence_manifest.v1` 已有 required artifact 集合。
2. 设计 offline intake 入口：
   - 若现有 `field_route_evidence_manifest.py --mode local` 已足够，则补齐参数、测试和文档；
   - 若不足，则新增 `field_route_evidence_offline_intake.py`，但输出必须仍进入现有 manifest gate。
3. 构造 fixture evidence packet：
   - 最小 not-proven packet；
   - manifest-ready packet；
   - 缺少关键 artifact packet；
   - unsafe claim packet。
4. 单元测试覆盖 artifact present/missing、schema mismatch、unsafe success/control claim 和 fail-closed。
5. 更新 sprint `tech-done.md`，写清本轮未依赖真实 SSH。

### B. Full-stack Software Engineer 协作

1. 核对 O6/O7 consumer detail 对 manifest 字段的读取路径。
2. 如 robot software 输出字段或 fixture 路径变化，更新 PC/workstation fixture 与测试。
3. 保持 UI/consumer 文案的 not_proven 与 fail-closed 语义，不把 offline packet 误显示成真实交付成功。

### C. Robot Algorithm Engineer 只读咨询

1. 确认 offline packet 中 route/map/keyframe/replay 的最小语义。
2. 输出哪些 artifact 可以支持“路线回放”，哪些只能支持“材料存在但不证明 delivery”。
3. 不修改 SLAM/Nav2/route recorder 代码。

## 验收命令

下一轮实现 sprint 至少执行并上报：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py onboard/scripts/field_route_evidence_preflight.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard.tests.test_field_route_evidence_manifest
python3 onboard/scripts/field_route_evidence_manifest.py --help
python3 onboard/scripts/field_route_evidence_manifest.py --mode local --input /tmp/trashbot_field_evidence_fixture --output /tmp/trashbot_field_evidence_manifest.json
rg -n "trashbot.field_evidence_manifest.v1|delivery_success|safe_to_control|primary_actions_enabled|not_proven|artifact_status|gate_pass" onboard pc-tools sprints/2026.06.09_21-03_board-offline-evidence-intake
git diff --check
```

如新增 `field_route_evidence_offline_intake.py`，还必须追加：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/scripts/field_route_evidence_offline_intake.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard.tests.test_field_route_evidence_offline_intake
python3 onboard/scripts/field_route_evidence_offline_intake.py --help
```

如触达 `pc-tools/workstation`，还必须追加：

```bash
cd pc-tools/workstation && npm run build && npm run test && npm run lint
```

当前只读设计轮的验证命令为：

```bash
rg -n "board_ssh_192_168_1_11_37878_unreachable|blocked_ssh_unreachable|offline evidence|trashbot.field_evidence_manifest.v1|OKR 最低优先级核对|robot-software-engineer|full-stack-software-engineer" sprints/2026.06.09_21-03_board-offline-evidence-intake
git diff --check -- sprints/2026.06.09_21-03_board-offline-evidence-intake
```

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的当前 Objective：O7（约 12%）。O6 为约 30%。
- 本 sprint 是否针对该 Objective：**部分针对 O7，并以前置方式服务 O6/O3**。
- 理由：O7 的路线回放和标注队列需要可消费的现场 evidence packet；继续 live SSH 会第三次消费同一 blocker，因此本轮把证据入口改成 offline intake，让 O7/O6 可继续推进。
- final.md 收口时需复核：offline intake 是否真的进入 O7 consumer detail；如没有进入，只能记为产品设计完成，不能提升 OKR 进度。

## 风险与对冲

1. **风险：离线 packet 仍然没有真实材料。** 对冲：fixture 只能证明软件路径，`final.md` 必须标 `not_proven`，不提升现场 O3。
2. **风险：新入口和既有 manifest mode 重叠。** 对冲：优先复用现有 `field_route_evidence_manifest.py --mode local`；只有参数/语义不足才新增脚本。
3. **风险：consumer 误读 offline packet 为成功交付。** 对冲：测试必须覆盖 `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`。
4. **风险：真实 SSH 后续恢复后路径分叉。** 对冲：live capture 的 run 目录也必须进入同一个 offline intake/manifest gate。

## 下一轮派发建议

按 AGENTS 规则，下一轮实现不应由主节点直接写代码。建议同一轮并行派发：

- `robot-software-engineer`：主线实现 offline intake/manifest/test/docs/sprint tech-done。
- `full-stack-software-engineer`：并行核对 O6/O7 consumer detail fixture 与 not_proven 展示，如需触达 PC 端则在限定范围内修改。
- `robot-algorithm-engineer`：只读咨询 route/map/keyframe/replay 最小语义，输出给主责 owner，不写代码。
