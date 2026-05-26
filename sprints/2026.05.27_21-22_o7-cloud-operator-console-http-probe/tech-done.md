# O7 Cloud Operator Console HTTP Probe

sprint_type: micro

## 实际改动

- 在 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py` 增加 `trashbot.o7.operator_console.v1` fail-closed builder，并在真实 `make_handler()` runtime 暴露无需 bearer 的 `GET /api/o7/operator-console`。
- 在 `cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py` 让 cloud wrapper 的活动导出指向 onboard builder，避免 `python -m ros2_trashbot_cloud_relay.remote_cloud_relay` 和 onboard HTTP handler 继续漂移。
- 在 PC workstation 增加 `GET /api/o7/cloud-operator-console-probe?baseUrl=<url>`，只允许 `http://127.0.0.1`、`http://localhost`、`http://[::1]` 本机回环 HTTP base URL，并对 schema、fetch、危险 true 字段全部 fail-closed。
- 在 O7 Previews 页面增加只读 `Cloud operator console probe` 区域，只展示 probe status、source base URL、remote schema、cloud API status、operator mode、KR ids、关键 false fields、blocked reasons 和 not proven。
- 更新 `docs/product/pc_tools_workstation.md`、`docs/interfaces/o7_realtime_operator_console.md`、`pc-tools/README.md`，明确该链路只是 local HTTP contract proof，不是公网云、4G、生产云、机器人在线或 O7 完成证明。

## 验证结果

- `cd pc-tools/workstation && npm run build`：通过，Vite build 输出 `✓ built in 2.10s`。
- `cd pc-tools/workstation && npm run test`：通过，`Test Files 2 passed (2)`，`Tests 33 passed (33)`。
- `cd pc-tools/workstation && npm run lint`：通过，无 ESLint 输出。
- `PYTHONPATH=onboard/src/ros2_trashbot_behavior python -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`：通过，`Ran 104 tests in 31.421s`，`OK`。

## 剩余风险

- 本轮没有连接公网 HTTPS/TLS、4G/SIM、production DB/queue、ROS2 graph、真实云端、真实机器人或硬件；所有真实能力字段保持 false。
- PC probe 只证明本机回环 HTTP contract 能被拉取和 fail-closed 检查，不证明 O7 实时地图、电梯状态、路线回放、标注、语音、手控/寻路任一真实能力完成。
