# Sprint 2026.05.10 13-14 - pre_start

## 状态

- 阶段：已启动
- Sprint 类型：流程修复 / agent 调度规则验证
- 是否涉及硬件/vendor：否。本轮不修改 WAVE ROVER、ESP32、Orange Pi、UART、底盘协议、引脚、电压、固件或机械结构；无需读取 `docs/vendor/VENDOR_INDEX.md`。

## 背景

用户要求检查 `AGENTS.md` 和 `registry.toml`，解释为什么近期写代码没有充分使用子agent，并修复本轮流程留档。上一个最新 sprint `2026.05.10_12-13` 已进入 final，因此本轮新开 `2026.05.10_13-14`。

本轮已并行启动 3 个只读 explorer 子agent 排查流程问题，初步结论包括：

- `AGENTS.md` 绑定 Cursor Task / `generalPurpose`，不直接适配 Codex `spawn_agent(worker)`。
- 主节点职责与“禁止改文件/跑测试”的文字要求存在冲突，导致 coordinator 和 executor 边界不清。
- `registry.toml` 缺少 `enabled`、`capabilities`、关键调度字段，降低了可发现性和可执行性。
- 最近 sprint 多为单 owner 任务，没有在文件范围互不重叠时充分并行派发。
- 当前应从已 final 的 12-13 进入新 sprint 13-14，而不是继续覆盖旧 sprint。

## 目标

修复并验证子agent调度规则，让主线程从执行者退回 coordinator：主线程负责拆解、派发、集成验收和 sprint 留档；代码、配置修复、测试和验证由合适的子agent执行，并在文件范围互不重叠时并行推进。

## Owner

- Product Manager / OKR Owner：本轮 owner，负责流程目标、验收口径、sprint 留档真实性。
- Robot Platform Engineer：协同配置修复，负责把 ROS2 项目内的 agent 调度配置改到可执行、可验证状态。

## 范围边界

- 本轮 sprint 留档只写入 `sprints/2026.05.10_13-14/`。
- 不修改 `AGENTS.md`、`registry.toml`、角色 toml 或业务代码。
- 配置修复由独立 worker 处理，本留档任务只记录当前已知状态和待集成占位。
- 不声称业务代码、硬件链路或 ROS2 功能已经完成。
