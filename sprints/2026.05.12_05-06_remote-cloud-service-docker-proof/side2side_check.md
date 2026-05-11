# Sprint 2026.05.12_05-06 Remote Cloud Service Docker Proof - Side By Side Check

## 状态

- 阶段：side2side_check
- 更新时间：2026-05-12 06:45 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 收口结论：Product Acceptance 通过
- 证据边界：`software_proof_docker_only`

## 用户价值和产品北极星

北极星仍是普通用户只用手机，通过 4G 云中转控制小车送垃圾，不要求手机和小车处于同一 WiFi。本轮的实际用户价值是把远程控制面从 `operator_gateway` local/mock fallback 中进一步拆出，形成可独立运行的 HTTP relay service proof，让后续真实云、HTTPS/TLS、公网入口、4G/SIM、OSS/CDN 能有明确替换边界。

本轮验收不是硬件、路线、真实送达或真实云验收；它只验收 independent Docker/local relay service、file-backed persistence、bearer auth、phone-safe errors 和 robot client compatibility 的软件证明。

## OKR 映射

| Objective | Acceptance 判断 |
| --- | --- |
| O6 4G 云中转 + OSS/CDN | 可从约 19% 保守提升到约 23%。依据是 independent Docker/local relay service、file-backed persistence、bearer auth、phone-safe errors、client compatibility、`docs/product/cloud_4g_infrastructure.md` 已有软件 proof。 |
| O5 手机体验与量产边界 | 最多小幅 +1pp。依据只限于 phone-safe errors、status_missing/status_stale、retry hint 和 future phone UI API contract；不能写成正式手机 UI 完成。 |
| O1/O2/O3/O4 | 不提升。本轮没有真实 WAVE ROVER、Nav2/fixed-route、相机、路线采集、真实送达或 HIL 证据。 |

## Side By Side 对照

| 验收项 | PRD / Tech Plan 口径 | Tech Done 证据 | Product Acceptance |
| --- | --- | --- | --- |
| 独立 HTTP relay service | 不依赖 ROS2 runtime 或 `operator_gateway` 进程，提供 `trashbot.remote.v1` command/status/ack API。 | Task A 新增 `remote_cloud_relay.py`，覆盖 `POST/GET commands/status/ack`，本机 Python/Docker 可启动。 | 通过；是 independent Docker/local service proof，不是生产云部署。 |
| Bearer auth | 缺 token/错 token 拒绝，正确 token 可访问，错误不泄露密钥。 | Task A targeted tests `Ran 6 tests in 2.593s OK`；Task B wrong token 映射为 `RemoteCloudError(reason="auth_failed")`。 | 通过；只证明本地 relay auth gate，不证明生产身份、rotate 或 HTTPS/TLS。 |
| File-backed persistence | commands/status/acks 写入 state file，重启后可读，尽量原子写入。 | Task A `FileBackedRelayStore` 使用临时文件和 `os.replace`，targeted tests 覆盖 persistence。 | 通过；只证明单机 file persistence，不证明生产 DB、多实例一致性或灾备。 |
| Phone-safe errors | auth failed、bad request、not found、status missing/stale、malformed JSON 不回显 raw traceback、ROS topic、硬件参数或密钥。 | Task A tests 覆盖 error redaction；`remote_4g_mvp.md` 和 `cloud_4g_infrastructure.md` 写清 phone-safe 边界。 | 通过；支撑未来手机 UI contract，但不是正式手机 UI。 |
| Robot client compatibility | `RemoteCloudClient` / `remote_bridge` 能对独立服务完成 status -> command poll -> ack 流程。 | Task B targeted tests `Ran 31 tests in 15.249s OK`，未发现生产 client 需要改动。 | 通过；ACK 仍只是 command envelope 处理状态，不是 delivery result。 |
| 合并集成围栏 | A/B 合并后 targeted smoke、py_compile、scoped diff check 通过。 | Task C `Ran 37 tests in 17.884s OK`；py_compile 和 scoped diff check 均通过。 | 通过；验收范围仍是本地软件围栏。 |

## 验证证据

工程验证来自 `tech-done.md`，Product Acceptance 仅复核证据并运行文档/OKR scoped diff check。

```text
Task A:
Ran 6 tests in 2.593s
OK

Task B:
Ran 31 tests in 15.249s
OK

Task C:
Ran 37 tests in 17.884s
OK
```

```text
py_compile:
通过，无输出。

scoped git diff --check:
通过，无输出。
```

## 做什么 / 不做什么

已完成：

- 独立 Docker/local HTTP relay service proof。
- command/status/ack API、idempotent command、ACK terminal state、status_missing/status_stale。
- bearer auth gate、phone-safe JSON errors、敏感字段脱敏。
- file-backed persistence 和 robot client compatibility proof。
- `docs/product/cloud_4g_infrastructure.md` 补齐 O6 KR2 的真实云边界、网络方向、OSS/CDN 目标和本轮 proof 限制。

未完成：

- 真实云部署、域名、公网入口、HTTPS/TLS、防火墙实配。
- 真实 4G/SIM、弱网/断网 carrier 测试。
- OSS/CDN 上传、STS、受限 AK、CDN 回源、生命周期和 rotate。
- 生产数据库、队列、多实例一致性、备份和灾备。
- 正式手机 UI、普通用户实机验收。
- Nav2/fixed-route、WAVE ROVER、真实运动、真实送达或 HIL。

## Next Recommendations

1. O6 下一轮优先做最小真实云入口 proof。
   - 证据依据：当前 OKR 快照 O6 仍只有约 23%，05-06 `tech-done.md` 已证明 independent Docker/local relay 和 file-backed persistence；`docs/product/cloud_4g_infrastructure.md` 明确仍缺真实云部署、HTTPS/TLS、公网入口、防火墙实配和生产持久化。
   - 责任 Engineer：`full-stack-software-engineer`。
   - 验收口径：云主机或等价公网环境可访问 HTTPS API，bearer auth 生效，commands/status/ack 可跨进程/重启恢复；仍不得声明 4G、OSS/CDN 或 HIL。

2. O6 随后补 OSS/CDN 最小对象链路。
   - 证据依据：04-05 final 和 05-06 tech-done 都只覆盖 JSON 控制面；`cloud_4g_infrastructure.md` 已写明 bucket、region、prefix、CDN base URL，但未实现 STS、受限 AK、上传、回源或生命周期。
   - 责任 Engineer：`full-stack-software-engineer`。
   - 验收口径：使用非生产密钥或受限凭证完成一条快照对象写入和 CDN/API 引用 proof，且密钥不入仓库。

3. O5 只在正式手机 UI 接入后再大幅推进。
   - 证据依据：O5 当前仍约 33%，本轮只提供 phone-safe errors 和 future phone UI API contract；04-05 final 已明确没有正式 UI 或用户实机验收。
   - 责任 Engineer：`full-stack-software-engineer`。
   - 验收口径：手机主路径可用、美观、中文优先、主操作小于等于 3 步，并能展示 auth/status/ack/degradation，而不是 raw JSON。

4. O1/O2/O3 暂不从本轮软件 proof 获得完成度。
   - 证据依据：当前 OKR 快照、04-05 final、05-06 tech-done 都明确没有真实 WAVE ROVER、真实 Nav2/fixed-route、同一 `evidence_ref` route replay 或 HIL；本轮 Task C 只是 `Ran 37 tests in 17.884s OK` 的本地软件围栏。
   - 责任 Engineer：`hardware-engineer`、`autonomy-engineer`、`robot-software-engineer`。
   - 验收口径：必须有真实串口/HIL evidence packet 和同一 evidence_ref 的 route/task 复盘，才能提升实机相关 OKR。

## 风险、阻塞和需要补齐的证据链

- Product Acceptance 仍是 `software_proof_docker_only`，不等于真实云、4G、OSS/CDN、Nav2/fixed-route、WAVE ROVER 或 HIL。
- ACK 不是 delivery result；手机端和 OKR 文档必须继续把 ACK 与真实送达/投放结果分开。
- file-backed store 不是生产数据库；不能据此声明生产队列、并发一致性或灾备完成。
- phone-safe errors 支撑 future phone UI API contract，但没有完成正式手机 UI 或普通用户实机验收。
