# Cloud Phone Command API Mainline Final

## 结果

本轮完成 `cloud_phone_command_api` 主链路，Objective 5 从“只读 evidence/review/handoff metadata”向真实任务级 command enqueue 前进。

交付内容：

- Relay：新增 bearer-gated `/api/commands/collect`、`/api/commands/confirm-dropoff`、`/api/commands/cancel`。
- Relay：手机请求规范化为既有 command store 合同，robot 继续 outbound polling。
- Relay：command store 写入失败 fail closed，返回 `503 command_store_unavailable`，不返回 queued receipt。
- Mobile：主动作 endpoint 切到 `/api/commands/*`，提交 cloud command envelope。
- Mobile：新增 queued receipt 面板，明确不是 delivery/dropoff/cancel terminal result。
- Docs：同步 `remote_4g_mvp`、`cloud_4g_infrastructure`、`cloud-relay/README`、`mobile_user_flow`。

## OKR 进度

- Objective 1：保持约 81%。本轮不碰 WAVE ROVER/UART/HIL/2D LiDAR/ToF。
- Objective 2：保持约 99%。本轮不证明真实 task record、route/elevator field pass、dropoff/cancel terminal result 或 delivery success。
- Objective 3：保持约 99%。本轮不证明真实路线采集、Nav2/fixed-route runtime 或 route completion signal。
- Objective 4：保持约 99%。`mobile/web` 有任务级入口和 receipt，但仍不是真实 iPhone/Android device behavior 或 true phone/browser proof。
- Objective 5：从约 68% 提升到约 72%。依据是新增真实可调用的 phone -> cloud command enqueue API 和 mobile endpoint 接入；边界仍是 `software_proof_docker_cloud_phone_command_api_gate`。

## 验证

- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`：通过。
- `PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py -k cloud_phone_command_api`：`Ran 4 tests in 2.769s OK`。
- `node --check mobile/web/app.js`：通过。
- `PYTHONPATH=mobile python3 -m unittest mobile/web/test_mobile_web_entrypoint.py -k cloud_phone_command_api`：`Ran 2 tests ... OK`。
- Scoped `git diff --check`：通过。

## 剩余风险

- 不是公网 HTTPS/TLS、真实 4G/SIM、OSS/CDN live traffic、production DB/queue 或 production worker/cutover 证明。
- 不是真实手机/browser、PWA install prompt/userChoice、HIL、Nav2/fixed-route、WAVE ROVER/UART 或真实送达证明。
- 命令入队不等于机器人执行完成；store unavailable 已 fail closed，但真实 production DB/queue 的持久化、告警、重试和多实例一致性仍未验证。
- 下一轮应推进真实部署链路或 command result reconciliation。
