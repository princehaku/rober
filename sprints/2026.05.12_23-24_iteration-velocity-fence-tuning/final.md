# Sprint 2026.05.12_23-24 Iteration Velocity Fence Tuning - Final

## 状态

- 阶段：final
- 时间：2026-05-12 23:59 Asia/Shanghai
- Sprint 类型：Epic（首个按新规则示范走完整六文档的 sprint）
- 主责 Owner：`product-okr-owner`（按并行豁免条件 3：CEO 明确指定 product-okr-owner 主导这次治理变更，且任务严格落在 5 个流程文件，与其他在跑 sprint 无接口耦合）
- Sprint 结论：**完成**。CEO 拍板的 6 个参数 100% 落地；4 处规则文件改动一致；OKR 既有完成度数字 0 改动；所有验收命令 exit 0。
- 证据边界：`process_doc_only`

## 触发与诊断回顾

CEO（用户）反馈"每次迭代东西太少、进度太慢、coding 改了对整体进展帮助不大、是否要并行研发"，主节点基于以下证据做了只读复盘：

1. 05-10/05-11/05-12 三天 sprint 数量 34+，绝大多数 30-60 分钟、单 owner 串行。
2. 连续 4 轮 Docker 环境 sprint 卡在同一 `registry mirror/proxy returns text/html` 根因。
3. OKR 完成度：O1=75%、O2=74%、O3=76%、O4=75%、O5=30%、O6=12%，但近 20 轮针对 O5/O6 不到 1/4。
4. 六文档契约对 30 分钟微切片 sprint 开销过大。

## 实际交付

| 文件 | 类型 | 关键改动 |
| --- | --- | --- |
| `AGENTS.md` | 修改 | 重写"并行启动强制规则"、新增"Epic / Micro Sprint 分层"、"OKR 最低优先级软提醒"、"同一 Blocker 重复消费红线" 三节、微调"Tech Plan 自动执行规则"和"Sprint 留档原则" |
| `.codex/agents/registry.toml` | 修改 | `[execution_policy]` 表新增 6 字段：`parallel_default`、`parallel_solo_exemptions`、`epic_micro_doc_policy`、`okr_lowest_objective_rule`、`repeated_blocker_cap`、`process_doc_reference`；微调 `tech_plan_execution_rule` 字段表述 |
| `docs/process/iteration_velocity.md` | 新建 | 总规则文档六节：背景 / Epic-Micro 判定矩阵 / 并行强制规则 / OKR 最低优先级软提醒 / Blocker 重复消费红线 / 与既有规则的关系 |
| `OKR.md` | 修改 | 仅在第 4.1 节末尾追加 2 行（1 段正文 + 1 空行）"最低 Objective 软提醒规则（2026-05-12 引入）"短段；**未修改任何 Objective / KR / 完成度数字 / 既有快照表** |
| `sprints/2026.05.12_23-24_iteration-velocity-fence-tuning/` | 新建 | 完整 Epic 六文档：pre_start / prd / tech-plan / tech-done / side2side_check / final |

`git diff --stat -- OKR.md` = `1 file changed, 2 insertions(+)`，0 删除。

## CEO 拍板参数落地核对

| CEO 决策 | 落地状态 |
| --- | --- |
| 修改范围 = 4 处 | ✅ 完成 |
| 并行默认 2-4 | ✅ 完成 |
| 主节点写代码口子 = 不开 | ✅ 完成 |
| 文档分层 Epic 六文档 / Micro 仅 tech-done | ✅ 完成 |
| OKR 最低优先级 = 软提醒 | ✅ 完成 |
| Blocker 2 轮上限强制切换或升级 | ✅ 完成 |

## 验收命令实跑

- `git diff --check -- AGENTS.md .codex/agents/registry.toml docs/process/iteration_velocity.md OKR.md sprints/2026.05.12_23-24_iteration-velocity-fence-tuning/tech-done.md`：exit 0
- `python3 -c "import tomllib; tomllib.load(...)"`：`toml OK`
- `Test-Path docs/process/iteration_velocity.md`：`process doc exists`
- `grep -c "sprint_type" AGENTS.md`：3
- `grep -c "iteration_velocity" .codex/agents/registry.toml`：1
- `grep -c "iteration_velocity.md" AGENTS.md`：5
- `git status --short`：3 M + 2 ?? 全部在授权 5 路径内
- `git diff --stat -- OKR.md`：`1 file changed, 2 insertions(+)`

主节点已独立复核全部命令，与子 agent 输出一致。

## OKR 影响

- **不直接提升任何 Objective（O1-O6）完成度**：本轮是流程治理改动，不动产品代码、不动硬件、不动主链路。
- **预期间接影响（需后续 sprint 真实压测）**：
  - 单轮 OKR 推进从近 10 轮的 0~+2pp 提升到 +3~5pp（按 Epic sprint 估算）。
  - O5（30%）和 O6（12%）每轮获得显式优先权重，每周至少 1-2 个 Epic sprint 直接攻击。
  - 同一根因 blocker 最多消费 2 轮，避免 Docker registry mirror 这类情况再次出现连续 4 轮空转。

## 做什么 / 不做什么

### 已做

- 重写并行启动强制规则，明确默认 2-4 子 agent。
- 引入 Epic / Micro Sprint 分层，减轻微切片文档负担。
- 新增 OKR 最低优先级软提醒，引导轮次配额向 O5/O6 倾斜。
- 新增 Blocker 重复消费红线，强制切换或升级。
- AGENTS.md / registry.toml / iteration_velocity.md / OKR.md 4 处规则文本互相引用，保持一致性。

### 未做

- 不抬任何 OKR 完成度。
- 不修改任何 ROS2 产品代码、测试代码、launch 参数、vendor 文件、硬件配置。
- 不修改 IC role 的 `.codex/agents/*.toml`。
- 不追溯过往 sprint 是否符合新规则。
- 不针对真实硬件 / HIL / 真实 4G / OSS / CDN。

## 剩余风险

1. **自指风险**：本 sprint 本身就是新规则的首个示范用例，规则未经其他 sprint 实战压测。建议下一个真正按本规则跑的 Epic sprint 在 `final.md` 提交规则压测反馈。
2. **未追溯过往 sprint**：既有 60+ sprint 没有 `sprint_type` 字段、blocker 标识不统一；`blocker_root_cause: <slug>` 是新引入推荐做法，主节点扫描历史 final.md 需要语义判断。
3. **PowerShell vs bash 验证口径差异**：验收命令按 bash 写，Windows PowerShell 需要等效改写（已在 tech-done.md 5.3 节给出 Test-Path fallback）。规则有效性不受影响，但跨平台 CI 时需要补 PowerShell 适配。
4. **软提醒 vs 硬规则**："OKR 最低优先级软提醒"是软提醒、不阻塞实现。如果未来 sprint 反复绕开最低 Objective 但每次都"理由合法"，需要 CEO 在下一次复盘时判断是否升级为硬规则。
5. **并行 2-4 在小项目可能过度**：默认 2-4 适配 4 个 IC 编制，但某些 read-only 或单 Objective sprint 可能 2 个就够。规则允许通过 `parallel_solo_exemptions` 条件 2 单线，但实际执行时需要主节点判断 sprint 复杂度。

## 下一步建议

1. **下一轮 sprint 必须是 Epic**：优先针对最低 Objective（O6=12% 或 O5=30%），并行 2-4 子 agent，作为新规则的首次实战验证。建议 O6 切到"真实云部署 staging（HTTPS/bearer/持久化队列）"或"OSS 图片上传链路（STS 临时凭证）"，O5 切到"正式手机端 UI 美观可用"。
2. **下一轮 Epic sprint 的 `final.md` 必须复盘新规则**：实际效果如何？2-4 并行是否过头？OKR 最低优先级核对是否流于形式？Micro/Epic 边界是否需要微调？
3. **主节点在派发下一轮 sprint 前**：扫描最近 2 轮 final.md 的 blocker 字段（按规则要求），避免无意识重复消费同一 blocker。
4. **OKR.md 4.1 节软提醒规则不修改任何 Objective 数字**：但建议下一次产品 OKR 复盘时考虑是否在 4.1 节新增"本轮目标 Objective"字段，让最低 Objective 优先级可机器追溯。

## 收口判断

本 sprint 可收口为**流程治理变更的首个证据**。它足以支撑后续 sprint 按新规则推进，但**不能用于宣称任何 OKR 完成度提升、不能宣称硬件证据、不能宣称 HIL**。

证据边界：`process_doc_only`。
