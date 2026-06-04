# Tech Plan: Runtime Material Runtime Hooks

## sprint_type

sprint_type: epic

## 任务分工

### Robot Software Engineer

- 文件范围：`onboard/scripts/upper_robot_api.py`、`onboard/scripts/test_upper_robot_api.py`、必要的 LiDAR collector 文件、`docs/interfaces/o7_upper_robot_api.md`、`docs/interfaces/lidar_ros2_closed_loop.md`、owner note。
- 任务：新增或复用只读 `POST /api/radar/scan-proof/refresh`，运行 read-only scan proof collector，写入/回读 artifact。
- 验收：upper API unittest、compileall、diff-check、SSH 非运动 readback。

### User Touchpoint Full-Stack Engineer

- 文件范围：`pc-tools/workstation/` direct-upper API/UI/test、`docs/interfaces/o7_direct_upper_pc_api.md`、`docs/product/pc_tools_workstation.md`、owner note。
- 任务：PC 同源代理 refresh 入口，UI 展示 fresh/stale/blocker 和 not_proven copy。
- 验收：workstation test/build/lint、diff-check、可用时 PC direct-upper smoke。

### Hardware Infra Engineer

- 文件范围：`docs/hardware/`、必要的 `docs/interfaces/lidar_ros2_closed_loop.md` 小段、owner note。
- 任务：vendor-sourced 复核 read-only scan proof 和 fresh/stale feedback 边界。
- 验收：vendor citation、SSH 只读/非运动检查、diff-check。

### Product Manager / OKR Owner

- 文件范围：`OKR.md`、`docs/process/okr_progress_log.md`、本 sprint `tech-done.md`、`side2side_check.md`、`final.md`。
- 任务：IC 返回后判断 evidence type、OKR 是否涨分、剩余 blocker 和下一轮抓手。

## OKR 最低优先级核对

- 当前最低 Objective：O8 约 42%；产品主线最低为 O2 约 72%、O3 约 73%。
- 本 sprint 是否针对最低 Objective：是。O8 通过 Epic evidence gate 继续推进；产品抓手针对 O3/O7 runtime material，并约束 O1 安全边界。
- 为什么不继续 O2：最近两轮已确认缺真实/受控电梯图片；本轮无新图片来源，继续找图会重复消费 blocker。

## Evidence Type Gate

- `robot_runtime_material`：只有 fresh scan proof refresh 成功或明确实时 readback artifact 可计入。
- `blocked_with_root_cause`：无 ROS2 topic、无法部署、hook 未配置等必须写成 blocker。
- `software_guard`：本地测试、接口和 UI 只能作为护栏，不单独推动 O3/O7 产品涨分。
- `vendor_feedback_material`：`T=1001` 仍只代表 vendor feedback，不等于 robot ACK 或 HIL。
