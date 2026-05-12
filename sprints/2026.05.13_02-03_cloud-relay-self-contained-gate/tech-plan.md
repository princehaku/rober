# Sprint 2026.05.13_02-03 Cloud Relay Self-Contained Gate - Tech Plan

## 状态

- 阶段：tech-plan
- sprint_type: epic
- 主 Objective：O5（云中转 + OSS/CDN 数据通路产品化；历史 sprint 中称 O6）
- 证据边界：`software_proof_docker_cloud_relay_self_contained_gate`
- 并行 owner：`full-stack-software-engineer` / `robot-software-engineer` / `product-okr-owner`

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节没有展开完整百分比表；可用最新 sprint evidence 为：O5 约 54%，O6/云中转约 53%，O1/O2/O3/O4 在最近 phone/cloud sprint 中未提升。
- 本 sprint 是否针对最低可行动 Objective：是，针对云中转 O6/O5 低完成度且 Docker-only 可推进的 P5 遗留。
- 不回到 O1/HIL 的理由：CEO 明确“本机没有真实硬件，只有docker”；最近多轮 HIL 根因仍是无真实串口/硬件，继续消费会违反同一 blocker 红线。
- final.md 收口时需复核：是否形成 cloud-relay 独立 Docker/local 软件证据；是否仍未触达真实云/4G/生产 DB/queue。

## Task A - cloud-relay self-contained runtime

Owner：`full-stack-software-engineer`

允许改动文件范围：

- `cloud-relay/**`
- `docs/product/cloud_4g_infrastructure.md`
- `docs/product/remote_4g_mvp.md`
- `docs/interfaces/ros_contracts.md`
- `mobile/README.md`
- `README.md`

要求：

1. 让 `cloud-relay/` 拥有清晰的 Python runtime 入口，Dockerfile 不再直接以旧的根目录路径作为唯一说明；可采用复制/包装方式，但必须避免发明第二套协议语义。
2. 更新 `cloud-relay/docker/Dockerfile`、`cloud-relay/docker-compose.yml`、`cloud-relay/scripts/docker_smoke.sh`，让 Docker/local smoke 以 `cloud-relay/` 为主入口。
3. 同步产品文档里的旧命令：`docker-compose.remote-cloud-relay.yml`、`scripts/remote_cloud_relay_docker_smoke.sh`、旧 `src/` 路径必须替换为当前入口；历史 sprint 文档不追溯。
4. 保持 phone-safe redaction、ACK 语义和 `production_ready=false`。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior python3 -m py_compile cloud-relay/src/ros2_trashbot_cloud_relay/__init__.py cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py
bash cloud-relay/scripts/docker_smoke.sh
git diff --check -- cloud-relay docs/product/cloud_4g_infrastructure.md docs/product/remote_4g_mvp.md docs/interfaces/ros_contracts.md mobile/README.md README.md
```

## Task B - robot compatibility fence

Owner：`robot-software-engineer`

允许改动文件范围：

- `onboard/src/ros2_trashbot_behavior/**`
- `onboard/src/ros2_trashbot_bringup/**`

要求：

1. 确认 `remote_bridge` outbound polling、local `operator_gateway` fallback、bringup 参数仍能保持现有语义。
2. 如果 Task A 需要改变 import / entry point，补最小兼容围栏；不得扩大到真实机器人动作。
3. 确认 ACK 不被升级为 delivery success，cloud-relay 自包含元数据不会污染 `trashbot.remote.v1` command/status/ack envelope。
4. 不直接改产品文档；如发现文档需要同步，返回具体路径和建议，由 Task A/Product 收口，避免并行写同一文件。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_static.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py
git diff --check -- onboard/src/ros2_trashbot_behavior onboard/src/ros2_trashbot_bringup
```

## Task C - product closeout and OKR

Owner：`product-okr-owner`

允许改动文件范围：

- `OKR.md`
- `sprints/2026.05.13_02-03_cloud-relay-self-contained-gate/**`
- `docs/product/cloud_4g_infrastructure.md`
- `docs/product/remote_4g_mvp.md`
- `docs/process/okr_progress_log.md`

要求：

1. 根据 Task A / Task B 的实际证据更新 `tech-done.md`、`side2side_check.md`、`final.md`。
2. 仅在 Docker/local self-contained gate 真实通过时，保守更新云中转 Objective；不得宣称真实云、4G/SIM、OSS/CDN 实流量或 HIL。
3. 检查收口文档引用路径存在，避免继承死路径。

验收命令：

```bash
test -f sprints/2026.05.13_02-03_cloud-relay-self-contained-gate/tech-done.md
test -f sprints/2026.05.13_02-03_cloud-relay-self-contained-gate/side2side_check.md
test -f sprints/2026.05.13_02-03_cloud-relay-self-contained-gate/final.md
rg -n "software_proof_docker_cloud_relay_self_contained_gate|production_ready=false|真实云|4G|HIL" OKR.md sprints/2026.05.13_02-03_cloud-relay-self-contained-gate docs/product/cloud_4g_infrastructure.md docs/product/remote_4g_mvp.md
git diff --check -- OKR.md sprints/2026.05.13_02-03_cloud-relay-self-contained-gate docs/product/cloud_4g_infrastructure.md docs/product/remote_4g_mvp.md docs/process/okr_progress_log.md
```

## 集成验收

主节点只做结果验收、证据核对、commit/push；不直接写产品代码或运行实现验证命令。若 Task A Docker smoke 因环境不可用失败，收口为 blocked，不提升 OKR。
