# O6 Consumer Read API Tech Done

## sprint_type

sprint_type: epic

## 实际改动

- 在 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py` 新增 `GET /api/o6/consumer/tasks` 与 `GET /api/o6/consumer/tasks/<task_id>` 两个只读聚合 endpoint。
- 聚合面复用既有 O6 local/mock store，不新增第二套 state：
  - task summary 复用 archive task
  - events 继续走 `_o6_cloud_archive_event_payload()`
  - evidence 继续走 `_o6_cloud_archive_evidence_ref_payload()`
  - labeling 复用底层 `pending|partial|labeled` 语义
  - inference 从 `model_inference.*` timeline 抽摘要
  - tunnel 只返回 robot 维度 latest known snapshot，并明确 `latest_known_robot_snapshot_not_task_aligned`
- 支持 `view=summary` 和 `include=trajectory,events,evidence,labeling,inference,tunnel`
- 对未知 `include`、未知 `view`、非法/过大 `limit`、unsafe query、missing task、`robot_id` mismatch 保持 fail-closed
- 在 `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py` 新增 consumer list/detail/fail-closed 回归测试
- 更新接口文档、PC 触点文档和 `cloud-relay/README.md`

## 用户旅程变化和触点收益

- PC / 后续手机读取 O6 任务列表时，不再需要前端自己 join `/api/o6/archive/*` 和 `/api/o6/tunnel/*`
- 单任务详情现在可一次性拿到 trajectory、events、evidence、labeling、inference、tunnel latest known status
- `view=summary` 和 `include=` 让手机或轻量查询避免默认拿全量 payload
- 所有返回继续显式标记 `proof_status=not_proven`、`safe_to_control=false`、`connects_cloud_production=false`、`robot_control_executed=false`

## 改动文件

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`
- `docs/product/pc_tools_workstation.md`
- `cloud-relay/README.md`

## 接口影响

- 新增：
  - `GET /api/o6/consumer/tasks`
  - `GET /api/o6/consumer/tasks/<task_id>`
- 不变：
  - `/api/o6/archive/*`
  - `/api/o6/tunnel/*`
- 推荐消费路径更新为：PC / 手机优先走 consumer read API；底层 archive/tunnel endpoint 继续保留给写入、调试和兼容调用方

## 验证结果

### 1. 语法检查

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
```

结果：通过

### 2. unittest

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
```

关键结果：

- `Ran 145 tests in 47.853s`
- `OK`

新增覆盖点包括：

- consumer list 倒序和状态聚合
- consumer detail 的 `view=summary` / `include=...`
- inference 字段保留
- 缺 labels / inference / tunnel 的 fail-closed 展示
- 未知 include/view、非法 limit、unsafe query、missing task、robot mismatch

## 失败定位与修复

- 首轮 unittest 命中过一个在地实现细节：`archive task` 初始 payload 的 `events[]` 更偏旧式轻量事件，直接把 `task.failure` 塞进 task POST 会碰到现有校验分支的 `evidence_ref` 假设。
- 修复方式：不改既有 archive task contract，测试种子改为先创建 task，再通过既有 `POST /api/o6/archive/events` 增量写入 `task.failure`，与真实聚合路径保持一致。

## 联调结论

- 前后端/ROS2 契约层面：consumer read API 已能在 relay 后端稳定聚合 O6 local/mock store 中的任务、证据、打标、推理和 tunnel 摘要
- 该结论边界仍是 local/mock software proof，不等于真实云 DB、真实公网、真实手机、真实机器人控制或真实交付成功

## 剩余风险

- 当前仍是 file-backed local/mock store，不证明真实 DB 索引、分页性能或多实例一致性
- tunnel 只有 latest known snapshot，没有 task 时间对齐历史
- `selected` 只是 store 最后一次 upsert 的单选标记，PC/UI 仍需避免把它解释成用户主动选择

## 需要其他 owner 配合事项

- `robot-software-engineer`：暂无必须跟进的代码改动；后续若要把 consumer read API 接到真实 O6 DB 或更丰富任务状态，需要一起定义真实状态源
- `full-stack-software-engineer` 后续可直接基于本接口推进 PC / 手机读侧接入

## 未提交说明

- 本轮未 commit / 未 push，等待主节点统一提交
