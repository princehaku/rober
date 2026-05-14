# Sprint 2026.05.14_22-03 Route Task Rehearsal Operator Review - Tech Plan

sprint_type: epic

## OKR 最低优先级核对

当前 `OKR.md` 4.1 数字最低 Objective 是 Objective 5，约 68%。本 sprint 不直接推进 Objective 5，理由是当前需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 才能继续移动 O5 completion；本机只有 Docker，没有这些真实外部材料。继续堆本地 O5 metadata depth 会重复消费同一外部材料 blocker。

Objective 1 约 75%，但 CEO 已明确“本机没有真实硬件，只有docker”。本轮不具备真实 WAVE ROVER、UART/串口、`T=1001` feedback、Nav2 上车或 HIL 条件，不能声明硬件完成度提升。

本 sprint 选择 Objective 2 和 Objective 3。二者均约 80%，且上一轮 `software_proof_docker_route_task_rehearsal_execution_bundle_gate` 已把 route/task rehearsal 做到 execution bundle + diagnostics 可消费 manifest。最近 final 明确后续不要继续扩展本地 bundle 包装层，因此本轮抓手改为操作员任务复盘/下一轮重跑决策：`software_proof_docker_route_task_rehearsal_operator_review_gate`。该结果仍只能计为 Docker/local software proof，不是 HIL、真实 Nav2/fixed-route、dropoff/cancel completion 或 delivery success。

## 技术方案

本轮新增一条只读 metadata 链路：

```text
route_task_rehearsal_execution_bundle.json
  -> operator review package
  -> operator_gateway_diagnostics.py summary
  -> mobile/web phone-safe review panel
```

统一 schema 建议：

- `schema=trashbot.route_task_rehearsal_operator_review.v1`
- `schema_version=1`
- `evidence_boundary=software_proof_docker_route_task_rehearsal_operator_review_gate`
- `overall_status=ready|blocked|missing|read_error|unsupported_schema|unsafe_copy`
- `evidence_ref`
- `route_task_rehearsal_bundle_ref` 或脱敏 bundle reference
- `crosscheck_status`
- `hil_alignment_status`
- `mismatch_summary`
- `next_rehearsal_decision`
- `not_proven`
- `safe_copy`

强制边界：

- 不读取硬件，不访问 serial/UART，不触发 Nav2，不发起 robot command。
- 不改变 `/api/collect`、`/api/dropoff/confirm`、`/api/cancel`、ACK、cursor 或 persistence 语义。
- 不把 review package、diagnostics summary、mobile panel 或 ACK 说成 delivery success。
- `safe_copy` 与 mobile 展示必须 whitelist-only。

## Task A - Autonomy Operator Review Generator

Owner：`autonomy-engineer`

文件范围：

- `pc-tools/evidence/route_task_rehearsal_operator_review.py`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`

接口输入：

- 必须支持 explicit `--execution-bundle <path>`，输入为上一轮 `route_task_rehearsal_execution_bundle.json`。
- 可选支持 `--output <path>` 或 `--output-dir <dir>`，默认写出 `route_task_rehearsal_operator_review.json`。
- 不允许读取硬件、Nav2 runtime、串口、ROS graph 或网络。

实现要求：

- 校验 execution bundle schema 与关键字段；missing/read_error/unsupported schema 必须生成 blocked review，而不是异常退出后无材料。
- 提取或保守派生 `evidence_ref`、`crosscheck_status`、`hil_alignment_status`、mismatch 摘要和 diagnostics 摘要。
- 生成 `next_rehearsal_decision`：
  - crosscheck pass 且 HIL `not_proven`：建议准备真实路线/任务材料或真实 HIL 上车复账，不继续扩展本地 bundle 包装层。
  - crosscheck fail：建议修 route status/task record mismatch 后重跑 rehearsal。
  - bundle missing/read_error/unsupported schema：建议重新生成 execution bundle。
  - unsafe/redaction fail：建议先修 safe copy whitelist。
- 输出 `not_proven`，至少包含真实 Nav2/fixed-route、真实路线采集、WAVE ROVER、真实串口、HIL、同一 `evidence_ref` 上车复账、dropoff/cancel completion、delivery success。
- `safe_copy` 只允许包含 schema/status/evidence_ref/crosscheck/HIL alignment/mismatch summary/next decision/evidence boundary/not_proven，不允许包含 artifact/raw path、local absolute path、credentials、ROS topic、`/cmd_vel`、serial/UART、baudrate、WAVE ROVER、traceback、checksum 或完整 raw artifact。

验收命令：

```bash
python3 -m py_compile pc-tools/evidence/route_task_rehearsal_operator_review.py
python3 pc-tools/evidence/route_task_rehearsal_operator_review.py --help
python3 pc-tools/evidence/route_task_rehearsal_operator_review.py --execution-bundle <临时 route_task_rehearsal_execution_bundle.json> --output <临时 route_task_rehearsal_operator_review.json>
python3 - <<'PY'
import json
from pathlib import Path
p = Path("<临时 route_task_rehearsal_operator_review.json>")
d = json.loads(p.read_text())
assert d["schema"] == "trashbot.route_task_rehearsal_operator_review.v1"
assert d["evidence_boundary"] == "software_proof_docker_route_task_rehearsal_operator_review_gate"
assert "next_rehearsal_decision" in d
assert "not_proven" in d
safe = json.dumps(d.get("safe_copy", {}), ensure_ascii=False)
for forbidden in ["Authorization", "OSS_ACCESS_KEY", "/cmd_vel", "serial", "UART", "baudrate", "WAVE ROVER", "traceback", "checksum"]:
    assert forbidden not in safe
PY
rg -n "route_task_rehearsal_operator_review|software_proof_docker_route_task_rehearsal_operator_review_gate|next_rehearsal_decision|not_proven|delivery success" pc-tools/evidence/route_task_rehearsal_operator_review.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
git diff --check -- pc-tools/evidence/route_task_rehearsal_operator_review.py pc-tools/README.md docs/navigation/fixed_route_workflow.md
```

## Task B - Robot Diagnostics Consumer

Owner：`robot-software-engineer`

文件范围：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

接口输入：

- 支持 explicit diagnostics 参数或环境变量 `TRASHBOT_ROUTE_TASK_REHEARSAL_OPERATOR_REVIEW` 指向 review package。
- 只读消费 Task A package；不得改变 command/status/ACK envelope。

实现要求：

- 在 `/api/diagnostics` 或 diagnostics builder 中新增 `route_task_rehearsal_operator_review` summary。
- missing/read_error/unsupported schema/crosscheck fail/unsafe copy 时保守输出 blocked 或 degraded summary。
- metadata-only 围栏必须证明 review package 不触发 Start/Confirm/Cancel、ACK POST、cursor/persistence、HIL、dropoff/cancel completion 或 delivery success。
- summary 只暴露 phone/support-safe 字段，不暴露 artifact/raw path、local path、traceback、checksum、ROS topic、`/cmd_vel`、serial/UART、baudrate、WAVE ROVER、credentials、DB/queue URL 或完整 raw artifact。

验收命令：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_operator_gateway_diagnostics
rg -n "route_task_rehearsal_operator_review|software_proof_docker_route_task_rehearsal_operator_review_gate|next_rehearsal_decision|not_proven|delivery success|primary_actions_enabled" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

## Task C - Full-stack Mobile Review Surface

Owner：`full-stack-software-engineer`

文件范围：

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `onboard/src/ros2_trashbot_behavior/test/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

接口输入：

- 消费 `/api/status`、`phone_readiness`、`/api/diagnostics` 中的 `route_task_rehearsal_operator_review` 或兼容 summary。
- 不直接读取 raw artifact、local path、full execution bundle 或 backend filesystem。

实现要求：

- 在首屏或诊断附近新增只读“路线/任务排练复盘”摘要。
- 展示 `overall_status`、`evidence_ref`、crosscheck/HIL boundary、mismatch 摘要、`next_rehearsal_decision`、`not_proven`、evidence boundary。
- Copy/export 只使用 whitelist-only `safe_copy`；若不存在安全 copy，则显示 blocked copy unavailable。
- Start Delivery、Confirm Dropoff、Cancel 保持现有 fail-closed 逻辑；operator review 不新增控制授权条件。
- UI 文案中文优先，明确该 review 是 software proof，不是 HIL、真实路线运行、dropoff/cancel completion 或 delivery success。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_mobile_web_entrypoint
python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "route_task_rehearsal_operator_review|software_proof_docker_route_task_rehearsal_operator_review_gate|next_rehearsal_decision|not_proven|delivery success|Start Delivery|Confirm Dropoff|Cancel" mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/fixtures/mobile_web_status.fixture.json onboard/src/ros2_trashbot_behavior/test/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/fixtures/mobile_web_status.fixture.json onboard/src/ros2_trashbot_behavior/test/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

## Task D - Product Closeout

Owner：`product-okr-owner`

文件范围：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.14_22-03_route-task-rehearsal-operator-review/tech-done.md`
- `sprints/2026.05.14_22-03_route-task-rehearsal-operator-review/side2side_check.md`
- `sprints/2026.05.14_22-03_route-task-rehearsal-operator-review/final.md`

实现要求：

- 汇总 Task A/B/C 实际改动、验证结果、失败定位和剩余风险。
- 明确 `software_proof_docker_route_task_rehearsal_operator_review_gate` 只证明 Docker/local operator review 链路。
- 复核 `docs/` 是否随功能同步更新。
- 评估是否对 Objective 2/3 做谨慎 OKR 更新；Objective 5 和 Objective 1 不得因本轮本地软件 proof 上调。

验收命令：

```bash
rg -n "2026.05.14_22-03_route-task-rehearsal-operator-review|software_proof_docker_route_task_rehearsal_operator_review_gate|Objective 2|Objective 3|Objective 5|not_proven|delivery success|HIL" OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_22-03_route-task-rehearsal-operator-review
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_22-03_route-task-rehearsal-operator-review/tech-done.md sprints/2026.05.14_22-03_route-task-rehearsal-operator-review/side2side_check.md sprints/2026.05.14_22-03_route-task-rehearsal-operator-review/final.md
```

## 并行启动要求

本轮符合 2+ owner 且文件范围互不重叠的 epic sprint，必须并行启动 3 个工程子 agent：`autonomy-engineer`、`robot-software-engineer`、`full-stack-software-engineer`。Task D 等三个工程任务完成并通过围栏后执行。

子 agent prompt 必须包含对应角色 System Prompt、本轮任务、文件范围、验收命令和输出要求。每个子 agent 必须返回实际改动文件列表、验证命令输出、失败定位和剩余风险。

## 风险边界

- 本轮不推进真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 worker/migration；Objective 5 仍受外部材料阻塞。
- 本轮不读取 WAVE ROVER、UART、Orange Pi 或硬件参数；本机只有 Docker，不能声明 HIL 或真实底盘证据。
- 本轮不证明真实 Nav2/fixed-route、真实路线采集、同一 `evidence_ref` 上车复账、dropoff/cancel completion 或 delivery success。
- 本轮所有控制按钮仍由既有 command safety 和 readiness gates 决定；operator review 是 metadata-only，不是控制授权。
- 代码技术注释若新增必须使用中文且保持注释比例要求；各 owner 需要在对应文件中自检。

## Product 验收围栏

本计划文档创建完成后先运行：

```bash
rg -n "sprint_type: epic|Objective 5|Objective 2|Objective 3|software_proof_docker_route_task_rehearsal_operator_review_gate|OKR 最低优先级核对|真实公网|本机.*Docker|not_proven|delivery success" sprints/2026.05.14_22-03_route-task-rehearsal-operator-review
git diff --check -- sprints/2026.05.14_22-03_route-task-rehearsal-operator-review/pre_start.md sprints/2026.05.14_22-03_route-task-rehearsal-operator-review/prd.md sprints/2026.05.14_22-03_route-task-rehearsal-operator-review/tech-plan.md
```
