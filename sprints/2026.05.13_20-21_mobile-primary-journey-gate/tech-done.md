# Sprint 2026.05.13_20-21 Mobile Primary Journey Gate - Tech Done

## Sprint 类型

- `sprint_type: epic`
- Closeout 时间：2026-05-13 20:21 Asia/Shanghai
- 主证据边界：`software_proof_docker_mobile_primary_journey_gate`

## 实际改动

### Task A：Full-stack mobile primary journey summary/gate

责任 Engineer：`full-stack-software-engineer`

实际改动文件：

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/test_mobile_web_entrypoint.py`
- `mobile/README.md`
- `docs/product/mobile_user_flow.md`

结果：

- 首屏新增“三步主路径”：目标垃圾站、已放入垃圾确认、发车安全 gate。
- Start gate 消费 destination、手动 load confirmation、`command_safety`、cloud/device/browser readiness、operation log、action feedback。
- 缺字段、blocked、offline、pending ACK、manual takeover 都 fail closed。
- `/api/collect` payload 保留兼容字段 `target`。
- ACK 仍只代表 accepted/processing evidence，不是 delivery success。

验证结果：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
Ran 15 tests in 0.004s
OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py
exit 0

git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/fixtures/mobile_web_status.fixture.json mobile/test_mobile_web_entrypoint.py mobile/README.md docs/product/mobile_user_flow.md
exit 0
```

### Task B：Robot metadata-only compatibility fence

责任 Engineer：`robot-software-engineer`

实际改动文件：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`

结果：

- 新增 `mobile_primary_journey_gate` / `mobile_primary_journey_summary` metadata-only compatibility fence。
- metadata-only response 不触发 collect、confirm_dropoff、cancel。
- metadata-only response 不 POST ACK、不推进 `last_ack_id`、不持久化 cursor、不写 cursor override。
- valid collect + mixed metadata 只按 command envelope 执行动作，ACK/cursor 不被 metadata 改写。
- 未改 production `remote_bridge.py`。

验证结果：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
Ran 106 tests in 53.759s
OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
exit 0

git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md
exit 0
```

## Product closeout 判断

Task A/B 证据成立，`software_proof_docker_mobile_primary_journey_gate` 可以作为 Objective 4 的谨慎增量证据：手机入口从 proof 面板堆叠推进到普通用户可理解的三步主路径，并且 robot metadata-only fence 证明手机 summary metadata 不污染 command、ACK 或 cursor。

本轮不提升 Objective 5。没有新增真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或其他真实外部 O5 材料。

## 证据边界

`software_proof_docker_mobile_primary_journey_gate` 只是 Docker/local mobile primary journey software proof。它证明本地 `mobile/web/` shell、fixture/unit test 和 robot metadata-only fence 能围住三步主路径与 fail-closed 行为。

明确 `not_proven`：

- 不是真实 iPhone/Android device behavior。
- 不是 production app。
- 不是真实 PWA install prompt。
- 不是真实 HTTPS/TLS、4G/SIM、OSS/CDN live traffic。
- 不是 production DB/queue、production worker 或 migration。
- 不是 Nav2/fixed-route、WAVE ROVER、HIL、真实投放、真实取消完成或真实送达。
- ACK、HTTP accepted、action receipt 仍只是 accepted/processing evidence，不是 delivery success。

## 偏差和剩余风险

- 本轮按计划未改 Objective 5 外部材料链路，Objective 5 保持约 68%。
- Objective 1/2/3 未调整；真实底盘、导航、任务送达和 HIL 缺口仍在。
- 真实 iPhone/Android、production app、真实 PWA install prompt、真实公网/4G/OSS/CDN/production DB queue 仍需要后续实证。
