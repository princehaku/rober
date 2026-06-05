# Pre Start: O10 AMCL/Nav2 Runtime Collector Epic

## sprint_type

sprint_type: epic

## 启动背景

本文件为 Product/OKR 收口补齐的 Epic 链路文档，事实依据来自本轮
`tech-done.md` 和远端 live 8787 验证结果。上一轮
`13-14_o10-amcl-nav2-readiness-epic` 已把 AMCL/Nav2 做到输入护栏：
canonical map proof 和 map artifacts 可读，但没有 AMCL/Nav2 runtime。

本轮用户价值是把"下一步 AMCL/Nav2 为什么不成立"从抽象风险，变成
live 8787 可回放的 blocker artifact，方便 Robot Software、Algorithm
和 Product 在下一轮直接定位到缺包、未启动 lifecycle 和 ROS graph 空的问题。

## 目标 Objective

- 主 Objective：O10 受控送达闭环实战战役。
- 关联 Objective：O8 Epic 证据治理。
- 不涨 Objective：O3/O7/O9。AMCL/Nav2 runtime 当前是 blocked artifact，
  不是定位、路径生成、PC 消费或真实材料 breakthrough 成功。

## Owner 与边界

| Owner | 本轮职责 | 边界 |
| --- | --- | --- |
| Robot Software Engineer | 交付 no-motion AMCL/Nav2 runtime proof collector、8787 refresh/latest endpoint、live blocker artifact | 不发 `/cmd_vel`，不调用 `/api/base/manual`，不发布 `/initialpose`，不发 Nav2 goal |
| Product Manager / OKR Owner | 收口用户价值、OKR 涨分、不可越界项和下一步 CEO blocker | 不改产品代码，不把 blocked artifact 写成 runtime success |

## 验收口径

- 本地 compileall、upper API 单测、scripts unittest discover 和 diff-check 通过。
- 远端部署到 `root@192.168.1.11` 后，`trashbot-upper-robot-api.service`
  active。
- `POST /api/nav2/proof/refresh` 返回 `blocked_with_root_cause`。
- `GET /api/nav2/proof/latest` 能 readback
  `/root/rober/onboard/runtime/nav2_lifecycle_latest.json`。
- artifact 必须写清 canonical map inputs ready、Nav2/AMCL 缺失 root causes、
  ROS graph 当前只有 `/parameter_events` 和 `/rosout`，以及
  `safe_to_control=false`。

## 风险

- 不证明地图可导航、AMCL localization、Nav2 path generation/path execution、
  HIL、delivery success 或 `safe_to_control=true`。
- 下一轮若继续只做 refresh/latest/readback，不应继续上调 O10。
