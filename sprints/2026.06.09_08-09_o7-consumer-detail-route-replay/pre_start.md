# O7 Consumer Detail Route Replay Pre-Start

## sprint_type

sprint_type: epic

## 1. 启动原因

最近两轮已经把 O6 consumer read API 和 O7 consumer read integration 做成了可用的 primary path。下一步不应该再重复“读模型打通”本身，而是把这份 O6 consumer detail 真正消费起来，变成 O7 route replay 的主数据源。

本轮选择 route replay，而不是继续做 fixture preview 的同类扩展，原因很直接：

- route replay 最容易把 `trajectory / events / evidence / tunnel` 这些 O6 consumer detail 字段变成用户可见价值。
- route replay 也是后续 labeling、voice、safe command 继续消费 O6 detail 的共同样板。
- 现有 route replay 相关能力仍停留在 fixture preview / local preview，尚未真正以 consumer detail 为主路径。

## 2. 上轮事实和当前证据

- `sprints/2026.06.09_06-07_o6-consumer-read-api/` 已确认 O6 consumer read 统一查询面完成 local/mock software proof。
- `sprints/2026.06.09_07-08_o7-pc-consumer-read-integration/` 已确认 O7/PC 任务列表与任务详情主路径切到 O6 consumer read contract。
- `docs/interfaces/o6_cloud_archive_api.md` 已明确 consumer read 返回 `task_summary`、`trajectory`、`events`、`evidence`、`labeling`、`inference`、`tunnel_status` 等聚合字段。
- `docs/product/pc_tools_workstation.md` 仍要求 PC 工作站保持 `pc-only`、`not_proven`、`safe_to_control=false`、`primary_actions_enabled=false` 的 fail-closed 边界。
- 现有 route replay 相关页签仍有 fixture preview/player/minimap 的历史资产，但这些都还没有把 O6 consumer detail 作为主数据源。

## 3. 本轮目标

把 O7 route replay 做成一个完整功能点：由 O6 consumer detail 驱动的历史回放、逐帧检查和证据浏览。

本轮要完成的是：

- route replay 主路径从 fixture preview 切到 O6 consumer detail。
- 回放视图能消费 task detail 中的 `trajectory / events / evidence / tunnel`。
- 本地 cursor、播放/暂停、前后帧切换仍只在 PC 本地生效，不发新请求、不写后端、不下发机器人控制。
- fallback fixture preview 只能保留为次路径或调试路径，不再是主产品路径。

## 4. 本轮 owner

- `full-stack-software-engineer`：主实现 owner，负责 workstation 路由、视图模型、UI 交互、测试和文档同步。
- `product-okr-owner`：阶段验收、范围收口和 OKR 方向判断。

## 5. 主要风险

- 如果 route replay 继续沿用 fixture preview 做主路径，就会把 O6 consumer detail 的价值再次浪费在静态样本上。
- 如果 consumer detail 的字段映射不统一，route replay、labeling、voice、safe command 后续会重复造轮子。
- 任何“可播放”“可控制”“真实回放成功”的文案都必须继续 fail closed，不能因为 UI 有了就抬高能力声明。
