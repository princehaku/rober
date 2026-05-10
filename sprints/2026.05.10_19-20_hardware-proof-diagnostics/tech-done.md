# Sprint 2026.05.10 19-20 Hardware Proof Diagnostics - Tech Done

## 状态

- 阶段：tech-done completed
- 时间：2026-05-10 19:47 Asia/Shanghai
- Owner：`full-stack-software-engineer`
- 硬件事实入口：已阅读 `docs/vendor/VENDOR_INDEX.md`；本轮只展示 `hardware_diagnostics_proof` artifact 中已有 vendor refs/risk，不新增硬件事实、不声明 HIL 或实车通过。

## 用户旅程变化和触点收益

- `/api/diagnostics` 现在总是返回 `hardware_proof`，手机/售后诊断不再只看到软件、路线、视觉证据。
- Operator 页面新增 Hardware proof 卡片，能把离线 proof 映射为 `software_proof`、`needs_hil`、`invalid_config`、`read_error` 四类可读状态。
- `needs_hil` 文案明确表达 software proof exists, hardware-in-loop still required；页面不宣称 hardware passed、HIL passed 或实车通过。
- 读取失败、坏 JSON、非对象 JSON、缺 status、未知 status、feedback parse failed 都保守降级，不会让 `/api/diagnostics` 崩溃或误报硬件可信。

## 实际改动

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
  - 新增 `summarize_hardware_proof(path)` 纯函数。
  - `build_diagnostics_payload()` 新增兼容参数 `hardware_proof_ref=""`。
  - payload 总是包含 `hardware_proof`。
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
  - 新增 `diagHardwareProof` 诊断卡及 badge、summary、next step、reasons DOM。
  - 新增 `hardwareProofView()` / `renderHardwareProof()`，只渲染四类保守状态。
- `src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 覆盖 `software_proof_ready` + HIL risk、无 HIL risk、`invalid_config`、`feedback_parse_failed`、missing/corrupt/non-dict/missing status。
  - 覆盖 `build_diagnostics_payload()` 注入 configured hardware proof。
- `src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
  - 扩展 fake diagnostics payload，断言 `/api/diagnostics` 返回 `hardware_proof` 关键字段。
  - 断言 HTML/JS 包含 hardware proof 卡片、四类状态和 needs-HIL 文案。
- `src/ros2_trashbot_behavior/test/test_operator_gateway_static.py`
  - 增加静态 contract 断言，防止 operator 页面出现 hardware/HIL passed 文案。
- `docs/interfaces/ros_contracts.md`
  - 增补 `/api/diagnostics.hardware_proof` 字段、状态映射和产品边界。

## 接口影响

- `/api/diagnostics` 新增字段：
  - `hardware_proof.status`
  - `hardware_proof.artifact_ref`
  - `hardware_proof.source_status`
  - `hardware_proof.exists`
  - `hardware_proof.read_error`
  - `hardware_proof.summary`
  - `hardware_proof.next_step`
  - `hardware_proof.vendor_sources`
  - `hardware_proof.risk_flags`
  - `hardware_proof.hil_recipe`
- 现有调用兼容：`hardware_proof_ref` 默认空字符串；未配置 artifact 时返回结构化 `read_error`。
- 未修改 `src/ros2_trashbot_hardware/`、launch 默认参数、UART 默认值、vendor 文件、factory firmware、`OKR.md`、`side2side_check.md`、`final.md`。

## 验证输出

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_behavior/test -p 'test_operator_gateway_diagnostics.py'
..............
----------------------------------------------------------------------
Ran 14 tests in 0.643s

OK
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_behavior/test -p 'test_operator_gateway_http.py'
...............
----------------------------------------------------------------------
Ran 16 tests in 8.051s

OK
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_behavior/test -p 'test_operator_gateway_static.py'
........
----------------------------------------------------------------------
Ran 8 tests in 0.041s

OK
```

```bash
python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py
# no output; command exited 0
```

```bash
PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh
Ran 6 tests in 0.104s
OK
Ran 24 tests in 0.139s
OK
Ran 39 tests in 3.634s
OK
Ran 9 tests in 0.067s
OK
Ran 118 tests in 17.461s
OK
Ran 13 tests in 0.578s
OK
```

```bash
git diff --check
# no output; command exited 0
```

## 失败定位和修复

- 首轮 `test_operator_gateway_static.py` 失败：新增 UI 文案里出现了 `HIL passed` 片段，即使语义是否定句，也不符合页面不得表达 HIL passed 的边界。
- 修复：把页面和 diagnostics summary 文案改成 `does not validate real hardware or HIL`、`hardware-in-loop still required before treating the robot as validated`，并重跑 targeted tests。

## 剩余风险

- 本轮只把离线 artifact 接入 diagnostics contract 和 operator 页面；没有运行真实 WAVE ROVER、UART、轮向、速度单位、反馈频率、IMU、电池 HIL。
- 由于本轮文件范围禁止修改 `operator_gateway.py`，实际节点尚未新增 ROS 参数来传入 `hardware_proof_ref`；当前直接调用 `build_diagnostics_payload(..., hardware_proof_ref=...)` 可读 artifact，未配置时 `/api/diagnostics.hardware_proof` 会保守返回 `read_error`。
- Product/Coordinator 后续需要在允许范围内收口 `side2side_check.md`、`final.md`、`OKR.md`，并决定是否安排下一轮为 operator gateway 节点增加 artifact ref 参数入口。
