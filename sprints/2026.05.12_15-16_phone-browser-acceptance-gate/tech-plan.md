# Sprint 2026.05.12_15-16 Phone Browser Acceptance Gate - Tech Plan

## 状态

- 阶段：tech-plan
- 主责：`full-stack-software-engineer`
- 计划结论：单 owner 闭环；实现阶段必须派 1 个 `full-stack-software-engineer` 子 agent 执行
- 目标证据边界：`software_proof_docker_phone_browser_acceptance_gate`

## 技术目标

在现有 `operator_gateway` 本地 phone-first HTML 和 `/api/status.phone_readiness.command_safety` 基础上，补齐真实浏览器 acceptance gate。上一轮 API/handler proof 不能重复作为本轮 P0；本轮必须由浏览器运行结果证明移动端首屏可读、按钮足够大、关键 copy 可见、主操作阻断和 diagnostics 入口语义正确。

## 文件范围

Full-stack 实现阶段允许改动：

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py`（仅当 status fixture 或 command safety output 需要小修）
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`（仅当 diagnostics copy 需要小修）
- `src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_static.py`
- `scripts/phone_browser_acceptance_gate.py`（若不存在则创建；用于 browser/layout proof）
- `docs/product/mobile_user_flow.md`
- `docs/interfaces/ros_contracts.md`（仅接口 contract 改动时）
- `sprints/2026.05.12_15-16_phone-browser-acceptance-gate/tech-done.md`

不得改动：

- 硬件配置、launch 硬件参数、vendor 文档。
- `OKR.md`、`side2side_check.md`、`final.md`，这些留给 Product 收口。
- 无关 sprint 或 unrelated local churn。

## 任务拆解

### Task A：Browser acceptance 脚本

Owner：`full-stack-software-engineer`

目标：

- 创建或扩展一个最小 browser acceptance script。
- 使用本地 operator HTML/API fixture 或 lightweight server，避免依赖真实 ROS2、硬件、云或 4G。
- 至少检查 `390x844` 和 `768x900` 两个 viewport。

验收点：

- 输出包含 `viewport=...`、`hit_area_status=passed`、`overlap_status=passed`、`ack_copy_visible=true`、`diagnostics_accessible=true`。
- 输出 `evidence_boundary=software_proof_docker_phone_browser_acceptance_gate`。
- 如生成截图，放入本 sprint evidence 子目录或在 `tech-done.md` 记录绝对/相对路径。

建议命令：

```bash
python3 scripts/phone_browser_acceptance_gate.py --output-dir sprints/2026.05.12_15-16_phone-browser-acceptance-gate/evidence
```

### Task B：Operator 首屏布局和 copy 修正

Owner：`full-stack-software-engineer`

目标：

- 修正 operator HTML/CSS/JS 以满足 44 CSS px hit area。
- 让 readiness、command safety 阻断文案、ACK 语义、recovery hint 和 diagnostics 入口在手机首屏清晰可见。
- 保持 Diagnostics accessible，但 Start/Confirm/Cancel 在 blocked state disabled。

验收点：

- Browser acceptance 通过。
- Existing HTTP/unit tests 继续通过。
- 不展示 raw JSON、ROS topic、serial、baudrate、token、cloud secret 或硬件参数。

### Task C：Targeted tests 和兼容性围栏

Owner：`full-stack-software-engineer`

目标：

- 保留上一轮 command safety API shape。
- 新增或调整 focused tests，仅覆盖页面结构、按钮 disabled 状态、copy 和 browser script helper。
- 不新增大批无关测试。

验收命令：

```bash
python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_operator_gateway_http.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_static.py
```

```bash
python3 -m py_compile \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
```

### Task D：产品文档和 sprint tech-done

Owner：`full-stack-software-engineer`

目标：

- 更新 `docs/product/mobile_user_flow.md`，写清本地 browser acceptance gate 的能力和边界。
- 如接口字段新增或语义变化，同步 `docs/interfaces/ros_contracts.md`。
- 创建 `tech-done.md`，记录实际改动、命令输出、截图/evidence 路径、失败定位和剩余风险。

验收点：

- `tech-done.md` 明确本轮只证明 Docker/local browser software proof。
- `tech-done.md` 明确未证明真实手机设备、正式 app、真实云/4G、OSS/CDN 实流量、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

## 接口影响

- 默认不要求新增 API 字段。
- 如果为 browser acceptance 增加 fixture 或 helper 字段，必须保持旧客户端可忽略。
- `phone_readiness.command_safety.actions.*.enabled`、`ack_semantics` 和 diagnostics gate 语义不得退化。
- ACK 语义保持：只代表 command accepted/processing evidence，不代表 delivery success。

## 实现阶段验收命令

Full-stack worker 必须运行并回报：

```bash
python3 scripts/phone_browser_acceptance_gate.py --output-dir sprints/2026.05.12_15-16_phone-browser-acceptance-gate/evidence
```

```bash
python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_operator_gateway_http.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_static.py
```

```bash
python3 -m py_compile \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
```

```bash
git diff --check -- \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_http.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_static.py \
  scripts/phone_browser_acceptance_gate.py \
  docs/product/mobile_user_flow.md \
  docs/interfaces/ros_contracts.md \
  sprints/2026.05.12_15-16_phone-browser-acceptance-gate/tech-done.md
```

Product planning 阶段验收命令：

```bash
git diff --check -- \
  sprints/2026.05.12_15-16_phone-browser-acceptance-gate/pre_start.md \
  sprints/2026.05.12_15-16_phone-browser-acceptance-gate/prd.md \
  sprints/2026.05.12_15-16_phone-browser-acceptance-gate/tech-plan.md
```

## 风险边界

- 如果浏览器依赖不可用，本轮 P0 阻塞；不能把 handler/unit test 当作替代完成。
- 如果只有桌面 viewport 通过，O5 不应上调，因为 KR7 要求手机主流尺寸适配。
- 如果 screenshots 通过但 command safety API 退化，必须先修 API 兼容性。
- 本轮不触碰硬件事实，不需要读取 vendor 资料；若后续涉及 WAVE ROVER、UART、速度、反馈或电气，必须回到 `docs/vendor/VENDOR_INDEX.md`。

## 子 Agent 交付要求

实现阶段必须给 `full-stack-software-engineer` 的 prompt 包含：

1. 完整角色 System Prompt。
2. 本轮任务：完成 O5 phone browser acceptance gate 的 Docker/local software proof。
3. 文件范围：以上 Full-stack 允许改动列表。
4. 验收命令：本 tech-plan 的实现阶段验收命令。
5. 输出要求：实际改动文件、命令输出片段、失败定位、剩余风险。

Product 收到实现结果后只做验收、留档和 OKR 更新，不直接写产品代码或测试代码。
