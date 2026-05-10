# Sprint 2026.05.10 13-14 - tech-plan

## 状态

- 阶段：计划已建立，执行中
- 本文档目标：明确流程修复的文件范围、任务分工、接口影响、验收命令和风险边界。

## 文件范围

本轮任务拆成互不重叠的文件范围：

- 只读 explorer 排查：允许读取 `AGENTS.md`、`registry.toml`、`.codex/agents/`、近期 `sprints/`，不允许改文件。
- 配置修复 worker：允许修改其任务 prompt 中明确列出的配置文件；本留档任务未知其最终文件清单，待 coordinator 集成填入。
- Sprint 留档修复：只允许修改 `sprints/2026.05.10_13-14/` 下的文件：
  - `sprints/2026.05.10_13-14/pre_start.md`
  - `sprints/2026.05.10_13-14/tech-plan.md`
  - `sprints/2026.05.10_13-14/tech-done.md`
  - `sprints/2026.05.10_13-14/final.md`

## 任务分工

- Product Manager / OKR Owner：确认本轮目标是流程修复和验收留档，不冒充业务代码交付。
- 3 个 explorer 子agent：已经并行执行只读排查，分别从 `AGENTS.md` 适配性、`registry.toml` 调度字段、近期 sprint 执行模式角度提供证据。
- Robot Platform Engineer worker：独立处理配置修复，最终结果由 coordinator 集成后写入 `tech-done.md`。
- Sprint 留档 worker：维护本目录 4 个 sprint 文档，记录真实进展、验证命令和风险。

## 接口影响

- 对 ROS2 runtime、launch、msg/srv/action、导航、行为状态机、硬件驱动无接口影响。
- 对硬件/vendor 无影响；本轮不涉及引脚、电压、UART 设备、波特率、JSON 指令、速度映射、反馈协议或机械尺寸。
- 对 agent 工作流有预期影响：后续主线程应以 coordinator 身份拆任务、派 worker、收集验证结果，并把 sprint 文档作为过程证据。

## 验收命令

Sprint 留档 worker 必须运行：

```bash
find sprints/2026.05.10_13-14 -maxdepth 1 -type f -print | sort
grep -RIn "待集成\|子agent\|spawn_agent\|并行" sprints/2026.05.10_13-14
```

Coordinator 后续集成配置修复时，应补充配置 worker 实际运行的验证命令和结果；不得用本留档验证冒充配置修复已完成。

## 风险边界

- 本文档记录的是流程修复 sprint，不代表业务代码、机器人功能或硬件链路完成。
- 配置修复 worker 的最终结果当前未知，必须保留“待集成 coordinator 填入最终验证结果”的状态，直到实际结果返回。
- 如果后续发现配置修复触及 `AGENTS.md`、`registry.toml` 或角色 toml，应由配置 worker 自己记录改动与验证；本留档任务不越权修改。
- 只读 explorer 的结论是排查证据，不等同于已经完成配置修复。
