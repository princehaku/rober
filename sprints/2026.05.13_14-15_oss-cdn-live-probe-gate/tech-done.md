# Sprint 2026.05.13_14-15 OSS/CDN Live Probe Gate - Tech Done

## Sprint 声明

- sprint_type: epic
- 主目标：Objective 5 云中转 + OSS/CDN 数据通路产品化。
- 证据边界：`software_proof_docker_oss_cdn_live_probe_gate`。
- 当前时间：2026-05-13 14:16 Asia/Shanghai。

## 实际改动

### Task A - Full-stack OSS/CDN Live Probe Gate

责任 Engineer：`full-stack-software-engineer`。

改动文件：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `cloud-relay/README.md`
- `docs/product/remote_4g_mvp.md`
- `docs/product/cloud_4g_infrastructure.md`

结果：

- 新增 `trashbot.oss_cdn_live_probe` schema v1、artifact writer、validator、preflight consumption、CLI/env 支持。
- 当前没有真实 OSS/CDN 凭证、真实云、4G/SIM 或公网 CDN 回源证据时，valid artifact 仍保持 `production_ready=false`、`overall_status=blocked`、`live_probe_complete=false`。
- 文档同步说明 live probe gate 只能作为上线前执行入口和 blocked-by-design proof，不等于真实 OSS/CDN live traffic。

### Task B - Robot Metadata Compatibility Fence

责任 Engineer：`robot-software-engineer`。

改动文件：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`

结果：

- remote bridge/protocol metadata-only fixtures 覆盖 `oss_cdn_live_probe`、`oss_cdn_live_probe_artifact`、`cdn_live_probe`。
- 证明这些字段不触发 backend action、不 POST ACK、不推进或持久化 cursor。
- 接口文档明确这些字段是 phone/support metadata，不属于 command/status/ACK envelope。

### Task C - Product Closeout

责任 Owner：`product-okr-owner`。

改动文件：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.13_14-15_oss-cdn-live-probe-gate/tech-done.md`
- `sprints/2026.05.13_14-15_oss-cdn-live-probe-gate/side2side_check.md`
- `sprints/2026.05.13_14-15_oss-cdn-live-probe-gate/final.md`

结果：

- Objective 5 从约 65% 保守上调到约 67%。
- Objective 1/2/3/4 不调整。
- closeout 明确本轮只形成 Docker/local software proof，不声明真实 OSS/CDN live traffic、真实云、真实 4G/SIM、production DB/queue、真实手机设备/browser、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

## 验证结果

### Task A 验证

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
Ran 64 tests in 7.096s OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py
OK

git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py cloud-relay/README.md docs/product/remote_4g_mvp.md docs/product/cloud_4g_infrastructure.md
OK
```

### Task B 验证

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
Ran 88 tests in 44.322s OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
exit 0

git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md
exit 0
```

### Task C 验收命令

```text
test -f OKR.md && test -f docs/process/okr_progress_log.md && test -f docs/product/remote_4g_mvp.md && test -f docs/interfaces/ros_contracts.md
exit 0

git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.13_14-15_oss-cdn-live-probe-gate
exit 0
```

## 偏差

- 无代码或测试改动由 Task C 执行。
- 本轮 closeout 使用 Task A/B 已返回的验证摘要作为工程证据，Task C 只运行计划指定的路径存在与 scoped diff check 验收。

## 剩余风险

- 没有真实 OSS/CDN 凭证、真实 OSS upload、真实 CDN 回源或 live traffic。
- 没有真实云、真实 4G/SIM、真实 HTTPS/TLS 公网入口。
- 没有 production DB/queue、migration、worker、多实例一致性、transaction isolation、backup/recovery。
- 没有真实手机设备/browser、production app 或真实 PWA install prompt。
- 没有 Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。
- ACK 仍只是 accepted/processing evidence，不是 delivery success。
