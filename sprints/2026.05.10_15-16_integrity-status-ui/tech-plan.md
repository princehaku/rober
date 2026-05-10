# Sprint 2026.05.10 15-16 Integrity Status UI - Tech Plan

## 状态

- 阶段：tech-plan completed，可进入 implementation。
- 时间：2026-05-10 15:00 Asia/Shanghai。
- 主责：User Touchpoint Full-Stack Engineer。
- 执行方式：1 owner 单线闭环，必须由 `full-stack-software-engineer` 子 agent 实现、验证并更新 `tech-done.md`。Coordinator 不直接写产品代码或测试代码。

## 目标

把 `/api/diagnostics.vision_samples.integrity_summary` 从后端诊断字段推进到手机本地 operator 页面，让用户看到视觉证据链诊断灯、缺失原因和恢复建议。测试只做护栏，重点是功能往 O5 手机体验前进。

## 用户价值和产品北极星

- 用户价值：普通用户或现场支持不需要 SSH、ROS2 CLI 或阅读 raw manifest，就能判断视觉证据链是否健康以及下一步怎么恢复。
- 产品北极星：普通用户只靠手机完成垃圾投递任务，并在异常时看到清楚的人话提示和可执行恢复路径。

## OKR 映射

- 主推进 Objective 5：手机体验与量产边界。补齐 operator 页面可读诊断，是 KR4 远程诊断最小数据包和 KR5 普通用户验收的直接 UI 落地。
- 消费 Objective 4：感知模块产品化。复用上一轮 manifest checker 的 `integrity_summary`、缺失文件、error/warning 和 context coverage，不新增视觉算法承诺。
- 不更新 `OKR.md`：本轮实现后由 Product Owner 在收口阶段基于 `tech-done.md` 和验收证据更新进度快照。

## 文件范围

Full-Stack Engineer 可改范围：

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
- `sprints/2026.05.10_15-16_integrity-status-ui/tech-done.md`

允许只读：

- `AGENTS.md`
- `OKR.md`
- `docs/product/mobile_user_flow.md`
- `docs/interfaces/ros_contracts.md`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `sprints/2026.05.10_14-15_diagnostics-manifest-summary/tech-done.md`

禁止改动：

- `OKR.md`
- `AGENTS.md`
- `.codex/agents/`
- `docs/vendor/`
- `src/ros2_trashbot_hardware/`
- `src/ros2_trashbot_vision/`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- ROS2 msg/srv/action 文件
- launch 硬件参数、UART、WAVE ROVER、ESP32、Orange Pi 相关配置
- 本 sprint 的 `pre_start.md`、`prd.md`、`tech-plan.md`

## 接口影响

- 不改 ROS2 msg/srv/action。
- 不改 `/api/diagnostics` payload shape。
- 页面只消费已有字段：
  - `vision_samples.integrity_summary.status`
  - `vision_samples.integrity_error_count`
  - `vision_samples.integrity_warning_count`
  - `vision_samples.missing_file_ref_count`
  - `vision_samples.missing_file_refs`
  - `vision_samples.integrity_errors`
  - `vision_samples.integrity_warnings`
  - `vision_samples.read_error`
  - `vision_samples.context_field_coverage`
  - `vision_samples.file_counts`
- `mobile_user_flow` 的 local API 不变，仍是 `/api/status`、`/api/diagnostics`、`/api/collect`、`/api/dropoff/confirm`、`/api/cancel`。

## 实施计划

### Task 1：补 HTTP 页面测试护栏

文件：

- 修改：`src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`

步骤：

1. 在 `FakeGateway.diagnostics_payload["vision_samples"]` 中补齐上一轮新增字段 fixture：
   - `integrity_summary.status = "warning"`
   - `integrity_error_count = 0`
   - `integrity_warning_count = 1`
   - `missing_file_ref_count = 1`
   - `missing_file_refs` 包含一个 `field` 和 `resolved_path`
   - `integrity_warnings` 包含一条简短 warning
   - `context_field_coverage` 和 `file_counts` 保持简单 dict
2. 在 `test_diagnostics_endpoint_returns_remote_support_package` 中追加断言，确认 HTTP JSON 仍透传这些字段。
3. 在 `test_index_page_contains_operator_controls` 中追加页面静态断言，至少包含：
   - `diagVisionIntegrity`
   - `diagVisionIntegrityBadge`
   - `diagVisionIntegritySummary`
   - `diagVisionIntegrityReasons`
   - `diagVisionIntegrityAdvice`
   - `renderVisionIntegrity`
   - `visionIntegrityView`
   - `integrity_summary`
   - `missing_file_refs`
   - `context_field_coverage`
   - `file_counts`

### Task 2：在 operator 页面增加视觉证据链诊断卡片

文件：

- 修改：`src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`

步骤：

1. 在 Support Diagnostics panel 中新增一个视觉证据链区域，放在现有 vision sample 指标附近，不删除 raw diagnostics JSON。
2. 新增稳定 DOM id：
   - `diagVisionIntegrity`
   - `diagVisionIntegrityBadge`
   - `diagVisionIntegritySummary`
   - `diagVisionIntegrityReasons`
   - `diagVisionIntegrityAdvice`
3. 新增 CSS class：
   - `.integrityBadge`
   - `.integrityBadge.ok`
   - `.integrityBadge.warning`
   - `.integrityBadge.error`
   - `.integrityBadge.muted`
4. 保持手机端可读：原因列表最多展示 3 条，路径使用 `overflow-wrap:anywhere`，不让长路径撑破页面。

### Task 3：实现字段到用户文案的映射

文件：

- 修改：`src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`

步骤：

1. 新增 JS 函数 `visionIntegrityView(visionSamples)`，返回：
   - `status`
   - `label`
   - `tone`
   - `summary`
   - `reasons`
   - `advice`
2. 状态映射要求：
   - `ok`：label `Healthy`，summary 表达视觉证据链完整。
   - `warning`：label `Needs review`，summary 表达证据链可用但需要复查。
   - `error`：label `Broken`，summary 表达视觉证据链不可信。
   - `not_configured`：label `Not configured`，summary 表达还没有配置视觉样本链。
   - `checker_unavailable`：label `Checker unavailable`，summary 表达当前软件包缺少 checker，不能直接判断样本链。
   - `checker_failed`：label `Checker failed`，summary 表达 checker 执行失败，需要支持排查。
   - unknown：label `Unknown`，summary 表达没有足够诊断数据。
3. 原因优先级：
   - 先取 `missing_file_refs`，每条格式为 `Missing <field>: <resolved_path or value>`。
   - 再取 `integrity_errors`。
   - 再取 `integrity_warnings`。
   - 最后取 `read_error`。
   - 最多展示 3 条；没有原因时展示 `No blocking evidence-chain issue reported.`
4. 恢复建议：
   - `ok`：`Continue the task flow. Keep collecting samples during real runs.`
   - `warning`：`Review the listed sample evidence before using it for route or anomaly decisions.`
   - `error`：`Recreate or repair the missing sample files, then rerun diagnostics.`
   - `not_configured`：`Configure vision_sample_manifest_ref or run a learning route that writes a manifest.`
   - `checker_unavailable`：`Install or source the vision package before relying on this support signal.`
   - `checker_failed`：`Share the diagnostics package with support and inspect the checker error.`
   - unknown：`Refresh diagnostics after the robot publishes a support package.`

### Task 4：接入 diagnostics 渲染流程

文件：

- 修改：`src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`

步骤：

1. 在现有 `showDiagnostics` 或等价渲染函数中调用 `renderVisionIntegrity(payload.vision_samples || {})`。
2. 新增 `renderVisionIntegrity(visionSamples)`：
   - 调用 `visionIntegrityView`。
   - 更新 badge 文案和 tone class。
   - 更新 summary。
   - 用 `li` 渲染 reasons。
   - 更新 advice。
3. 保持现有 `diagVisionSamples`、`diagLatestVisionSample`、`diagReviewQueue`、`diagNextReviewSample` 逻辑继续工作。
4. 如果 `/api/diagnostics` 请求失败，页面仍显示原有错误路径，不新增未捕获异常。

### Task 5：验证并写 tech-done

文件：

- 创建：`sprints/2026.05.10_15-16_integrity-status-ui/tech-done.md`

步骤：

1. 运行验收命令。
2. 如果测试失败，先定位并修复，不把第一轮失败直接交差。
3. 在 `tech-done.md` 记录：
   - 实际改动文件列表
   - 用户旅程变化
   - 接口影响
   - 验证结果
   - 失败定位（如有）
   - 剩余风险

## 验收命令

Full-Stack Engineer 必须至少运行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_behavior/test -p 'test_operator_gateway_http.py'
python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py
git diff --check
```

如果实现意外触碰 diagnostics builder 或 vision checker contract，还必须运行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_behavior/test -p 'test_operator_gateway_diagnostics.py'
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_vision/test -p 'test_vision_sample_manifest.py'
```

如果本地环境允许，应继续运行完整护栏：

```bash
PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh
```

## 风险边界

- 本轮不证明真实 camera/odom manifest 持续产生，只证明手机 operator 页面能消费 diagnostics 字段。
- 本轮不证明真实手机浏览器视觉效果；需要后续 `side2side_check.md` 或人工浏览器截图补证据。
- 不允许因为 UI 需要就扩大后端 contract；如果字段不足，在 `tech-done.md` 记录下一轮需求，不在本轮改 diagnostics builder。
- 测试是护栏，不做无关重构。
- `OKR.md` 只能只读；进度更新留给实现后 Product 收口。
