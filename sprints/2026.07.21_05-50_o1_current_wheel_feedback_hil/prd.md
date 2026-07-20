# PRD：O1 当前轮速反馈 HIL

## 用户价值与产品北极星

用户需要的是小车在真实、受控运动中能够报告与运动一致的当前轮速，并在停止后可靠回零。北极星不是“API 能调用”，而是一次可审计的 `pre-stop -> bounded nonzero motion -> dedicated stop -> post-stop` 反馈闭环。

## OKR 映射与方向判断

- 映射 Objective：O1，当前完成度 95%。
- 方向：继续，但仅补当前轮速闭环的最后一段 HIL 证据。
- O5 85% 的 provider/runtime `2/2` 本轮暂停；O6/O7 93% 因未授权 systemd holder 维护窗暂停。
- 本轮不归档 KR；只有 Hardware 证据链与 Product 验收同时成立，才讨论 O1 相关 KR 的状态更新。

## In scope

- Phase0 只读 gate：唯一 control owner、service/health、stopped、无 active hold、feedback path、operator 看护、路线清空、物理限位与 emergency stop 就绪。
- 冻结并校验唯一一次非零请求：forward `<= 0.08 m/s`，duration `<= 300 ms`。
- 捕获反馈请求 `T=130`、bridge/serial/raw `T=1001`、Upper receipts。
- 捕获三段各一份：pre-stop、during-motion nonzero、dedicated post-stop；计数必须为 `1/1/1`。
- 唯一非零 transport attempt 后立即 stop；`retry=0`，失败也执行 `no-retry` cleanup。

## Out of scope

- 不修改或重启未授权 systemd holder，不进入 O6/O7 维护窗。
- 不修改 `06-20`、`06-45` WIP，不暂存、不提交、不推送其他 owner 的 dirty worktree。
- 不做路线执行、送达、自动驾驶或额外运动重试。
- 不把上层请求直接宣称为 `T=13` wire 证据；只有 raw serial 捕获可支持该判断。
- 不自动设置或宣称 `safe_to_control=true`、`route_execution_success=true`、`delivery_success=true`。

## 功能与安全要求

1. Phase0 所有 gate 必须为 true；任一为 false 时，必须在发送非零请求前 abort，授权保持 `frozen_unconsumed`。
2. 只有唯一一次非零 transport attempt 实际发出，授权才算消费；消费后状态必须进入 `consumed_no_retry`。
3. 请求前进速度必须 `<= 0.08 m/s`，持续时间必须 `<= 300 ms`，不得隐式延长或自动重放。
4. `pre-stop/nonzero/post-stop=1/1/1`；中段 `T=1001 L/R` 至少一侧为非零，post-stop 必须为 `L/R=0/0`。
5. 唯一尝试之后，无论采集是否完整，都必须执行 dedicated stop，且 `retry=0`。
6. 必须保存 request hash、请求/响应、时间戳、`T=130`、bridge/serial/raw `T=1001` 与 Upper receipts，以便关联同一轮次。

## 验收标准

- Phase0 artifact 明确记录全部 gate 的布尔值与采集时间；存在 false 时没有任何 nonzero transport receipt。
- 冻结请求经 `jq` 校验，forward `<=0.08`、duration `<=300`，并保存 SHA-256。
- 只有一个非零 transport receipt，`retry=0`；随后存在一个 dedicated stop receipt。
- 同一轮证据满足 `pre-stop/nonzero/post-stop=1/1/1`，运动段 raw `T=1001 L/R` 为非零，停止段 raw `T=1001 L/R=0/0`。
- `T=130` 请求、bridge/serial/raw `T=1001` 与 Upper receipts 可按时间/attempt id 互相对应。
- 若 raw serial 没有观察到 `T=13`，结论写为 `T=13 wire not proven`。
- `hil_pass` 只能表示本 PRD 的当前轮速闭环验收结果；即使 `hil_pass=true`，也不自动代表 `safe_to_control`、`route_execution_success` 或 `delivery_success`。

## Owner、交付物与剩余风险

- 责任 Engineer：`robot-hardware-engineer`。
- 交付物：本 sprint 的 `artifacts/`，以及 `tech-done.md`、`side2side_check.md`、`final.md`；Product 验收后按需更新 `docs/`、`OKR.md`、progress log。
- 剩余风险：物理轮胎离地/打滑可能产生非零轮速但不代表实际位移；一次窗口也不能证明长期可靠性、路线安全或送达成功。
