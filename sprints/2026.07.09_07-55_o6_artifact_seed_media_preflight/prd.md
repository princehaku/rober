# O6 Artifact Seed Media Preflight PRD

## 用户价值

运营人员拿到现场包后，需要能把 `route.csv`、replay JSONL、keyframe/media ref 放进统一 O6 archive，并在 PC 工作台判断这些材料是否足够用于路线回放和标注，而不是手工拼文件路径或只看 manifest 字符串。这个能力直接服务“可复盘、可打标、可训练”的核心后端方向。

## 目标

1. O6 提供本地/mock artifact seed 合同：围绕同一 `task_id` 安全生成或接收 route/replay/keyframe/evidence 摘要，并可通过 archive detail 和 consumer detail 回读。
2. O7 PC 消费 O6 consumer detail 的新增 artifact/media 状态，展示 route replay 与 labeling 使用的媒体可访问性、缺口和 fail-closed 边界。
3. 保持真实能力边界：不读取生产 OSS，不连接生产 DB，不下发控制，不声明媒体真实可访问或投递成功。

## 非目标

- 不实现真实 OSS/CDN 上传或下载。
- 不实现真实生产 annotation API、rollback/autosave 或训练 worker。
- 不启动 ROS2 runtime、SSH 上车、Nav2 或底盘控制。
- 不改变 O1/O3/O5 的真实硬件/现场验收结论。

## 验收标准

- O6 local/mock archive 有可测试的 artifact seed/readback 主路径，并覆盖 unsafe path/token/raw content fail-closed。
- O7 consumer adapter/UI 能显示 O6 detail 派生的 media/artifact preflight 状态，且危险 true 字段仍 fail-closed。
- sprint `tech-done.md` 记录实际改动、验证结果和剩余风险；Epic 收口补 `side2side_check.md` 和 `final.md`。

## OKR 映射

- O6 KR2/KR3/KR6：任务记录、轨迹、事件和 evidence refs 的 archive/read model 继续增强。
- O7 KR3/KR4：PC 历史回放和标注工作台从本地 mock UI 前进到消费 O6 artifact/media 状态。

本轮若通过，只能保守提升 O6/O7 软件侧进度，不归档任何 KR。
