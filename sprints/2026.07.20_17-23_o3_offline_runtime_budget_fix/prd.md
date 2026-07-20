# O3 Offline Runtime Budget Fix - PRD

## Product metadata

- `sprint_type: epic`
- Product owner：`product-okr-owner`
- Delivery owners：`robot-software-engineer`、`robot-algorithm-engineer`
- 产品方向：`继续 Objective 3 supporting lane；暂停 Objective 5 provider/runtime 2/2`
- proof boundary：`software_proof_o3_o10_offline_runtime_budget_contract_only`

## 用户问题

上位机 `/api/nav2/proof/refresh` 的 helper 在当前 80s outer process budget 内没有完成 final assembly。上一轮 current run 在已完成关键 TF probe 后仍进入非关键 `ros2 pkg list`，外层超时发送 SIGINT，最终只能保留 partial artifact。操作者因此无法区分“readiness 已自然判定为 NO-GO”和“collector 被预算截断”。

## 产品目标

在不访问上位机、不启动 ROS/Nav2、不产生运动的前提下，使 API 与 O10 helper 共享同一明确预算合同，并用 deterministic hostile/offline tests 证明：

1. helper 知道外层 process budget，并为 final artifact 预留时间；
2. 关键 localization/path readiness probe 优先于非关键 package inventory；
3. `ros2 pkg list` 在预算不足时显式跳过，预算有限时 timeout 被 remaining budget 收敛；
4. helper 在外层 timeout 前自然退出并写出 final artifact；
5. 验收不依赖 SIGINT、timeout fallback 或 partial artifact。

## OKR 映射与方向判断

- Objective 5（约 85%）：`暂停`。provider/runtime blocker 已消费 `2/2`，本轮禁止第三轮。
- Objective 3 supporting lane：`继续`。本轮修复 O10 readiness helper 的工程阻塞，为下一次 current localization/path proof 提供必要前置。
- Objective 1（约 94%）：仅间接受益；没有 current HIL、route execution 或 safe-to-control 证据，不计分。
- Mission Objective 0：保持 `blocked_before_attempt_on_current_localization_readiness`；本 sprint 不产生 mission attempt 或 success。
- KR 历史归档：本轮 planning 不归档 KR；只有实现和工程验证完成后才可接受为 software-side supporting contract，且仍不进入 route/HIL/delivery 历史完成区。

## P0 需求

### R1：预算合同

- 外部 HTTP endpoint、request body 和 response schema 保持兼容。
- `upper_robot_api.py` 以现有 `process_timeout_s` 为 outer truth，通过内部 helper CLI 参数 `--outer-process-timeout-s` 传给 O10 helper。
- O10 helper 从进程开始使用 monotonic deadline，并在 outer timeout 内预留固定 final-artifact reserve；80s case 必须在 reserve 前停止启动新的非关键命令。
- artifact 必须记录 outer budget、remaining/final reserve 以及 package probe 的执行或跳过 boundary，便于验收但不得宣称 live readiness。

### R2：probe 优先级与 `ros2 pkg list`

- lifecycle、current pose/TF freshness、persisted pose audit 和 planner-only gate 属于关键 readiness 路径。
- `ros2 pkg list` 仅为非关键 diagnostic，不得阻塞 final artifact。
- remaining budget 不足时，package batch 返回 `executed=false` 和明确的 `package_check_skipped_to_preserve_final_artifact_budget` boundary；不得把跳过伪装成 package missing、package available 或 command success。
- remaining budget 尚可时，package command timeout 必须 clamp 到 `remaining - final_reserve`，不能继续使用不受全局 budget 约束的固定窗口。

### R3：自然 final artifact

- helper 自然返回时写 `artifact_kind=final`、`last_phase=final`、`current_command=null`。
- blocked/offline 是合法 final outcome；不得为了返回 0 隐瞒 blocker。
- hostile slow-command case 不得出现 `sigint_before_final_artifact`、`helper_process_timeout_after_partial_artifact` 或只接受 `partial_artifact_preserved=true`。
- 既有外层 timeout fallback 保留为异常兜底，但不能作为本需求 happy-path 的验收方式。

### R4：测试与文档

- 单测使用 fake monotonic clock、stub command runner 或缩放 budget，不真实等待 80 秒，不依赖本机 ROS 安装。
- hostile fixture 覆盖“关键 probe 已返回、`ros2 pkg list` 会慢到越界”；offline fixture 覆盖 ROS/source 不可用时仍自然 final。
- 两套既有 unittest 全量通过；新增技术注释全中文，相关修改代码中文注释比例 `>20%`。
- 同步 field-route preflight 与 fixed-route workflow，明确 budget contract、package skip 语义和 proof boundary。

## 非目标

- 不增加 outer timeout 来回避根因。
- 不重构或新增 wrapper/readback/export/API surface。
- 不做 SSH、ROS live、Nav2 lifecycle/action、path generation、route execution、底盘/UART/HIL 或 delivery。
- 不修改定位输入，不发布 `/initialpose`，不复用旧运动授权开启第三个窗口。
- 不修改 `OKR.md` 百分比，不创建完成 KR 历史记录。

## 验收场景

| 场景 | 输入 | 必须结果 |
| --- | --- | --- |
| 80s contract | API 计算 outer `process_timeout_s=80` | helper argv 收到同一预算；内部 final reserve 可见；不得扩大 outer timeout |
| hostile slow package command | critical probes 已完成，stub `ros2 pkg list` 超慢 | package command 被跳过或 timeout 收敛；在 outer budget 前自然 final |
| offline ROS fixture | source/ROS CLI 不可用 | blocked/fail-closed final artifact，自然退出，无 SIGINT/partial 依赖 |
| regression | 现有正常与 timeout fixture | 原有 response/safety 字段兼容；异常 timeout fallback 仍可用 |

## Product 验收口径

Product 只接受 `software_runtime_budget_contract_ready`：代码、测试、文档和 deterministic fixture 全绿，且最终 artifact 语义满足自然 final。拒绝把这些结果表述为 `route_execution_success=true`、`hil_pass=true`、`delivery_success=true`、`safe_to_control=true`、`robot_control_executed=true` 或 `okr_credit=true`。

## 剩余证据链

本 sprint 后仍需独立的新授权与现场 gate，才能进行新的 no-motion current proof；只有同窗口 current pose/TF freshness、persisted pose、planner/controller 和 path 事实成立，才可讨论 route attempt。真实 route、operator、WAVE ROVER feedback、HIL 和 delivery 证据均不在本 sprint。
