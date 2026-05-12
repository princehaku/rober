# Sprint 2026.05.12_18-19 Phone PWA Installability Gate - Tech Done

## 状态

- 阶段：tech-done
- 完成时间：2026-05-12 18:55 Asia/Shanghai
- Owner：`full-stack-software-engineer`
- Evidence boundary：`software_proof_docker_phone_pwa_installability_gate`

## 实际改动

- `operator_gateway_http.py`
  - 新增 `GET /manifest.webmanifest`，字段包含 `name`、`short_name`、`start_url`、`scope`、`display`、`theme_color`、`background_color`、`icons`，且 `start_url` / `scope` 不指向 `/api/*`。
  - 新增 `GET /service-worker.js`，只缓存静态 shell；`/api/*`、`/robots/*`、command、ACK、diagnostics 和所有非 GET 请求走 network/no-store。
  - 新增 `GET /offline.html`，离线壳层显示手机断开和重新连接提示，Start/Confirm Dropoff/Cancel 保持 disabled。
  - HTML head 增加 manifest link、theme color、description、Apple mobile web app capable/title/status bar meta，并注册 service worker。
  - 新增安全 SVG icon routes 供 manifest 引用，不暴露硬件、ROS、串口、凭证或 raw JSON 细节。
- `test_operator_gateway_http.py`
  - 覆盖 manifest 字段、`start_url`/`scope` 非 API、service worker API/command/ACK bypass、offline shell disabled primary actions、PWA 静态路由不回归 `/api/status` 和 `/api/collect` contract。
- `test_operator_gateway_static.py`
  - 增加静态断言，确保 PWA 常量、路由、service worker registration、offline shell 和 API bypass policy 保留在源码中。
- `docs/product/mobile_user_flow.md`
  - 新增 Local PWA Installability Gate，写清 manifest、mobile meta、service worker、offline shell、API bypass 和本轮证据边界。

未新增 `scripts/phone_pwa_installability_gate.py`；本轮 HTTP/static tests 已覆盖 P0 installability 和 cache policy，不需要额外 helper artifact。

## 用户旅程变化

普通手机用户打开本地 fallback 页面时，浏览器可以识别 manifest/mobile meta 并注册静态 shell service worker。离线或断连时，用户看到的是“手机已断开、需要重新连接”的壳层和 disabled 主操作，而不是可误触的控制按钮、raw JSON、ROS topic、串口、baudrate、token、Authorization 或 OSS secret。

## 接口影响

- 新增静态路由：`/manifest.webmanifest`、`/service-worker.js`、`/offline.html`、`/pwa-icon-192x192.svg`、`/pwa-icon-512x512.svg`。
- 未修改 `/api/status`、`/api/diagnostics`、`POST /api/collect`、`POST /api/dropoff/confirm`、`POST /api/cancel` payload schema。
- Service worker 明确不缓存或 replay API、diagnostics、command POST、remote command/status/ack endpoints 或 ACK/status JSON。
- ACK 语义未改变：仍只代表 command accepted/processing evidence，不代表 delivery success、Nav2/fixed-route、真实云、真实 4G、WAVE ROVER motion 或 HIL。

## 验证结果

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_static.py
..............................................
----------------------------------------------------------------------
Ran 46 tests in 20.155s

OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py
exit 0
```

## 失败定位

- 首轮 unittest 失败在 `test_pwa_static_shell_does_not_expose_robot_or_secret_details` 的源码切片：测试匹配到后续 `SERVICE_WORKER_JS` 路由引用，未定位到常量定义。
- 修复：将静态测试切片锚点改为 `SERVICE_WORKER_JS =`，并从该位置查找后续 `\nHTML =`。
- 修复后同一围栏 unittest 通过。

## 剩余风险

- 本轮没有真实 iPhone/Android 设备、Safari/Chrome install prompt 或 home-screen 安装验证。
- 本轮没有真实云、真实 4G/SIM、HTTPS/TLS 公网入口、生产账号、真实 OSS/CDN、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。
- Service worker 策略已用 HTTP/static tests 围住，但仍需后续真实手机浏览器验收确认平台差异。

## Task B Robot Compatibility Fence

- 完成时间：2026-05-12 16:28 Asia/Shanghai
- Owner：`robot-software-engineer`
- Evidence boundary：`software_proof_docker_phone_pwa_installability_gate`

### 兼容性结论

- 未修改产品代码或 robot bridge 代码。
- 未补充测试代码；现有 `test_remote_bridge.py` 已覆盖 command/status/ack envelope、ACK 失败不持久化 cursor、云端/鉴权/畸形响应不触发本地 action 且不推进 `last_ack_id`。
- `test_operator_gateway_http.py` 已覆盖 PWA 静态路由不回归 `/api/status` 与 command contract，service worker 对 `/api/*`、`/robots/*`、command 与 ACK route 走 `no-store` bypass。
- Task A 的 PWA shell 未改变 command/status/ack envelope，未缓存 ACK/status，未触发额外 local action，未推进 cursor。

### Task B 验证结果

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_bridge.py
.............................
----------------------------------------------------------------------
Ran 29 tests in 14.214s

OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_http.py
.....................................
----------------------------------------------------------------------
Ran 37 tests in 20.025s

OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py
exit 0
```

### Task B 失败定位

- 未出现失败。

### Task B 剩余风险

- 本围栏只证明本地 Python HTTP/bridge contract 与 service worker source policy，没有证明真实手机浏览器、真实 service worker runtime、真实云、真实 4G/SIM、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。
