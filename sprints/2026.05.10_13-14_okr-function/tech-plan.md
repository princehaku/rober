# Sprint 2026.05.10 13-14 OKR Function - Tech Plan

## 状态

- 阶段：tech-plan 已完成，可进入 implementation。
- 主责：Autonomy Algorithm Engineer。
- 执行方式：1 owner 单线闭环，必须由 `autonomy-engineer` 子 agent 实现、验证并更新 `tech-done.md`。Coordinator 不直接写生产代码或测试代码。

## 目标

为 route/camera 样本闭环增加一个可运行的离线验证/汇总能力，让真实采集后的 vision sample manifest 可以被检查、汇总，并暴露给后续 diagnostics/人工复盘使用。

## 文件范围

Autonomy Engineer 可改范围：

- `src/ros2_trashbot_vision/`
- `src/ros2_trashbot_nav/` 中与 route/keyframe manifest contract 直接相关的只读或最小适配代码
- `docs/interfaces/` 或 `docs/vision/` 中 manifest/diagnostics contract 文档，如实现需要
- `sprints/2026.05.10_13-14_okr-function/tech-done.md`

禁止改动：

- `AGENTS.md`
- `OKR.md`，实现完成后由后续收口更新
- `sprints/2026.05.10_13-14/`
- 硬件/vendor、WAVE ROVER、ESP32、Orange Pi、UART、launch 硬件参数
- 手机 UI/API 生产代码，除非另开 full-stack owner 任务

## 接口影响

- 不改 ROS2 msg/srv/action contract。
- 不要求 ROS2 daemon、Nav2、相机或硬件在线。
- 新能力应以纯函数和/或 CLI 包装暴露，后续可被 diagnostics 调用。
- 输出 summary 必须是结构化数据，字段名保持稳定；如需要人类可读输出，应作为附加层，不替代结构化结果。

## 建议实现步骤

1. 读取现有 `ros2_trashbot_vision` 样本写入、manifest 生成和测试，确认 manifest 当前字段。
2. 设计 summary contract，至少包含：
   - `manifest_path`
   - `sample_count`
   - `file_counts`
   - `context_counts`
   - `negative_sample_count`
   - `anomaly_sample_count`
   - `errors`
   - `warnings`
3. 实现 manifest 加载、路径归一化、引用文件存在性检查、字段覆盖统计和错误收集。
4. 增加 CLI 或 console script；若改 packaging 风险较高，可先提供模块级 CLI：`python3 -m <module> <manifest>`。
5. 增加 focused tests：
   - valid manifest 汇总成功。
   - manifest 引用缺失文件时返回 error/warning。
   - 空 manifest 或缺关键字段时不静默成功。
6. 运行目标测试和可用 smoke。
7. 更新 `sprints/2026.05.10_13-14_okr-function/tech-done.md`，写清实际改动、验证结果、偏差和剩余风险。

## 验收命令

Autonomy Engineer 必须至少运行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_vision/test -p 'test_*.py'
python3 -m py_compile $(find src/ros2_trashbot_vision -name '*.py' -print)
git diff --check
```

如果改动触及 nav manifest/route contract，还必须运行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_nav/test -p 'test_*.py'
```

如果本地环境允许，应继续运行完整护栏：

```bash
PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh
```

Product planning 本轮验收命令：

```bash
find sprints/2026.05.10_13-14_okr-function -maxdepth 1 -type f -print | sort
sed -n '1,220p' sprints/2026.05.10_13-14_okr-function/tech-plan.md
```

## 优先级

- P0：manifest 离线检查和结构化 summary 可运行，坏数据可判定。
- P1：summary 字段便于 diagnostics/人工复盘后续消费。
- P2：CLI 输出美化、文档扩展、更多 fixture 场景。

## 风险边界

- 本轮不声明真实 camera/odom 数据集完成；没有实采 manifest 时，只能提升 Objective 4 的离线闭环能力。
- 本轮不接入手机 diagnostics API；只要求输出能被后续消费。
- 本轮不触碰硬件事实，因此不需要读取 vendor 文档；若实现中意外涉及硬件参数，必须立即停下并先读 `docs/vendor/VENDOR_INDEX.md`。
- 测试是护栏，不是主目标；避免为了测试数量做无关重构。

## 子 Agent Prompt

后续 coordinator 应启动 1 个 `spawn_agent(agent_type=worker)`，角色为 `autonomy-engineer`，prompt 必须包含：

- `.codex/agents/autonomy-engineer.toml` 的完整 `prompt` 字段。
- 本轮任务：实现 route/camera sample manifest 离线检查与汇总能力。
- 文件范围：本 tech-plan 的 Autonomy Engineer 可改范围和禁止范围。
- 验收命令：本 tech-plan 的 Autonomy Engineer 验收命令。
- 输出要求：
  1. 实际改动的文件列表
  2. 验证命令输出结果
  3. 失败定位（如有）
  4. 剩余风险

