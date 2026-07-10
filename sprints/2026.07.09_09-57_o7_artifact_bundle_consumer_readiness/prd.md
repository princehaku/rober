# O7 Artifact Bundle Consumer Readiness PRD

## 用户价值

PC 端运营和调试人员拿到同一个 `task_id` 的现场或离线材料后，需要一眼看出：

- 这份材料里有哪些 route / replay / keyframe / evidence / review item。
- 哪些媒体样本可以被用来回放或标注，哪些还被阻塞。
- 下一步还缺什么证据，才能进入更高置信度的回放或标注工作。

如果这些信息仍分散在多个 wrapper、多个摘要或多个局部页面里，运营人员就只能手工拼接线索，无法稳定判断数据是否可用。本轮要把 O7 consumer detail 主路径变成明确的 `artifact_bundle_readiness` 视图，帮助后续回放、标注和训练数据准备。

## 目标

1. O7 consumer detail 主路径显式消费 O6 `artifact_bundle` / `artifact_bundle_consumer_ingest`。
2. 生成 `artifact_bundle_readiness` 或同等命名摘要，汇总同一 `task_id` 的计数、样本 refs、blocked reasons、next required evidence。
3. route replay / labeling 优先使用 bundle / preflight 里的阻塞原因和样本媒体 refs，而不是继续依赖旧的 debug fallback。
4. 保持所有危险字段 false，不把 local/mock 证据包装成真实生产能力。

## 非目标

- 不新增 O6 写入入口。
- 不做真实生产云、真实 OSS/CDN、真实媒体下载、真实 annotation API、真实 dataset export。
- 不做真实 RTC/视频、真实 ASR/TTS、真实机器人运动或真实送达结果证明。
- 不扩展到新的硬件集成或底盘控制路径。

## 验收标准

- O7 consumer detail 可从 O6 bundle / preflight 计算出稳定的 readiness 摘要。
- readiness 摘要覆盖 route / replay / keyframe / evidence / review item 计数，样本 refs，blocked reasons，next required evidence。
- route replay 与 labeling 页面优先显示 bundle 里读到的阻塞原因和媒体 refs。
- 危险字段和真实能力字段继续 fail-closed。
- 对应 sprint 文档完整，且验证命令可落地执行。

## OKR 映射

- O7 KR3：历史路线回放从局部 mock 视图前进到消费 bundle / preflight 的统一 readiness 摘要。
- O7 KR4：数据标注界面从单独的本地 fixture 前进到与 O6 bundle 联动的可用性判断。
- O6 仅作为 consumer compatibility 的 secondary objective，不追求新的写入能力。

## 方向判断

本轮方向是继续推进 O7，且以 O6 兼容消费为抓手。这里的产品结果不是“更多后端写入”，而是“PC 端更快判断材料是否可用、哪里被阻塞、下一步该补什么证据”。
