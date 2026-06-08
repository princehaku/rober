# O6 Consumer Read API Final

## 本轮结论

- O6-KR6 的统一消费侧 REST 查询面已完成 local/mock software proof
- PC / 后续手机现在有统一的任务列表与任务详情读模型，不必继续在消费侧拼多条 O6 低层 endpoint

## 结果摘要

- 新增 `GET /api/o6/consumer/tasks`
- 新增 `GET /api/o6/consumer/tasks/<task_id>`
- 复用既有 O6 archive / evidence / labeling / inference / tunnel local/mock 数据源
- 保持 fail-closed 与 not_proven 边界
- 接口文档、PC 触点文档和 relay README 已同步

## 验证证据

- `python3 -m py_compile ...` 通过
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py` 通过
- 关键日志：`Ran 145 tests in 47.853s`、`OK`

## 对 OKR 的影响

- 直接推进 Objective 6 / KR6：统一 REST API（或后续 WebSocket）供 PC 端和手机端消费历史任务列表、任务详情、轨迹数据、事件流、标注状态
- 本轮是 O6 local/mock software proof，不提升为真实 production cloud 完成

## OKR 最低优先级核对回顾

- 当前最低 Objective 仍是 O6
- 本轮确实针对 O6，并把之前分散的 O6 写/查 proof 收敛成统一消费读模型
- “降低 O7/手机消费复杂度”的理由仍成立：前端不再需要重复 join 低层 archive/tunnel endpoint

## 未完成事项 / 风险

- 仍缺真实云 DB、真实公网 HTTPS/TLS、真实手机端接入、真实机器人/任务现场验证
- 当前只支持 latest known tunnel snapshot，不支持 task 时间对齐的 tunnel 历史
- 当前分页仍是 local/mock 轻量时间裁剪，不是生产 cursor

## 下轮建议

- 让 PC 端优先接入 `GET /api/o6/consumer/tasks` 与 `GET /api/o6/consumer/tasks/<task_id>`
- 若继续推进 O6 production 化，再把同一读 contract 映射到真实 DB/对象存储与真实鉴权

## 提交状态

- 本轮未 commit / 未 push，由主节点统一提交
