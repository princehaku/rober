# O1 当前轮速反馈 HIL

## Sprint 类型

- `sprint_type: epic`
- 状态：`frozen_unconsumed`
- 授权 ID：`ceo_20260721_0651_current_wheel_feedback_hil_v8`
- 主责 owner：`robot-hardware-engineer`

## 目标与产品价值

在受控、短时、有人看护的真实底盘运动窗口内，只补齐当前轮次缺失的证据：运动期间 `T=1001` 的左右轮速 `L/R` 必须出现非零值，并在专用 stop 后回到 `0/0`。这使 O1 的 95% 状态能够由“可发控制”推进到“当前真实反馈闭环可验证”，而不是继续消费接口包装或只读摘要。

## OKR 路由与方向判断

- O5 当前 85%，provider/runtime 两条前置证据已达到 `2/2`，本轮暂停继续消费。
- O6/O7 当前均为 93%，受未授权 systemd holder 维护窗限制，本轮不进入 holder 修改或维护。
- 本轮转向 O1（95%），仅验证当前轮速反馈 HIL 缺口；不扩大为路线执行、送达或安全控制认证。
- 方向判断：继续 O1 的一次受控 HIL 尝试；若 Phase0 不满足则立即暂停，不以新的 wrapper、proposal 或 readback 替代现场证据。

## Anti-repeat 与消费状态

- 不重复消费 `01-54` 已验证过的准备/边界材料。
- 不修改、不复用 `06-20` 的 WIP。
- 不修改、不复用 `06-45` 的 WIP。
- v6 已是 `consumed_no_retry`，不得重试。
- v7 只有未落盘 proposal，不算本轮授权消费，也不得冒充执行证据。
- v8 只有在唯一一次非零 transport attempt 实际发出时才从 `frozen_unconsumed` 变为已消费；Phase0 失败不消费授权。

## CEO 授权与安全限制

- 唯一授权：`ssh root@192.168.1.11 -p 37878`。
- 允许一次前进运动，速度不超过 `0.08 m/s`，持续时间不超过 `300 ms`。
- 前提：operator 全程看护、路线清空、小车处于受限物理位置，并可立即执行 emergency stop。
- 非零发送前必须确认唯一 control owner、相关 service/health 正常、底盘静止、无 active hold、feedback path 可用。
- 任何 Phase0 gate 为 false：在非零发送前 abort，保持 `frozen_unconsumed`。
- 唯一非零 transport attempt 后无论成功或失败均 `retry=0`、`no-retry`，并立即执行专用 stop。

## 本轮范围与验收口径

- 只补：during-motion 非零 `T=1001 L/R`，以及 dedicated post-stop `T=1001 L/R=0/0`。
- 必须形成 `pre-stop / nonzero / post-stop = 1/1/1` 的同轮证据链，并保留时间戳、原始串口/bridge 证据与 Upper receipts。
- 不把成功自动解释为 `safe_to_control=true`、`hil_pass=true`、`route_execution_success=true` 或 `delivery_success=true`；这些结论必须由对应独立验收给出。
- 本 Epic 后续必须由 Hardware owner 更新 `tech-done.md`、`side2side_check.md`、`final.md` 和 `artifacts/`，Product 验收后才允许更新必要的 `docs/`、`OKR.md` 与 progress log。

## 风险与阻塞

- 未授权的 systemd holder 维护窗仍是 O6/O7 阻塞，本轮禁止旁路修改。
- 串口 raw evidence 若看不到 `T=13`，不得仅凭上层请求声称 wire 上出现 `T=13`。
- 反馈链断开、service/health 异常、非唯一 owner、底盘未静止、active hold、operator/路线/物理限制任一不满足，都必须在非零前终止。
