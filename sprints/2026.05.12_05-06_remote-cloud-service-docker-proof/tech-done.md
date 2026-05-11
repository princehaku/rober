# Sprint 2026.05.12_05-06 Remote Cloud Service Docker Proof - Tech Done

## 状态

- 阶段：tech-done
- 更新时间：2026-05-12 06:33 Asia/Shanghai
- 证据边界：`software_proof_docker_only`
- Task A Owner：`full-stack-software-engineer`
- Task B Owner：`robot-software-engineer`

## Task A - Independent Relay Service

### 用户旅程变化和触点收益

- 手机/云端控制面从 `operator_gateway` 内嵌 mock 进一步拆出为独立 HTTP relay service proof。
- 普通手机用户仍只看到 command/status/ack、bearer 鉴权失败、状态缺失/过期、请求格式异常等 phone-safe JSON 语义。
- 服务端响应和 state file 不暴露 raw ROS topic、底层速度控制、串口、baudrate、WAVE ROVER 参数、Authorization header、bearer token 或 credential-bearing URL。

### 实际改动

- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
  - 新增 independent HTTP relay service module。
  - 新增 `FileBackedRelayStore`，保存 commands/status/acks，使用临时文件和 `os.replace` 做原子替换。
  - 实现 `POST /robots/{robot_id}/commands`、`GET /robots/{robot_id}/commands/next?last_ack_id=<id>`、`POST/GET status`、`POST/GET ack`。
  - 实现 bearer auth gate、command idempotency、collect target 校验、expired command skip、terminal ACK states、phone-safe errors 和敏感字段脱敏。
- `src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
  - 新增 targeted unittest 覆盖 contract/auth/persistence/error redaction。
- `docs/product/cloud_4g_infrastructure.md`
  - 新增 O6 KR2 云服务端基线和 Docker/local proof 边界文档。
- `docs/product/remote_4g_mvp.md`
  - 补充 independent relay service 与 operator fallback 的边界、启动方式、status_missing/status_stale 和 persistence 口径。
- `sprints/2026.05.12_05-06_remote-cloud-service-docker-proof/tech-done.md`
  - 记录 Task A 实际改动、验证结果、风险和剩余缺口。

### 接口影响

- 新增独立模块入口：

```bash
PYTHONPATH=src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=dev-token \
python3 -m ros2_trashbot_behavior.remote_cloud_relay \
  --host 127.0.0.1 \
  --port 8088 \
  --state-path /tmp/trashbot_remote_cloud_relay.json
```

- 保持 `trashbot.remote.v1` HTTP API：

```text
POST /robots/{robot_id}/commands
GET  /robots/{robot_id}/commands/next?last_ack_id=<id>
POST /robots/{robot_id}/status
GET  /robots/{robot_id}/status
POST /robots/{robot_id}/commands/{command_id}/ack
GET  /robots/{robot_id}/commands/{command_id}/ack
```

- `GET status` 在 independent relay 中明确返回 `status_missing` 或 `status_stale`，避免手机端把缺失/过期状态误读为健康状态。

### 验证结果

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py
......
----------------------------------------------------------------------
Ran 6 tests in 2.593s

OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
```

结果：通过，无输出。

```text
git diff --check -- \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py \
  src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py \
  docs/product/cloud_4g_infrastructure.md \
  docs/product/remote_4g_mvp.md \
  sprints/2026.05.12_05-06_remote-cloud-service-docker-proof/tech-done.md
```

结果：通过，无输出。

### 失败定位和修复记录

- 未出现需要修复的测试失败。
- scoped `git diff --check` 已通过。

### 剩余风险

- 当前证据是 Docker/local independent relay `software_proof_docker_only`。
- 不等于真实云部署、HTTPS/TLS、公网入口、真实 4G/SIM、弱网/断网恢复、生产数据库、OSS/CDN、STS、Nav2/fixed-route、WAVE ROVER、真实运动或 HIL。
- file-backed store 只证明单机重启可恢复，不证明生产并发、多实例一致性、备份、灾备或权限分级。
- ACK 只代表 robot bridge 已处理 command envelope，不代表真实垃圾送达完成；手机端仍必须继续读取 status。

## Task B - Remote Bridge Client Compatibility

### 用户旅程变化和触点收益

- robot outbound polling client 已对 independent relay service 的 status/command/ack shape 做 targeted compatibility proof。
- 手机侧可继续依赖 status 观察任务进展；terminal ACK 仍只表示 command envelope 已被 robot bridge 处理，不表示真实送达完成。
- 鉴权失败、云响应异常、云不可达继续保持 phone-safe failure：不执行不可信 command、不推进 cursor、不伪造 terminal ACK。

### 实际改动

- `src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
  - 补齐源码路径导入围栏，保证 macOS 本地直接执行指定 unittest 时能导入 `ros2_trashbot_behavior`。
  - 新增 independent relay compatibility 测试：直接启动 Task A `build_server`，验证 `RemoteCloudClient.post_status -> get_next_command -> post_ack` 闭环与 relay HTTP response shape 兼容。
  - 新增 bearer auth compatibility 测试：wrong token 经 independent relay 返回 401 后，client 映射为 `RemoteCloudError(reason="auth_failed", retry_hint="check_auth")`。
- `src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py`
  - 未改生产代码；现有 client 已兼容 relay `{"command": ...}`、status/ack JSON object 和 401/403 auth failed shape。
- `src/ros2_trashbot_behavior/test/test_remote_bridge.py`
  - 未改；既有用例继续覆盖 malformed response/cloud unreachable/auth failed 不提交本地 action、不推进 cursor、不伪造 terminal ACK。

### 接口影响

- 无生产接口变更。
- `trashbot.remote.v1` status/command/ack API shape 保持与 Task A independent relay 一致。
- ACK 语义保持为 command envelope 处理结果；delivery result 仍必须来自 status、task record 或后续行为层 evidence。

### 验证结果

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py \
  src/ros2_trashbot_behavior/test/test_remote_bridge.py
/opt/homebrew/Cellar/python@3.13/3.13.2/Frameworks/Python.framework/Versions/3.13/lib/python3.13/threading.py:1265: ResourceWarning: unclosed <socket.socket [closed] fd=4, family=2, type=1, proto=6>
  def _make_invoke_excepthook():
ResourceWarning: Enable tracemalloc to get the object allocation traceback
...............................
----------------------------------------------------------------------
Ran 31 tests in 15.249s

OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py
```

结果：通过，无输出。

```text
git diff --check -- \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py \
  src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py \
  src/ros2_trashbot_behavior/test/test_remote_bridge.py \
  sprints/2026.05.12_05-06_remote-cloud-service-docker-proof/tech-done.md
```

结果：通过，无输出。

### 失败定位和修复记录

- 首轮指定 unittest 失败于 `test_remote_bridge_protocol.py` 直接运行时缺少源码路径：

```text
ModuleNotFoundError: No module named 'ros2_trashbot_behavior'
```

- 修复：按同目录 `test_remote_bridge.py` 的既有模式，在 `test_remote_bridge_protocol.py` 中加入 `REPO_ROOT` / `sys.path.insert` 导入围栏。
- 末轮 unittest 在 Python 3.13 下出现一次 ThreadingHTTPServer closed socket `ResourceWarning`，但测试结果为 OK；该 warning 不改变 compatibility proof 结论。
- 未发现 `RemoteCloudClient` 与 independent relay service response shape 不兼容；未修改生产 client。

### 剩余风险

- 当前 compatibility proof 只覆盖本地 independent relay + Python client 的 `software_proof_docker_only` 级别。
- 不等于真实云部署、HTTPS/TLS、公网入口、真实 4G/SIM、弱网/断网恢复、OSS/CDN、生产数据库、Nav2/fixed-route、WAVE ROVER、真实运动或 HIL。
- ACK 不是 delivery result；手机端和产品口径必须继续把 ACK 与真实任务送达/投放结果分开展示。

## Task C - Merged Integration Fence

### 执行时间和 Owner

- 执行时间：2026-05-12 03:22 Asia/Shanghai
- Owner：`robot-software-engineer`
- 证据边界：`software_proof_docker_only`

### 实际改动

- 未改产品代码。
- 未改测试代码。
- 仅追加更新 `sprints/2026.05.12_05-06_remote-cloud-service-docker-proof/tech-done.md`，记录 Task C 合并集成围栏结果。

### 验证结果

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py \
  src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py \
  src/ros2_trashbot_behavior/test/test_remote_bridge.py
.....................................
----------------------------------------------------------------------
Ran 37 tests in 17.884s

OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py
```

结果：通过，无输出。

```text
git diff --check -- \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py \
  src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py \
  src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py \
  src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py \
  src/ros2_trashbot_behavior/test/test_remote_bridge.py \
  docs/product/cloud_4g_infrastructure.md \
  docs/product/remote_4g_mvp.md \
  sprints/2026.05.12_05-06_remote-cloud-service-docker-proof/tech-done.md
```

结果：通过，无输出。

### 失败定位和修复记录

- 本轮 Task C 合并集成围栏未失败。
- 未触发代码修复需求；没有 BLOCKED/NEEDS_CONTEXT。

### 剩余风险

- 当前 integration smoke 只证明 independent relay、RemoteCloudClient protocol client 和 remote bridge targeted tests 在本地 Python 围栏中可同时通过。
- integration smoke 不等于真实云部署、真实 4G/SIM、OSS/CDN、生产数据库、HTTPS/TLS、公网弱网恢复、Nav2/fixed-route、WAVE ROVER、真实运动或 HIL。
- ACK 仍只表示 robot bridge 已处理 command envelope，不代表真实导航、收集、投放或任务完成。
- 真实云、4G 和 HIL 证据需要后续由 Full-Stack、Hardware、Autonomy 按各自 owner 范围补齐。
