# O7 Artifact Bundle Consumer Readiness Pre-Start

- sprint_type: epic
- start_time: 2026-07-09 09:57 CST
- product_owner: product-okr-owner
- target_objectives: O7
- secondary_objective: O6 consumer compatibility only
- primary_owner: full-stack-software-engineer

## 上轮状态

最近一轮 `sprints/2026.07.09_08-56_o6_artifact_bundle_ingest/` 已完成 O6 `POST /api/o6/archive/artifact-bundle`，并让 archive task detail / consumer detail 暴露 `artifact_bundle` / `artifact_bundle_consumer_ingest` alias。

这意味着 O6 写入侧的 bundle 入口已经就位，但 O7 侧仍只是在消费预备态，没有把 `artifact_bundle` / `artifact_bundle_consumer_ingest` 显式转成面向 PC 用户的 readiness 摘要。

## 本轮目标

本轮直接针对 O7 KR3 / KR4，把 PC O7 consumer detail 主路径改成显式消费 O6 `artifact_bundle` / `artifact_bundle_consumer_ingest`，并产出 `artifact_bundle_readiness` 或同等命名的摘要：

- 同一 `task_id` 下的 route / replay / keyframe / evidence / review item 计数。
- 样本 refs、blocked reasons、next required evidence。
- route replay / labeling 的阻塞原因和样本媒体 refs 优先从 bundle / preflight 读取。
- 所有危险字段保持 false，不声明真实云、真实媒体、真实送达或真实生产能力。

本轮不是新增 O6 写入入口，也不是真实硬件集成。

## Blocker 核对

- 最近两轮 sprint final 都是验收通过，不存在同一 blocker 连续消费到第 3 轮的情况。
- 真实生产云、真实 OSS/CDN、真实媒体可访问、真实 annotation API、真实 dataset export、真实 RTC/视频、真实 ASR/TTS、真实机器人运动都仍未到位；本轮不等待这些条件，直接推进 O7 consumer readiness 的软件侧合同。
- 这轮必须避免把 O6 再写一层 wrapper 当成 O7 进展；目标是消费 O6 bundle，而不是重复堆 O6 写入侧。

## 验收口径

- O7 consumer detail 主路径必须显式读取 O6 bundle / preflight 信息，并落到 `artifact_bundle_readiness` 级别摘要。
- readiness 摘要必须包含计数、样本 refs、blocked reasons、next required evidence。
- route replay / labeling 必须优先展示来自 bundle / preflight 的阻塞原因和样本媒体 refs。
- 所有危险字段继续 fail-closed，不能把 local/mock / not_proven 误写成真实可用。
- sprint `tech-done.md` 需要记录实际改动、验证结果和剩余风险，Epic 收口时还要补 `side2side_check.md` 和 `final.md`。
