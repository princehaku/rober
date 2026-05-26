# O7 Cloud Archive Fixture-Backed Relay Tech Done

## sprint_type

micro

## 实际改动

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - 为 `GET /api/o7/cloud-archive/tasks` 增加 `TRASHBOT_O7_CLOUD_ARCHIVE_TASKS_JSON` 只读 fixture 输入。
  - 未配置、读取失败、坏 JSON、schema 不符或 unsafe fixture 时继续返回原 blocked empty contract。
  - 安全 fixture 可生成非空 `task_list`、`selected_task`、`latest_task`、`safe_summaries`、`route_replay_inspector`、`labeling_queue_inspector`、`voice_asr_tts_inspector` 和 `safe_command_inspector` 摘要。
  - 验收修复：route replay frame 的 `frame_index/timestamp_ms/x_m/y_m/yaw_rad/speed_mps` 和 navigate goal 的 `x_m/y_m/yaw_rad` 统一走安全数值转换，malformed fixture 不会触发 500，非有限或非数值字段降级为 `index` 或 `None`。
  - 所有真实云、语音、标注、控制、机器人 ACK、硬件和成功字段继续固定 false。
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
  - 覆盖未配置仍空、配置安全 fixture 后非空但危险字段 false、不安全 fixture 仍 blocked empty、malformed numeric fixture 不 500 且数值字段被安全化。
- `docs/interfaces/o7_cloud_archive_task_api.md`
  - 记录 cloud relay env fixture-backed contract、fail-closed 规则和真实能力边界。
- `docs/interfaces/o7_realtime_operator_console.md`
  - 补充 O7 console 对 cloud relay archive fixture 模式的消费边界。
- `pc-tools/README.md`
  - 补充 PC probe 可探测 relay runtime fixture 摘要，但仍不是生产能力。
- `cloud-relay/README.md`
  - 补充部署侧 env 配置、忽略 query path、安全拦截和未证明范围。

## 验证结果

- `cd onboard && python3 -m pytest src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py -k "o7_cloud_archive"`
  - 首次运行失败于当前 `/opt/anaconda3` pytest 缺少 `iniconfig`，未进入项目测试。
  - 安装当前用户 Python 依赖 `iniconfig` 后重跑，验收修复后最终结果：`4 passed, 105 deselected in 2.46s`。
- `git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o7_cloud_archive_task_api.md docs/interfaces/o7_realtime_operator_console.md pc-tools/README.md cloud-relay/README.md sprints/2026.05.27_29-30_o7-cloud-archive-fixture-backed-relay/tech-done.md`
  - 通过，无输出。
- `python3 -m compileall -q onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
  - 通过。

## 剩余风险

- 本轮没有打通真实生产云 archive、RTC/视频、真实标注提交、真实 ASR/TTS runtime、真实手控/寻路、机器人 ACK 或硬件 HIL。
- `cloud_runtime_fixture_connected=true` 只表示 relay runtime 读取了本机脱敏 fixture；不得解释为 `real_cloud_archive_connected=true`。
- 本地 Docker CLI 不可用，未运行 Docker/Humble build；本轮验证范围是 Python 单测和语法编译。
