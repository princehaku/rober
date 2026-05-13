# Sprint 2026.05.13_14-15 OSS/CDN Live Probe Gate - PRD

## 用户价值

普通手机用户和部署同学需要知道“诊断对象链接是否真的可被 CDN 读取”，而不是只看到 bucket、prefix 和 CDN URL 形态正确。本轮提供一个上线前 live probe gate：在未来有真实 CDN/外部 URL 时可以执行 HTTP live probe；在当前 Docker-only 主机上保持 blocked-by-design，不夸大为真实 OSS/CDN live traffic。

## OKR 映射

- Objective 5 KR3：OSS 写入策略和对象引用已形成 manifest，本轮补 live probe 入口，用于验证 CDN 引用可访问性。
- Objective 5 KR4：CDN base URL 作为只读视图入口，本轮让 diagnostics/preflight 能解释 CDN live probe 的 ready/blocked 状态。
- Objective 5 KR6：OSS/CDN 不可达时必须 graceful degradation，本轮输出 phone-safe safe summary 和 retry hint。

## 本轮范围

### In Scope

- 新增 `trashbot.oss_cdn_live_probe` artifact schema v1。
- 新增 CLI 写入参数和 preflight consumption：
  - `--write-oss-cdn-live-probe-artifact`
  - `--oss-cdn-live-probe-artifact`
  - `TRASHBOT_REMOTE_CLOUD_OSS_CDN_LIVE_PROBE_ARTIFACT`
- Live probe 结果必须 phone-safe：不写入 Authorization、bearer token、AK/SK、root password、credential-bearing URL、local path、ROS topic、串口、WAVE ROVER 参数或 `/cmd_vel`。
- `production_ready=false` 和 `overall_status=blocked` 在当前 Docker-only proof 中必须保留。
- Robot remote bridge/protocol 增加 metadata-only fence，确保 `oss_cdn_live_probe` 不被解释为 command/status/ACK envelope。

### Out of Scope

- 不接真实阿里云账号、OSS AK/SK、STS、CDN 配置或公网域名。
- 不做真实上传、不做生产 CDN 回源验证、不做真实 4G/SIM。
- 不改硬件、Nav2/fixed-route、WAVE ROVER、HIL 或任务送达链路。

## 验收口径

- Full-stack gate 能生成 live probe artifact，并能被 production preflight 消费。
- 当前无真实 CDN 时仍保持 `production_ready=false`、`overall_status=blocked`，并保留 `not_proven`。
- Robot compatibility fence 证明 metadata-only response 不触发 backend action、不 POST ACK、不推进或持久化 cursor。
- 文档和 sprint closeout 明确证据边界为 `software_proof_docker_oss_cdn_live_probe_gate`。
