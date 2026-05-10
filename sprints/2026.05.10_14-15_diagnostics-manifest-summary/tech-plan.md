# Sprint 2026.05.10 14-15 Diagnostics Manifest Summary - Tech Plan

## 状态

- 阶段：tech-plan 已完成，可进入 implementation。
- 主责：User Touchpoint Full-Stack Engineer。
- 执行方式：1 owner 单线闭环，必须由 `full-stack-software-engineer` 子 agent 实现、验证并更新 `tech-done.md`。Coordinator 不直接写生产代码或测试代码。

## 目标

把上一轮新增的 vision sample manifest 离线 checker 接入 operator diagnostics payload，让 `/api/diagnostics` 不只返回 manifest 路径和简化样本队列，还能告诉手机/远程支持样本链完整性、缺失引用、error/warning 和上下文覆盖。

## 文件范围

Full-Stack Engineer 可改范围：

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`
- `sprints/2026.05.10_14-15_diagnostics-manifest-summary/tech-done.md`

允许只读：

- `src/ros2_trashbot_vision/ros2_trashbot_vision/vision_sample_manifest.py`
- `src/ros2_trashbot_vision/test/test_vision_sample_manifest.py`
- `OKR.md`

禁止改动：

- `AGENTS.md`
- `.codex/agents/`
- 硬件/vendor、WAVE ROVER、ESP32、Orange Pi、UART、launch 硬件参数
- `src/ros2_trashbot_vision/` 生产代码，除非 import contract 明确无法复用且必须修复
- `sprints/2026.05.10_13-14/` 和 `sprints/2026.05.10_13-14_okr-function/`

## 接口影响

- 不改 ROS2 msg/srv/action contract。
- `/api/diagnostics` 的 `vision_samples` 字段保持旧字段兼容，并新增结构化完整性字段。
- 新增字段建议：
  - `integrity_summary`
  - `integrity_error_count`
  - `integrity_warning_count`
  - `missing_file_ref_count`
  - `context_field_coverage`
  - `file_counts`

## 验收命令

Full-Stack Engineer 必须至少运行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_behavior/test -p 'test_operator_gateway_diagnostics.py'
python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
git diff --check
```

如果 import 或 contract 触及 vision checker，还必须运行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_vision/test -p 'test_vision_sample_manifest.py'
```

如果本地环境允许，应继续运行完整护栏：

```bash
PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh
```

## 风险边界

- 本轮不证明真实 camera/odom manifest 存在；真实数据仍是 Objective 4 后续缺口。
- 如果 behavior 包对 vision 包 import 在安装环境中有依赖风险，必须保守 fallback，不能让 `/api/diagnostics` 因 checker import 失败整体不可用。
- 测试是护栏，不做无关重构。
