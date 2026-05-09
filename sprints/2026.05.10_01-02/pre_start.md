# Sprint 2026.05.10_01-02 Pre Start

## 状态

- 当前阶段：PRE-START。
- 上轮交接：Objective 3 fixed-route dry-run visual gate 已进入软件验证闭环；Docker/Humble 与 HIL 仍未作为本轮默认门禁。
- 本轮目标：优先推进完成度较低的 Objective 5 远程诊断最小数据包，同时保留 Objective 4 样本上下文作为后续切片。

## Owner

| 角色 | 责任 |
| --- | --- |
| `User Touchpoint Full-Stack Engineer` | 本地手机/浏览器网关诊断接口、HTTP contract 和文档 |
| `Product Manager / OKR Owner` | 对齐 Objective 5 KR4，更新 OKR 进度和 sprint 留档 |
| `Autonomy Algorithm Engineer` | 提供 fixed-route status/视觉样本后续接入边界 |

## 本轮验收口径

1. 本地 operator gateway 提供可被手机/远程支持读取的最小诊断包入口。
2. 诊断包至少包含软件版本、地图/路线版本、最近任务状态、失败码、日志引用和视觉样本 manifest 引用。
3. `/api/status`、`/api/collect`、`/api/dropoff/confirm`、`/api/cancel` 现有行为不回退。
4. 本轮只做软件接口和静态/单元验证，不声明云端账号、Docker/Humble、HIL 或真实手机 App 完成。

## 风险

| 风险 | 处理 |
| --- | --- |
| 诊断字段缺少真实 map/route 版本来源 | 先通过参数暴露，后续由路线/地图生成流程写入 |
| 日志和视觉样本 manifest 文件可能不存在 | 诊断包只提供引用，不把不存在当成功证据 |
| 用户体验仍是最小浏览器页 | 本轮推进可消费接口，不声明 polished app |
