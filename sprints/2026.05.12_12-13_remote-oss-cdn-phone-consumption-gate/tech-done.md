# Sprint 2026.05.12_12-13 Remote OSS/CDN Phone Consumption Gate - Tech Done

## 状态

- 阶段：tech-done
- 主责 Engineer：`full-stack-software-engineer`
- 证据边界：`software_proof_docker_phone_manifest_consumption`
- 结论：已把上一轮 OSS/CDN manifest artifact proof 接入 operator phone/API 消费面；仍不证明真实 OSS upload、CDN reachable、真实云、真实 4G、delivery success 或 HIL。

## 实际改动

- `remote_cloud_relay.py`
  - 新增 `build_phone_oss_cdn_manifest_summary()`，复用既有 manifest 校验规则。
  - 输出 phone-safe `oss_cdn_manifest` summary，覆盖 `ready`、`missing`、`invalid`、`stale`。
  - summary 不返回 full artifact、object key、checksum、本地路径或凭证。
- `operator_gateway.py`
  - 新增 `oss_cdn_manifest_artifact_ref` 参数，默认读取 `TRASHBOT_REMOTE_CLOUD_OSS_CDN_MANIFEST_ARTIFACT`。
  - diagnostics 调用传入同一 manifest artifact ref。
- `operator_gateway_http.py`
  - `/api/status.phone_readiness.oss_cdn_manifest` 接入同一 helper。
  - operator 首屏显示 "诊断对象引用已准备/缺失/损坏/过期" 和 retry hint。
  - `missing`、`invalid`、`stale` 会阻止首屏进入 green ready。
- `operator_gateway_diagnostics.py`
  - `/api/diagnostics.oss_cdn_manifest` 接入同一 helper。
- Targeted tests
  - 扩展 operator HTTP、diagnostics、remote_cloud_relay 现有测试，未新增测试文件。
- Product docs
  - 更新手机流程、云/4G 基建和 remote 4G MVP 文档中的 phone manifest consumption contract。

## 验证结果

已运行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_operator_gateway_http.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
```

结果：`Ran 62 tests in 16.283s OK`

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
```

结果：`Ran 24 tests in 6.374s OK`

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
```

结果：通过，无输出。

```bash
git diff --check -- \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_http.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py \
  src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py \
  docs/product/mobile_user_flow.md \
  docs/product/cloud_4g_infrastructure.md \
  docs/product/remote_4g_mvp.md \
  sprints/2026.05.12_12-13_remote-oss-cdn-phone-consumption-gate/tech-done.md
```

结果：通过，无输出。

## 偏差和剩余风险

- `ready` 只代表 phone/API 可消费本地 manifest 摘要；保留 `not_proven`。
- 未运行真实手机浏览器、真实 OSS 上传、CDN 回源、真实云、真实 4G/SIM、Nav2/fixed-route、WAVE ROVER 或 HIL。
- 本轮没有改 Robot bridge command/status/ack shape；Robot compatibility fence 由并行 worker 或主会话另行汇总。
