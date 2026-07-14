# Tech Plan - O3 TF Receipt-Time Freshness Recovery

## 方案摘要

由 `robot-algorithm-engineer` 单线闭环。先离线改造 TF callback artifact 与 edge freshness contract，
再补回归和文档；仅在安全前置检查证明可复用既有 runtime 时，最多执行一次 read-only/no-topic-write/
no-motion live capture。计划不涉及硬件协议、引脚、电压、UART、波特率或底盘控制，因此不引入新的
vendor 假设。

## OKR 最低优先级核对

1. `OKR.md` 4.1 当前最低 Objective 是 O5，约 `85%`；O6/O7 约 `93%`，O1 约 `94%`。
2. 本 sprint 不直接针对 O5，针对 O3 current localization/TF 前置链。
3. 原因：O5 的 production/public-cloud external evidence 依赖当前环境没有的新生产材料，且相邻
   CDN/relay/browser/export/review/readiness wrapper 已被连续消费并退役。继续做 O5 support-only 包装
   不会满足 Mission Objective 0。本 sprint 消费上轮唯一新 blocker `map_to_odom_fresh` 的精确根因，
   可在当前代码、既有 artifact 和可选只读 live window 中真实推进。

## 文件范围

Engineer 只允许修改或创建：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `sprints/2026.07.15_05-55_o3_tf_receipt_time_freshness_recovery/tech-done.md`
- `sprints/2026.07.15_05-55_o3_tf_receipt_time_freshness_recovery/artifacts/algorithm/*`

不得修改旧 sprint、`OKR.md`、launch/config、hardware/vendor 文件或其他工程代码。Product closeout 文件
不属于 Engineer 范围。

## 实现步骤

### 1. TF callback receipt 采集

- 在 `collect_amcl_rclpy_probe` 的 `/tf` 与 `/tf_static` callback 入口各取一次 `now_ms()`。
- 扩展 transform artifact builder 或在 callback 后标准化，为 TFMessage 中每条 transform 写入同一个
  `received_at_ms`；不得在后续 summary 阶段补写当前时间。
- compact/merge 逻辑保留 receipt 字段。CLI fallback 没有 callback receipt 时保持 `None`，不得用命令
  finish time 代替。

### 2. Edge freshness 合同

- `tf_edge_freshness_entry` 选择目标 transform 后读取 header epoch 与 `received_at_ms`，并输出
  `evaluated_at_ms`。
- 派生 `header_age_at_receipt_ms`、`receipt_age_at_evaluation_ms`、
  `header_age_at_evaluation_ms`；负 age 超过允许的毫秒级 clock-skew 容差时 fail-closed，并在 artifact
  写明 reason。默认不新增可调 threshold，沿用 `3000ms`。
- dynamic edge 的 gate status 基于 `header_age_at_receipt_ms`。header 在 callback 时已旧则 stale；receipt
  缺失/非法或 header 未解析则 unknown；collector 后续耗时只体现在诊断 age。
- static edge 继续保持 static/source 语义，不把 zero/static stamp 误套 dynamic freshness。
- 保留现有 `timestamp`、`source_class`、publisher attribution 与 blocker contract；如字段结构升级，
  文档明确兼容关系。

### 3. 回归测试

至少覆盖：

1. header 在 receipt 时 `<3000ms`，但 evaluation 晚于 receipt `>3000ms`：必须 fresh，且三类 age 正确。
2. header 在 receipt 时已经 `>3000ms`：必须 stale，不能被新 receipt 掩盖。
3. dynamic transform 缺 `received_at_ms`：unknown/fail-closed。
4. header stamp missing/invalid：unknown/fail-closed。
5. 同一 TFMessage 多 transform 共享 callback receipt，目标 edge 能保留该值。
6. static transform 与 publisher attribution 既有测试不回退。
7. 上轮形态 `header_age_at_evaluation_ms≈5090ms`、receipt 时 age clean 的 synthetic regression，明确证明
   collector delay 不再误报 stale，但不篡改旧 artifact。

### 4. 文档与可选现场验证

- 更新 `docs/navigation/field_route_evidence_preflight.md`，解释三类时间、decision age、缺 receipt
  fail-closed 和 3000ms threshold。
- 所有本地验证通过后，先只读检查远端既有 runtime。只有不需要 start/stop runtime 且调用默认
  `initialpose_opt_in=false`、`managed_runtime_opt_in=false`、path opt-in=false 时，才可部署相同 SHA 并
  最多运行一次 capture。
- 现场命令及其 stdout/stderr/exit、SHA、graph/process before/after 与 forbidden-command scan 必须进入
  本 sprint artifact。任何安全前置不满足就跳过现场 capture，不得修 launch/config 或扩大授权。

## 接口影响

- JSON artifact 的 TF transform/edge freshness 增加 receipt/evaluation timing 字段；这是 additive contract。
- dynamic freshness 的判定时间基准从“collector 最终生成时刻”收敛为“header 在 callback receipt 时的
  age”，threshold 不变。
- 不改变 ROS topic、message type、launch 参数、控制 API、UART 或硬件配置。

## 风险与防护

- Receipt 是 collector 本地 wall clock；header 与主机 clock 不一致时可能出现负 age。必须显式输出
  clock-skew reason 并 fail-closed，不得 `abs()` 或 clamp 成 fresh。
- merge/fallback 可能选到只有 CLI stamp 的 transform；缺 receipt 时保持 unknown。
- optional live capture 不是必须通过项；不应为生成 artifact 破坏 no-start/no-stop safety boundary。
- 本轮最多证明 freshness contract 与 current read-only observation，不证明机器人真实物理位姿或 Mission
  closure。所有 control/route/delivery/HIL 字段保持 false。

## 验收命令

Engineer 必须运行、记录完整结果，并在失败时修复后复验：

```bash
python3 -m py_compile \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/tests/test_nav2_runtime_proof_helper.py

python3 -m unittest onboard/tests/test_nav2_runtime_proof_helper.py

rg -n "received_at_ms|header_age_at_receipt_ms|receipt_age_at_evaluation_ms|header_age_at_evaluation_ms|3000|initialpose|no-topic-write|no-motion" \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/field_route_evidence_preflight.md \
  sprints/2026.07.15_05-55_o3_tf_receipt_time_freshness_recovery/tech-done.md

git diff --check -- \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/field_route_evidence_preflight.md \
  sprints/2026.07.15_05-55_o3_tf_receipt_time_freshness_recovery
```

若执行 optional live capture，还必须记录并验证：

```bash
python3 -m json.tool \
  sprints/2026.07.15_05-55_o3_tf_receipt_time_freshness_recovery/artifacts/algorithm/runtime-proof.json \
  >/dev/null

rg -n "initialpose|NavigateToPose|cmd_vel|api/base/manual|UART|managed_runtime.*started|planner|controller|path" \
  sprints/2026.07.15_05-55_o3_tf_receipt_time_freshness_recovery/artifacts/algorithm
```

现场 acceptance 必须由结构断言证明：`received_at_ms` 存在；三类 age 可复算；decision 使用
`header_age_at_receipt_ms`；`initialpose_publish_attempts=0`；没有 runtime start/stop、control、route、
delivery 或 HIL 行为。若现场没有 fresh TF，只能按 exact blocker fail-closed 收口，不能回退到 wrapper。
