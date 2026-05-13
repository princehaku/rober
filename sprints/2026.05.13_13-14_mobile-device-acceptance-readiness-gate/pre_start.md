# Sprint 2026.05.13_13-14 Mobile Device Acceptance Readiness Gate - Pre Start

## Sprint 声明

- sprint_type: epic
- 主目标：Objective 4 手机用户体验与低成本量产边界。
- 证据边界：Docker/local software proof only；本机没有真实手机设备、真实云、4G、Nav2/fixed-route、WAVE ROVER 或 HIL。

## 启动依据

1. `OKR.md` 4.1 当前最低完成度是 Objective 4 约 64%，Objective 5 已在 `2026.05.13_12-13_cloud-db-queue-external-probe-gate` 上调到约 65%。
2. `sprints/2026.05.13_11-12_mobile-cloud-readiness-summary-gate/final.md` 明确剩余风险包括真实手机设备/browser、production app、真实 PWA install prompt、真实云/4G、机器人运动和真实送达证据。
3. `sprints/2026.05.13_12-13_cloud-db-queue-external-probe-gate/final.md` 建议下一轮按 Objective 4 推进手机用户体验/量产边界，除非 CEO 指定继续攻坚真实云 DB/queue。
4. `docs/product/mobile_user_flow.md` 已有本地 browser acceptance gate、PWA installability gate、action feedback、cloud readiness summary，但普通手机用户仍缺一个首屏可见的“设备/浏览器验收准备状态”来解释为什么当前还不是 production app 或真实手机验收。

## 本轮抓手

把“真实手机/browser/production app 缺口”产品化为 phone-safe readiness gate：

- 手机首屏展示 mobile device acceptance readiness，说明 viewport/touch target/PWA/offline/diagnostics/cloud gate 是否达到本地软件证明。
- 缺少真实设备、production app、真实云或机器人证据时继续 fail closed，不打开 Start/Confirm/Cancel。
- robot remote bridge/protocol 证明该 metadata-only readiness 不触发 backend action、不 POST ACK、不推进 cursor。

## Owner

- `full-stack-software-engineer`：mobile UI、fixture、static smoke、产品/接口文档。
- `robot-software-engineer`：robot metadata-only compatibility fence 和接口文档。
- `product-okr-owner`：待 A/B 完成后更新 sprint closeout、OKR 和进度日志。

## 风险

- 本轮不能证明真实 iPhone/Android、真实安装提示、production app、真实云/4G、Nav2/fixed-route、WAVE ROVER 或 HIL。
- 不把 browser/unit/static smoke 描述成真实手机验收。
- 不新增广泛测试，只保留 targeted mobile static smoke、robot compatibility fence、`py_compile` 和 scoped diff check。
