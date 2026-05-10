# Sprint 2026.05.11 01-02 Hardware Proof Param Gate - Tech Plan

## 状态

- 阶段：tech-plan completed，可直接进入 implementation。
- 时间：2026-05-11 01:13 Asia/Shanghai。
- 执行方式：单 owner 子 agent 闭环。

## Owner

- `robot-software-engineer`

## 文件范围

允许改动：

- `src/ros2_trashbot_behavior/`
- `src/ros2_trashbot_bringup/`
- `docs/interfaces/`
- `OKR.md`
- `sprints/2026.05.11_01-02_hardware-proof-param-gate/`

禁止改动：

- `src/ros2_trashbot_hardware/`（本轮不改硬件协议实现）
- `docs/vendor/`
- 范围外任何文件

## 实现任务

1. `operator_gateway.py`
   - 声明并读取 `hardware_proof_ref` 参数。
   - diagnostics 构建时传入 `hardware_proof_ref`。
2. `bringup.launch.py` / `autonomous.launch.py`
   - 新增 `operator_hardware_proof_ref` launch 参数。
   - 透传到 operator gateway node 参数 `hardware_proof_ref`。
3. 测试
   - 更新 `test_operator_gateway_static.py`（参数声明与 diagnostics 透传断言）。
   - 更新 `test_launch_contract_static.py`（两份 launch 的参数声明与映射断言）。
4. 文档和进度
   - 更新 `docs/interfaces/ros_contracts.md` 参数说明。
   - 更新 `OKR.md` 当前进度快照与本轮新增证据。
   - 回填 `tech-done.md`、`side2side_check.md`、`final.md`。

## 验收命令

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_behavior/test -p 'test_*operator*py'
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_bringup/test -p 'test_launch_contract_static.py'
PYTHONDONTWRITEBYTECODE=1 bash -lc "changed_py=$(git diff --name-only -- src/ros2_trashbot_behavior src/ros2_trashbot_bringup docs/interfaces | grep -E '\\.py$' || true); if [ -n \"$changed_py\" ]; then python3 -m py_compile $changed_py; else echo 'no python files changed for py_compile'; fi"
PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh
git diff --check -- src/ros2_trashbot_behavior src/ros2_trashbot_bringup docs/interfaces OKR.md sprints/2026.05.11_01-02_hardware-proof-param-gate
```

## 风险边界

- 不做 Docker/Humble、不做 WAVE ROVER HIL。
- 若测试失败，必须先修复再回填证据，不能带失败收口。
