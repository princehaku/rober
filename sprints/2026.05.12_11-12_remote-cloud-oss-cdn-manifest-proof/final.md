# Sprint 2026.05.12_11-12 Remote Cloud OSS/CDN Manifest Proof - Final

## 状态

- 阶段：final
- 收口时间：2026-05-12 09:21 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 兼容性围栏：`robot-software-engineer`
- Product verdict：通过，按 `software_proof_docker_oss_cdn_manifest` 收口。

## 用户价值和产品北极星

北极星仍是普通手机用户不需要同 WiFi、不接触 ROS2/SSH/命令行，也能通过云端控制小车并查看任务诊断引用。

本轮交付的用户价值是把未来诊断图片、日志包或任务记录的大对象引用做成可校验 manifest contract。后续手机/云端可以基于同一 schema、prefix、CDN URL、checksum、脱敏摘要和 `not_proven` 边界展示诊断状态，而不是临时拼对象路径或暴露底层云/机器人细节。

## OKR 映射和 KR 进展

- Objective：O6 4G 云中转 + OSS/CDN 数据通路产品化。
- KR3：bucket `bytegallop`、region `oss-cn-hangzhou`、对象前缀 `rober/<robot_id>/<date>/<task_id>/` 已进入可生成/可校验 manifest artifact。
- KR4：CDN base URL `https://cdn.bytegallop.com/rober/` 和 object key 到 CDN URL 的组合规则已进入 test/preflight proof。
- KR5：artifact/preflight 输出的 phone-safe redaction 已被 targeted tests 和文档口径覆盖。
- KR6：本轮为后续 OSS 写失败/CDN 不可达区分提供 manifest gate，但尚未证明真实降级。

基于 `tech-done.md` 和 `side2side_check.md`，建议 O6 从约 34% 保守上调到约 36%。不得提升 O1/O2/O3/O4/O5。

## 本轮核心抓手

本轮核心抓手是 `software_proof_docker_oss_cdn_manifest`：manifest artifact 生成/校验、preflight 消费、evidence boundary 提升和 phone-safe 输出边界。

## 做了什么

- Full-stack worker 新增 OSS/CDN manifest artifact 生成/校验和 CLI 参数。
- Preflight 新增 `oss_cdn_manifest` check；有效 artifact 使本地 evidence boundary 到 `software_proof_docker_oss_cdn_manifest`。
- 同步 `docs/product/cloud_4g_infrastructure.md` 与 `docs/product/remote_4g_mvp.md`，明确 manifest proof 与真实 OSS/CDN 的差异。
- Robot compatibility worker 确认 remote command/status/ack 与 ACK/cursor 保守语义未退化。
- Product Owner 完成 PRD P0 side-by-side acceptance、final 收口，并更新 `OKR.md` O6 当前快照。

## 不做什么和不得宣称事项

- 不宣称真实 OSS upload、STS issuance、CDN origin fetch、lifecycle policy、production account 已完成。
- 不宣称真实云部署、HTTPS/TLS 公网入口、真实 4G/SIM、弱网恢复、生产 DB/queue、多实例一致性或真实灾备已完成。
- 不宣称正式手机 UI 已消费 manifest。
- 不宣称 Nav2/fixed-route、真实送达、WAVE ROVER、串口反馈或 HIL 有新增进展。
- 不把 ACK、preflight pass、manifest pass 或 CDN URL shape 写成 delivery success。

## 验证证据

- Full-stack targeted tests：`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py` -> `Ran 23 tests in 6.388s OK`。
- Full-stack py_compile：`remote_cloud_relay.py` 通过。
- CLI smoke：manifest generate `ok=True`；preflight consume `evidence_boundary=software_proof_docker_oss_cdn_manifest`、`oss_cdn_manifest=pass`、整体 `blocked` 符合生产缺口未证明预期。
- Robot compatibility fence：`test_remote_bridge_protocol.py` 与 `test_remote_bridge.py` -> `Ran 31 tests in 15.132s OK`。
- Scoped `git diff --check`：实现/测试/产品文档/`tech-done.md` 通过；Product 收口文件和 `OKR.md` 另行执行 scoped diff check。

## 风险、阻塞和证据链缺口

- 当前证据仍是 Docker/local software proof，不是真实云、真实 4G/SIM 或真实 OSS/CDN 流量。
- 后续 O6 的高价值下一步是外部实证：STS/受限 AK、真实 OSS upload、CDN 回源探测、HTTPS/TLS 公网入口、生产鉴权/rotate 和弱网恢复。
- 正式手机 UI 消费 manifest 前，还需补 artifact 过期、刷新、权限和私有对象策略。

## Sprint 文档状态

- `pre_start.md`：已完成。
- `prd.md`：已完成。
- `tech-plan.md`：已完成。
- `tech-done.md`：已由 Full-stack worker 更新。
- `side2side_check.md`：本次 Product acceptance 已创建。
- `final.md`：本次 Product 收口已创建。
