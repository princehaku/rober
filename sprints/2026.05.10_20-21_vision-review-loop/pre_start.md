# Sprint 2026.05.10 20-21 Vision Review Loop - Pre Start

## 状态

- 阶段：pre_start completed。
- 时间：2026-05-10 20:12 Asia/Shanghai。
- Product Owner：`product-okr-owner`。
- 实现 owner：`full-stack-software-engineer`。
- Sprint：`sprints/2026.05.10_20-21_vision-review-loop/`。

## 用户价值和产品北极星

当前 operator 端的 vision review queue 只能看不能做，导致“发现可疑样本 -> 人工判定 -> 状态闭环”断在最后一步。用户价值是把人工复核从提示升级为可执行动作：operator 能直接对队列样本给出 review decision 并落盘，让后续排障、模型改进和任务复盘有可追溯证据。

本轮仍服务北极星：面向普通手机用户的低成本垃圾投递机器人，需要可解释、可复盘、可维护的感知闭环，而不是只显示状态不产出决策。

## OKR 映射

- 主目标：Objective 4（感知模块产品化）
  - 推进 KR3：把样本目录/manifest 从“只读证据”推进到“可写复核结论”。
  - 推进 KR4：行为/产品链路依赖稳定 contract，不耦合具体视觉算法；人工判定作为可选但可执行闭环。
- 次目标：Objective 5（手机触点可用性）
  - 让 operator 能在一个入口完成“看队列 + 给结论”，减少人工线下记账。

## KR 拆解或更新

- 新增 sprint KR-A：operator 支持提交 review decision（如 `approved` / `rejected` / `needs_retry`）并附带 reason/comment。
- 新增 sprint KR-B：decision 以结构化 JSONL 或等价落盘格式写入本地 artifact，并携带 sample_id、timestamp、operator、source_ref。
- 新增 sprint KR-C：queue 视图可反映已判定状态，避免重复判定同一样本。
- 新增 sprint KR-D：保留测试护栏，仅覆盖 API contract、落盘成功/失败、重复提交幂等或冲突提示等关键路径。

## 本轮核心抓手

- 把 queue 从“只读提示”变成“可执行人工复核闭环”。
- 以最小改动打通：operator UI -> review API -> decision store -> queue 状态回显。
- 测试定位为护栏，不做大规模回归扩写。

## 做什么 / 不做什么

做：

- 增加 review decision 写接口与落盘逻辑。
- 在 operator 端增加可提交判定的交互（按钮/最小表单）。
- 增加关键护栏测试并保留现有链路稳定性。

不做：

- 不做真实硬件/HIL，不接入真实相机或上车验证。
- 不做模型训练、自动重标注平台、云端账号权限系统。
- 不重构整套 vision pipeline，只做本轮功能切片闭环。

## 优先级和验收口径

- P0：operator 可对 queue 样本提交 review decision，接口返回成功并可追溯。
- P0：decision 可落盘，字段完整（sample_id、decision、reason/comment、timestamp、operator/source）。
- P0：queue 状态能体现“待判定/已判定”，避免误判重复提交。
- P0：本轮约定验收命令通过（见 tech-plan）。
- P1：错误场景（文件不可写、非法 decision、样本不存在）有可读报错。

## 对应责任 Engineer

- 主责实现与验证：`full-stack-software-engineer`。
- Product 负责范围边界、验收口径和 sprint 收口，不直接实现代码。

## 风险、阻塞和需要补齐的证据链

- 风险：若 decision schema 不稳定，后续统计和复盘会碎片化。
- 风险：并发判定/重复提交可能造成状态覆盖，需要最小冲突策略。
- 阻塞：若现有 queue 数据结构没有稳定 `sample_id`，需先在实现中补齐唯一标识策略。
- 证据缺口：本轮不含真实 HIL/硬件链路，不能把软件闭环等同于上车可用。

## 需要创建或更新的 sprint 文档

本轮已创建并完成：

- `sprints/2026.05.10_20-21_vision-review-loop/pre_start.md`
- `sprints/2026.05.10_20-21_vision-review-loop/prd.md`
- `sprints/2026.05.10_20-21_vision-review-loop/tech-plan.md`

后续实现阶段必须更新：

- `sprints/2026.05.10_20-21_vision-review-loop/tech-done.md`
- `sprints/2026.05.10_20-21_vision-review-loop/side2side_check.md`
- `sprints/2026.05.10_20-21_vision-review-loop/final.md`
