# Tech Plan: Runtime Material Followup

## sprint_type

sprint_type: epic

## 任务分工

### Robot Software Engineer

- 目标：SSH 上位机，做非运动 ROS2/8787 runtime 检查，拿 fresh `/scan`、`/map`、AMCL/TF/Nav2 material 或明确 blocker。
- 文件范围：`onboard/scripts/`、`docs/interfaces/`、本 sprint owner note。
- 验收：upper SSH readback；如改代码则跑 upper API / LiDAR collector tests、compileall、scoped diff-check。

### Robot Algorithm Engineer

- 目标：查找真实/受控电梯图片 manifest；没有则只记录 blocker，不跑 fixture 涨分。
- 文件范围：`docs/vision/`、`onboard/src/ros2_trashbot_vision/`、`pc-tools/evidence/`、本 sprint owner note。
- 验收：manifest/image 查找、checker 输出、vision unittest、scoped diff-check。

### User Touchpoint Full-Stack Engineer

- 目标：验证 PC same-origin operator-report POST/GET 到真实 8787；只触达 report artifact。
- 文件范围：`pc-tools/workstation/`、`docs/product/`、`docs/interfaces/`、本 sprint owner note。
- 验收：workstation tests/build/lint、8787 operator-report smoke、scoped diff-check。

### Hardware Infra Engineer

- 目标：vendor-sourced stop-first preflight；只做非运动 serial/status/feedback material。
- 文件范围：`docs/hardware/`、`onboard/scripts/`、本 sprint owner note。
- 验收：vendor citation、SSH device/status checks、必要 tests/compileall、scoped diff-check。

## OKR 最低优先级核对

- 当前最低 Objective：O8 约 40%；产品主线最低为 O2 约 72%、O3 约 73%。
- 本 sprint 是否针对最低 Objective：是。O8 通过 evidence gate 和 owner timeout 修复推进；产品抓手直接针对 O2/O3，并联动 O7/O1。
- 若 O2/O3 不涨分，必须写清 root cause 和下一步现场/运行时决策。

## 最近 2 轮 blocker scan

- `17-18_runtime-material-epic`: O2 无真实 manifest；O3 上位机无应用 ROS graph；O1 无 HIL 条件。
- `19-20_runtime-material-continue`: O2 checker 落地但无图片；三个 owner 超时。
- 本轮规避策略：小任务并行，允许 blocked closeout，但必须产出 owner note 和命令证据。

## evidence type gate

- `blocked_with_root_cause`: O2/O3 若缺材料，只记录 blocker，不涨分。
- `vendor_feedback_material`: O1 非运动 `T=130 -> T=1001`，不等于 ACK/HIL。
- `robot_runtime_material`: O7 operator report readback 可作为 PC/8787 artifact route material，不等于控车。
- `software_guard`: 代码/测试修复只作为护栏，不能替代真实 runtime。
