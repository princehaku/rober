# Sprint 2026.05.19_13-14 Mobile PWA Cache Recovery - Tech Plan

## sprint_type: epic

Run time: 2026-05-19 13:05 Asia/Shanghai。

## 1. 技术目标

实现 `mobile_pwa_cache_recovery_gate`：让本地 `mobile/web` PWA 的 service-worker/cache/version/offline shell recovery 能摆脱旧 offline shell，使 Browser QA 可以复核当前手机入口。该目标仅是 Objective 4 touchpoint 的 `software_proof` 修复，不证明真实手机、真实 PWA prompt/user choice、Objective 5 external proof、Objective 1 HIL、PR #4 field pass 或 PR #5 hardware materials。

## 2. OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5，约 68%。
- 本 sprint 是否针对该最低 Objective：否。
- 不针对理由：Objective 5 当前下一步需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实 external proof；当前本机只有 Docker，继续本地 O5 wrapper 不能提高真实 O5 进度。
- 下一低项：Objective 1，约 81%。Objective 1 需要真实 WAVE ROVER/UART/HIL 与 PR #5 2D LiDAR / ToF 真实材料；10-11 sprint 已做硬件真实材料升级请求，本轮不能再包装同一 blocker。
- 本轮选择 Objective 4 touchpoint bugfix 的理由：最新 sprint 的 Browser QA 失败是可在本机推进的真实缺口，且直接影响后续手机入口可验证性；本轮不宣称真实手机/browser 通过。
- final.md 收口时需复核：O5/O1 真实材料是否仍不可用；Browser QA recovery 是否只作为 `software_proof` 记录。

## 3. 分工和文件范围

### 3.1 Full-Stack 主责：`full-stack-software-engineer`

允许改动范围：

- `mobile/web/service-worker.js`
- `mobile/web/offline.html`
- `mobile/web/app.js`
- `mobile/web/manifest.webmanifest`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`
- 当前 sprint 的 `tech-done.md`、`side2side_check.md`、`final.md` 中 Full-Stack 相关段落

实现要求：

- 梳理 service-worker cache name/version，必要时 bump cache version 并在 activate 阶段清理旧 cache。
- 确保 fetch/offline fallback 不会让旧 offline shell 长期覆盖当前 app shell。
- Offline shell recovery 只能展示恢复/刷新路径，不启用 Start Delivery、Confirm Dropoff、Cancel，不暗示 delivery success。
- 所有新增技术注释必须使用中文，并维持代码注释比例超过 20%。
- 更新 `docs/product/mobile_user_flow.md`，写清 `mobile_pwa_cache_recovery`、`service-worker`、`offline shell`、`software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

验收命令：

```bash
python3 mobile/web/test_mobile_web_entrypoint.py
python3 -m py_compile mobile/web/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
node --check mobile/web/service-worker.js
rg -n "mobile_pwa_cache_recovery|service-worker|offline shell|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" mobile/web docs/product/mobile_user_flow.md sprints/2026.05.19_13-14_mobile-pwa-cache-recovery
git diff --check -- mobile/web docs/product/mobile_user_flow.md sprints/2026.05.19_13-14_mobile-pwa-cache-recovery
```

如本地 browser 工具可用，补充 Browser QA：

```bash
# 由 full-stack-software-engineer 选择 repo 现有本地 server/browser 入口执行。
# 目标：清理或绕过旧 service worker/cache 后截图当前 mobile/web shell。
```

### 3.2 Robot 只读咨询：`robot-software-engineer`

允许范围：

- 只读查看 `mobile/web` 相关 diff、现有 command gating 文档和 sprint 计划。
- 不修改产品代码、Robot 代码、测试代码、硬件配置或 launch 参数。

咨询要求：

- 确认本轮不改变 Start Delivery、Confirm Dropoff、Cancel gating。
- 确认 cache recovery 不触发 robot commands、ACK、cursor、diagnostics fetch、ROS2 topic/service/action 或 `/cmd_vel`。
- 明确 `delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false` 仍成立。

验收命令：

```bash
rg -n "Start Delivery|Confirm Dropoff|Cancel|command_safety|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|/cmd_vel|ACK|cursor|diagnostics fetch" mobile/web docs/product/mobile_user_flow.md sprints/2026.05.19_13-14_mobile-pwa-cache-recovery
```

### 3.3 Product 收口：`product-okr-owner`

允许改动范围：

- `sprints/2026.05.19_13-14_mobile-pwa-cache-recovery/tech-done.md`
- `sprints/2026.05.19_13-14_mobile-pwa-cache-recovery/side2side_check.md`
- `sprints/2026.05.19_13-14_mobile-pwa-cache-recovery/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
- 必要的 `docs/product/` 收口文档段落

收口要求：

- 只有 Full-Stack 和 Robot evidence 到位后再收口。
- Objective 5 不提高，Objective 1 不提高。
- Objective 4 只记录本地 Browser QA cache recovery 的 `software_proof`；不得宣称真实手机/browser、production app、真实 PWA prompt/user choice 或 external proof。
- 如果 Browser QA 仍失败，必须写清失败定位：service-worker 缓存、旧 offline shell、截图命令超时、browser 工具限制或其他原因。

验收命令：

```bash
rg -n "mobile_pwa_cache_recovery|Objective 5|Objective 1|Objective 4|PR #4|PR #5|Browser QA|service-worker|offline shell|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" OKR.md docs/process/okr_progress_log.md docs/product/mobile_user_flow.md sprints/2026.05.19_13-14_mobile-pwa-cache-recovery
git diff --check -- OKR.md docs/process/okr_progress_log.md docs/product/mobile_user_flow.md sprints/2026.05.19_13-14_mobile-pwa-cache-recovery
```

## 4. 接口影响

- 不新增 ROS2 topic/service/action。
- 不新增 robot command。
- 不修改 `/api/collect`、`/api/dropoff/confirm`、`/api/cancel` payload contract。
- 不改变 Start Delivery、Confirm Dropoff、Cancel 的既有 `command_safety` 和 legacy gate 组合。
- 不引入 Objective 5 cloud/production dependency。

## 5. 验收口径

本轮完成条件：

- Browser QA 不再停留在旧 offline shell；或仍失败但有明确定位和下一步修复点。
- `mobile/web` service-worker/cache/offline shell recovery 有 targeted test/static validation。
- `docs/product/mobile_user_flow.md` 明确记录 `mobile_pwa_cache_recovery_gate`。
- Sprint 收口文档明确 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

本轮不接受的完成口径：

- 把 Browser QA 截图通过写成真实手机通过。
- 把 offline shell recovery 写成 delivery success。
- 因 cache recovery 放开 Start Delivery、Confirm Dropoff 或 Cancel。
- 把本地 Docker/browser evidence 写成 Objective 5 external proof、Objective 1 HIL、PR #4 field pass 或 PR #5 hardware proof。

## 6. 风险和回滚边界

- Service-worker 策略容易影响已安装 PWA 的旧缓存；Full-Stack 必须优先保证旧缓存可清理、离线可恢复、失败可解释。
- Offline fallback 不能吞掉当前 app shell 的正常加载；如果 fetch 策略变更导致当前 shell不可达，必须回滚或改为更保守的 network-first/app-shell 策略。
- 所有 cache recovery 逻辑必须保持 phone-safe，不暴露 raw JSON、ROS topic、`/cmd_vel`、serial/UART、baudrate、credentials、DB/queue URL、OSS AK/SK、本地路径、traceback、checksum、完整 artifacts 或 success/control copy。

## 7. 主节点规划阶段验收

当前阶段只创建规划文件，不进入实现，不写 `tech-done.md`、`side2side_check.md`、`final.md`。

必须通过：

```bash
test -f sprints/2026.05.19_13-14_mobile-pwa-cache-recovery/pre_start.md && test -f sprints/2026.05.19_13-14_mobile-pwa-cache-recovery/prd.md && test -f sprints/2026.05.19_13-14_mobile-pwa-cache-recovery/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|Objective 1|Objective 4|PR #4|PR #5|Browser QA|service-worker|offline shell|mobile_pwa_cache_recovery|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|full-stack-software-engineer|product-okr-owner" sprints/2026.05.19_13-14_mobile-pwa-cache-recovery
git diff --check -- sprints/2026.05.19_13-14_mobile-pwa-cache-recovery
```
