# Tech Plan: Runtime Material Continue

## sprint_type

sprint_type: epic

## 任务分工

### Robot Software Engineer

- 目标：推进 O3/O7 non-motion ROS2 runtime，优先让上位机产出 fresh `/scan` 或明确 driver/supervisor blocker。
- 文件范围：`sprints/2026.06.04_19-20_runtime-material-continue/owner_notes/robot-software-engineer.md`，必要时 `onboard/scripts/`、`docs/interfaces/`。
- 接口边界：不执行底盘运动命令，不调用 `/api/base/manual`，不发布 `/cmd_vel`。
- 验收命令：
  - SSH 到 `root@192.168.1.11 -p 37878` 的非运动 ROS2/8787 检查。
  - 如有代码改动：`python3 -m unittest onboard.scripts.test_upper_robot_api`、`python3 -m compileall -q onboard/scripts`。
  - `git diff --check -- onboard/scripts docs/interfaces sprints/2026.06.04_19-20_runtime-material-continue`

### Robot Algorithm Engineer

- 目标：推进 O2 真实/受控 elevator image manifest；找到则跑 OpenCV eval，找不到则产出采集模板和 blocker。
- 文件范围：`sprints/2026.06.04_19-20_runtime-material-continue/owner_notes/robot-algorithm-engineer.md`，必要时 `docs/vision/`、`onboard/src/ros2_trashbot_vision/`、`pc-tools/evidence/`。
- 接口边界：没有真实/受控图片时，不把 fixture eval 写成 O2 涨分材料。
- 验收命令：
  - manifest/image 查找命令与输出。
  - 如生成模板或 eval：对应 checker/eval 命令。
  - `python3 -m unittest discover -s onboard/src/ros2_trashbot_vision/test`
  - `git diff --check -- docs/vision onboard/src/ros2_trashbot_vision pc-tools/evidence sprints/2026.06.04_19-20_runtime-material-continue`

### User Touchpoint Full-Stack Engineer

- 目标：推进 O7 PC operator workflow，让 PC 端展示并回放真实 operator report evidence ref，同时保持 not_proven 和安全边界。
- 文件范围：`sprints/2026.06.04_19-20_runtime-material-continue/owner_notes/full-stack-software-engineer.md`，必要时 `pc-tools/workstation/`、`docs/product/`、`docs/interfaces/`。
- 接口边界：不做空心 UI；不绕过 8787/ROS2 契约硬编码完成态；不触发底盘运动。
- 验收命令：
  - `cd pc-tools/workstation && npm test -- --run`
  - `cd pc-tools/workstation && npm run build`
  - `cd pc-tools/workstation && npm run lint`
  - PC same-origin smoke against `http://192.168.1.11:8787`。
  - `git diff --check -- pc-tools/workstation docs/product docs/interfaces sprints/2026.06.04_19-20_runtime-material-continue`

### Hardware Infra Engineer

- 目标：推进 O1 stop-first HIL 准入；若安全条件不足，补非运动 feedback 和明确 blocker。
- 必读：`docs/vendor/VENDOR_INDEX.md` 和其指向的 WAVE ROVER UART/JSON vendor 文件。
- 文件范围：`sprints/2026.06.04_19-20_runtime-material-continue/owner_notes/robot-hardware-engineer.md`，必要时 `docs/hardware/`、`onboard/scripts/`。
- 接口边界：没有现场看护、物理净空、人工急停和授权时，不执行 forward/back/left/right pulse。
- 验收命令：
  - vendor/source citation。
  - SSH 非运动 serial/device/status 检查。
  - 如改脚本：相关 `python3 -m unittest` 与 `python3 -m compileall`。
  - `git diff --check -- docs/hardware onboard/scripts sprints/2026.06.04_19-20_runtime-material-continue`

### Product Manager / OKR Owner

- 目标：聚合 owner notes，更新 `tech-done.md`、`side2side_check.md`、`final.md`，必要时更新 `OKR.md` 和 `docs/process/okr_progress_log.md`。
- 文件范围：`OKR.md`、`docs/process/okr_progress_log.md`、`sprints/2026.06.04_19-20_runtime-material-continue/`。
- 验收命令：
  - `git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.06.04_19-20_runtime-material-continue`
  - `rg -n "O2|O3|O7|O1|O8|evidence_type|not_proven|safe_to_control|needs_real_image_manifest|/scan|/map" OKR.md docs/process/okr_progress_log.md sprints/2026.06.04_19-20_runtime-material-continue`

## 接口影响

默认优先采真实/受控材料，不主动扩公开接口。若发现现有接口阻断真实 runtime 且能小范围修复，owner 必须同步更新相关 docs、测试和 owner note，并保持 fail-closed 安全字段。

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：O8 约 40%，产品主线最低为 O2 约 72%、O3 约 73%。
- 本 sprint 是否针对最低 Objective：是。O8 负责治理和证据 gate；本轮产品抓手直接针对 O2/O3，并联动 O7/O1。
- 如果本轮未能为 O2/O3 涨分，必须在 `final.md` 写明 root cause 和下一轮是否需要 CEO/现场决策。

## 最近 2 轮 blocker scan

- `16-17_o2-elevator-opencv-state-integration`：O2 adapter 完成但无真实图片、真实相机 runtime 或受控电梯材料。
- `17-18_runtime-material-epic`：O3 上位机 ROS2/包存在但 application nodes 未运行；O2 仍无真实 manifest；O1 安全条件不足；O7 operator report route 已通但非现场 workflow。
- 本轮规避策略：不继续 O5/O6；O2 必须找真实/受控 manifest 或写采集 blocker；O3 必须尝试 fresh non-motion ROS2 runtime 或写 supervisor blocker；O1 未满足安全前提时不做 motion。

## evidence type gate

- `software_guard`：可合并、可作为护栏，不涨 O1/O2/O3/O7 产品百分比。
- `robot_runtime_material`：可支持 O3/O7/O1 小幅涨分候选，必须来自真实上位机 runtime。
- `field_hil_material`：可支持 O1/O7 涨分候选，必须有现场安全前提和 stop-first 材料。
- `user_acceptance_material`：可支持 O2/O7 涨分候选，必须有用户/现场验收材料。
- `blocked_with_root_cause`：不涨分，但可触发 Product/CEO 决策或下一轮 owner 调整。

## 风险

- 上位机可能缺 supervisor 或 ROS2 driver 启动脚本，导致 O3 继续 blocked。
- 电梯图片可能仍不存在，O2 只能输出 blocker 和采集模板。
- HIL 安全条件可能仍不满足，O1 必须 fail closed。
- 当前工作树已有 17-18 未提交改动；owner 不得回滚或覆盖不属于自己的文件。
