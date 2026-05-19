# Sprint 2026.05.20_04-05 PR5 Vendor Source Review Reply Dispatch - Pre Start

## 1. Sprint 类型和启动原因

- sprint_type: epic
- Sprint 主题：`pr5_vendor_source_review_reply_dispatch`
- 启动时间：2026-05-20
- 启动来源：Automation `skill-progression-map` 要求开始下一轮迭代，基于近期 PR/评审推荐并推进最低可执行 OKR。
- 本轮目标：把 03-04 的 `pr5_vendor_source_review_packet` 推进为可发布到 GitHub unresolved review thread `PRRT_kwDOSWB9286CJ3tX` 的 fail-closed reply-dispatch 能力。

## 2. 已读资料和事实来源

- `AGENTS.md`：确认本轮为 Epic sprint，必须写 `pre_start.md -> prd.md -> tech-plan.md` 后进入实现；实现阶段需由对应 Engineer worker 执行。
- `OKR.md` 4.1：Objective 5 当前约 68%，为最低数值；Objective 1 当前约 81%；Objective 4 当前约 99%。
- `sprints/2026.05.20_03-04_pr5-vendor-source-review-packet/tech-done.md` 和 `final.md`：上轮只完成 repo-local / Docker-only `software_proof_docker_pr5_vendor_source_review_packet_gate`，`PRRT_kwDOSWB9286CJ3tX` 仍 `not_proven`。
- `docs/vendor/VENDOR_INDEX.md`：本地 vendor tree 可作为 WAVE ROVER、Orange Pi、UART JSON、firmware/vendor app 的 source boundary；不能证明项目 2D LiDAR / ToF 真实 SKU、采购、安装、接线、电源、标定或 HIL-entry。
- GitHub live PR #5 review threads：PR #5 已 merged/closed；`PRRT_kwDOSWB9286CJ3tQ` 与 `PRRT_kwDOSWB9286CJ3tU` resolved；`PRRT_kwDOSWB9286CJ3tX` unresolved，评论要求 “Cite vendor sources for new mandatory sensor assumptions”。

## 3. 上轮未完成项和本轮边界

上轮 03-04 已经把 PR #5 vendor/source review 缺口整理成 packet、Robot diagnostics safe alias 和 mobile/web 只读展示，但没有生成可直接发到 GitHub review thread 的 reply Markdown，也没有把 reply 的安全边界做成机器可复核的 dispatch artifact。

本轮只推进 reply-dispatch 软件能力：

- 生成 GitHub review-thread reply Markdown / summary。
- 明确 local `docs/vendor/` 只证明 source boundary。
- 明确 2D LiDAR / ToF 仍为 `hardware_material_pending` / `not_proven`。
- 明确 Robot diagnostics 和 mobile/web 只能只读展示，不打开 Start Delivery / Confirm Dropoff / Cancel。
- Product closeout 不提高 Objective 5、Objective 1 或 Objective 4 完成度。

## 4. 同一 Blocker 重复消费核对

最近 `2026.05.20_00-01_cloud-ack-outage-replay-guard`、`2026.05.20_01-02_cloud-pending-ack-status-guard`、`2026.05.20_02-03_cloud-command-expiry-safety-guard` 已连续做本地 O5 command/status/ACK guard，但 O5 外部材料仍缺。本轮不继续 O5 local metadata depth。

最近 `2026.05.20_03-04_pr5-vendor-source-review-packet` 只做了 review packet。本轮不是第三次包装同一个 “缺真实材料” blocker，而是把已形成的 packet 变成可发布、可审查、可 fail-closed 的 review reply dispatch。它仍不关闭真实材料 blocker。

## 5. Owner 和进入实现条件

本轮为跨 owner Epic，计划完成后进入实现阶段，默认并行派发：

- `hardware-engineer`：reply dispatch artifact / Markdown source-boundary semantics。
- `robot-software-engineer`：Robot diagnostics reply-dispatch safe alias。
- `full-stack-software-engineer`：mobile/web 只读展示 reply-dispatch 状态。
- `product-okr-owner`：验收口径、GitHub reply 文案边界、OKR closeout。

进入实现前必须满足：

- `prd.md` 明确用户价值、OKR 映射、KR 拆解、优先级和验收口径。
- `tech-plan.md` 明确 owner、文件范围、接口影响、验收命令和 `OKR 最低优先级核对`。
- 本计划阶段不得修改 `OKR.md`、`docs/process`、产品代码、测试代码或其他 sprint。
