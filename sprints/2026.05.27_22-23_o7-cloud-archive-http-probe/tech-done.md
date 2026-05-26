# O7 Cloud Archive HTTP Probe

## sprint_type

micro

## 实际改动

- `remote_cloud_relay.py` 新增公开只读 `GET /api/o7/cloud-archive/tasks` contract：不要求 bearer，不读取真实 archive store，不执行控制动作，固定返回 `archive_status=blocked_not_proven`、空任务、`real_cloud_archive_connected=false`、`playback_available=false`、`submit_enabled=false` 和所有危险控制/语音/标注字段 false。
- PC workstation 新增 `GET /api/o7/cloud-archive/tasks-probe?baseUrl=<local-loopback-url>`：只允许 `http://127.0.0.1`、`http://localhost`、`http://[::1]`，只读拉取远端 `/api/o7/cloud-archive/tasks`，扫描 schema、task count、selected/latest、inspector 状态和危险 true 字段。
- `O7 Previews` 新增 Cloud archive tasks probe 区块，展示 probe 状态、remote schema、archive status、task count、selected/latest、inspector 状态、dangerous true fields、关键 false fields、blocked reasons 和 not proven。
- 同步更新 `docs/interfaces/o7_cloud_archive_task_api.md`、`docs/interfaces/o7_realtime_operator_console.md`、`docs/product/pc_tools_workstation.md` 和 `pc-tools/README.md`，明确该 contract 不等于真实云 archive、真实路线回放、真实标注提交、真实 ASR/TTS、真实手控/寻路或真实控制。

## 验证结果

- `cd pc-tools/workstation && npm run build`：通过。Vite 输出 `✓ 31 modules transformed`、`✓ built in 2.17s`，随后 server TypeScript 编译通过。
- `cd pc-tools/workstation && npm run test`：通过。`Test Files 2 passed (2)`、`Tests 34 passed (34)`。
- `cd pc-tools/workstation && npm run lint`：通过，ESLint 无输出。
- `PYTHONPATH=onboard/src/ros2_trashbot_behavior python -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`：通过。`Ran 105 tests in 31.861s`、`OK`。
- `git diff --check -- onboard/src/ros2_trashbot_behavior pc-tools/workstation docs/product/pc_tools_workstation.md docs/interfaces/o7_cloud_archive_task_api.md docs/interfaces/o7_realtime_operator_console.md pc-tools/README.md sprints/2026.05.27_22-23_o7-cloud-archive-http-probe`：通过，无空白错误。

## 剩余风险

- 当前只证明本机 HTTP contract 和 PC probe，可用于 O7 preview/diagnostic；不证明真实公网云、production DB/queue、真实 archive store、OSS/CDN、机器人在线、ROS2、硬件、路线回放播放、标注提交、ASR/TTS 播放或手控/寻路可用。
- cloud relay archive tasks 当前没有真实持久化数据源，因此任务列表按要求 fail-closed 为空。
