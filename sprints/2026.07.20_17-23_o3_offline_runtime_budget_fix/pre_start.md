# O3 Offline Runtime Budget Fix - Pre Start

## Sprint metadata

- `sprint_type: epic`
- 时间窗：`2026.07.20_17-23`
- 状态：`planning_complete_ready_for_parallel_engineering`
- Product owner：`product-okr-owner`
- Engineer owners：`robot-software-engineer`、`robot-algorithm-engineer`
- 主责集成 owner：`robot-software-engineer`
- 目标 lane：`Objective 3 supporting lane / O10 local-offline runtime budget compatibility`
- proof boundary：`software_proof_o3_o10_offline_runtime_budget_contract_only`

## 用户价值与产品北极星

用户需要的是一次 readiness helper 能在上位机 API 的有限等待窗口内**自然**形成可判定的 final artifact，而不是在 80s 外层超时后依靠 SIGINT 和 partial artifact 猜测现场状态。北极星仍是可信定位、planner-only path、再到受看护路线执行；本 sprint 只清除进入下一次现场证明前的确定性软件 runtime blocker。

## 上轮事实与唯一入口

上一轮 `sprints/2026.07.20_13-20_o3_nav2_localization_readiness_recovery/` 已接受 strict-no-motion API 合同与 owned stop，但两个 helper 窗口分别耗时 `81243ms` 和 `80444ms`。第二窗口在 API `80s` process budget 后只保留 partial artifact，最后成功 phase 为 `tf_probe`，中断时 command 为 `ros2 pkg list`；根因包含 `helper_process_timeout_after_partial_artifact` 与 `sigint_before_final_artifact`。

上一轮 final 已明确唯一入口为 `next_offline_runtime_budget_fix`：先在本地/离线修复 API budget、probe order 和 final-artifact 时序；禁止第三个上车 proof/window。本 sprint 不创建新的 wrapper、readback、handoff 或现场证据包。

## Objective 切换与 blocker 红线

- 当前 `OKR.md` 最低总体 Objective 是 Objective 5，约 `85%`。
- Objective 5 的 provider/runtime blocker 已连续消费 `2/2`；按同一 blocker 最多两轮规则，本 sprint 不允许第三轮 O5 provider、tunnel、public endpoint、readiness packet 或诊断包装。
- 合法切换到 Objective 3 supporting lane：修复 O10 helper 与上位机 80s 外层预算的不相容，直接解锁未来一次新的 current localization/path proof，而不是重复消费 O5 blocker。
- Objective 3 已在历史区记录为软件侧约 99%；本 sprint 是 O3/O1/Mission supporting 工程修复，不承诺上调任何主 Objective 百分比。

## 本轮核心抓手

冻结 API→helper 内部预算合同：上位机继续拥有外层 process timeout，helper 获得明确的 outer budget，并在内部预留 final-artifact 收口窗口。关键 readiness probe 优先；`ros2 pkg list` 属于非关键诊断，只能在剩余预算充足时以收敛 timeout 执行，否则显式跳过并自然落 final artifact。

## 范围与责任 Engineer

### `robot-software-engineer`

- 修改 `onboard/scripts/upper_robot_api.py`：向 helper 传递实际 outer process budget，保持 HTTP request/response 与安全字段兼容。
- 修改 `onboard/tests/test_upper_robot_api.py`：覆盖 80s outer budget 传递、自然退出/final-artifact 优先语义、既有 timeout fallback 回归。
- 同步 `docs/navigation/field_route_evidence_preflight.md`。
- 在双方工程证据返回后，独占更新本 sprint `tech-done.md` 并执行集成验收。

### `robot-algorithm-engineer`

- 修改 `onboard/scripts/o10_amcl_nav2_runtime_proof.py`：实现 monotonic budget/deadline、关键/非关键 probe 顺序、`ros2 pkg list` budget-aware skip/clamp 与 final-artifact reserve。
- 修改 `onboard/tests/test_nav2_runtime_proof_helper.py`：增加 hostile slow-command 与 offline fixture，证明无需 signal/partial fallback 即可自然写 final artifact。
- 同步 `docs/navigation/fixed_route_workflow.md`。

两个 owner 的工程文件范围互不重叠，必须并行派发。内部预算 CLI 合同以 `tech-plan.md` 为共同接口；不得互改对方文件。

## 硬边界

- 本 sprint 仅本地/离线软件实现与测试；禁止 SSH、SCP、远端部署、ROS live、Nav2 action、上车 API 调用和任何控制/运动。
- 禁止第三个 proof/window；禁止 `/initialpose`、goal、`/cmd_vel`、UART、base manual/stop。
- 不生成或更新 `artifacts/` 现场材料，不把旧 partial artifact 改写成新证据。
- 不以增加外层 timeout 掩盖 helper 顺序问题；80s 兼容 case 必须保留。
- 所有新增技术注释使用中文，相关修改代码中文注释比例必须 `>20%`。
- 软件测试不等于 route、HIL、delivery、safe-to-control、Mission success 或 OKR credit。

## 启动与完成门槛

Planning 三文档顺序完成后，由主节点在同一轮并行派发两个 Engineer。实现完成至少满足：hostile slow-command/offline fixture 自然结束；final artifact 在 outer budget 前写出；`artifact_kind=final`、`current_command=null`；非关键 package probe 被预算收敛或显式跳过；没有 `sigint_before_final_artifact`、`helper_process_timeout_after_partial_artifact`，且不是依靠 partial artifact 验收。

## 风险

- helper 现有阶段链很长，单纯移动 `ros2 pkg list` 可能仍让 final assembly 越界；必须使用全程 monotonic remaining-budget，而非只改一个 command timeout。
- package availability 目前参与诊断输出；预算跳过必须保留明确 boundary，不能伪装为 package 缺失或成功。
- 80s 是当前关键兼容 case，不代表所有 request 都固定 80s；实现应消费 API 实际 outer budget，同时用 80s case 做验收。
- 本地 fixture 无法证明真实 ROS CLI、DDS、AMCL、TF 或 planner 时延；现场证据仍待未来独立授权窗口。
