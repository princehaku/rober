# Nav2 Planner Empty Path Recovery

sprint_type: micro

## 目标

继续推进真实上车 evidence capture，不使用 subagent。上一轮已经证明 TF/localization 链路成立，
本轮处理新的 Nav2 blocker：`ComputePathToPose` goal accepted 但 `path_point_count=0`。
边界仍是 no-motion proof：不请求 `/api/base/manual`、不发布 `/cmd_vel`、不打开 `/dev/ttyS5`、
不执行 NavigateToPose/controller。

硬件事实来源先读 `docs/vendor/VENDOR_INDEX.md`。本轮没有改 WAVE ROVER UART 或底盘控制；
仍以 vendor 事实约束：底盘是 UART newline JSON，Orange Pi 串口不能沿用 Raspberry Pi 路径假设。

## 实际改动

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - 新增 map yaml/PGM runtime analysis，记录 bounds、origin、resolution、width/height 和
    free/unknown/occupied/other cell 计数。
  - 当固定 no-motion proof 的 start/goal 被当前地图裁剪到 bounds 外时，仅对
    planner-only `ComputePathToPose` 请求启用 `use_start=true`，把 start/goal 夹到地图内侧。
  - artifact 保留原始 start/goal、适配后的 start/goal、地图 bounds、cell 计数和
    `map_bounds_adapted_no_motion_planner_probe`，避免把自适应 proof 误解成真实运动。
  - 记录 Nav2 action result 的 `error_code/error_msg` 字段，便于后续定位 planner 失败。
- `onboard/tests/test_nav2_runtime_proof_helper.py`
  - 新增固定 proof 点越界时的 map-bounds 自适应回归测试。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步说明 `检查路径（高级）` 的 map-aware no-motion proof 行为和最新真实上位机证据。

## 验证结果

- 本地单元测试：
  - `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper`
  - 结果：31 tests OK。
- 本地语法检查：
  - `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/tests/test_nav2_runtime_proof_helper.py`
  - 结果：通过。
- 上位机部署：
  - `scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - 远端 `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py` 通过。
- 地图根因证据：
  - artifact：`artifacts/06_remote_map_inventory.json`
  - 当前 `trashbot_map.yaml` bounds 为 `x=-6.1478..5.1021`、`y=-5.9246..-0.0246`。
  - 固定 proof 的原始 `(0,0)->(0.8,0)` 在 y 方向越过 map 上边界。
  - 当前 runtime maps 的 PGM 计数均显示 `free=0`，本轮只证明 planner 可在当前 unknown-space map
    上生成 no-motion 软件路径，不证明真实可行驶路线。
- 上位机 API refresh：
  - artifact：`artifacts/07_upper_api_refresh_after_map_adaptive_goal.json`
  - artifact：`artifacts/08_upper_runtime_nav2_latest_after_map_adaptive_goal.json`
  - 结果：`status=nav2_no_motion_path_generation_runtime_observed`。
  - 结果：`path_generation_succeeded=true`、`path_generated=true`、`path_point_count=30`、`root_causes=[]`。
  - 结果：原始 goal `(0.8,0)` 被记录为 out-of-bounds；planner-only adapted goal 为
    `(0.8,-0.27467727804371744)`，adapted start 为 `(0,-0.27467727804371744)`。
  - 结果：`safe_to_control=false`、`sends_motion_commands=false`、`uses_base_uart=false`。
- 清场：
  - `ps` 未发现 managed Nav2/lidar runtime 残留进程。
  - `fuser -v /dev/ttyS5 /dev/ttyACM0` 未显示占用者。

## 剩余风险

- 本轮恢复的是 no-motion ComputePathToPose 软件证据，不是 NavigateToPose、controller、
  `/cmd_vel`、手动移动、固定路线或 delivery success。
- 当前地图质量仍弱：PGM 没有 free cell，说明需要重新做带真实移动/视角变化的建图证据。
- Camera 仍是 `/dev/video1` first-frame timeout，PC 实时图传可见内容未证明。
- 非 stop 运动 gate 仍缺 visible camera、外部视频、轮速反馈非零和 LiDAR motion delta。
