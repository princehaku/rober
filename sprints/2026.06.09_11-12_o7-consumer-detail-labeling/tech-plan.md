# O7 Consumer Detail Labeling Queue Tech Plan

## sprint_type

sprint_type: epic

## 1. 技术方案概述

本轮采用单 owner、单主路径的实现方式，由 `full-stack-software-engineer` 负责把现有 O7 Previews / consumer-detail 语义收敛成只读标注队列检查视图。

实现思路是：

1. 复用现有 O6 consumer read / consumer detail 语义，不新增生产接口。
2. 在 PC workstation 内把 `labeling / evidence / events / trajectory` 摘要映射成标注队列 UI 的只读视图模型。
3. 保持 submit / export / rollback 关闭，所有危险状态继续 fail closed。
4. 把测试和文档一起同步更新，确保 O7 的 labeling 主路径可以被复盘和验收。

## 2. 任务分工

- `full-stack-software-engineer`
  - 负责 workstation 前端组件、视图模型、状态机、按钮开关、空态 / 阻塞态 / 危险态文案、测试和文档同步。
  - 负责让 labeling queue 主路径从 consumer detail 中生成，而不是继续依赖独立 fixture。
- `product-okr-owner`
  - 负责验收口径、范围收口、方向判断和 sprint 留档复核。

本轮不拆多 owner，不并行派多个工程师。原因是这是一条强耦合的 PC workstation 单线主路径，接口和 UI 状态都集中在同一套前端语义里，单 owner 更容易把 fail-closed 边界写死。

## 3. 文件范围

允许工程实现的主要文件范围：

- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/test/App.test.ts`
- `pc-tools/workstation/README.md`
- `docs/product/pc_tools_workstation.md`

说明：

- 组件层负责 labeling queue 的页面态和交互态。
- server adapter 如需补齐 consumer-detail 摘要字段归一化，可在 workstation 内完成，但不得扩展为新的生产接口。
- 测试必须覆盖只读边界和 fail-closed 语义。
- 文档同步必须写清主路径、边界和残余风险。

## 4. 接口影响

本轮不改 O6 consumer read 生产契约，不新增对外生产 API。

可能涉及的 workstation 内部接口影响仅限于：

- O7 Previews 页面内部状态模型增加 labeling queue 的 consumer-detail 主路径。
- `labeling / evidence / events / trajectory` 的摘要展示字段与顺序固定化。
- 关闭态能力显式增加 `submit_enabled=false`、`export_enabled=false`、`rollback_enabled=false` 或等价 fail-closed 字段。

必须保持的外部边界：

- 不直连机器人。
- 不发送命令。
- 不暴露真实 bearer / token / credentials。
- 不把 local/mock / fixture 状态解释成真实生产成功。

## 5. 验收命令

工程实现完成后，必须至少跑以下命令并给出结果：

```bash
cd pc-tools/workstation && npm run build
cd pc-tools/workstation && npm run test
cd pc-tools/workstation && npm run lint
git diff --check
```

说明：

- `build/test/lint` 证明 workstation UI、类型、测试和静态质量。
- `git diff --check` 证明没有新增 whitespace / patch formatting 问题。
- 如 build 或 test 失败，必须先定位并修复，再重新验证，不得把首轮失败直接作为收口。

## 6. 风险边界

1. `labeling queue` 可能被误做成“可提交页面”，因此 submit/export/rollback 必须在 UI 与测试中双重关闸。
2. `consumer detail` 可能字段很多，必须只展示白名单摘要，避免 raw payload 泄露或 UI 过载。
3. 如果 summary 映射不统一，后续 route replay、voice、safe command 会重复造字段解析逻辑，因此这轮必须优先固化 consumer-detail 视图模型。
4. 这轮仍然是 local/mock / software proof，不证明真实云端、真实训练流水线或真实标注生产系统已接通。

## 7. OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：**O6 云端核心后端（0%）**。
- 本 sprint 是否针对该 Objective：**否**。
- 如不针对，理由：O6 当前仍缺隧道接入、存档、打标 API 和推理接口的更底层工作；上一轮已把 O6 consumer read 语义转成 O7 route replay 主路径，本轮继续沿同一 consumer-detail 语义推进 O7 KR4，可避免重复消费 O6 的读模型工作，并把现有数据结构真正转成 PC 运营调试价值。
- final.md 收口时需复核：上述理由是否仍成立，还是应把下轮抓手切回 O6 最低 Objective。

## 8. 设计完成后的执行要求

本轮设计完成后，工程实现必须一次性交付到可验收状态，不得只交 PRD 或只交视觉稿。实际验收要看：

- 只读标注队列检查视图是否真的基于 consumer detail。
- submit/export/rollback 是否真的关闭。
- 缺数据、blocked、危险字段时是否真的 fail closed。
- 文档和测试是否真的同步更新。
