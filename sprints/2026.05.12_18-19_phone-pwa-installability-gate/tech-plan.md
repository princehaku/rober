# Sprint 2026.05.12_18-19 Phone PWA Installability Gate - Tech Plan

## 状态

- 阶段：tech-plan
- 创建时间：2026-05-12 18:19 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 兼容性围栏：`robot-software-engineer`
- 目标 evidence boundary：`software_proof_docker_phone_pwa_installability_gate`

## 技术目标

把 `operator_gateway` 的本地 fallback 手机页推进到 PWA/installability software proof，同时保持 API 和 command safety 语义不退化：

- manifest 可被手机浏览器识别；
- mobile meta 完整；
- service worker 只提供静态 shell route；
- `/api/*` 动态状态、diagnostics、commands 和 ACK 不被离线缓存污染；
- 离线 shell 保持 phone-safe 且主操作 disabled；
- 证据边界明确停留在 Docker/local software proof。

## 计划改动文件范围

`full-stack-software-engineer` 允许改动：

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_static.py`
- 如必须新增 focused helper：`scripts/phone_pwa_installability_gate.py`
- 如必须新增 helper 测试：对应单个 helper/test 文件
- `docs/product/mobile_user_flow.md`
- `sprints/2026.05.12_18-19_phone-pwa-installability-gate/tech-done.md`

`robot-software-engineer` 允许改动：

- 原则上不改实现；若 Full-stack 改动影响 command/status/ack compatibility，可仅补充或调整 compatibility fence 测试。
- 如确需改动，必须先在子 agent 输出中说明接口影响和文件范围。

`product-okr-owner` 后续允许改动：

- `sprints/2026.05.12_18-19_phone-pwa-installability-gate/side2side_check.md`
- `sprints/2026.05.12_18-19_phone-pwa-installability-gate/final.md`
- `OKR.md`

禁止范围：

- 不改硬件、launch 串口参数、WAVE ROVER 配置或 Nav2/fixed-route 行为。
- 不新增真实云、真实 4G/SIM、TLS、公网入口、STS、OSS/CDN 实流量。
- 不缓存 `/api/*`、command POST、diagnostics、ACK 或动态 status。
- 不把 PWA 壳层写成正式 app、真实设备验收或生产账号系统。

## 设计要点

1. Manifest route
   - 提供 `manifest.webmanifest` 或等价静态 route。
   - 字段至少包含 `name`、`short_name`、`start_url`、`scope`、`display`、`theme_color`、`background_color`、`icons`。
   - `start_url` 和 `scope` 必须落在 operator shell，不指向 `/api/*`。

2. Mobile meta
   - HTML head 增加 viewport、theme color、apple mobile web app capable/title/status bar、description。
   - 不改变已有 command safety 的首屏信息结构。

3. Service worker
   - 提供 shell route 和静态资源缓存。
   - 对 `/api/`、`/api/status`、`/api/diagnostics`、`POST /api/collect`、`POST /api/dropoff/confirm`、`POST /api/cancel` 必须 bypass cache 或 network-only。
   - 失败时返回离线 shell，不返回过期 API JSON。

4. Offline shell copy
   - 文案说明“当前只能查看离线壳层，需要重新连接后才能控制机器人”。
   - Start、Confirm dropoff、Cancel disabled。
   - Diagnostics 可作为安全入口或提示重新连接，但不能误解锁主操作。

5. Evidence artifact
   - 若新增 helper，输出 JSON 到 sprint evidence 目录。
   - Artifact 必须写明 `evidence_boundary=software_proof_docker_phone_pwa_installability_gate` 和 `not_proven` 列表。

## 接口影响

- `/api/status` payload 不应因 PWA 改动变更 schema。
- `/api/diagnostics` payload 不应因 PWA 改动变更 schema。
- Command endpoints 不应新增 service worker 离线 replay、queue 或缓存行为。
- ACK 语义保持 command accepted/processing evidence，不等于 delivery success。
- Browser/static serving 可新增 manifest/service-worker/offline shell route。

## 责任拆分

Task A - Full-stack implementation and tests：

- Owner：`full-stack-software-engineer`
- 目标：实现 manifest、mobile meta、service worker shell route、offline shell copy、API bypass tests、docs/product 同步和 `tech-done.md`。
- 输出：改动文件、targeted test 输出、py_compile 输出、helper 输出或不新增 helper 的说明、scoped diff check 输出、剩余风险。

Task B - Robot compatibility fence：

- Owner：`robot-software-engineer`
- 触发条件：只有当 Task A 涉及 command/status/ack API 或 service worker request routing 可能影响 robot bridge 兼容性时执行。
- 目标：确认 PWA shell 不改变 command/status/ack envelope，不缓存 ACK/status，不触发额外 local action，不推进 cursor。
- 输出：验证命令、结果和剩余风险。

Task C - Product acceptance：

- Owner：`product-okr-owner`
- 目标：核对证据边界，更新 `side2side_check.md`、`final.md` 和 `OKR.md`。
- 输出：O5 是否保守上调、O6 是否仅作为支撑、未完成事项。

## 验收命令

规划任务本身不运行工程测试。实现阶段只允许围栏验证：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_static.py
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py
```

若实现新增或修改 browser acceptance / PWA helper，则只运行对应单个 helper 或测试，例如：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/phone_pwa_installability_gate.py --output-dir sprints/2026.05.12_18-19_phone-pwa-installability-gate/evidence
```

最后运行 scoped diff check，范围只包含本轮改动文件：

```bash
git diff --check -- src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_static.py docs/product/mobile_user_flow.md sprints/2026.05.12_18-19_phone-pwa-installability-gate/tech-done.md
```

如新增 helper 或 helper test，必须把对应文件追加到 `git diff --check -- ...`。

## 验收口径

通过条件：

- Manifest、mobile meta、service worker、offline shell 和 API bypass 均有测试或 helper evidence。
- Existing HTTP/static tests 通过。
- `operator_gateway_http.py` py_compile 通过。
- Scoped diff check 通过。
- `docs/product/mobile_user_flow.md` 已同步 PWA/installability 证据边界。
- `tech-done.md` 写清实际改动、验证结果、失败定位和剩余风险。

不通过条件：

- Service worker 缓存或离线 replay `/api/*`、commands、diagnostics、ACK 或 status。
- 离线 shell 让 Start/Confirm/Cancel 可执行。
- 文案暴露 raw JSON、ROS topic、`/cmd_vel`、serial、baudrate、token、Authorization header、OSS secret 或硬件参数。
- 把本轮写成正式 app、真实手机设备验收、真实云/4G、HIL 或真实送达。

## 风险和缓解

- 风险：service worker 缓存 API 导致 stale command safety。缓解：单测检查 `/api/*` bypass，helper artifact 记录 `api_cache_policy_status=passed`。
- 风险：离线 shell 被用户理解为可控制机器人。缓解：offline copy 明确“需要重新连接”，主操作 disabled。
- 风险：PWA 入口扩大成真实 app 叙事。缓解：docs 和 sprint final 固定 `software_proof_docker_phone_pwa_installability_gate`，`not_proven` 写清真实设备/云/硬件缺口。
- 风险：实现为 UI-only，忘记 docs 同步。缓解：`docs/product/mobile_user_flow.md` 是 Task A 必改文件。

## 子 Agent 启动建议

当前 tech-plan 已具备 owner、文件范围、接口影响、验收命令和风险边界。下一步进入 implementation，应启动 1 个 `full-stack-software-engineer` 子 agent 单线闭环 Task A。Task B 仅在 Task A 返回 API/cache 兼容性风险时启动或作为只读围栏补充。

