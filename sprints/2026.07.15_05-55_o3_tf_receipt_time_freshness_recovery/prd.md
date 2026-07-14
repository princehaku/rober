# PRD - O3 TF Receipt-Time Freshness Recovery

## 产品问题

上一轮真实上位机 artifact 已观察到 AMCL dynamic `map->odom`，但 clean gate 在 collector 末尾用
`generated_at_ms - header_stamp_epoch_ms` 得到 `5090ms`，超过 `3000ms`。TF callback 没有记录
`received_at_ms`，所以这个值同时包含 TF 自身延迟和 collector 后续工作耗时，无法支持可信判断。

## 产品北极星与 OKR 映射

- 北极星：同一真实 runtime 窗口内，定位与 TF 证据可复核、可归因、可保守准入，为后续 controlled
  route execution 提供可信前置条件。
- 对齐 O3 自主导航与 O1 现场安全前置链；本轮不声称路线、履约、HIL 或 safe-to-control。
- O5 最低进度不变，但缺生产外部材料，且相邻 wrapper 已退役；本轮不为追求百分比伪造 O5 增量。

## 核心抓手

把 TF transform 的 callback receipt time 提升为一等证据，并显式拆分三类时间：

1. `header_stamp_epoch_ms`：消息声明的采样/生成时间。
2. `received_at_ms`：本进程 callback 实际接收该 TF message 的本地时间；同一 TFMessage 内的 transforms
   可共享同一 callback receipt time。
3. `evaluated_at_ms`：生成 freshness summary 的时间。

必须派生并输出：

- `header_age_at_receipt_ms = received_at_ms - header_stamp_epoch_ms`：消息到达时的真实 header age，
  是 dynamic current-observation clean 判定的 age。
- `receipt_age_at_evaluation_ms = evaluated_at_ms - received_at_ms`：collector 在接收后继续工作的耗时，
  只作诊断，不得把它追加到消息 stale gate。
- `header_age_at_evaluation_ms = evaluated_at_ms - header_stamp_epoch_ms`：保留旧口径作诊断与兼容审计。

## 验收口径

### 必须满足

- `/tf` 与 `/tf_static` rclpy callback 都记录 `received_at_ms` 到每条 transform artifact。
- `map->odom` dynamic edge 同时输出 header、receipt、evaluation 及上述三类 age。
- threshold 保持 `3000ms`，不得为通过测试放宽。
- clean freshness 只在 header stamp 可解析、receipt 存在且非未来异常、
  `header_age_at_receipt_ms <= 3000` 时为 fresh；真正迟到的旧 header 仍必须 stale。
- `received_at_ms` 缺失、非法、来源为 CLI 无 callback receipt 或 header 不可解析时必须
  unknown/fail-closed，不能回退到 `finished_at_ms` 或 `generated_at_ms` 冒充 receipt。
- 兼容保留原有 `timestamp`/source/publisher attribution 事实；更新 targeted regression 与导航文档。
- 所有新增技术注释使用中文，且受影响新增逻辑保持仓库要求的注释密度。

### 可选现场验收

离线实现与 tests 全绿后，最多一次只读/no-topic-write/no-motion live capture。它只能复用既有 runtime；
若不能通过命令和 artifact 证明没有 runtime start/stop，则跳过并在 `tech-done.md` 记录原因。现场通过
仅代表 receipt-time contract 的 current observation，不代表 localization ground truth、route、delivery、
HIL 或 safe-to-control。

## 明确拒绝项

- 不允许再次发布 `/initialpose`，包括 rclpy、CLI、wrapper 或间接调用。
- 不允许启动/停止 runtime，不允许 planner/controller/path/NavigateToPose/cmd_vel/base manual/UART/运动。
- 不把历史 artifact 重写成新现场证据；离线回归必须标注 synthetic/offline。
- 不改变 O5/O1/O3/O6/O7 主百分比，除非后续 Product 基于新的 live evidence 单独验收。

## 责任与证据链

- Owner：`robot-algorithm-engineer`。
- 工程证据：代码 diff、targeted unittest、py_compile、结构断言、docs、`tech-done.md`。
- 可选现场证据：本 sprint 自有 artifact、命令/exit、local/remote SHA、forbidden-command scan；不得覆盖
  上轮 artifact。
- Product 收口：工程完成后再生成 `side2side_check.md`、`final.md`，并保守更新 OKR/process log。

