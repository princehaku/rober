# Tech Plan: Runtime Material Epic

## 任务分工

### Robot Software Engineer

- 目标：通过 `ssh root@192.168.1.11 -p 37878` 检查上位机 ROS2/8787 runtime，优先采集 O3/O7 材料。
- 文件范围：`sprints/2026.06.04_17-18_runtime-material-epic/owner_notes/robot-software-engineer.md`、必要时 `onboard/scripts/`、`docs/interfaces/`。
- 禁止：不改硬件运动参数，不执行底盘运动命令。
- 验收命令：SSH 上位机只读/非运动检查；本地最小测试或 compile；scoped `git diff --check`。

### User Touchpoint Full-Stack Engineer

- 目标：验证 PC/8787 operator workflow 是否能连接真实上位机 API，形成 O7 evidence ref。
- 文件范围：`sprints/2026.06.04_17-18_runtime-material-epic/owner_notes/full-stack-software-engineer.md`、必要时 `pc-tools/`、`docs/product/`、`docs/interfaces/`。
- 禁止：不做空心 UI，不绕过 8787/ROS2 契约硬编码状态。
- 验收命令：PC/package 现有测试；对 8787 endpoint 的 live/manual smoke；scoped `git diff --check`。

### Robot Algorithm Engineer

- 目标：查找真实或受控电梯图片 manifest；若存在，运行 OpenCV offline eval；若不存在，输出 blocker 和最小采集方案。
- 文件范围：`sprints/2026.06.04_17-18_runtime-material-epic/owner_notes/robot-algorithm-engineer.md`、必要时 `onboard/src/ros2_trashbot_vision/`、`docs/vision/`。
- 禁止：没有真实/受控图片时不得把 fixture eval 写成 O2 涨分材料。
- 验收命令：OpenCV eval/checker 或明确文件不存在的命令证据；相关测试/compile；scoped `git diff --check`。

### Hardware Infra Engineer

- 目标：按 vendor 来源复核 O1 stop-first/HIL 准入；安全条件不足则只采集非运动 feedback/阻塞证据。
- 文件范围：`sprints/2026.06.04_17-18_runtime-material-epic/owner_notes/robot-hardware-engineer.md`、必要时 `docs/hardware/`、`onboard/scripts/`。
- 必读：`docs/vendor/VENDOR_INDEX.md` 和其指向的 WAVE ROVER UART/JSON vendor 文件。
- 禁止：没有现场看护、物理净空和人工急停材料时，不执行 forward/back/left/right 运动 pulse。
- 验收命令：vendor/source citation、SSH 非运动 serial/device/status 检查、scoped `git diff --check`。

### Product Manager / OKR Owner

- 目标：聚合 owner notes，写 `tech-done.md`、`side2side_check.md`、`final.md`，必要时更新 `OKR.md` 和 `docs/process/okr_progress_log.md`。
- 文件范围：`OKR.md`、`docs/process/okr_progress_log.md`、`sprints/2026.06.04_17-18_runtime-material-epic/`。
- 验收命令：关键词检查、diff check、OKR 百分比边界检查。

## 接口影响

本轮默认优先采证，不主动改变公开接口。若 owner 发现现有接口阻断真实 runtime 且能小范围修复，必须同步更新相关 docs 并运行最小验证。

## OKR 最低优先级核对

- 当前 OKR.md 4.1 节完成度最低的 Objective：O8，约 35%。
- 本 sprint 是否针对该 Objective：是，但只作为治理约束和 evidence type gate；产品主线同时覆盖 O2/O3/O7/O1。
- 理由：O8 是执行治理，不新增产品能力；本轮必须用 O8 约束跨 owner Epic，同时把真实材料拉回 O2/O3/O7/O1。
- final.md 收口时需复核：是否真的按 Epic 六文档、owner health、blocker scan 和 evidence type gate 收口。

## 最近 2 轮 blocker scan

- `16-05_okr-six-sprint-strategy-rewrite`：发现 O5/O6 重复消费 URL/token/cloud blocker，结论是切回真实材料 Epic。
- `16-17_o2-elevator-opencv-state-integration`：O2 adapter 完成但 blocker 是无真实图片/runtime/受控电梯材料。
- 本轮规避策略：不继续 O5/O6；O2 若无图片必须写 blocker，O3/O7/O1 直接使用上位机入口或安全准入采证。

## 证据类型 gate

- `software_guard`：可以合并，但不涨 O1/O2/O3/O7 产品百分比。
- `robot_runtime_material`：可支持 O3/O7 涨分候选。
- `field_hil_material`：可支持 O1/O7 涨分候选。
- `user_acceptance_material`：可支持 O7/O2 涨分候选。
- `blocked_with_root_cause`：不涨分，但可触发下一轮 owner 决策或 CEO blocker。

## 风险

- SSH 入口可能不可达或无免密；必须保留错误输出。
- 上位机 8787 可能只返回 dry-run/stub；只能证明合同，不证明真实 ROS2 driver。
- 真实电梯图片可能不存在；不能用 fixture 代替真实材料涨分。
- HIL 安全条件可能不足；必须 fail closed。
