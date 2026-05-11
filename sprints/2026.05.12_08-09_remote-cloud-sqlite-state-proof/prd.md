# Sprint 2026.05.12_08-09 Remote Cloud SQLite State Proof - PRD

## 状态

- 阶段：prd
- 创建时间：2026-05-12 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 支撑 Engineer：`robot-software-engineer`
- 证据边界：目标为 `software_proof_docker_sqlite_state_store`

## 用户价值和产品北极星

本轮要把 O6 从“file-backed state proof 能跑”推进到“commands/status/acks 有 SQLite-backed 可恢复证明”。对普通手机用户的价值是：未来云中转重启后，手机命令、机器人状态和 ACK 轨迹不应无声丢失；但用户也必须能看到保守、可理解的 readiness 说明，知道当前还不是生产 DB/queue、真实云或真实 4G 通过。

北极星仍是普通用户只用手机，通过 4G 云中转完成 trash delivery。当前 PRD 不把 SQLite proof 包装成真实云部署完成，不把 ACK 包装成真实送达，不把 Docker-only evidence 包装成 4G、OSS/CDN、Nav2、WAVE ROVER 或 HIL 证据。

## 背景和证据

1. `OKR.md` 2026-05-12 08:00 快照：
   - O6 约 30%，是当前最低且 Docker-only 主机可推进的目标。
   - O5 约 33%，主要缺正式手机 UI 和普通用户验收；本轮只提供 phone-safe readiness 支撑。
   - O1/O2/O3/O4 完成度约 74%-76%，但当前主机无真实硬件、真实路线、真实相机、真实 4G 或 HIL，不适合作为本轮主线。
2. `sprints/2026.05.12_07-08_remote-cloud-production-preflight/final.md`：
   - 已有 `software_proof_docker_preflight_gate`。
   - 明确下一轮 O6 应优先补真实云最小 staging 条件。
   - 明确 state store 仍是 file-backed proof，生产 DB/queue 缺口存在。
3. 近期 remote cloud 链路已具备：
   - independent relay service。
   - bearer auth。
   - phone-safe errors。
   - Docker deploy/readiness。
   - preflight blocked/warning/pass 输出。
   - robot compatibility fence。
4. 当前产品风险：
   - file-backed proof 可证明最小形态，但对后续云化的恢复语义太弱。
   - 直接跳到生产 DB/queue 会扩大范围，且当前没有真实云资源。
   - SQLite 是本轮在 Docker-only 环境下可验证、可恢复、可保守描述的最小下一步。

## OKR 映射

| KR | 本轮产品诉求 |
| --- | --- |
| O6 KR1 云中转服务端最小契约 | 不改变 commands/status/ack HTTP API shape；只替换或扩展 state backend。 |
| O6 KR2 云服务端基线 | 为后续 staging/production 提供比 file-backed 更接近服务端状态层的单实例 proof。 |
| O6 KR5 凭证管理 contract | SQLite backend 和 preflight 输出不得泄露 bearer token、Authorization header 或敏感路径。 |
| O6 KR6 graceful degradation | relay 重启、state backend 选择、SQLite 不可用或锁冲突时，要有 phone-safe blocked/warning。 |
| O5 KR5/KR7 支撑项 | 沉淀用户可读状态恢复和 retry hint，不交付正式手机 UI。 |

## KR 拆解或更新

### P0 - SQLite state backend selection

- 支持 `TRASHBOT_REMOTE_CLOUD_STATE_BACKEND=sqlite` 或等价配置。
- SQLite backend 可以有独立 path 配置；缺 path、不可写、初始化失败时输出 phone-safe 错误。
- 默认行为不得破坏既有 file-backed/local proof；是否切换默认由 Engineer 基于兼容风险决定，但本轮验收必须显式运行 SQLite backend。

### P0 - commands recovery

- 在 SQLite backend 下，phone/API 写入 command 后，relay 重启或 store 重新打开，robot 仍能按既有 get-next-command 语义读取。
- 幂等键、command id、terminal 状态不能因重启重复制造新的语义。
- 不能暴露 `/cmd_vel` 或底层速度入口。

### P0 - status recovery

- robot post_status 后，relay 重启或 store 重新打开，phone/API 仍能读取最近 status。
- status shape 兼容既有 contract，不新增手机必须理解的 raw ROS topic 或硬件字段。
- status 缺失、过期或 store 不可读时给出 phone-safe reason。

### P0 - ack recovery

- robot post_ack 后，relay 重启或 store 重新打开，ACK 记录仍可查询或用于 cursor/terminal 语义。
- ACK 只能代表 command envelope 已处理或 terminal ACK 已记录，不代表 trash delivery 完成。
- cloud unreachable、auth failed、malformed response 和 blocked preflight 不能推进 cursor。

### P0 - Preflight SQLite boundary

- preflight 能识别 `TRASHBOT_REMOTE_CLOUD_STATE_BACKEND=sqlite`。
- SQLite backend 可用时可以对 state store proof 给出 pass，但必须对 production DB/queue、多实例、备份、灾备给出 warning 或 blocked。
- 输出必须包含 `software_proof_docker_sqlite_state_store` 或等价 evidence boundary。

### P0 - Phone-safe output

- 输出字段应适合手机端或 operator 页面使用，例如 `state_backend`、`overall_state`、`checks[]`、`status`、`reason`、`safe_summary`、`retry_hint`、`evidence_boundary`。
- 不暴露 bearer token、Authorization header、OSS AK/SK、root password、raw traceback、ROS topic、串口、baudrate、WAVE ROVER 参数或 `/cmd_vel`。

## 做什么 / 不做什么

做：

- 定义并实现 SQLite-backed state store proof。
- 用 targeted tests/smoke 证明 commands/status/acks 在 SQLite backend 下可恢复。
- 复用已有 independent relay 和 preflight，不重新发明 HTTP API。
- 用 robot compatibility fence 确认 remote bridge status-command-ack 与 cursor/ACK 语义不退化。
- 在后续收口中保守更新 O6，其他 Objectives 不提升。

不做：

- 不部署真实云，不购买域名，不申请证书，不实配防火墙。
- 不接真实 4G/SIM，不跑 carrier 弱网实测。
- 不完成 OSS/CDN 上传、STS 发放、CDN 回源、生命周期或 rotate 实流量。
- 不迁移生产 DB/queue，不验证多实例一致性、备份或灾备。
- 不做正式手机 UI、美观验收、普通用户实机验收。
- 不修改硬件、Nav2、fixed-route、WAVE ROVER 或 HIL 相关实现。

## 优先级和验收口径

| 优先级 | 用户可感知价值 | 验收口径 |
| --- | --- | --- |
| P0 SQLite backend | 云中转状态不再只停留在 file-backed proof | 显式设置 SQLite backend 后 relay 可启动并读写 state。 |
| P0 commands recovery | 手机命令不会因 relay 重启无声丢失 | command 写入、重启、robot poll 后仍符合既有语义。 |
| P0 status recovery | 手机可继续看到最近机器人状态 | status 写入、重启、查询后 shape 兼容且 phone-safe。 |
| P0 ack recovery | ACK/cursor 轨迹可复盘 | ACK 写入、重启、查询或 cursor 语义保持，不伪造 delivery。 |
| P0 Preflight boundary | 避免把 SQLite proof 写成生产完成 | preflight 输出 software proof、production DB/queue 缺口和 phone-safe warning。 |
| P0 Compatibility fence | robot bridge 不被云端实现细节破坏 | status-command-ack tests 通过，失败不推进 cursor。 |
| P1 Docs/sprint evidence | 后续团队能接力真实 staging | `tech-done.md` 记录命令、输出、失败定位和剩余风险。 |

## 对应责任 Engineer

- 主责：`full-stack-software-engineer`
  - SQLite state backend。
  - commands/status/acks recovery proof。
  - preflight backend boundary。
  - targeted relay tests/smoke。
  - 必要 `docs/product/` 同步和当前 sprint `tech-done.md`。
- 支撑：`robot-software-engineer`
  - remote bridge compatibility acceptance。
  - 确认 status-command-ack 与 cursor/ACK conservative semantics 未变。
- Product Acceptance：`product-okr-owner`
  - 检查 O6 证据边界。
  - 维护后续 `side2side_check.md`、`final.md` 和必要 OKR 保守更新。

## 风险、阻塞和需要补齐的证据链

- SQLite 是 local/Docker 单实例 proof，不等于生产 DB/queue、多实例一致性、备份或灾备。
- 如果 SQLite backend 只能在真实云资源下运行，说明本轮设计过重，应退回 Docker-only proof。
- 如果实现改变 HTTP API shape 或 robot polling semantics，必须优先修复兼容性。
- 如果 preflight 输出把 SQLite pass 写成 production ready，必须改回 software proof 边界。
- O5 只能获得 phone-safe readiness 支撑；正式手机 UI 不在本轮验收范围。
- O1/O2/O3/O4 不因本轮 state store proof 变化提升。
