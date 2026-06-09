# Nav2 initialpose no-motion proof

## sprint_type

micro

## 设计边界

本轮只把 08:15 的 AMCL root cause 向前推进一格：允许在显式 opt-in 的 no-motion 证明窗口里向 `/initialpose` 发布一次 PoseWithCovarianceStamped，用来验证 AMCL 是否能产生 `/amcl_pose` 与 localization TF 证据。

默认行为必须保持 read-only：`/api/nav2/proof/refresh` body 不传 opt-in 时，helper 不发布 `/initialpose`，artifact 继续记录 `initialpose_publish_attempted=false` 和 `initialpose_published=false`。

opt-in 只影响 AMCL 初始位姿输入，不改变安全边界：

- 不发送 Nav2 goal。
- 不调用 compute path action/service。
- 不发布 `/cmd_vel`。
- 不调用 `/api/base/*`。
- 不启动 `/api/nav2/start`、`/api/map/start` 或 autonomous execution。
- 不打开 WAVE ROVER/base UART `/dev/ttyS5`。
- 不把定位证据提升成 path execution、fixed-route execution、HIL、safe_to_control 或 delivery_success。

硬件边界依据 `docs/vendor/VENDOR_INDEX.md`：WAVE ROVER 上下位机链路是 UART newline-delimited JSON，Vendor Raspberry Pi 默认路径不是 Orange Pi 固定事实；本轮 helper 不触碰底盘 UART，因此不消费 WAVE ROVER 控制协议。

## 功能点

- Helper 新增显式 opt-in CLI：`--initialpose-opt-in`。
- Helper 新增 pose CLI：`--initialpose-x`、`--initialpose-y`、`--initialpose-yaw`、`--initialpose-frame-id`。
- Helper 默认 body/CLI 不传 opt-in 时完全保持旧 read-only collector 行为。
- Helper opt-in 时只发布一次 `/initialpose`，并在发布后重新采集一次 `/amcl_pose` 与 `map -> odom`、`map -> base_link` TF listener 结果。
- Artifact 明确记录 initialpose 尝试状态、成功状态、pose 数值、边界说明、`/amcl_pose` 采集、TF listener/lifecycle 结果和 safety flags。
- Upper API `/api/nav2/proof/refresh` 从 HTTP body 接收 opt-in 和 pose 参数，传给 helper；默认 body 缺省时不改变旧行为。
- 静态测试覆盖默认不发布、opt-in 参数存在，以及禁止 goal/compute path/base/cmd_vel/UART 的 guard。

## 实际改动

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - 新增 `--initialpose-opt-in`、`--initialpose-x`、`--initialpose-y`、
    `--initialpose-yaw`、`--initialpose-frame-id`。
  - 默认不传 opt-in 时保持 read-only，不发布 `/initialpose`。
  - opt-in 时只发布一次 `/initialpose`，随后采集 post `/amcl_pose`、
    `map -> odom` 与 `map -> base_link` TF listener 结果。
  - Artifact 新增 `initialpose_request`、`initialpose_publish_attempted`、
    `initialpose_published`、`initialpose_boundary`、`localization_tf_observed`
    和对应 command 结果。
  - 修复远端验证暴露的 ROS2 CLI timeout 残留问题：每个 ROS 命令使用独立
    process group，超时后清理整组，避免 `ros2 topic echo/pub` 污染后续 proof。
- `onboard/scripts/upper_robot_api.py`
  - `/api/nav2/proof/refresh` 从 body 读取 `initialpose_opt_in` 和 pose 参数，
    只有 JSON boolean `true` 会透传 opt-in。
  - 默认 body 不传时不追加任何 initialpose 参数。
- `onboard/tests/test_nav2_runtime_proof_helper.py`
  - 覆盖 helper 参数、默认 no initialpose、opt-in initialpose、进程组清理 guard。
  - 继续禁止 `/cmd_vel`、Nav2 goal、compute path、`/api/base/*`、串口入口。
- `docs/navigation/fixed_route_workflow.md`
  - 增补 08:45 no-motion initialpose/localization proof 边界。
- `docs/hardware/board_sensor_stack_smoke.md`
  - 增补 08:45 现场 smoke 边界、允许 body 形状和安全限制。
- `sprints/2026.06.10_08-45_nav2_initialpose_no_motion_proof/artifacts/remote_capture/`
  - 保存远端 preflight、default read-only、opt-in initialpose、orphan cleanup、
    final cleanup 与 helper JSON evidence。

## 验证结果

- `python3 -m pytest onboard/tests/test_nav2_runtime_proof_helper.py`
  - 结果：失败，当前 macOS Python 环境缺 `pytest`。
  - 日志：`/opt/homebrew/Caskroom/miniconda/base/bin/python3: No module named pytest`
  - 定位：环境依赖缺失，不是测试断言失败。
- `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper`
  - 结果：通过。
  - 日志：`Ran 5 tests in 0.045s`，`OK`。
- `python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py --help`
  - 结果：通过。
  - 关键输出包含 `--initialpose-opt-in`、`--initialpose-x`、
    `--initialpose-yaw`、`--initialpose-frame-id`。
- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/scripts/upper_robot_api.py`
  - 结果：通过。
- `git diff --check`
  - 结果：通过，无 whitespace error。

远端 no-motion 验证：

- 远端：`root@192.168.1.11:37878`，`hostname=op-z3-b6.home`。
- 部署方式：只把本轮 helper 复制到
  `/tmp/rober_20260610_0845_nav2_initialpose/o10_amcl_nav2_runtime_proof.py`；
  未覆盖正式仓库脚本，未重启 `upper_robot_api` 服务。
- 默认 read-only rerun artifact：
  `artifacts/remote_capture/default_readonly_nav2_lifecycle_latest_rerun.json`
  - `initialpose_publish_attempted=false`
  - `initialpose_published=false`
  - `initialpose_boundary=default_read_only_not_published_by_collector_no_motion_boundary`
  - `publishes_cmd_vel=false`
  - `calls_base_manual=false`
  - `uses_base_uart=false`
  - `safe_to_control=false`
  - `delivery_success=false`
- Opt-in rerun artifact：
  `artifacts/remote_capture/optin_initialpose_nav2_lifecycle_latest_rerun.json`
  - `initialpose_publish_attempted=true`
  - `initialpose_published=false`
  - pose：`frame_id=map`、`x=0.0`、`y=0.0`、`yaw=0.0`、
    `orientation_z=0.0`、`orientation_w=1.0`
  - `initialpose_publish` 执行但 `TimeoutExpired`，因为当前远端没有 active
    AMCL/Nav2 graph/subscriber 窗口。
  - `map_server_active=false`、`amcl_active=false`、`planner_active=false`、
    `controller_active=false`
  - `/scan_once_observed=false`、`/map_once_observed=false`、
    `/amcl_pose_observed=false`
  - `localization_tf_observed.map_to_odom=false`
  - `localization_tf_observed.map_to_base_link=false`
  - `path_generated=false`
  - `publishes_cmd_vel=false`
  - `calls_base_manual=false`
  - `uses_base_uart=false`
  - `safe_to_control=false`
  - `delivery_success=false`
- 首次远端运行暴露 helper timeout 残留 `ros2 topic echo --once /amcl_pose`
  孤儿进程；已精确清理 PID，并修复 helper process group cleanup。
- 修复后 final cleanup：
  `artifacts/remote_capture/final_cleanup_check_rerun.log`
  - 无 `ros2 topic echo/pub`、`tf2_echo` 残留。
  - `lsof /dev/ttyS5 /dev/ttyACM0` 无输出。
  - `fuser -v /dev/ttyS5 /dev/ttyACM0` 无输出。

## 剩余风险

- 本轮仍是 no-motion localization proof，不是 Nav2 path execution、
  fixed-route execution、HIL、真实底盘运动或 delivery success。
- 远端没有 active AMCL/Nav2 stack 窗口，opt-in `/initialpose` 发布命令超时；
  因此尚未证明 `/amcl_pose` 或 `map -> odom`/`map -> base_link` 可观测。
- `/api/nav2/proof/refresh` body 透传已实现并通过静态测试覆盖，但远端未重启
  `upper_robot_api`，避免触碰可能占用 `/dev/ttyS5` 的服务；远端本轮只直接运行
  helper。
- 指定 pytest 命令因本机缺 `pytest` 未能通过；同一测试文件已用 `unittest`
  入口通过，后续需要在带 pytest 的开发容器或安装 pytest 后补跑原命令。
- 本轮未发送 `/cmd_vel`，未调用 `/api/base/*`，未发送 Nav2 goal，未调用 compute
  path，未打开 WAVE ROVER/base UART `/dev/ttyS5`。

## 完成前自检

- 文件改动均在本轮允许范围内；未回滚 08:15 未提交文档或 artifacts。
- 代码注释新增部分使用中文，说明 opt-in 和 process group cleanup 的原因。
- `docs/` 已同步最新边界，没有把定位 proof 写成 path execution 或 delivery
  success。
- 发现远端验证缺口后已继续定位并修复 timeout 残留问题，重新验证清场结果通过。

本轮记录时间：2026-06-10 07:18:46 CST。

## 返工记录：TF timeout 判定修正

验收发现 `tf2_echo` 是持续输出命令，正常观测到 transform 后也可能被外层
`timeout` 结束并返回 124。原实现复用 `topic_once_observed()`，要求 `ok=True`，
会把“stdout 已有 transform 但 returncode=124”的情况误判为未观测。

本次修正：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - 新增 `tf_echo_transform_observed()`。
  - 判定不要求 `returncode=0` 或 `ok=True`。
  - 只有 stdout/stderr 中同时出现可验证的 `translation` 与 `rotation` 内容，且
    没有 `could not transform`、`invalid frame id`、`lookup/extrapolation`
    等明确失败文本时，才返回 observed。
  - `localization_tf_observed.map_to_odom` 与 `map_to_base_link` 改用该函数。
- `onboard/tests/test_nav2_runtime_proof_helper.py`
  - 新增函数级单元测试：`returncode=124` 且 stdout 含 transform 时判 true。
  - 新增保守性测试：lookup failure 与空输出判 false。
  - 静态 guard 确认 artifact 字段使用 `tf_echo_transform_observed(...)`。

返工验证：

- `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper`
  - 结果：通过。
  - 日志：`Ran 7 tests in 0.041s`，`OK`。
- `python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py --help`
  - 结果：通过。
  - 关键输出仍包含 `--initialpose-opt-in`、`--initialpose-x`、
    `--initialpose-yaw`、`--initialpose-frame-id`。
- `git diff --check`
  - 结果：通过，无 whitespace error。
- 远端 direct-helper rerun：
  - helper：`/tmp/rober_20260610_0845_nav2_initialpose/o10_amcl_nav2_runtime_proof_tf_rework.py`
  - artifact：
    `artifacts/remote_capture/optin_initialpose_tf_rework_latest.json`
  - 当前现场仍无 active AMCL/Nav2 transform 输出，因此
    `localization_tf_observed.map_to_odom=false`、
    `localization_tf_observed.map_to_base_link=false` 是保守正确结果。
  - `initialpose_publish_attempted=true`、`initialpose_published=false`。
  - `publishes_cmd_vel=false`、`calls_base_manual=false`、`uses_base_uart=false`、
    `safe_to_control=false`、`delivery_success=false`、`path_generated=false`。
  - `artifacts/remote_capture/final_cleanup_check_tf_rework.log` 显示无
    `ros2 topic echo/pub`、`tf2_echo` 残留，`lsof/fuser /dev/ttyS5 /dev/ttyACM0`
    无输出。

剩余风险：

- 本次修正覆盖了 `tf2_echo` timeout 但 stdout 已有 transform 的判定缺陷；
  远端现场本次没有 transform stdout，因此没有实测 true 分支，只由本地单元测试覆盖。
- 远端仍没有 active AMCL/Nav2 stack 窗口，initialpose 发布仍超时；本轮仍是
  no-motion localization proof，不是 path execution、fixed-route execution、
  HIL、真实底盘运动或 delivery success。

返工记录时间：2026-06-10 07:23:46 CST。
