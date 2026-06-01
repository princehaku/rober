# O6 Archive Live Health

## sprint_type

micro

## 实际改动

- 在 `cloud-relay/src/ros2_trashbot_cloud_relay/archive_core.py` 新增 bearer-gated `GET /api/o6/archive/health`。
- health 响应 schema 固定为 `trashbot.o6.archive_health.v1`，capability 固定为 `o6_archive_live_health`。
- health 只汇总 O6 archive proof store 计数和脱敏 `latest_task_ref`，不返回本地 state path、完整 evidence URI、token、traceback 或 DB/queue URL。
- store JSON 损坏或不可读时返回 HTTP 503，`archive_api_status=store_unavailable`，并保持 `redaction_status=passed`。
- 补充 `cloud-relay/tests/test_archive_core.py`，覆盖未授权、空 store、ready store、脱敏、store_unavailable 和 fail-closed 控制标记。
- 同步更新 `cloud-relay/README.md` 与 `docs/interfaces/o6_cloud_archive_core_api.md`。

## 用户旅程变化和触点收益

PC、手机和运维后续可以用同一个 bearer-gated live health endpoint 判断 O6 archive API 是否在线、是否已有 proof 数据、是否因本地 proof store 损坏而不可用。该入口不会把 software proof 误包装成生产云能力，也不会暴露本机路径或控制能力。

## 接口影响

- 新增 `GET /api/o6/archive/health`。
- 复用现有 `/api/o6/*` bearer gate，未授权返回 401。
- 响应状态：
  - `empty`：store 可读但 task/event/annotation/inference 均为空。
  - `ready`：store 可读且至少存在一类 archive 数据。
  - `store_unavailable`：store JSON 损坏、schema 错误或不可读，HTTP 503。
- 固定边界：`storage_backend=json_file_proof`、`production_ready=false`、`production_db_connected=false`、`real_oss_upload=false`、`real_inference_model_runtime=false`、`safe_to_control=false`、`sends_commands=false`、`robot_control_executed=false`、`delivery_success=false`。

## 验证结果

- `python3 -m py_compile cloud-relay/src/ros2_trashbot_cloud_relay/archive_core.py`
  - 结果：通过，无输出。
- `PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior:onboard/src/ros2_trashbot_nav python3 -m unittest cloud-relay/tests/test_archive_core.py -k "archive_health or o6_routes"`
  - 结果：当前 `unittest -k` 未按该表达式匹配到用例，输出 `Ran 0 tests in 0.000s` / `NO TESTS RAN`，退出码 5。
  - 处理：按验收说明改跑整个测试文件。
- `PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior:onboard/src/ros2_trashbot_nav python3 -m unittest cloud-relay/tests/test_archive_core.py`
  - 结果：通过，关键输出：`Ran 7 tests in 2.972s` / `OK`。
- `git diff --check -- cloud-relay/src/ros2_trashbot_cloud_relay/archive_core.py cloud-relay/tests/test_archive_core.py cloud-relay/README.md docs/interfaces/o6_cloud_archive_core_api.md sprints/2026.06.01_13-14_o6-archive-live-health/tech-done.md`
  - 结果：通过，无输出。
- Coordinator 复核：
  - `python3 -m py_compile cloud-relay/src/ros2_trashbot_cloud_relay/archive_core.py` 通过，无输出。
  - `PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior:onboard/src/ros2_trashbot_nav python3 -m unittest cloud-relay/tests/test_archive_core.py` 通过，关键输出：`Ran 7 tests in 2.842s` / `OK`。
  - `PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior:onboard/src/ros2_trashbot_nav python3 -m unittest discover -s cloud-relay/tests -p 'test_*.py'` 通过，关键输出：`Ran 9 tests in 4.958s` / `OK`。
  - `git diff --check` 通过，无输出。

## 剩余风险

- 该入口只证明本地/Docker software-proof O6 archive API 可观测性。
- 仍不证明 production DB/queue、真实 OSS upload、真实推理 runtime、live external probe、真实云、真实 4G/SIM 或真实上车数据。

## Product/OKR closeout

- 用户价值和产品北极星：PC、手机和运维可以通过 `GET /api/o6/archive/health` 快速判断 O6 archive API 是否在线、proof store 是否可读、是否已有 archive proof 数据；该入口服务于“云端核心后端成为统一数据源”的北极星，但仍是本地/Docker software proof。
- OKR 映射和方向判断：Objective 6 继续推进，不暂停、不替换；进度从 `90%+ mock/software completion` 保守调整到 `约 91% software + archive live health proof`。O1/O5/O7 不因本轮变化。
- KR 拆解和历史归档：本轮补强 O6 KR6 的 REST API 可观测性和 KR2/KR4/KR5 的 proof store 健康入口；没有 KR 达到真实 production/现场完成标准，因此不移动到历史归档区。
- 本轮核心抓手：把 archive core 从“已有 mock archive/query 能力”推进到“live health 可被外部触点安全探测”，并用脱敏和 fail-closed 字段防止误读为生产云能力。
- 需要做什么：下一步优先补 production DB/queue、真实 OSS upload、真实推理 runtime、external live probe、真实云、真实 4G/SIM 和上车数据。
- 优先级和验收口径：当前最低完成度排序更新为 O5 最低，O1/O6 并列约 91%，O7 约 95%；O6 后续验收必须证明真实生产存储、外部 live probe 或真实上车数据之一，而不是继续叠加本地 JSON proof。
- 对应责任 Engineer：后续 production DB/queue、OSS、API/live probe 由 `full-stack-software-engineer` 主责；若进入上车数据和 ROS2 event feed 联调，由 `robot-software-engineer` 补接口事实。
- 风险、阻塞和证据链：本轮证据只覆盖 `py_compile`、`cloud-relay/tests/test_archive_core.py` 全文件 7 OK 和 scoped diff-check；`unittest -k "archive_health or o6_routes"` 在当前环境匹配 0 个测试并退出 5，已按计划 fallback。仍缺 production DB/queue、真实 OSS、真实推理 runtime、external live probe、真实云、真实 4G/SIM 和真实上车数据。
- 历史记录位置：本轮记录同步写入 `docs/process/okr_progress_log.md` 的 `2026-06-01 13-14｜o6-archive-live-health` 小节；`OKR.md` 第 4/4.1/5 节同步更新。
- 需要创建或更新的 sprint 文档：本 Micro sprint 只要求更新本 `tech-done.md`，不创建 epic 六件套。
