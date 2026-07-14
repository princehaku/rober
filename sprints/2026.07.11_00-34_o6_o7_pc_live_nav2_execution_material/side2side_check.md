# O6/O7 PC Live Nav2 Execution Material Side-by-Side Check

## 对照目标

- 计划口径：把已有 PC live Nav2 执行材料安全接入 Algorithm -> O6 -> O7，同步保留 `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`route_execution_success=false`、`hil_pass=false`。
- 实际口径：三段链路都完成，但只消费 prior live material summary，不宣称 current live rerun、delivery、HIL 或左右轮反馈证明。

## 逐项核对

| 检查项 | 计划要求 | 实际结果 | 判定 |
| --- | --- | --- | --- |
| Algorithm additive | 生成 `trashbot.pc_live_nav2_execution_material.v1`，写入顶层和 `field_motion_evidence_packet` | 已完成，并增加 canonical + legacy 双写 | 通过 |
| O6 archive/readback/include | 新增 `trashbot.o6.pc_live_nav2_execution_material.v1`，支持 field/bundle/detail/include | 已完成，且 section-local fail-closed 生效 | 通过 |
| O7 默认消费与展示 | 默认 include，展示 ready 状态、source sprint、goal accepted、UART/base command/IMU 事实和 remaining evidence | 已完成，保持只读显示，不新增动作按钮 | 通过 |
| 固定 false 字段 | `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`route_execution_success=false`、`hil_pass=false` | 全链路保持 false | 通过 |
| 字段漂移修平 | canonical 优先，legacy 兼容，不因 alias 漂移误判 blocked | 已返工完成，集成验收通过 | 通过 |
| claim 边界 | 不声称真实送达、HIL、左右轮非零反馈或生产云完成 | 文档、O6/O7 UI 和产品收口均保持保守 | 通过 |

## 用户价值核对

- 对普通 operator 的价值不是“又多一层 summary”，而是把已有 live Nav2 执行事实放到 O7 主路径里，能直接看清楚：
  - Nav2 goal 是否被 accepted；
  - 是否确实走过 base UART；
  - 是否确实观察到 nonzero base command；
  - 是否有 IMU attitude delta；
  - 为什么仍不能宣称 route execution success、delivery success 或 safe-to-control。

## 验收结论

- 本轮达到 epic sprint 计划中的产品收口标准。
- O6/O7 可以保守上调到约 `~93%`，但只能计作同任务执行材料链路更完整，不是现场任务闭环完成。

## 未通过项

- 无。

## 后续必须补的证据

- current same-run WAVE ROVER wheel L/R nonzero feedback；
- current live Nav2 route execution success；
- delivery result / operator confirmation / production cloud readback 中至少一类新的外部或准现场证据；
- O1 current HIL acceptance 与 external video / LiDAR motion delta。
