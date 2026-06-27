# Nav2 latest 轮速缺口只读回放

sprint_type: micro

## 实际改动

- `onboard/scripts/upper_robot_api.py`
  - 新增 `enrich_nav2_goal_execution_latest_payload()`，让 `/api/nav2/goal/execution/latest` 在只读读取旧 artifact 时派生 `nav2_goal_execution_proven`、`nav2_goal_execution_not_proven` 和 `hil_pass`。
  - 当旧 artifact 是 `goal_succeeded` 但同窗口 `base_feedback_summary.wheel_feedback_lr_nonzero_proven=false` 时，latest 回包会补出 `wheel_feedback_lr_nonzero` 缺口，并把嵌套 `latest_result.nav2_goal_execution_proven/hil_pass` 压回 false。
  - 该逻辑不重写 artifact、不启动 Nav2、不发送 `T=1/T=11/T=13`、不调用 `/cmd_vel`、manual、delivery 或 stop。
- `onboard/tests/test_upper_robot_api.py`
  - 新增旧 artifact 回放单测，覆盖旧记录自称 `nav2_goal_execution_proven=true/hil_pass=true` 但 wheel raw L/R 未非零时，latest 读回必须保持未证明。
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录 2026-06-27 起 Nav2 latest 只读回放会派生 wheel raw L/R 缺口，避免把旧 action succeeded 误读为自动驾驶完成。

## 验证结果

- 通过：`python3 -m unittest onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_nav2_goal_execution_latest_derives_wheel_lr_gap_from_old_artifact`
- 通过：`python3 -m unittest onboard.tests.test_upper_robot_api`
- 通过：`git diff --check`
- 通过：同步 `onboard/scripts/upper_robot_api.py` 到 `root@192.168.1.11:37878`，重启 8787 上位机 API 后只读调用 `/api/nav2/goal/execution/latest`，返回 `nav2_goal_execution_proven=false`、`nav2_goal_execution_not_proven=["wheel_feedback_lr_nonzero","delivery_success","operator_dropoff_confirmation"]`、`hil_pass=false`。
- 通过：PC 7001 代理只读调用 `/api/robot-control/nav2/goal/execution/latest?baseUrl=http://192.168.1.11:8787`，返回 `proxy_status=latest_loaded`、`nav2_goal_execution_proven=false`、`hil_pass=false`、`base_command_nonzero_count=49`、`base_feedback_sample_count=239`、`base_feedback_latest_left_speed=0`、`base_feedback_latest_right_speed=0`。
- 现场只读 SSH 复核：
  - `/dev/video0` 为 `cedrus`，真实 DV20 UVC 摄像头为 `/dev/video1`，兄弟 `/dev/video2` 为 metadata 节点。
  - `/api/camera/first-frame/probe` 默认与 `auto_format_fallback=true` 全矩阵均为 `open_ok=true/read_ok=false/failure_reason=capture_read_call_timeout`，没有发现其它进程占用 `/dev/video1`。
  - `runtime/nav2_goal_execution_latest.json` 显示上次 Nav2 action `goal_succeeded`，发出 49 条非零 PWM 底盘命令，T=1001 反馈样本 239 条但 wheel raw L/R 仍为 `0/0`，IMU pitch 有变化。

## 剩余风险

- 本轮未在未获现场安全确认的情况下执行真实 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 摄像头仍未读到真实首帧；当前证据指向 UVC 设备 open 后不吐帧，不是浏览器独占。仍需现场检查 USB、摄像头输入/供电，或换 known-good UVC 复测。
- 自动驾驶真实可动仍需现场勾选安全确认后按当前策略重跑路线，并在同一执行窗口观察 wheel raw L/R 非零。
