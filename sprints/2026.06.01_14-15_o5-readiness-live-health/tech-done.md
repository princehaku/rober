# O5 Readiness Live Health Tech Done

## Sprint Type

sprint_type: micro

## 实际改动

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - 新增 `GET /api/o5/readiness/health` bearer-gated 只读 endpoint。
  - 新增 `trashbot.o5.readiness_health.v1` / `o5_readiness_live_health` 固定 schema/capability。
  - 复用 `production_preflight_payload()` 汇总 O5 readiness，但只返回枚举化 readiness item、blocked/warning/pass 计数、当前 evidence boundary、真实材料缺口和 next required evidence。
  - 固定 `production_ready=false`、`safe_to_control=false`、`sends_commands=false`、`robot_control_executed=false`、`delivery_success=false`。
  - 增加整包敏感 marker 自检，避免向 phone/support/external probe 回显 bearer token、Authorization、URL、本地路径、完整 artifact、checksum、ROS topic、`/cmd_vel`、serial/UART 或 WAVE ROVER 字段。
- `cloud-relay/tests/test_o5_mock_control_plane.py`
  - 新增 readiness health HTTP 测试，覆盖未授权 401、授权响应固定 false-state、安全计数、真实材料缺口和敏感 marker 不外泄。
- `cloud-relay/README.md`
  - 记录 O5 readiness live health endpoint 的 bearer gate、schema、capability、字段边界和 not production-ready 语义。
- `docs/product/remote_4g_mvp.md`
  - 将 `GET /api/o5/readiness/health` 加入 MVP Cloud API，并说明 phone/support/external probe 使用方式、固定 fail-closed 字段和不可声明真实公网/4G/production 完成。

## 用户旅程变化和触点收益

- Phone/support/外部部署探测现在可以读取 O5 live readiness/status，而不是只能依赖离线 preflight 或聊天结论。
- 用户触点明确展示“当前缺什么真实材料”和“下一步要补什么证据”，同时继续禁止 Start/Confirm/Cancel 等控制动作被 readiness 误解为可用。
- 该 endpoint 是 O5 从 mock/software proof 向可部署 live observability 的推进，不提升为真实公网、真实 4G、production DB/queue、OSS/CDN live traffic 或真实手机/browser 完成。

## 接口影响

- 新增 HTTP route：`GET /api/o5/readiness/health`。
- 鉴权：复用 relay bearer gate；未授权返回 401。
- 响应 schema：`trashbot.o5.readiness_health.v1`。
- capability：`o5_readiness_live_health`。
- 响应固定安全字段：`production_ready=false`、`safe_to_control=false`、`sends_commands=false`、`robot_control_executed=false`、`delivery_success=false`。
- 不新增 ROS2 action/topic/service 契约，不触发 robot control，不读硬件。

## 验证结果

```text
$ python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
<no output; exit 0>
```

```text
$ PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior python3 -m unittest cloud-relay/tests/test_o5_mock_control_plane.py
...
----------------------------------------------------------------------
Ran 3 tests in 2.871s

OK
```

```text
$ git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py cloud-relay/tests/test_o5_mock_control_plane.py cloud-relay/README.md docs/product/remote_4g_mvp.md sprints/2026.06.01_14-15_o5-readiness-live-health/tech-done.md
<no output; exit 0>
```

## 前后端 / ROS2 联调结果

- Cloud-relay HTTP 层：已用本地 unittest 启动真实 `ThreadingHTTPServer`，验证 `/api/o5/readiness/health` 401 和 bearer 授权读取。
- Phone/support 触点：接口只返回 phone-safe readiness 摘要，可作为 UI/support 状态来源。
- ROS2：本轮未新增 ROS2 契约，未调用 Nav2、行为 action、底盘或硬件；`robot_control_executed=false` 是显式接口边界。

## 剩余风险

- 未进行真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、OSS/CDN live traffic、真实手机/browser 或外部网络探测。
- endpoint 读取的是本地 runtime env/artifact 所形成的 preflight 语义摘要；真实材料仍需后续通过 external probe / evidence intake / production store queue 证据补齐。
- 不涉及真实运动或底盘控制，本轮不需要机器人侧配合；后续若把 readiness 接入手机 UI，需要保持控制按钮继续由 command_safety 和真实任务状态共同 gate。

## Product Closeout

### 用户价值和产品北极星

本轮把 O5 从“mock/software control plane 已可测”推进到“phone/support/external probe 可读 live readiness/status”的产品状态。北极星仍是普通手机用户只需要看到小车和云端是否具备可发车条件、缺什么证据、为什么不能控制，而不是理解 ROS2、云部署或 preflight 细节。

### OKR 映射和方向判断

- Objective 5：云中转控制面产品化。
- 方向判断：继续，不调整、不暂停、不替换。
- 进度判断：从 `90%+ mock/software completion` 保守调整为 `约 91% software + readiness live health proof`。
- 边界：`real material not_proven` 仍成立；真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、production worker/cutover、OSS/CDN live traffic、真实手机/browser 仍未证明。

### KR 更新和历史归档

- KR1 / KR5 / KR6 获得软件侧 readiness observability 补强：bearer-gated live endpoint、脱敏缺口摘要、fail-closed 控制字段和 graceful degradation 缺口表达更清晰。
- 没有 KR 可移入历史归档区；O5 当前 KR 仍需留在当前推进区，直到真实公网、4G、production store/queue、OSS/CDN 和真实手机/browser 证据齐备。
- 历史记录位置：`docs/process/okr_progress_log.md` 的 `2026-06-01 14-15｜o5-readiness-live-health` 条目，以及 `OKR.md` 第 4 / 4.1 / 5 节。

### 本轮核心抓手

核心抓手是用 `GET /api/o5/readiness/health` 把 O5 的可部署前置条件变成 live、bearer-gated、phone-safe 的状态入口，同时保持 `production_ready=false`、`safe_to_control=false`、`sends_commands=false`、`robot_control_executed=false`、`delivery_success=false`。

### 需要做什么

1. 下一步由 Full-Stack 继续把 readiness health 接入手机/支持侧只读状态展示，但控制按钮必须继续由 command safety 和真实任务状态共同 gate。
2. O5 真实材料采集仍按 `docs/interfaces/o1_o5_90_evidence_boundary.md` 推进：真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、OSS/CDN live traffic、真实手机/browser。
3. 若 production store/queue 或 external probe 接入，必须继续保持敏感信息脱敏和 fail-closed 字段不被 UI 文案弱化。

### 优先级和验收口径

- 当前排序：O1 / O5 / O6 并列约 91%，O7 约 95%；O5 不再单独低于 O1/O6，但仍是最高优先级梯队。
- 验收口径：本轮只验收 software/readiness live health proof；不得表述为真实公网、真实 4G、production DB/queue、OSS/CDN live traffic 或真实手机/browser 完成。

### 对应责任 Engineer

- 主责：User Touchpoint Full-Stack Engineer。
- 后续真实云/production store 联调需要 Full-Stack 主责，Robot Software 只在 robot ACK / outbound polling / command result 与上车链路接入时参与；Hardware Infra 仅在真实 4G/SIM 或板端网络材料采集时参与。

### 风险、阻塞和证据链

- 风险：readiness endpoint 可能被误读为“可控制”或“生产就绪”，因此 OKR 和接口边界继续固定所有安全字段为 false。
- 阻塞：真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、OSS/CDN live traffic、真实手机/browser 尚未提供。
- 已补证据链：`py_compile` 通过、O5 mock control plane unittest `Ran 3 tests ... OK`、scoped diff-check 通过、OKR 当前快照和 `docs/process/okr_progress_log.md` 已更新。

### Sprint 文档同步

- 已更新本 `tech-done.md` 的 Product closeout。
- 已更新 `OKR.md` 当前进度快照和最高优先级排序。
- 已更新 `docs/process/okr_progress_log.md` 最新条目。
