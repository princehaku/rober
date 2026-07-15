# Tech Plan - O3 Live TF Receipt Capture

## 方案摘要

由 `robot-algorithm-engineer` 单线闭环。先完成 vendor/现场参数来源核对与本地回归，再同步 helper 到真实
上位机，执行一次 helper-owned strict-no-motion localization-only runtime capture。只采定位/传感器证据，
不发布 `/initialpose`，不启动 planner/controller，不接触底盘控制。

## OKR 最低优先级核对

1. `OKR.md` 4.1 当前最低 Objective 是 O5，约 `85%`；O6/O7 约 `93%`，O1 约 `94%`。
2. 本 sprint 不直接针对 O5，针对 O3 current localization evidence chain，并支持 O1 live route/HIL 前置。
3. 原因：本轮只读真实上位机审计确认 cloudflared/ngrok/frp/WireGuard/tailscale 全部缺失，无 relay/tunnel
   进程；仓库只有 loopback Docker relay，缺公网 endpoint、TLS/DNS、provider runtime 与凭证，无法产生
   success-class external evidence。O5 相关 wrapper 已退役。当前可执行的更强 artifact 是上轮明确留下的
   live TF receipt capture，不再重复离线合同。

## 授权解释与安全边界

- 本轮 CEO 提供 SSH 主机并要求持续推进 OKR，视为新授权：允许一次 helper-owned strict-no-motion
  localization-only runtime 的启动、采集与 cleanup。
- 授权仅覆盖 map_server、AMCL、LiDAR 与必要 static TF；不覆盖 `/initialpose`、planner/controller/path、
  NavigateToPose、`/cmd_vel`、`/api/base/manual`、base UART、运动、route、delivery 或 HIL。
- 若 vendor/设备、map、ROS source、process ownership 或 cleanup 前置不清，Engineer 必须 fail closed。

## 文件范围

Engineer 只允许修改或创建：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`（仅现场暴露明确 helper bug 时）
- `onboard/tests/test_nav2_runtime_proof_helper.py`（仅对应 helper bug 回归）
- `docs/navigation/field_route_evidence_preflight.md`
- `sprints/2026.07.15_08-06_o3_live_tf_receipt_capture/tech-done.md`
- `sprints/2026.07.15_08-06_o3_live_tf_receipt_capture/artifacts/algorithm/*`

不得修改旧 sprint、launch/config、hardware/vendor 文件或其他业务代码。Product closeout 阶段才允许更新
`OKR.md`、`docs/process/okr_progress_log.md`、`side2side_check.md`、`final.md`。

## 实施步骤

### 1. 本地与资料前置

- 阅读 `docs/vendor/VENDOR_INDEX.md`，并在 `tech-done.md` 引用：WAVE ROVER base 是 newline-delimited UART
  JSON，但本轮 `--no-base-uart` 禁止打开任何 base serial；LiDAR `/dev/ttyACM0`、`150000` 只能引用仓库
  既有 2026-07-13 现场 capture，不把它写成 vendor 通用事实。
- 运行 helper `py_compile` 与全部 targeted unittest；失败则定位修复后复验。
- 计算 local helper SHA。远端只读 preflight 核对进程、map、ROS source 和 LiDAR device；不得读取 credential。

### 2. 部署与唯一 live capture

- 仅把当前 helper 同步到 `/tmp/rober_o3_live_tf_receipt_capture.py`；记录 remote SHA 与 local SHA。
- capture 命令必须显式包含：
  `--strict-no-motion --no-base-uart --managed-runtime-opt-in --reuse-existing-lidar-lifecycle`
  `--managed-lidar-serial-port /dev/ttyACM0 --managed-lidar-serial-baudrate 150000`。
- 命令不得包含 `--initialpose-opt-in` 或 `--path-generation-opt-in`；输出写到本 sprint 独立远端临时路径。
- helper 管理并清理自己创建的 process group；拉回 raw JSON、stdout/stderr/exit、pre/post process inventory。
- 若 helper 已进入 runtime，则不得为了追求 clean 结果重跑；只接受本次事实。

### 3. Artifact 结构验收

- 核对 managed runtime start/cleanup、map_server/AMCL、scan/pose/TF source 与 exact blocker。
- 对所有含 callback receipt 的 TF transform 核对 `received_at_ms`；若 dynamic `map->odom` 存在，复算：
  `received_at_ms - header_stamp_epoch_ms = header_age_at_receipt_ms`；
  `evaluated_at_ms - received_at_ms = receipt_age_at_evaluation_ms`；
  `evaluated_at_ms - header_stamp_epoch_ms = header_age_at_evaluation_ms`。
- decision threshold 固定 `3000ms`；missing/invalid/clock-order abnormal 必须 fail closed。
- 断言 `initialpose_publish_attempts=0`，无 path/planner/controller/control/UART/route/delivery/HIL。

### 4. 文档、留档与提交

- 更新导航文档和 `tech-done.md`，记录实际改动、完整验证、失败定位、proof boundary、四个 delta 与剩余风险。
- 若仅生成 artifact/文档也必须如实列出；不得声称代码改动。
- 完成后提交本 sprint scope，commit message 使用 `okr(nav): capture live TF receipt evidence`；推送当前
  `master` 到 `origin/master`，并记录 commit SHA、push 输出、`HEAD == origin/master` 与 clean worktree。

## 接口影响

- 预期不改 ROS topic/message/launch/control 接口；本轮只生成新的 runtime JSON artifact。
- 只有现场暴露已修 helper 合同的明确 bug 时，才允许 additive 修复与 targeted regression；不得扩展功能。
- 不改硬件配置、serial default、map 或 production cloud 配置。

## 风险与失败分支

- 若远端前置不满足：不启动 runtime，记录 exact blocker，不生成伪 artifact。
- 若 runtime 启动后无 `/amcl_pose` 或 dynamic `map->odom`：按 current live exact blocker 收口，禁止发布
  `/initialpose`，禁止重跑。
- 若 helper cleanup 有 residual：Engineer 必须只清理 helper-owned process group并复核；不得杀死未知进程。
- 若现场暴露代码 bug：修复、补测试、本地复验后才允许一次新的 capture；前一次必须证明未越过安全边界，
  并在 `tech-done.md` 完整保留。

## 验收命令

Engineer 必须执行并记录；测试失败时修复后复验：

```bash
python3 -m py_compile \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/tests/test_nav2_runtime_proof_helper.py

python3 -m unittest onboard/tests/test_nav2_runtime_proof_helper.py

python3 -m json.tool \
  sprints/2026.07.15_08-06_o3_live_tf_receipt_capture/artifacts/algorithm/runtime-proof.json \
  >/dev/null

rg -n "received_at_ms|header_age_at_receipt_ms|receipt_age_at_evaluation_ms|header_age_at_evaluation_ms|3000|initialpose|no-base-uart|managed_runtime|cleanup|cmd_vel|base/manual|UART|route_execution_success|delivery_success|hil_pass" \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/field_route_evidence_preflight.md \
  sprints/2026.07.15_08-06_o3_live_tf_receipt_capture/tech-done.md \
  sprints/2026.07.15_08-06_o3_live_tf_receipt_capture/artifacts/algorithm

git diff --check -- \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/field_route_evidence_preflight.md \
  sprints/2026.07.15_08-06_o3_live_tf_receipt_capture
```

结构断言必须至少证明：local/remote SHA 一致；final live run count=`1`；
`managed_runtime_started=true` 或明确 pre-start blocker；`initialpose_publish_attempts=0`；
`path_generation_requested=false`；`uses_base_uart=false`；`publishes_cmd_vel=false`；
`calls_base_manual=false`；`robot_control_executed=false`；`route_execution_success=false`；
`delivery_success=false`；`hil_pass=false`；helper-owned cleanup residual=`0`。若 dynamic `map->odom` 存在，
还必须证明三类 age 等式与 receipt-time decision basis；若不存在，只能以 exact blocker 收口。
