# Sprint 2026.05.13_02-03 Cloud Relay Self-Contained Gate - Tech Done

## 状态

- 阶段：tech-done
- sprint_type: epic
- 主 Objective：Objective 5 云中转 + OSS/CDN 数据通路产品化（历史 O6）
- 证据边界：`software_proof_docker_cloud_relay_self_contained_gate`
- 结论：完成。证据只覆盖 Docker/local self-contained runtime，不覆盖真实云、4G、OSS/CDN 实流量或 HIL。

## 实际改动

### Task A - full-stack-software-engineer

改动范围：

- `cloud-relay/src/ros2_trashbot_cloud_relay/__init__.py`
- `cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py`
- `cloud-relay/docker/Dockerfile`
- `cloud-relay/docker-compose.yml`
- `cloud-relay/scripts/docker_smoke.sh`
- `cloud-relay/README.md`
- `docs/product/cloud_4g_infrastructure.md`
- `docs/product/remote_4g_mvp.md`
- `mobile/README.md`
- `README.md`

实际结果：

- `cloud-relay/` 具备自包含 Python runtime module 入口，Dockerfile/compose/smoke 使用新 module 入口运行 relay。
- 保持 `trashbot.remote.v1` commands/status/ack 语义，不新增第二套协议。
- 产品文档同步新 `cloud-relay/` 入口，并保留真实生产云/4G/OSS/CDN 未证明口径。

验证结果：

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
Ran 63 tests ... OK
备注：保留一个既有 ResourceWarning，命令 exit 0。

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior python3 -m py_compile cloud-relay/src/ros2_trashbot_cloud_relay/__init__.py cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py
通过

bash cloud-relay/scripts/docker_smoke.sh
通过：覆盖 build、start、/readyz、/healthz、production preflight blocked with production_ready=false、command/status/ACK、backup/restore drill、restart recovery。

git diff --check -- cloud-relay docs/product/cloud_4g_infrastructure.md docs/product/remote_4g_mvp.md docs/interfaces/ros_contracts.md mobile/README.md README.md
通过
```

### Task B - robot-software-engineer

改动范围：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`

实际结果：

- 新增 compatibility fence：cloud-relay self-contained runtime metadata 不污染 `trashbot.remote.v1` command/status/ack envelope。
- 确认 metadata-only blocked response 不触发 robot action、不 ACK、不推进 cursor。
- 确认 ACK 仍只表示 command envelope accepted / processing / failed，不升级为 delivery success。
- 修复测试中旧 `src/...` 路径假设为当前 `onboard/src/...`。

验证结果：

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_static.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py
Ran 97 tests in 45.900s OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py
通过

git diff --check -- onboard/src/ros2_trashbot_behavior onboard/src/ros2_trashbot_bringup
通过
```

### Task C - product-okr-owner

改动范围：

- `OKR.md`
- `sprints/2026.05.13_02-03_cloud-relay-self-contained-gate/tech-done.md`
- `sprints/2026.05.13_02-03_cloud-relay-self-contained-gate/side2side_check.md`
- `sprints/2026.05.13_02-03_cloud-relay-self-contained-gate/final.md`
- `docs/process/okr_progress_log.md`

实际结果：

- 将本轮工程证据收口为 Docker/local self-contained gate。
- Objective 5（历史 O6）从约 53% 保守上调到约 55%。
- 明确 `production_ready=false`，不得写成真实云、4G、OSS/CDN 或 HIL 证据。

## 偏差

- 原计划允许 Product 如需修正文档口径时可改 `docs/product/cloud_4g_infrastructure.md` 与 `docs/product/remote_4g_mvp.md`；本轮 engineer 已完成产品文档同步，Product 未再改 `docs/product/**`。
- 未执行 broad regression，符合本轮围栏化验证要求。

## 剩余风险

- 仍没有真实云、公网 HTTPS/TLS、真实 4G/SIM、生产 DB/queue、多实例一致性或生产备份/灾备。
- 仍没有真实 OSS upload、CDN origin fetch 或 OSS/CDN 实流量。
- 仍没有正式手机 app/真实手机设备验收。
- 仍没有 WAVE ROVER、真实串口、HIL、Nav2/fixed-route 上车运行或真实送达闭环。
