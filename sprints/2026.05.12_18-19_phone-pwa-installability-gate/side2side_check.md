# Sprint 2026.05.12_18-19 Phone PWA Installability Gate - Side By Side Check

## 状态

- 阶段：side2side_check
- 验收时间：2026-05-12 18:59 Asia/Shanghai
- Owner：`product-okr-owner`
- Evidence boundary：`software_proof_docker_phone_pwa_installability_gate`

## 产品北极星与用户价值

北极星：手机是普通用户唯一入口；普通用户不应接触命令行、ROS2、raw JSON、串口、硬件参数或凭证。

本轮用户价值：本地 operator fallback 页面从“浏览器里可用”推进到“具备 PWA/installability 壳层证据”。用户断网或离线时看到 phone-safe 离线提示和 disabled 主操作，而不是误以为机器人还能被控制。

## OKR 映射

- O5 KR1：本地手机入口继续承载连接、状态查看、发车、确认和异常处理主流程；本轮补齐 PWA manifest/installability 入口形态。
- O5 KR5：离线壳层和 command gate 不暴露命令行、SSH、ROS2、串口、raw JSON、token、Authorization 或 OSS secret。
- O5 KR7：manifest、mobile meta、service worker、offline shell 和 API bypass 已进入 software proof。
- O6 KR6：远程 readiness / diagnostics / ACK 相关状态仍只作为 phone-safe 素材；本轮不提升 O6。

## Side By Side 验收

| 计划验收项 | Task A / B 证据 | 产品验收 |
| --- | --- | --- |
| Manifest 可访问且字段完整，`start_url` / `scope` 不指向 `/api/*` | Task A 新增 `/manifest.webmanifest`；HTTP/static unittest 覆盖 manifest 字段和非 API scope | 通过 |
| HTML head 包含 mobile/installability meta | Task A 新增 viewport、theme color、description、Apple mobile web app capable/title/status bar meta | 通过 |
| Service worker 不缓存动态控制面 | Task A service worker bypass `/api/*`、`/robots/*`、command、ACK、diagnostics 和所有非 GET，使用 `cache: 'no-store'` | 通过 |
| 离线壳层 phone-safe 且主操作 disabled | Task A 新增 `/offline.html`，Start/Confirm Dropoff/Cancel disabled | 通过 |
| API/command/ACK 兼容性不退化 | Task B `test_remote_bridge.py` 29 tests OK；`test_operator_gateway_http.py` 37 tests OK；未改 robot bridge 产品代码 | 通过 |
| 文档同步 | `docs/product/mobile_user_flow.md` 新增 Local PWA Installability Gate，并写清 evidence boundary 和 not proven | 通过 |

## 验证证据

Task A：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_static.py
Ran 46 tests in 20.155s
OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py
exit 0
```

Task B：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_bridge.py
Ran 29 tests in 14.214s
OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_http.py
Ran 37 tests in 20.025s
OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py
exit 0
```

## 失败定位

Task A 首轮 unittest 失败在静态测试锚点，只匹配到后续 `SERVICE_WORKER_JS` 路由引用，未定位到常量定义；Full-stack 已修复锚点并重跑通过。Task B 未出现失败。

## OKR 验收结论

O5 可从约 43% 保守上调到约 46%。理由是 KR7 从本地 Chrome browser acceptance 进一步推进到 PWA/installability software proof，且 service worker 缓存边界有测试围栏。

O6 不上调。本轮只把已有远程/诊断状态作为 phone-safe 手机素材，没有新增真实云、4G、STS、OSS/CDN、生产账号或公网入口证据。

O1/O2/O3/O4 不上调。本轮没有硬件、Nav2/fixed-route、视觉实景、WAVE ROVER、HIL 或真实送达证据。

## 剩余风险

- 没有真实手机设备 Safari/Chrome install prompt 或 home-screen 安装验证。
- 没有真实 service worker runtime 在物理手机上的离线行为证明。
- 没有生产 app、app-store/native install、生产账号、真实云、真实 4G/SIM、OSS/CDN 实流量、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。
