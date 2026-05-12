# Sprint 2026.05.12_12-13 Remote OSS/CDN Phone Consumption Gate - Tech Plan

## 状态

- 阶段：tech-plan
- Product Owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 兼容性围栏：`robot-software-engineer`
- 计划结论：进入实现阶段时由 Full-stack 单线闭环，Robot 只做 command/status/ack 兼容性围栏。

## 技术方案

在现有 operator gateway phone readiness / diagnostics 和上一轮 `remote_cloud_relay` OSS/CDN manifest artifact proof 之间增加一个 phone-safe consumption gate。实现应复用已有 manifest 校验逻辑或 helper，不重新发明 bucket/prefix/CDN URL rule，也不把 manifest artifact 原文暴露给手机。

建议实现形态：

- 在 behavior/operator gateway 侧新增或复用 manifest summary helper，输入为上一轮 manifest artifact path/env 或 diagnostics 配置。
- helper 输出 `oss_cdn_manifest` phone-safe summary，而不是 full artifact。
- summary 状态覆盖 `ready`、`missing`、`invalid`、`stale`。
- `/api/status.phone_readiness` 或 `/api/diagnostics` 挂载该 summary；若两者都接入，应共用同一 helper，避免状态口径分叉。
- operator 首屏只展示普通用户文案和 retry hint，不展示 raw object key、内部路径、secret、ROS topic 或硬件参数。
- Robot bridge API 不变化；manifest consumption 是 operator/API 层能力。

## API summary contract

P0 字段建议：

```json
{
  "state": "ready",
  "schema": "trashbot.oss_cdn_manifest",
  "schema_version": 1,
  "object_count": 2,
  "cdn_url_rule": "cdn_base_url + manifest object relative path",
  "evidence_boundary": "software_proof_docker_phone_manifest_consumption",
  "not_proven": [
    "real_oss_upload",
    "sts_issuance",
    "cdn_origin_fetch",
    "https_tls_public_ingress",
    "real_cloud",
    "real_4g_sim",
    "production_db_or_queue",
    "nav2_or_fixed_route_delivery",
    "wave_rover_or_hil"
  ],
  "safe_summary": "诊断对象引用已准备",
  "retry_hint": "如手机无法查看诊断，请刷新状态或重新生成诊断引用。",
  "updated_at": "2026-05-12T12:00:00+08:00",
  "staleness": "fresh"
}
```

状态规则：

- `ready`：artifact 存在且 schema/checksum/prefix/CDN rule 校验通过；仍必须保留 `not_proven`。
- `missing`：artifact 未配置、路径不存在或读取失败；phone readiness 不得变成 green。
- `invalid`：schema/checksum/prefix/CDN rule 失败；输出 safe summary，不输出 traceback。
- `stale`：artifact created_at/updated_at 超过默认 freshness threshold 或时间字段不可用。

## 文件范围

Full-stack 主责允许范围：

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`（仅复用/导出 manifest 校验 helper 时允许）
- `src/ros2_trashbot_behavior/test/test_operator_gateway_http.py`
- `src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`（仅当 helper contract 需要补最小覆盖）
- `docs/product/mobile_user_flow.md`
- `docs/product/cloud_4g_infrastructure.md`
- `docs/product/remote_4g_mvp.md`
- `sprints/2026.05.12_12-13_remote-oss-cdn-phone-consumption-gate/tech-done.md`

Robot compatibility 允许范围：

- `src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `sprints/2026.05.12_12-13_remote-oss-cdn-phone-consumption-gate/tech-done.md`（只追加验证片段或交给 Full-stack 汇总）

禁止范围：

- 不修改硬件/vendor 资料、Nav2/fixed-route、WAVE ROVER、串口、launch 硬件参数。
- 不新增真实 `.env`、云密钥、OSS AK/SK、bearer token 或生产账号配置。
- 不修改 `OKR.md`，除非实现收口后由 Product Owner 基于证据另行更新。
- 不新增大量测试文件；优先扩展已有 targeted test。

## 接口影响

- `/api/status` 可以新增或扩展 `phone_readiness.oss_cdn_manifest`。
- `/api/diagnostics` 可以新增或扩展 `oss_cdn_manifest` summary。
- 既有 command/status/ack HTTP shape 不变。
- ACK 语义不变：ACK 只表示 robot bridge 处理 command envelope，不代表 delivery success。
- Phone-safe summary 不应暴露 full manifest；调试需要 raw artifact 时只能保留在本地/受控工程路径，不进入普通用户首屏。

## 验收命令

Full-stack 最小围栏：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_operator_gateway_http.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
```

如复用或调整 manifest helper：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
```

Python 编译围栏：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
```

Robot compatibility fence：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py \
  src/ros2_trashbot_behavior/test/test_remote_bridge.py
```

文档和范围检查：

```bash
git diff --check -- \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_http.py \
  src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py \
  src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py \
  src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py \
  src/ros2_trashbot_behavior/test/test_remote_bridge.py \
  docs/product/mobile_user_flow.md \
  docs/product/cloud_4g_infrastructure.md \
  docs/product/remote_4g_mvp.md \
  sprints/2026.05.12_12-13_remote-oss-cdn-phone-consumption-gate/tech-done.md
```

本计划文档自身验收：

```bash
git diff --check -- \
  sprints/2026.05.12_12-13_remote-oss-cdn-phone-consumption-gate/pre_start.md \
  sprints/2026.05.12_12-13_remote-oss-cdn-phone-consumption-gate/prd.md \
  sprints/2026.05.12_12-13_remote-oss-cdn-phone-consumption-gate/tech-plan.md
```

## Team 执行方式

进入 implementation 时：

- 派 1 个 `full-stack-software-engineer` worker 单线负责 API summary、operator 首屏、targeted tests、产品文档同步和 `tech-done.md`。
- 派 1 个 `robot-software-engineer` worker 执行 remote bridge compatibility fence；若无退化，只提供验证片段，不扩大实现。
- Product Owner 只做验收口径、证据边界、side-by-side acceptance 和 final 收口。

## 工程质量要求

- 新增或修改代码中的技术注释必须使用中文，并保持有意义注释比例超过 20%。
- 注释重点解释为什么要区分 `ready/missing/invalid/stale`、为什么 `ready` 不等于真实 OSS/CDN 或 delivery success。
- 不允许在代码、测试 fixture、文档或日志样例中写入真实 AK/SK、Authorization、bearer token、root password。

## 风险边界

- `software_proof_docker_phone_manifest_consumption` 只证明手机/API 可以消费 manifest 摘要，不证明真实 OSS upload、CDN fetch、真实云、真实 4G 或 HIL。
- Docker/local API 即使显示 manifest ready，也不能声明 production ready。
- stale/invalid/missing 必须降级为可理解的用户提示，不能被 readiness 聚合成 green。
- 本轮不读取 vendor 硬件资料，因为不涉及 WAVE ROVER、ESP32、Orange Pi、UART、波特率、JSON 底盘协议、速度映射、反馈协议、引脚、电压、固件或机械尺寸。

## 完成后收口要求

- `tech-done.md` 必须写清实际改动、验证结果、偏差和未证明事项。
- `side2side_check.md` 必须对照 PRD P0 验收 `ready/missing/invalid/stale`、redaction、operator 文案和 remote bridge compatibility。
- `final.md` 必须明确是否建议 O6 从约 36% 保守上调；没有实现证据不得更新 OKR 进度。
