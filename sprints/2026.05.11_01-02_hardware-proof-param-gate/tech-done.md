# Sprint 2026.05.11 01-02 Hardware Proof Param Gate - Tech Done

## 状态

- 阶段：tech-done completed
- 时间：2026-05-11 01:26 CST
- Owner：`robot-software-engineer`

## 实际改动

1. `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py`
- 新增参数声明：`hardware_proof_ref`（默认空字符串）。
- 新增参数读取：`self.hardware_proof_ref = os.path.expanduser(...)`。
- `/api/diagnostics` 构建时新增透传：`hardware_proof_ref=self.hardware_proof_ref`。

2. `src/ros2_trashbot_bringup/launch/bringup.launch.py`
- 新增 launch 参数：`operator_hardware_proof_ref`。
- 映射到 operator gateway node 参数：`hardware_proof_ref`。

3. `src/ros2_trashbot_bringup/launch/autonomous.launch.py`
- 新增 launch 参数：`operator_hardware_proof_ref`。
- 映射到 operator gateway node 参数：`hardware_proof_ref`。

4. `src/ros2_trashbot_behavior/test/test_operator_gateway_static.py`
- 增加静态断言：`hardware_proof_ref` 参数声明、读取与 diagnostics 透传。

5. `src/ros2_trashbot_bringup/test/test_launch_contract_static.py`
- 增加静态断言：两份 launch 必须声明 `operator_hardware_proof_ref`，并透传到 operator gateway 的 `hardware_proof_ref`。

6. `docs/interfaces/ros_contracts.md`
- 在 Operator Gateway 参数表新增 `hardware_proof_ref` 合同。
- 明确边界：software proof 只是软件证据，不等价 HIL pass。

7. `OKR.md`
- 仅更新「4.1 当前 OKR 进度快照」Objective 1 行：补充本轮参数链路证据，进度从约 74% 调整到约 75%。

## 验证结果

1. `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_behavior/test -p 'test_*operator*py'`
- 结果：`Ran 48 tests in 9.624s`，`OK`

2. `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_bringup/test -p 'test_launch_contract_static.py'`
- 结果：`Ran 9 tests in 0.059s`，`OK`

3. `PYTHONDONTWRITEBYTECODE=1 bash -lc 'changed_py=...; python3 -m py_compile $changed_py'`
- 结果：退出码 0，无报错。
- 说明：原命令在本 shell 的双层引号展开下会把文件列表误当 shell 语句；改为等价单引号写法后执行成功。

4. `PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh`
- 结果：全通过。
- 关键片段：
  - `Ran 6 tests ... OK`
  - `Ran 24 tests ... OK`
  - `Ran 44 tests ... OK`
  - `Ran 9 tests ... OK`
  - `Ran 128 tests ... OK`
  - `Ran 13 tests ... OK`

5. `git diff --check -- src/ros2_trashbot_behavior src/ros2_trashbot_bringup docs/interfaces OKR.md sprints/2026.05.11_01-02_hardware-proof-param-gate`
- 结果：无输出（通过）。

## 偏差与处理

- 无功能偏差。
- 验收命令 3 在本 shell 的直接双层引号拼接下出现误执行；已定位为 shell 展开差异，并用等价命令完成 `py_compile` 验证。

## 剩余风险

- 仍无真实 WAVE ROVER HIL 证据；当前仅补齐 software-proof 参数入口与透传。
- `hardware_proof_ref` 默认为空，未配置时 `/api/diagnostics.hardware_proof.status` 仍会保守返回 `read_error`，属于预期。
