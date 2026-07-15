# Final - O6/O7 真实传感器数据集回放

## Sprint Metadata

- `sprint_type: epic`
- Sprint：`sprints/2026.07.15_10-59_o6_o7_live_sensor_dataset_replay/`
- Closeout date：`2026-07-15 Asia/Shanghai`
- Product status：`accepted_blocked_fail_closed_no_mission_credit`
- Proof boundary：`live_upper_computer_read_only_sensor_inventory_blocked_scan_publisher_unconfirmed`
- Exact status：`blocked_scan_publisher_unconfirmed`

## Product Acceptance 结论

本轮接受一次真实上位机 read-only inventory 和按 gate 停止 capture 的安全决策，拒绝把 inventory 算作 current-run mission artifact。SSH inventory exit `0`；ROS setup、rosbag/sqlite3、`--max-bag-size`、磁盘和无冲突 recorder gate 通过；但 `/scan` 仅在 topic list 中显示 `sensor_msgs/msg/LaserScan`，bounded verbose info exit `1`、`Unknown topic '/scan'`，publisher count 未确认，同时观察到 ROS CLI 自动 daemon 副作用。

因此 `capture_gate=false`、`inventory_invocation_count=1`、`live_capture_invocation_count=0`。没有 DB3、metadata、keyframe、semantic replay、artifact-bundle input 或 Full-stack Phase C；两次 helper 实现派单均在产品代码、测试和文档零文件落盘前中断。Product 不把规划、inventory 或中断派单包装成 dataset/replay/O6/O7 交付。

## 用户价值、抓手与工作项

用户获得的是明确的安全阻塞定位：问题已收敛到 `/scan publisher_count` 无法在无 daemon 副作用的稳定 graph 窗口中确认，而不是 rosbag、sqlite、max-size、磁盘或冲突 recorder 不可用。这减少了误录、重复 SSH 与用 fixture 代替真实数据的风险，但没有提供可回放、归档或标注的数据集。

本 sprint 抓手到此退役：只读 inventory 已消费一次，当前 sprint **不得重跑**，不得新增 helper、wrapper、review、readback、fixture、离线 mock receipt 或 Full-stack Phase C 来包装 blocker。

## 实际改动与验证边界

- Sprint 规划：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 工程事实：`artifacts/algorithm/read_only_inventory.json`、`tech-done.md`。
- Product 收口：`side2side_check.md`、`final.md`，并同步 `OKR.md` 与 `docs/process/okr_progress_log.md`。
- 产品代码、测试代码、硬件配置、导航文档、O6/O7 合同均零改动。
- 本次 Product closeout 只运行文件存在、JSON 解析、required `rg`、scoped `git diff --check` 与 `git status -sb`；按任务边界未执行 SSH、构建、产品测试、硬件 smoke 或 live capture。

## Mission / OKR / KR 决策

- `current_run_artifact_delta=false`
- `external_artifact_delta=false`
- `live_control_delta=false`
- `user_action_delta=false`
- `mission_objective_0_satisfied=false`
- `okr_credit=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `safe_to_control=false`

O5 维持约 `85%`，O6/O7 各维持约 `93%`，O1 维持约 `94%`，主百分比全平。O6/O7 KR `不归档`；没有完成 KR，历史区不新增归档记录。证据历史固定在本 sprint 文档链与唯一 inventory artifact。

## OKR 方向与下一轮路由

方向调整为：本轮 blocked 收口后下一轮默认切换 Objective，优先选择不依赖 `/scan` inventory blocker、可以产生 task/map/route/keyframe/rosbag/replay/delivery result 的最低可行动 lane。

若 Product/CEO 仍要求恢复该能力，必须另建新 sprint 并提供 fresh authorization，由 `robot-algorithm-engineer` 采用 `ROS2CLI_NO_DAEMON=1` 或 daemon-off 的同 shell、graph-stabilized bounded probe，只在重新证明 `/scan publisher_count>=1` 且 runtime 无副作用后恢复唯一 capture gate。`full-stack-software-engineer` 仍须等待真实 DB3 与 semantic sections 冻结后才进入 Phase C，禁止 fixture 替代。

## 剩余风险

1. `/scan` publisher 未确认，根因可能是 ROS graph 稳定窗口、daemon/cache 或 publisher 瞬态；本轮证据不能进一步归因。
2. 无 DB3/keyframe/replay，O6 真实机器人数据和 O7 真实回放/标注数据流缺口完全未关闭。
3. 无 Full-stack Phase C，未证明 O6 archive/O7 consumer 的 task/hash/topic/message/timestamp lineage。
4. 无路线执行、送达、HIL、控制安全或用户动作证据；所有相关 success/safe 字段保持 false。
