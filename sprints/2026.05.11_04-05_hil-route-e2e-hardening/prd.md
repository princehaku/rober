# Sprint 2026.05.11 04-05 HIL + Route E2E Hardening - PRD

## 状态

- 阶段：prd in progress
- 时间：2026-05-11 03:20 Asia/Shanghai
- Owner：`product-okr-owner`
- 产品方向：把 O1/O2/O3 从“有证据但未闭环”推进到“可复现、可追溯、可上报真机状态”。

## 为什么要做

- 目前 `Objective 1`、`Objective 2`、`Objective 3` 均停在低位，优先权高于 O4/O5。
- 最新 `final` 和 `pre_start` 都重复指出关键缺口是同类问题：真实硬件闭环、固定路线实跑、任务失败恢复复盘。
- 本轮通过“最小围栏 + 明确 evidence source”把风险先关进最短路径。

## 本轮 KR 映射（下沉到具体交付）

### Objective 1：硬件协议可信底盘
- KR1：将上报 source 分层：`software_proof` 与 `hil_pass` 不再混用。
- KR2：实现并记录至少一组 WAVE ROVER HIL 采样：启动参数、T=1/T=13 命令行为、反馈字段频率、IMU/电池字段缺失与解释。
- KR3：把 `hardware_smoke_wave_rover.py` 的输入输出和 `robot_bringup_checklist` 对齐为可复验模板。

### Objective 2：送垃圾任务闭环
- KR1：在真实任务路径中补齐 `DELIVERING -> DROPOFF -> RETURNING -> IDLE/ERROR` 的失败恢复与任务记录。
- KR2：所有失败/超时返回 `error_code` 和 `human_intervention_required`。
- KR3：`task_record` 记录真实任务的 `source`, `result_path`, `state_transition_history` 与时间戳。

### Objective 3：可验证导航与固定路线
- KR1：`fixed-route` 路线任务产出 `evidence_ref`，与 `task_record` 对齐。
- KR2：补齐路线缺失、关键点跳变、导航失败的复现字段。
- KR3：最小路线验收表支持 dry-run 与实机分层（dry-run=可回放证据，HIL=行驶证据）。

## 做什么

1. 先硬件再行为：先交付可审计 HIL，随后让行为层和导航链路引用同一 evidence。
2. 任务记录先于页面：先让后端字段统一，再让 operator/diagnostics 消费。
3. review 质量围栏修复：修复 `test_*review*py` 的命名/覆盖缺口。
4. 每条变更必须带 evidence source，不允许“dry-run 伪装实机”。

## 不做

- 本轮不做 elevator 识别模型和真实楼层识别模型。
- 不新增大规模端到端测试，仅保留围栏测试。
- 不改 hardware 之外的界面大改和系统重构。

## 优先级

- P0：O1 HIL 证据闭环。
- P1：O2 任务失败恢复与复盘记录。
- P2：O3 固定路线复盘字段。
- P3：`README.md` trailing whitespace 与 review 命名测试项清洁（降低验收摩擦）。
## 验收口径

1. HIL 任务和软件路径明确分离，`source` 可追溯。
2. 任务失败不会被当作成功返回，失败路径有 `error_code`。
3. 固定路线与任务记录可在 operator 与 diagnostics 中交叉追溯。
4. 围栏测试 + `py_compile` + scoped `git diff --check` 通过。

## 对应责任 Engineer

- `robot-software-engineer`
- `hardware-engineer`
- `autonomy-engineer`
- `full-stack-software-engineer`
