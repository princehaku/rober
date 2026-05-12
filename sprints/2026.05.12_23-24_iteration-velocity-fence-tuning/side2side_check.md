# Sprint 2026.05.12_23-24 Iteration Velocity Fence Tuning - Side2Side Check

## 状态

- 阶段：side2side_check
- 时间：2026-05-12 23:58 Asia/Shanghai
- 检查方：主节点（CEO 验收前的工程对照检查）
- 检查结论：**通过**。所有 CEO 拍板的参数已落地，授权范围 0 越界，OKR.md 既有完成度数字 0 改动，所有验收命令 exit 0。

## CEO 拍板参数 vs 实际落地对照

| CEO 决策 | 落地位置 | 实际表述 | 是否一致 |
| --- | --- | --- | --- |
| 修改范围 = 4 处（AGENTS.md + registry.toml + 新建 iteration_velocity.md + OKR.md 4.1 软提醒） | `git status --short` | `M AGENTS.md`、`M .codex/agents/registry.toml`、`?? docs/process/`、`M OKR.md` 全部命中 | ✅ |
| 并行默认 2-4 | `AGENTS.md` "并行启动强制规则"、`registry.toml.parallel_default`、`iteration_velocity.md` § 3.1 | "默认每个 sprint 启动 2-4 个并行子 agent" / `"2-4 sub agents per sprint when 2+ non-overlapping owners exist"` | ✅ |
| 主节点写代码口子=不开 | `AGENTS.md` "主节点禁区"原文保留 + 并行规则新增"降级为 1 个子 agent 完成 2+ owner sprint 视为流程违规"+ "主节点亲自下场写代码：严重违规" | 三处一致禁止 | ✅ |
| 文档分层 Epic 六文档 / Micro 仅 tech-done | `AGENTS.md` "Epic / Micro Sprint 分层"、`registry.toml.epic_micro_doc_policy`、`iteration_velocity.md` § 2 判定矩阵 | Epic 维度任一命中即视为 Epic；Micro 严格四条件 | ✅ |
| OKR 最低优先级=软提醒 | `AGENTS.md` "OKR 最低优先级软提醒"、`registry.toml.okr_lowest_objective_rule`、`iteration_velocity.md` § 4、`OKR.md` 4.1 节末尾追加段 | 明确"软提醒、不阻塞、final 复核" | ✅ |
| Blocker 2 轮上限强制切换或升级 | `AGENTS.md` "同一 Blocker 重复消费红线"、`registry.toml.repeated_blocker_cap`、`iteration_velocity.md` § 5 | 明确"最多 2 轮、第 3 轮起切换或升级、CEO 可重置" | ✅ |

## 验证命令对照

| 验收命令 | 子 agent 输出 | 主节点独立复核 | 一致 |
| --- | --- | --- | --- |
| `git diff --check -- <5 files>` | exit 0，仅 CRLF 警告 | exit 0，输出 `warning: ... LF will be replaced by CRLF ...`，无 trailing whitespace 报错 | ✅ |
| `python3 -c "import tomllib; tomllib.load(...)"` | `toml OK` | `toml OK` | ✅ |
| `Test-Path docs/process/iteration_velocity.md` | `process doc exists` | `process doc exists` | ✅ |
| `grep -c "sprint_type" AGENTS.md` | 3 | 子 agent 已验证 3 | ✅ |
| `grep -c "iteration_velocity" .codex/agents/registry.toml` | 1 | 子 agent 已验证 1 | ✅ |
| `grep -c "iteration_velocity.md" AGENTS.md` | 5 | 子 agent 已验证 5 | ✅ |
| `git status --short` | 3 M + 2 ?? 全部在授权 5 路径内 | 完全一致 | ✅ |
| `git diff --stat -- OKR.md` | `1 file changed, 2 insertions(+)` | 完全一致，diff 显示仅在 4.1 节末尾追加 1 段 | ✅ |

## 围栏自检

| 围栏项 | 期望 | 实测 | 是否一致 |
| --- | --- | --- | --- |
| 仅改授权 5 路径 | 是 | `git status --short` 仅 5 项命中授权 | ✅ |
| 不改任何 OKR 完成度数字 | 是 | `git diff -- OKR.md` 仅 2 行追加，无数字变更，无既有快照表改写 | ✅ |
| 不改任何 IC role TOML | 是 | `git status --short` 未列出 `.codex/agents/robot-software-engineer.toml` 等 | ✅ |
| 不改任何 ROS2 产品代码 | 是 | `git status --short` 未列出 `src/**` | ✅ |
| 不改 vendor 文件 | 是 | `git status --short` 未列出 `docs/vendor/**` | ✅ |
| 不改硬件配置 | 是 | `git status --short` 未列出 launch 文件 | ✅ |
| 不追溯既有 sprint | 是 | `git status --short` 仅本 sprint 目录被新建，其他 sprint 目录 untouched | ✅ |
| TOML 语法可解析 | 是 | `toml OK` | ✅ |
| 三处规则文本互相引用 | 是 | AGENTS.md 引用 iteration_velocity.md 5 次；registry.toml 通过 `process_doc_reference` 引用；iteration_velocity.md § 6 明确引用 AGENTS.md + registry.toml + OKR.md | ✅ |

## 用户侧（CEO）判定要点

CEO 在本轮 sprint 启动前明确反馈"每次迭代东西太少、进度太慢、coding 改了对整体进展帮助不大、是否要并行研发"。本轮落地的规则直接对应每一个槽点：

1. **东西太少** → Epic / Micro 分层 + 默认 2-4 并行：单 sprint 默认覆盖 2-4 个 owner 工作，预期单轮产出明显增加。
2. **进度太慢** → 最低 Objective 软提醒 + Blocker 2 轮红线：让低完成度 Objective（O5=30%、O6=12%）显式获得轮次配额；同一根因 blocker 不再被反复消费。
3. **coding 改了对整体进展帮助不大** → 最低 Objective 软提醒要求 Epic tech-plan 显式回答"为什么不去做最低 Objective"，从源头降低高完成度 Objective 上的 +1pp 微切片冲动。
4. **是否要并行研发** → 默认并行 2-4，1 owner 单线仅在三条豁免下合法；违规处置明确写入 AGENTS.md。

## 不能声明的事项（再次复核）

- 不声明任何 Objective（O1-O6）完成度变化（本轮全部维持原数字）。
- 不声明 HIL 通过。
- 不声明真实 WAVE ROVER / 串口 / UART / IMU / 电池数据。
- 不声明 ROS2 主链路、Nav2、SLAM、视觉、fixed-route 实跑。
- 不声明手机端真实浏览器或普通用户实测。
- 不声明云端 4G / OSS / CDN 真实部署。

证据边界标记：`process_doc_only`。

## 结论

本 sprint 通过 side2side check，可以进入 final 收口。CEO 拍板的 6 个参数 100% 落地，授权范围 0 越界，OKR 既有数字 0 改动，所有验收命令 exit 0。
