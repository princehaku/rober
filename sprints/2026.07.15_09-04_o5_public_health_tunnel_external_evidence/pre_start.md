# Pre-start - O5 Public Health Tunnel External Evidence

## Sprint Metadata

- `sprint_type: epic`
- Sprint：`sprints/2026.07.15_09-04_o5_public_health_tunnel_external_evidence/`
- Target Objective：O5「真实云端部署与公网可验证入口」，当前完成度约 `85%`，为 `OKR.md` 4.1 节最低 Objective。
- Product owner：`product-okr-owner`
- Delivery owner：`full-stack-software-engineer`
- 计划状态：前三阶段已定义；不得在实现和验证完成前预生成 `tech-done.md`、`side2side_check.md` 或 `final.md`。

## 用户价值与产品北极星

本轮要让开发机能够从真实公网、通过 certificate-valid HTTPS 验证上位机 relay 的唯一只读健康信号，同时证明公网入口无法触达任务、命令、状态写入或机器人控制面。用户获得的是一份可复核的真实外部健康证据，而不是另一份本地 preflight、readback、export、browser 或 mock wrapper。

该证据只回答「临时公网入口能否安全暴露 `/healthz`」；它不回答稳定域名、生产凭证、4G、production DB/queue、worker、OSS/CDN、真实手机或真实送达是否就绪。

## 上轮事实与切换理由

- O5 约 `85%`，低于 O6/O7 约 `93%`、O1 约 `94%`，本轮直接选择最低 Objective。
- 只读可行性审计确认上位机是 `aarch64`，已有 `docker`、`node`、`npm`、`python3`、`curl`，但缺少 `cloudflared`，且没有 `cloudflared` / `remote_cloud_relay` 运行进程。
- relay 的 GET/POST 共用同一 HTTP listener。命令 POST 虽有 bearer gate，但 token 为空会放行，且部分 archive POST 写路由位于 auth gate 之前；因此 Cloudflare quick tunnel 直连 relay 明确 `NO-GO`。
- 当前最低项已有新的可推进抓手：真实公网 HTTPS health-only capture。它会产生 `external_artifact_delta`，不再消费 O5 已接受并退役的 preflight/readback/export/browser/voice/packet/mock 包装。
- 最近 O3 已重复证明无受控 initial pose 时缺 dynamic `map->odom`；在没有新授权或 persisted pose 前不再重复该 runtime，本轮转向可推进的 O5。

## 本轮范围与唯一抓手

实现一个纯 Python 标准库 loopback allowlist proxy：

- relay 仅监听或发布到 `127.0.0.1`。
- proxy 仅监听 `127.0.0.1`，只允许精确 `GET /healthz` 与 `HEAD /healthz`。
- 其他 path 返回 `404`；精确 `/healthz` 上的其他 method 返回 `405`。
- 带 query、重复斜杠、百分号编码、absolute-form target、path traversal 或任意编码绕过必须 fail closed。
- proxy 不转发客户端 body、Authorization、Cookie、token 或任意控制相关 header。
- quick tunnel 只能指向 proxy，禁止指向 relay。

完成本地实现和负向测试后，只运行一次 bounded live capture。`full-stack-software-engineer` 仅可从 Cloudflare 官方 release/API 获取 ARM64 runtime；必须验证 HTTPS、官方版本元数据和 SHA256，禁止硬编码未知 checksum。relay、proxy、cloudflared 和临时目录必须全部由 capture helper 建立 ownership、跟踪并清理。

## 禁止范围

- 禁止任何 command、task、manual control、`/cmd_vel`、UART、route、delivery 或 HIL 行为。
- 禁止公网暴露 `/readyz`、`/preflightz`、`/api/*`、`/robots/*`、静态页面或 relay 原始端口。
- 禁止安装系统包、写持久 systemd/service、修改防火墙或把 cloudflared 放进系统 PATH。
- 禁止保存 raw public URL、token、Authorization/header、request/response body 或 tunnel 原始日志。
- 禁止把 temporary tunnel 推导为 production ready、Mission Objective 0、真实手机、4G、稳定 DNS 或送达成功。

## Owner 与交付边界

`full-stack-software-engineer` 单 owner 闭环负责实现、单元/集成测试、失败修复、一次 live capture、`tech-done.md` 与脱敏 artifacts。Product Owner 只在 Engineer 返回后核对证据、更新 `side2side_check.md` / `final.md`，并判断 OKR 计分。

Engineer 后续允许改动：

- `cloud-relay/scripts/healthz_allowlist_proxy.py`
- `cloud-relay/test/test_healthz_allowlist_proxy.py`
- `cloud-relay/docker-compose.yml`
- `cloud-relay/README.md`
- 当前 sprint 的 `tech-done.md` 与 `artifacts/`

范围外文件不得改动。

## Product 计分预案

只有所有本地安全 gate、官方 runtime provenance、一次真实公网 HTTPS 正向与负向验证、state checksum 不变、脱敏和 cleanup residual=`0` 同时通过，才接受：

- `current_run_artifact_delta=true`
- `external_artifact_delta=true`
- O5 `85% -> 86%`
- `production_ready=false`
- `mission_objective_0_satisfied=false`
- KR `不归档`

任一 gate 失败则 O5 保持 `85%`，两个 delta 均不得宣称成功，并记录 exact blocker 后停止；不得再用相邻 wrapper 补分。

## 启动风险

1. Cloudflare 官方 API/release 或 quick tunnel 在 live window 不可达，会导致本轮 flat。
2. 官方 asset 若没有可验证的 SHA256 digest、架构或版本不匹配，必须 fail closed，不能运行二进制。
3. Cloudflare edge 可能返回 3xx；正向只接受 certificate-valid HTTPS `2xx/3xx`，但不得跟随到非 HTTPS 或非预期 host。
4. quick tunnel 是临时 provider endpoint，不能替代稳定 DNS、生产凭证、4G、production DB/queue、worker、OSS/CDN 或真手机证据。
5. 任何 relay state 变化、控制面可达、raw URL 泄露或 cleanup residual 非零都否决本轮计分。
