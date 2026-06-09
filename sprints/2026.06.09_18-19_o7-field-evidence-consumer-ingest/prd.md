# PRD - O7 Field Evidence Consumer Ingest

## 1. 问题定义

上一轮已经把 `field_evidence_manifest` 做成了 fail-closed 的软件门禁，但它还没有进入 O7 的实际消费链。结果是：

- 现场材料即使被整理出来，PC 端仍然没有一个可运行入口把它转成路线回放或标注队列。
- 真实 SSH 仍不稳定时，团队容易再次陷入“等待远端材料”而不是推进可验证功能。
- O7 的 route replay / labeling 仍然停留在预览态，缺少一个能承接 manifest 的稳定上游。

## 2. 用户价值

给 operator / reviewer 的价值是把“材料可读”升级成“材料可用”：

- 能从 `field_evidence_manifest` 进入路线回放和标注入口。
- 能在本地 fixture 下完成完整软件验证，不依赖现场 SSH。
- 能在真实 SSH 恢复后直接复用同一套消费链，不需要重写入口。

## 3. 产品北极星

北极星不变，还是让现场路线材料进入可复用的数据闭环。  
这轮的北极星抓手是：**把现场 evidence manifest 变成 O7 可运行的 route replay / labeling consumer。**

## 4. OKR 映射

### 主映射

- **O7：PC 端运营调试与数据训练平台**
  - KR3：历史路线回放
  - KR4：数据标注/打标界面

### 次映射

- **O6：云端核心后端**
  - 作为上游来源和未来扩展，不作为本 sprint 的主交付面

## 5. 本轮范围

### 必做

1. 设计并实现一个 O7 consumer ingest 入口，能消费 `field_evidence_manifest` 和本地 route replay / labeling fixture。
2. 把 manifest 里的 task / evidence / artifact 关系映射到 O7 route replay 和 labeling 视图。
3. 保持 fail-closed：缺少关键材料时，只能返回 blocked / not_proven，不能伪装成真实回放或真实标注成功。
4. 同时支持 local/mock fallback 与 live SSH fallback 的一致输出结构。

### 不做

1. 不把本轮定义成 SSH-only 任务。
2. 不修改 ROS2、底盘、串口、launch 默认值或硬件协议。
3. 不把 preview 误写成真实送达、真实回放成功或真实标注成功。
4. 不把 O6 archive 全量重构塞进同一轮。

## 6. 目标用户和使用场景

### 用户

- Operator：需要在 PC 端查看路线回放、材料覆盖和标注队列。
- Reviewer：需要确认现场证据是否足以进入回放和标注消费链。

### 场景

1. 用户拿到一份 `field_evidence_manifest`。
2. PC 工作台读取本地 fixture 或 live SSH 可达的远端结果。
3. 工作台给出路线回放和标注候选，但仍保留 fail-closed 边界。
4. 如果材料不完整，UI 只能展示 blocked reason 和缺口，不能展示成功态。

## 7. 验收口径

1. 入口可以在 local/mock 条件下运行，不依赖 SSH。
2. 入口可以消费 `field_evidence_manifest`，并把它映射到 O7 route replay / labeling 的可视化数据结构。
3. 当 artifact 不完整时，结果必须 fail-closed。
4. 当 live SSH 不可达时，系统必须仍能完成 local/mock 验收，不把 SSH 不可达当成终止条件。
5. 所有 `safe_to_control`、`delivery_success`、`primary_actions_enabled` 保持 false，直到真实现场证据到位。

## 8. 预期产物

- O7 consumer ingest 的 server 侧适配器
- O7 route replay / labeling 的消费数据契约
- 一组 local fixture 测试
- 一份把 manifest 接入 O7 的文档说明

