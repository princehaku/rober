# O7 Consumer Detail Labeling Queue PRD

## 1. 用户价值和产品北极星

`rober` 的北极星不是把 PC 页面堆满，而是让运营和开发者能够基于真实任务存档快速判断问题、复盘证据并准备后续训练或标注工作。

这轮的用户价值很具体：**让操作员在 PC 端看到一份可检查、可追溯、只读的标注队列视图**，直接来自 O6 consumer detail 的 `labeling / evidence / events / trajectory` 语义。这样做的意义不是“多一个页面”，而是把 O7 的数据标注入口从静态 fixture 变成能和真实任务语义对齐的主路径。

## 2. 要解决的问题

1. 操作员需要在 O7 Previews 中检查待标注任务的证据链，而不是反复翻 archive fixture。
2. 标注入口需要和 route replay 使用同一份 consumer-detail 语义，避免任务、证据、事件、轨迹各做一套映射。
3. 标注界面必须明确只读边界，不能把 preview 误设计成可提交、可导出、可回滚的真实生产动作。

## 3. 目标范围

本轮只做 O7 KR4 的一个完整功能点：**O6 consumer detail 驱动的只读标注队列检查视图**。

范围内能力：

- 从 consumer detail 加载 task 后，展示标注队列检查所需的最小信息。
- 只展示白名单摘要：`labeling`、`evidence`、`events`、`trajectory` 的限量字段。
- 显示当前标注状态、待审阅项、证据引用、事件摘要、轨迹摘要和失败/阻塞原因。
- 保持视图是只读的，`submit`、`export`、`rollback` 关闭。
- 保持 fail-closed 文案，不把 mock / fixture / blocked 状态说成真实完成。

## 4. 非目标

- 不做真实标注服务后端，不新增生产 API，不改 O6 consumer read contract。
- 不开放 submit / export / rollback / retry / control 类操作。
- 不证明真实云端数据集、真实训练流水线、真实 OSS、真实生产 DB 已接通。
- 不把 O7 labeling queue 伪装成训练平台或数据生产流水线。

## 5. KR 映射

| O7 KR | 本轮关系 | 说明 |
| --- | --- | --- |
| KR4 数据标注 / 打标界面 | 直接推进 | 这是本轮主目标 |
| KR3 历史路线回放 | 强关联 | labeling 依赖同一份 consumer-detail 轨迹和证据链 |
| KR5 ASR/TTS | 间接关联 | 同一套 task detail 语义未来可承载语音证据 |
| KR6 手控 / 寻路 | 间接关联 | 统一证据链后才方便挂接安全控制审计 |

## 6. 体验原则

- 默认只读，默认关闸，默认 fail closed。
- 页面中的“可用”只能表示可检查，不表示可提交。
- 页面中的“导出”“回滚”“提交”必须保持关闭态，直到单独的真实能力与验收证据到位。
- 缺 detail、缺 labeling、缺 evidence、缺 events、轨迹缺失、任务未知或 blocked 时，必须明确提示，不得自动降级成“空状态成功”。

## 7. 验收标准

- O7 Previews 中能够从 consumer detail 进入只读标注队列检查视图。
- 视图至少展示 labeling / evidence / events / trajectory 的限量摘要。
- `submit`、`export`、`rollback` 明确关闭。
- 缺数据或危险字段时 fail closed，不展示真实标注成功、真实导出成功或真实回滚成功。
- 对应 sprint 文档、产品文档和测试证据一起更新。
