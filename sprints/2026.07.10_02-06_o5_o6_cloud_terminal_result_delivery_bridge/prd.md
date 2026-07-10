# O5/O6 Cloud Terminal Result Delivery Bridge PRD

## 用户价值

普通用户最终只关心任务有没有真实完成。运营和支持同学需要从云端命令结果主路径追到同一 `task_id` 的送达结果证据，而不是在 O5 command/result、O6 archive detail 和 O7 workstation 之间手工对照。

本轮把已经存在的 robot-facing `cloud_command_terminal_result` 软件终态，纳入 O6/O7 delivery result evidence 读模型，让 closure packet 的“delivery record/operator confirmation”缺口可以直接消费云端主路径材料。

## 需求

1. field route evidence manifest 支持读取 `trashbot.cloud_command_terminal_result.v1` 安全 JSON。
2. 该输入被转换为标准 `trashbot.delivery_result_evidence.v1`，沿用既有 O6/O7 合同。
3. 转换必须保持 same task lineage：输入 `command_id` / `task_record_ref` 可作为 safe refs，不得覆盖 manifest 主 `task_id`。
4. O6 readback 必须保留 `source_schema=trashbot.cloud_command_terminal_result.v1`、`source=cloud_command_terminal_result` 等安全来源信息。
5. O7 不需要新增控制入口；现有 delivery result evidence UI 只读展示即可。

## 非目标

- 不声明真实送达成功。
- 不把 terminal ACK、terminal result 或 operator claim 当成 verified delivery success。
- 不连接真实 production DB/queue、OSS/CDN、TLS/4G。
- 不引入新的 O7 UI action、提交、控制或发车能力。

## 验收标准

- Algorithm 单测覆盖 ready、schema mismatch、危险 true/unsafe text fail-closed。
- O6 单测覆盖 field evidence 或 artifact bundle 携带该来源后，consumer detail / include 可回读。
- 文档说明 cloud terminal result bridge 的证据边界与未证明项。
- 验证命令通过，若失败需 owner 定位并返工。
