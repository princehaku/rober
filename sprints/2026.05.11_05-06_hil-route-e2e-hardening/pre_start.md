# Sprint 2026.05.11 05-06 HIL + Route E2E Hardening - Pre Start

## 状态

- 阶段：pre-start started
- 时间：2026-05-11 05:06 Asia/Shanghai
- 目录：`sprints/2026.05.11_05-06_hil-route-e2e-hardening/`
- Owner：`product-okr-owner`
- 本轮目标：接续 `2026.05.11_04-05_hil-route-e2e-hardening`，将 O1/O2/O3 从 dry-run 软件证据推进到可追溯实机可复现证据。

## 证据-建议-验收映射表（来源 + 动作 + 验收）

| 证据来源 | 关键证据 | 建议动作 | 验收动作 |
| --- | --- | --- | --- |
| `OKR.md` 4.1 当前快照（O1/O2/O3约75%~76%） | 三个目标都远低于可上线阈值，且仍标注“真实 WAVE ROVER HIL/反馈/路线实跑缺失” | 将本轮拆解为 O1→O2→O3 的顺序闭环：先补硬件反馈闭环，再补任务失败恢复，再补固定路线复盘一致性 | 每个目标交付对应 `evidence_ref`（见下方《实机证据链》）并更新到 sprint 记录 |
| `sprints/2026.05.11_03-04_hil-reality-closure/pre_start.md` / `prd.md` / `tech-plan.md` | 明确 dry-run 与实机不能混用；重复提出硬件 HIL 与任务复盘先行、review test 命名问题 | 继续保留“主线不回退 dry-run 合法性、但新增必需的 HIL source 标注”边界；复用“source=software_proof / hil_pass”策略 | 行为与导航层 task record / operator diagnostics 中出现同一 `source` 与 `evidence_ref` 链路 |
| `sprints/2026.05.11_04-05_hil-route-e2e-hardening/pre_start.md` | 本轮复用重复问题清单：未关闭 O1/O2/O3 低完成度 + `review` 命名验收缺口 | 增设“验收优先级冻结清单”：优先消化 O1/O2/O3，review 命名修复作为 P3 外围 |
| `OKR.md` 2026.05.10_21-22_review-progress-metrics 复盘行 | `test_*review*py` 命名导致 `NO TESTS RAN`，全量 `git diff --check` 受 `README.md` 尾空格影响 | 在本轮新增动作中约束为：只做本 sprint scoped diff；review 测试覆盖缺口要以可执行 test 命名或替代命令显式化 | 工程化验收记录包含一次有效 review 测试执行日志或替代验收命令（非 `NO TESTS RAN`） |
| `sprints/2026.05.11_04-05_hil-route-e2e-hardening/tech-plan.md` | 指定 O1/O2/O3 的实现主线与字段口径：`source`、`result_path`、错误码、复盘字段 | 继续强化“证据字段一体化”：task record、autonomy state、operator diagnostics 使用同一 source + reference 模式 | 同一次失败复现任务可在 operator/diagnostics 与 task_record 三端交叉追溯 |

## 本轮核心抓手（按 O1/O2/O3 低完成度闭环）

- O1：硬件协议与反馈链路闭环
  - 目标：产出一次可复现的 WAVE ROVER HIL 证据，不再把软件 proof 当实机结论。
  - 交付：`hil_pass` 与 `software_proof` 双源分层；硬件反馈字段频率、T=1/T=13 行为、IMU/电池/里程计来源标注、命令-反馈样例留存。
- O2：送达任务真实失败恢复闭环
  - 目标：主链任务必须完整覆盖 `DELIVERING -> DROPOFF -> RETURNING -> IDLE/ERROR` 的可追踪状态与失败码。
  - 交付：失败恢复路径和人工接管建议形成可复盘记录，不再默认成功。
- O3：固定路线可验证闭环
  - 目标：route 状态与任务证据字段可回放，出现 route 断点/缺失时能复现。
  - 交付：`checkpoint/current_index/target/evidence_ref` 全链路写入并可重跑。

## 本轮不做事项（避免扩散）

- 不扩展真实电梯控制能力，不新增 elevator assisted 识别/楼层 OCR 的新模型。
- 不新增大规模测试矩阵，仅保留围栏测试与最小修复。
- 不把 README 尾空格清理作为本轮验收主目标（作为旁路 P3 外围任务）。
- 不把 dry-run 软件证据包装成 HIL 结论。

## O1/O2/O3 证据链（dry-run 软件证据 -> 实机可追溯）

1. 证据入口标准化
   - 对每类证据明确 `evidence_source ∈ {software_proof, hil_dry_run, hil_pass}`。
   - 任何 `hil_pass` 必须有时间戳文件名、参数快照和原始日志/采样原始文件。
2. 统一写入任务记录
   - 任务记录必须写入 `source`, `result_path`, `state_transition_history`, `failure_code`, `human_intervention_required`。
   - `operator` 与 `diagnostics` 只消费已归档 `evidence_ref`，避免重复解释。
3. 复现实机失败案例
   - 对一次 real route 失败/超时案例，保留 `evidence_ref` 指向同一次 run 的 task record 与硬件日志。
   - 形成最小复现场景：正常返回、导航失败、超时、取消。

## 下一步验收动作

1. hardware 侧先产出一版 `hil_pass` 跑数（参数和日志齐全）。
2. robot/behavior 侧在同一 run 基础上补齐失败恢复与任务复盘字段。
3. nav/behavior 侧把 fixed-route 与任务状态字段对齐并可重放。
4. full-stack 侧同步显示 `evidence_source` 与 `evidence_ref`。
5. 仅在以上 1-4 完成后推进 tech-done 与 side2side_check。 
