# Sprint 2026.05.12_18-19 Phone PWA Installability Gate - Final

## 状态

- 阶段：final
- 收口时间：2026-05-12 19:00 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 兼容性围栏：`robot-software-engineer`
- Evidence boundary：`software_proof_docker_phone_pwa_installability_gate`

## 本轮核心抓手

本轮把本地 operator fallback 手机页从 browser acceptance 推进到 PWA/installability software proof：manifest、mobile meta、service worker 静态 shell、offline shell 和 API bypass 均有围栏证据。

这仍是本地/Docker 软件证据，不是正式手机 app、真实手机安装、真实云/4G 或机器人实机送达。

## 实际完成

- Task A `full-stack-software-engineer` 已推送 `6236def9ca9a42b9a5d4597f5a95488da8fd9d6e`。
- Task A 改动 `operator_gateway_http.py`、`test_operator_gateway_http.py`、`test_operator_gateway_static.py`、`docs/product/mobile_user_flow.md` 和 `tech-done.md`。
- Task A 新增 `/manifest.webmanifest`、`/service-worker.js`、`/offline.html`、PWA icons、mobile/installability meta 和 service worker registration。
- Service worker 明确 bypass `/api/*`、`/robots/*`、command routes、ACK routes、diagnostics 和所有非 GET 请求，并使用 `cache: 'no-store'`。
- Task B `robot-software-engineer` 已推送 `154ffee04d5d1b1031e19b82438ae22799c69d67`。
- Task B 只更新 `tech-done.md`，未改产品代码或测试代码；结论是 PWA shell 不改变 command/status/ack envelope，不缓存 ACK/status，不触发额外 local action，不推进 cursor。

## 验证结果

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

Product acceptance 本轮只运行 scoped diff check，不运行 broad tests。

## OKR 更新

- O5：约 43% -> 约 46%，证据边界更新为 `software_proof_docker_phone_pwa_installability_gate`。
- O6：保持约 45%，本轮只提供 phone-safe 状态素材，不构成真实云或 4G 进展。
- O1/O2/O3/O4：保持不变。

## 未完成事项和风险

- 未证明生产 app、app-store/native install、真实手机设备 Safari/Chrome install prompt 或 physical phone service worker runtime。
- 未证明真实云、真实 4G/SIM、HTTPS/TLS 公网入口、production account、真实 STS、OSS/CDN 实流量或生产运维。
- 未证明 Nav2/fixed-route、WAVE ROVER、HIL、真实底盘运动或真实垃圾送达。
- 后续若推进 O5，应优先做真实 iPhone/Android 设备验收；若推进 O6，应进入真实云/4G/OSS/CDN production proof，而不是继续只堆本地素材。

## 收口结论

本轮达到 `software_proof_docker_phone_pwa_installability_gate`。PWA 壳层和缓存边界能支持普通手机入口的下一步验收，但所有实机、真实手机、真实云和真实送达缺口仍保持 blocked。
