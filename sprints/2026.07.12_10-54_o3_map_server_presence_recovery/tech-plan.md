# Tech Plan - O3 Map Server Presence Recovery

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_10-54_o3_map_server_presence_recovery/`
- Owner: `robot-software-engineer`
- Product owner: `product-okr-owner`
- Target: strict no-motion `/map_server` presence recovery/proof

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1/当前最高优先级显示最低 Objective 是 O5，约 `85%`。O1/O6/O7 约 `93%`。
2. 本 sprint 不直接针对 O5。
3. 原因：O5 当前缺真实 production external evidence；上一轮和 OKR 已明确 readiness packet、surface、review、handoff、support-only work 不能继续计分。本轮选择 O3/O1 strict no-motion 现场链路，因为它能在真实上位机上推进 current-run map server presence proof，并可能解锁后续 `/map`、TF、planner/path readiness。
4. 方向判断：O5 `暂停` support-only；O3/O1 `继续`；O6/O7 `暂停等待新材料`。本轮不调整百分比，不归档 KR。

## 上轮证据输入

来自 `sprints/2026.07.12_09-54_o3_map_server_graph_lifecycle_visibility/`：

- `canonical_classification=map_server_node_absent`
- `failure_detail=lifecycle_retry_node_not_found`
- `/map_server` retry `stderr="Node not found\n"`
- `amcl_lifecycle_reference.current_active=true`
- `path_generation_attempted=false`
- `path_generated=false`
- no-motion fields false

主节点只读最新 artifact 后的进入边界：

- `managed_runtime_requested=false`
- `managed_runtime_started=false`
- `managed_runtime_boundary=default_read_only_existing_ros_graph_no_runtime_start`

本轮必须把边界从只读 existing graph 升级到 explicit managed runtime/API recovery proof。

## 技术方案

Robot Software 单 owner 闭环。

实施建议路径：

1. 在 helper 中识别 `/map_server` presence recovery stage，保留上一轮 graph/lifecycle classification。
2. 对 true-board run 增加 explicit managed runtime recovery path：
   - 首选 helper 参数：`--managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml`。
   - 可接受等价路径：调用 `/api/nav2/start` 启动 no-motion managed runtime，再执行 `/api/nav2/proof/refresh` 或 helper proof refresh。
3. Artifact 必须记录：
   - `managed_runtime_requested`
   - `managed_runtime_started`
   - managed map yaml safe basename/path policy
   - recovery command/API path
   - `/map_server` process/node/lifecycle manager presence
   - lifecycle first/retry stdout/stderr/returncode/timeout
   - canonical classification
   - strict no-motion safety fields
4. 如果 `/map_server` 越过 `Node not found`，继续读取最小 lifecycle state，不进入 NavigateToPose 或 path execution。
5. 如果仍是 `Node not found`，输出更窄 blocker：launch未启动、process未起、lifecycle manager未管辖、map yaml missing、node name mismatch、source/runtime error 等；不得只写 generic timeout。

## 允许文件范围

Robot Software 实施允许改动：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/scripts/o11_nav2_lifecycle.sh`
- `onboard/src/ros2_trashbot_bringup/launch/`
- `onboard/src/ros2_trashbot_bringup/CMakeLists.txt`，仅当 map server launch/install 入口需要修复
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `onboard/src/ros2_trashbot_bringup/test/`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.12_10-54_o3_map_server_presence_recovery/tech-done.md`
- `sprints/2026.07.12_10-54_o3_map_server_presence_recovery/artifacts/`

不得改动：

- WAVE ROVER、ESP32、UART、串口、波特率、接线、硬件配置。
- `OKR.md`
- `docs/process/okr_progress_log.md`
- O5/O6/O7 API/UI/archive 代码。
- 历史 sprint 目录。

如发现必须依赖硬件串口、接线、波特率、JSON 指令、速度映射或 feedback 协议事实，停止相关实现假设，派 `rober-hardware-engineer` 读取 `docs/vendor/VENDOR_INDEX.md` 及其指向资料后再继续；本轮默认不触碰硬件配置。

## 接口影响

允许影响：

- `o10_amcl_nav2_runtime_proof.py` artifact schema 增加 additive fields，描述 `/map_server` presence recovery。
- no-motion helper 可新增 managed runtime opt-in 参数或补充已有参数读法。
- bringup launch 可修复 map server/lifecycle manager presence，但必须保持 motion/control 默认关闭。
- navigation docs 同步 proof boundary。

禁止影响：

- 不改变 `/cmd_vel`、`/api/base/manual`、WAVE ROVER UART 或真实底盘控制入口。
- 不执行 NavigateToPose 或 Nav2 route execution。
- 不把 map server recovered 自动转成 `safe_to_control=true`。
- 不改变 O5/O6/O7 合同。

## 验收命令

Robot Software 必须运行并记录以下命令。若实施选择等价 `/api/nav2/start` + proof refresh 路径，必须把实际命令/API 响应和 artifact 字段写入 `tech-done.md`。

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

Local fail-closed dry-run：

```bash
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --strict-no-motion \
  --no-base-uart \
  --timeout-s 18 \
  --managed-runtime-opt-in \
  --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml \
  --output-json sprints/2026.07.12_10-54_o3_map_server_presence_recovery/artifacts/local_o10_map_server_presence_recovery.raw.json
```

True-board strict no-motion run/pull artifact：

```bash
ssh -p 37878 root@192.168.1.11 \
  'mkdir -p /root/rober/onboard/scripts /tmp/rober_o10_artifacts'
```

```bash
scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

```bash
ssh -p 37878 root@192.168.1.11 \
  'cd /root/rober/onboard && /usr/bin/timeout 420s /usr/bin/python3.10 scripts/o10_amcl_nav2_runtime_proof.py --strict-no-motion --no-base-uart --timeout-s 18 --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --output-json /tmp/rober_o10_artifacts/live_o10_map_server_presence_recovery.raw.json'
```

```bash
scp -P 37878 root@192.168.1.11:/tmp/rober_o10_artifacts/live_o10_map_server_presence_recovery.raw.json \
  sprints/2026.07.12_10-54_o3_map_server_presence_recovery/artifacts/live_o10_map_server_presence_recovery.raw.json
```

Scoped diff check：

```bash
git diff --check -- \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/scripts/o11_nav2_lifecycle.sh \
  onboard/src/ros2_trashbot_bringup \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/field_route_evidence_preflight.md \
  docs/navigation/fixed_route_workflow.md \
  sprints/2026.07.12_10-54_o3_map_server_presence_recovery
```

Planning阶段验收命令：

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|O5|85%|map_server|managed_runtime_requested=false|managed_runtime_started=false|strict no-motion|robot-software-engineer|--managed-runtime-opt-in|git diff --check" sprints/2026.07.12_10-54_o3_map_server_presence_recovery
```

```bash
git diff --check -- sprints/2026.07.12_10-54_o3_map_server_presence_recovery
```

## 验收判定

Accept：

- true-board artifact 越过 `/map_server` `Node not found`，或更窄地证明 recovery path 的下一个 blocker。
- no-motion 字段全部 false。
- managed runtime recovery path 被明确记录。
- local dry-run fail-closed。
- tests 和 scoped `git diff --check` 通过。

Needs retry：

- artifact 仍只显示 `managed_runtime_requested=false`、`managed_runtime_started=false`。
- primary blocker 仍是 generic timeout，没有 recovery command/API 证据。
- `/scan`、TF、planner timeout 被当作 primary result。
- docs 或 sprint `tech-done.md` 未记录 proof boundary。

Reject：

- 发送 NavigateToPose。
- 发布 `/cmd_vel`。
- 调用 `/api/base/manual`。
- 打开 WAVE ROVER UART。
- 改硬件配置或未读 vendor 资料就假设硬件事实。

## 风险边界

- `/map_server` presence recovered 仅证明 map server node/lifecycle 可见性改善，不证明 `/map` sample、TF、localization ready、path generation、route execution、delivery success、safe-to-control 或 HIL。
- 如果 true-board SSH 不可达，本轮只能记录 blocked，不能用 local artifact 替代 true-board proof。
- 如果本轮结束仍是 `map_server_node_absent`，必须触发同一 blocker 红线：升级 CEO 决策或切换 Objective，不能继续包装诊断。

## 后续文档要求

Robot Software 实施完成后必须更新：

- `sprints/2026.07.12_10-54_o3_map_server_presence_recovery/tech-done.md`

Product 验收阶段再更新：

- `sprints/2026.07.12_10-54_o3_map_server_presence_recovery/side2side_check.md`
- `sprints/2026.07.12_10-54_o3_map_server_presence_recovery/final.md`
