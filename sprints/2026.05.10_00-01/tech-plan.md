# Sprint 2026.05.10_00-01 Tech Plan

## 技术方案

1. 修改 `FixedRouteAutonomy._visual_gate_pass()`：
   - 保留 `enable_visual_gate=false` 的直接通过。
   - 移除 `dry_run` 对 visual gate 的直接绕过。
   - 为缺 keyframe、缺 live frame、缺 live descriptor、匹配不足写入可解释错误。
2. 修改 `_run_route()`：
   - visual gate 未通过时保持 `waiting_visual_gate`，不推进 `current_index`。
   - status JSON 继续包含 `current_target`、`current_index`、`last_error`、`failure_reason`。
3. 更新 nav dry-run 离线测试：
   - 原有 bypass 测试改为 visual gate enabled 时等待。
   - 保留 visual gate disabled 时 completed。

## 验证计划

| 命令 | 目的 |
| --- | --- |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_nav/test -p "test_fixed_route_dry_run_offline.py"` | 定向验证 dry-run/visual gate |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_nav/test -p "test*.py"` | nav 包回归 |
| `PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh` | 全局软件护栏 |

## 不做事项

- 不改 WAVE ROVER/串口/硬件协议。
- 不声明 Docker Humble build 或 HIL 通过。
- 不改 `.codex/agents/*.toml` 当前未提交用户改动。
