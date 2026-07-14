# Tech Done - O3 TF Receipt-Time Freshness Recovery

## Sprint Metadata

- `sprint_type: epic`
- Owner：`robot-algorithm-engineer`
- 状态：离线实现、targeted regression、文档同步与完整围栏已完成；现场只读 preflight 证明既有
  runtime 未 active，因此按安全合同跳过 optional live capture。
- 自主能力目标：修复 current localization 的 TF freshness 判定，把 collector 后续耗时与 transform
  到达 callback 时的真实 header age 分开。
- 本轮抓手：`/tf`、`/tf_static` callback receipt-time 一等证据和 dynamic edge fail-closed clean gate。

## 实际改动与接口影响

### `onboard/scripts/o10_amcl_nav2_runtime_proof.py`

- `/tf` 与 `/tf_static` rclpy callback 在入口各记录一次 `received_at_ms`，同一 TFMessage 的每条
  transform 共享该 receipt；CLI fallback 或旧 artifact 没有 callback receipt 时保持 `None`。
- `tf_edge_freshness_entry` 增加 `received_at_ms`、`evaluated_at_ms`、
  `header_age_at_receipt_ms`、`receipt_age_at_evaluation_ms`、
  `header_age_at_evaluation_ms`；`build_tf_source_freshness` 增加 summary `evaluated_at_ms`。
- dynamic freshness threshold 保持 `3000ms`，decision 固定使用
  `header_age_at_receipt_ms`；既有 `freshness.age_ms` 作为兼容字段，值与该 decision age 相同。
- header 到达 callback 时已超过 threshold 仍为 stale；缺/非法 receipt、header invalid、非墙钟时间或
  超出小量容差的时间逆序保持 unknown/fail-closed，禁止用 command finish/generated time 补写。
- static source、`timestamp`、source class 和 unique AMCL publisher attribution 语义不变。

### `onboard/tests/test_nav2_runtime_proof_helper.py`

- 新增上轮 `header_age_at_evaluation_ms=5090ms`、receipt 时 age=`90ms` 的 synthetic regression，证明
  collector 延迟不再误报 stale。
- 新增真正迟到 header、缺/非法 receipt、invalid/future header、同 TFMessage 多 transform 共用 receipt
  等 fail-closed 回归；既有 static/source/publisher attribution tests 继续通过。

### `docs/navigation/field_route_evidence_preflight.md`

- 同步三类 age、decision basis、`3000ms` threshold、CLI/旧 artifact 缺 receipt fail-closed 及
  no-topic-write/no-motion 安全边界。

## 数据、样本与调试输出变化

- TF transform artifact 新增 callback `received_at_ms`。
- edge freshness 现在可复算：
  `received_at_ms - header_stamp_epoch_ms = header_age_at_receipt_ms`；
  `evaluated_at_ms - received_at_ms = receipt_age_at_evaluation_ms`；
  `evaluated_at_ms - header_stamp_epoch_ms = header_age_at_evaluation_ms`。
- 上轮已有现场 artifact 未被修改或冒充新现场证据；本轮 synthetic regression 仅证明离线合同语义。

## 失败定位与修复链

- 首轮代码实现后直接运行 targeted 围栏，`py_compile` 与全部 `160` 项 unittest 均一次通过；没有发现
  需要二次修复的测试失败。
- 已确认旧根因是 dynamic edge 使用 collector `generated_at_ms` 计算 age，把采样后的约 5 秒执行耗时
  混入 stale gate；修复后 evaluation age 只保留为诊断字段。

## 验证结果

- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/tests/test_nav2_runtime_proof_helper.py`：
  PASS，exit `0`。
- `python3 -m unittest onboard/tests/test_nav2_runtime_proof_helper.py`：
  首轮 `Ran 160 tests in 2.238s`、最终 `Ran 160 tests in 2.244s`，均 `OK`、exit `0`。
- required anchor `rg`：PASS，exit `0`；命中 receipt、三类 age、`3000`、initialpose、
  no-topic-write/no-motion 合同字段。
- scoped `git diff --check`：PASS，exit `0`。
- 完整四段验收命令整体 exit `0`。
- 离线结构断言：`tf_receipt_time_offline_structural_assertions_ok`，exit `0`；证明 receipt 存在、三类
  age 可按整数等式复算、decision/兼容 `age_ms` 使用 `header_age_at_receipt_ms`，并核对现场预检
  `initialpose_publish_attempts=0`、runtime start/stop=`0`、topic write=`0`、control/route/delivery/HIL=`0`。

## 可选现场证据边界

- 现场前置条件：仅允许一次 pure read-only SSH preflight；只有 existing map_server/AMCL runtime active，
  且能确定 helper 默认 `initialpose_opt_in=false`、`managed_runtime_opt_in=false`、path opt-in=false，运行不会
  start/stop/cleanup runtime 时才允许单次 capture。
- 永久禁止本 sprint 再次发布 `/initialpose`；禁止 managed runtime start/stop、planner/controller/path、
  NavigateToPose、`/cmd_vel`、`/api/base/manual`、UART 或运动。
- `2026-07-14T23:10:35Z` 通过 SSH 执行一次 pure read-only process inventory；命令只读取 UTC 时间与
  `ps`，未部署 helper、未调用 ROS topic/service/action、未修改文件、未 start/stop runtime。
- 输出只命中本次远端 `zsh -c` 与 `grep`，未观察到 map_server、AMCL、lifecycle manager 或既有 helper
  进程。因此无法满足“复用 active runtime”前置条件，决定
  `skip_optional_live_capture_existing_runtime_not_active`；没有第二次 SSH/capture。
- 预检留档：`artifacts/algorithm/read_only_ssh_preflight.log`。因 capture 未执行，不生成或伪造
  `runtime-proof.json`；`initialpose_publish_attempts=0`，managed runtime start/stop、topic write、
  control/route/delivery/HIL actions 均为 `0`。

## 剩余风险与下一步建议

- Receipt 是 collector 主机 wall clock；虽然异常时间顺序已 fail-closed，跨进程/设备 header 时钟偏差仍需
  通过现场 artifact 解释，不能把 receipt-time clean 等同于物理定位 ground truth。
- 本轮未形成新 live callback receipt artifact；原因是纯只读 preflight 已确认现有 runtime 不 active，
  安全边界禁止为取证启动 runtime。离线合同已完整验证，但 current live freshness 状态仍未知。
- 即使 receipt-time clean，也不证明 planner/controller/path、route execution、delivery、HIL 或
  safe-to-control；`initialpose_publish_attempts=0`、control/route/delivery/HIL 行为必须保持零/false。
