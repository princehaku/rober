# Sprint 2026.05.10 19-20 Hardware Proof Diagnostics - Tech Plan

## 状态

- 阶段：tech-plan completed。
- 时间：2026-05-10 19:20 Asia/Shanghai。
- Product Owner：`product-okr-owner`。
- 实现 owner：`full-stack-software-engineer`。
- 执行方式：单 owner 单线闭环，由 `full-stack-software-engineer` 负责实现、测试、修复和 `tech-done.md`。

## Goal

把 `hardware_diagnostics_proof` 离线 artifact 接入 operator diagnostics API 和手机 operator 页面，让售后诊断能保守展示 hardware software proof、needs HIL、invalid config 和 read error。

## Architecture

在 `operator_gateway_diagnostics.py` 中新增无 ROS 依赖的 artifact summary builder，由 `build_diagnostics_payload()` 注入 `/api/diagnostics.hardware_proof`。在 `operator_gateway_http.py` 中增加可读的 hardware proof card，复用现有 dependency-free HTML/JS 页面模式。

实现必须让 artifact 读取失败降级为结构化 payload，不能破坏 `/api/diagnostics`。UI 只表达 software proof 和 needs HIL，不把未上车 proof 包装成硬件通过。

## Tech Stack

- Python stdlib：`json`、`os`、`unittest`、`http.server`。
- 现有 ROS2 behavior package 测试模式：package-scoped `python3 -m unittest discover`。
- 现有 operator gateway：dependency-free HTML/CSS/JS string served by `operator_gateway_http.py`。

## 文件范围

允许 `full-stack-software-engineer` 修改：

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_static.py`
- `docs/interfaces/ros_contracts.md`
- `sprints/2026.05.10_19-20_hardware-proof-diagnostics/tech-done.md`
- `sprints/2026.05.10_19-20_hardware-proof-diagnostics/side2side_check.md`
- `sprints/2026.05.10_19-20_hardware-proof-diagnostics/final.md`
- `OKR.md`

禁止修改：

- `src/ros2_trashbot_hardware/` 运行时代码、测试、setup 或硬件配置。
- launch 默认参数、UART 默认值、vendor 文件、factory firmware。
- 与 operator diagnostics/html 无关的 ROS2 package。

## 接口设计

新增 `/api/diagnostics.hardware_proof` summary，建议字段：

| Field | Contract |
| --- | --- |
| `status` | 产品状态：`software_proof`、`needs_hil`、`invalid_config`、`read_error`。 |
| `artifact_ref` | 当前读取的 artifact 路径或配置引用；为空时配合 `read_error`。 |
| `source_status` | artifact 原始 status，例如 `software_proof_ready`、`invalid_config`、`feedback_parse_failed`。 |
| `exists` | artifact 文件是否存在并可打开。 |
| `read_error` | 读取失败、JSON 解析失败或字段不符合预期时的错误说明。 |
| `summary` | 面向手机/售后的短文案，必须保守，不宣称硬件通过。 |
| `next_step` | 下一步动作：重跑 proof、修配置、运行 WAVE ROVER HIL、联系支持。 |
| `vendor_sources` | artifact 中已有 vendor source refs。不得在这里新增未查证硬件事实。 |
| `risk_flags` | artifact 中已有 risk flags。存在 HIL 风险时必须推动 `needs_hil`。 |
| `hil_recipe` | artifact 中已有 HIL recipe 的摘要或原始结构；供售后/工程师继续验证。 |

状态映射：

- artifact status `software_proof_ready` 且仍有 HIL 风险：`needs_hil`。
- artifact status `software_proof_ready` 且没有 HIL 风险：`software_proof`，但页面仍要写明这是 software proof。
- artifact status `invalid_config`：`invalid_config`。
- artifact status `feedback_parse_failed`：`read_error` 或 `needs_hil`，由 Engineer 根据 artifact 内容选择更保守表达；不得显示为硬件通过。
- artifact 未配置、缺失、不可读、JSON decode error、非 dict、缺 status：`read_error`。

## 实现任务

### Task 1: Diagnostics Payload

**Files:**

- Modify: `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- Test: `src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`

Steps:

1. 在 diagnostics tests 中新增 artifact fixtures，覆盖：
   - `software_proof_ready` + risk flags -> `needs_hil`。
   - `software_proof_ready` + no risk flags -> `software_proof`。
   - `invalid_config` -> `invalid_config`。
   - missing file / corrupt JSON / non-dict JSON -> `read_error`。
2. 修改 `build_diagnostics_payload()` 签名，新增 `hardware_proof_ref` 可选参数，默认空字符串以保持现有调用兼容。
3. 新增 `summarize_hardware_proof(path)` 或同等纯函数，返回稳定 summary dict。
4. 确保 `build_diagnostics_payload()` 总是包含 `hardware_proof=summarize_hardware_proof(hardware_proof_ref)`。
5. 运行 targeted diagnostics tests。

Expected command:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_behavior/test -p 'test_operator_gateway_diagnostics.py'
```

Expected result：全部通过。

### Task 2: HTTP API and Phone Page

**Files:**

- Modify: `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- Test: `src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
- Test: `src/ros2_trashbot_behavior/test/test_operator_gateway_static.py`

Steps:

1. 让 fake gateway diagnostics fixture 包含 `hardware_proof` 四类状态中的代表样例。
2. 在 endpoint test 中断言 `/api/diagnostics` 返回 `hardware_proof.status`、`summary`、`next_step`、`read_error`、`risk_flags`。
3. 在 HTML 中新增 hardware proof diagnostics card，元素 id 建议包含：
   - `diagHardwareProof`
   - `diagHardwareProofBadge`
   - `diagHardwareProofSummary`
   - `diagHardwareProofNextStep`
   - `diagHardwareProofReasons`
4. 新增 JS renderer，例如 `hardwareProofView()` 和 `renderHardwareProof()`，只输出四类产品状态。
5. 更新页面静态测试，确保 HTML 包含 `hardware_proof`、四类状态和 needs-HIL 文案。
6. 运行 targeted HTTP tests。

Expected command:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_behavior/test -p 'test_operator_gateway_http.py'
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_behavior/test -p 'test_operator_gateway_static.py'
```

Expected result：全部通过。

### Task 3: Interface Docs and Sprint Records

**Files:**

- Modify: `docs/interfaces/ros_contracts.md`
- Create/Modify: `sprints/2026.05.10_19-20_hardware-proof-diagnostics/tech-done.md`
- Later acceptance: `sprints/2026.05.10_19-20_hardware-proof-diagnostics/side2side_check.md`
- Later final: `sprints/2026.05.10_19-20_hardware-proof-diagnostics/final.md`
- Later OKR closeout: `OKR.md`

Steps:

1. 在 Operator Gateway diagnostics contract 下新增 `/api/diagnostics.hardware_proof` 字段表。
2. 明确 product boundary：software proof 不等于 HIL pass；页面只能表达 `software_proof`、`needs_hil`、`invalid_config`、`read_error`。
3. 在 `tech-done.md` 记录实际改动、验证输出、失败定位和剩余风险。
4. 实现验收后由 Product/OKR Owner 更新 `side2side_check.md`、`final.md` 和必要的 `OKR.md` 进度快照。

Expected command:

```bash
git diff --check -- docs/interfaces/ros_contracts.md sprints/2026.05.10_19-20_hardware-proof-diagnostics/tech-done.md
```

Expected result：无 whitespace error。

### Task 4: Verification Guardrail

**Files:**

- No new implementation files beyond the scope above.

Steps:

1. py_compile changed behavior files。
2. 跑 targeted diagnostics/http/static tests。
3. 跑 full smoke，补齐上一轮小修后的完整回归缺口。
4. 跑 diff check。
5. 如果失败，先定位根因并修复，再重跑对应命令。

## 验收命令

`full-stack-software-engineer` 必须运行并在 `tech-done.md` 粘贴关键输出：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_behavior/test -p 'test_operator_gateway_diagnostics.py'
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_behavior/test -p 'test_operator_gateway_http.py'
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_behavior/test -p 'test_operator_gateway_static.py'
python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py
PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh
git diff --check
```

本计划阶段验证命令：

```bash
git diff --check -- sprints/2026.05.10_19-20_hardware-proof-diagnostics/pre_start.md sprints/2026.05.10_19-20_hardware-proof-diagnostics/prd.md sprints/2026.05.10_19-20_hardware-proof-diagnostics/tech-plan.md
```

## 产品边界

页面只能表达：

- software proof
- needs HIL
- invalid config
- read error

页面不能表达：

- hardware passed
- HIL passed
- 实车验证通过
- 真实 UART/轮向/速度单位/反馈频率已确认

## 风险和阻塞

- 若 artifact path 没有现成参数入口，Engineer 需要新增最小参数或配置字段，但不能硬编码路径。
- 若 proof artifact 结构后续变化，summary builder 必须保守降级到 `read_error` 或 `needs_hil`。
- 本轮不消灭 Objective 1 HIL 风险，只让 Objective 5 售后诊断能看见风险。
- 完整 smoke 必须重跑；否则上一轮小修后的跨包风险仍未关闭。

## 完成前自检

- 是否只修改了允许范围内文件。
- 是否没有宣称硬件已通过。
- 是否所有 read error 都不会让 `/api/diagnostics` 崩溃。
- 是否保留 vision diagnostics 和 existing operator flow。
- 是否把验证结果和剩余风险写入 `tech-done.md`。
- 是否为 Product/OKR Owner 后续 `side2side_check.md`、`final.md`、`OKR.md` 收口留下明确证据。
