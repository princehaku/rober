# O7 Consumer Detail Route Replay Tech Plan

## 1. 方案总览

本轮按 Epic 管理，但实现边界保持单线闭环：由 `full-stack-software-engineer` 主实现 O7 route replay 的 consumer-detail 主路径。

实现思路是把现有 route replay 相关 UI 从“fixture preview 主导”改成“consumer detail 主导”：

```text
O6 consumer read detail
  -> workstation route replay adapter / view model
  -> route replay panel / player / minimap
  -> local-only cursor and playback state
```

核心原则只有三条：

- 主路径必须消费 O6 consumer detail。
- 播放控制只改浏览器本地 state，不触发额外后端写入。
- 所有成功态必须继续 fail closed，不能越界成真实控制或真实交付。

## 2. 依赖与事实依据

- `docs/interfaces/o6_cloud_archive_api.md`：consumer read contract 已明确支持 `trajectory / events / evidence / labeling / inference / tunnel` 聚合字段。
- `docs/product/pc_tools_workstation.md`：PC 工作站边界仍然是 `pc-only`、`not_proven`、`safe_to_control=false`、`primary_actions_enabled=false`。
- `sprints/2026.06.09_06-07_o6-consumer-read-api/tech-done.md`：O6 consumer read API 已完成。
- `sprints/2026.06.09_07-08_o7-pc-consumer-read-integration/tech-done.md`：O7/PC 已有 consumer read primary path。
- 现有 route replay 相关 fixture 资产只能作为 secondary / fallback，不能继续占据主路径语义。

## 3. 实施任务

### Task A - Route Replay Consumer Detail 主路径

Owner: `full-stack-software-engineer`

允许改动：

- `pc-tools/workstation/src/**`
- `pc-tools/workstation/test/**`
- `pc-tools/README.md`
- `docs/product/pc_tools_workstation.md`
- `docs/interfaces/o7_realtime_operator_console.md`
- `sprints/2026.06.09_08-09_o7-consumer-detail-route-replay/**`

任务要点：

- 把 route replay 的主数据源切到 O6 consumer detail。
- route replay panel / player / minimap 直接消费 detail 中的 trajectory、events、evidence、tunnel summary。
- fixture preview 只允许保留为次路径、调试路径或 fallback，不得再作为主入口。
- 本地 cursor、播放/暂停、逐帧切换都只能在前端 state 中完成。
- 缺 detail、缺 trajectory、unknown task、非法 include/view、blocked 状态必须 fail closed。
- 保持 UI 上不出现任何真实控制成功、真实机器人运动、真实云接通的表述。

## 4. 验收命令

工程同学完成后必须至少执行：

```bash
cd pc-tools/workstation && npm run build
cd pc-tools/workstation && npm run test
cd pc-tools/workstation && npm run lint
git diff --check
```

如果实现过程中没有改到非 workspace 文件，不需要额外引入别的验证命令。

## 5. OKR 最低优先级核对

当前 `OKR.md` 4.1 节完成度最低的 Objective 是：

- O6：0%

本 sprint **不直接针对最低 Objective**，原因是：

1. O6 consumer read 这条最低层读模型已经在上一轮完成，本轮继续做 O6 本体的新增读写只会重复已经打通的 primary path。
2. 本轮最有价值的动作，是把刚完成的 O6 consumer detail 真正消费到 O7 route replay，让 O6 立即转化为用户可见的历史回放能力。
3. route replay 是后续 labeling / voice / safe command 继续消费同一 detail 语义的样板，能减少后续重复 join 成本。

这不是放弃 O6，而是先把 O6 的成果变成 O7 的可见产品价值，再把更深的 O6 生产化工作留给后续专门 sprint。

## 6. 风险与缓冲

- 如果 route replay 主路径没有真正切到 consumer detail，这轮就会退化成另一种 fixture preview。
- 如果 view model 过度复制 O6 数据结构，后续 labeling / voice / safe command 会继续重复 join。
- 如果测试只覆盖 happy path，没有覆盖缺 task、缺 trajectory、blocked 状态，就不能收口。
- 本轮默认不提升 O7 百分比，除非工程证据明确证明 route replay 的主路径已经真正消费 consumer detail。
