# Repo-wide Structure and Comment Refactor Tech Plan

## 总体策略

本轮采用 4 owner 并行。每个 owner 只改自己文件范围内的模块，优先“兼容入口 + 内部子目录”模式：外部 import、entry point、launch 和测试路径尽量不变，内部按职责拆到子模块。拆分时先写或调整聚焦测试，再移动实现，最后补中文注释与 docs。

## 文件范围与分工

### 1. Robot Platform Engineer

允许改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_orchestrator.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge_protocol.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/delivery_*.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/task_record.py`
- `onboard/src/ros2_trashbot_behavior/test/test_task_orchestrator_*.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge*.py`
- `docs/interfaces/`
- `docs/behavior/`

任务：

- 把 behavior 主链路中可独立的状态、错误、兼容 helper 拆入内部子模块。
- 保持现有 public import 和 ROS2 action/topic/service 契约。
- 为复杂状态分支补中文注释，解释为什么要保留 software-proof / not-proven / safe-to-control 边界。

验收命令：

```bash
cd /mnt/e/rober/onboard && python3 -m pytest src/ros2_trashbot_behavior/test/test_task_orchestrator_static.py src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py src/ros2_trashbot_behavior/test/test_remote_bridge_static.py
```

### 2. Hardware Infra Engineer

允许改动：

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/`
- `onboard/src/ros2_trashbot_hardware/test/`
- `docs/hardware/`
- `docs/vendor/` 只读，除非发现索引明显缺失且必须补引用；不得改 vendor 原始资料。

任务：

- 先读 `docs/vendor/VENDOR_INDEX.md` 及其指向的 WAVE ROVER/ESP32/Orange Pi 本地资料。
- 将 `esp32_bridge.py` 中协议编码、反馈解析、ROS 发布/订阅、参数处理拆为清晰单元，保留原入口。
- 在代码注释或 docs 中明确 vendor source 与未验证边界。

验收命令：

```bash
cd /mnt/e/rober/onboard && python3 -m pytest src/ros2_trashbot_hardware/test/test_waveshare_json_bridge.py src/ros2_trashbot_hardware/test/test_hardware_diagnostics_proof.py
```

### 3. Autonomy Algorithm Engineer

允许改动：

- `onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/`
- `onboard/src/ros2_trashbot_nav/test/`
- `onboard/src/ros2_trashbot_vision/ros2_trashbot_vision/`
- `onboard/src/ros2_trashbot_vision/test/`
- `docs/navigation/`
- `docs/vision/`

任务：

- 将 route、fixed-route dry-run、visual gate proof、vision sample/trash detector helper 按数据模型、解析、proof summary、runtime adapter 目录化。
- 保持 dry-run 测试和现有 launch/entry behavior 兼容。
- 补中文注释说明算法参数、证据边界和为什么不把视觉 detector 作为 MVP 强依赖。

验收命令：

```bash
cd /mnt/e/rober/onboard && python3 -m pytest src/ros2_trashbot_nav/test/test_fixed_route_dry_run_offline.py src/ros2_trashbot_nav/test/test_route_csv_to_yaml.py src/ros2_trashbot_nav/test/test_visual_gate_proof.py src/ros2_trashbot_vision/test/test_trash_detector_static.py src/ros2_trashbot_vision/test/test_vision_sample_manifest.py
```

### 4. User Touchpoint Full-Stack Engineer

允许改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_static.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway*.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_mobile_web_entrypoint.py`
- `docs/product/`
- `docs/interfaces/`

任务：

- 将 operator gateway diagnostics 和 remote cloud relay 的数据模型、状态归一化、HTML/API 渲染、evidence guard、测试 fixture 分层。
- 保持 mobile/web 当前安全只读和 primary action disabled 语义。
- 补中文注释说明为什么 UI 不把 not-proven 写成 proven、为什么控制按钮保持 disabled。

验收命令：

```bash
cd /mnt/e/rober/onboard && python3 -m pytest src/ros2_trashbot_behavior/test/test_operator_gateway_static.py src/ros2_trashbot_behavior/test/test_operator_gateway_http.py src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py src/ros2_trashbot_behavior/test/test_mobile_web_entrypoint.py
```

## 集成验收

所有 owner 返回后，主节点只做结果验收和必要重试调度。若文件冲突或验证失败，退回对应 owner 修复。

建议最终验收命令由 `robot-software-engineer` 或重新派发的集成 worker 执行：

```bash
cd /mnt/e/rober/onboard && python3 -m compileall -q src
cd /mnt/e/rober && bash onboard/scripts/docker_humble_build.sh
```

若 Docker/Humble 因本机环境、网络或镜像源失败，必须记录失败根因，并至少保留 `compileall` 与相关 package pytest 的结果。

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5（约 68%）。
- 本 sprint 是否针对该 Objective：否，主要针对全仓可维护性和结构化治理。
- 不针对理由：CEO 明确选择“全仓扫描后分 2-4 个 owner 并行重构”；本轮不依赖真实外部云/4G/OSS/CDN 材料，且不应把 local-only refactor 写成 O5 external proof。
- final.md 收口时需复核：本轮是否仍未新增外部证据；若没有，OKR 完成度保持不变。

## 风险与回滚策略

- 若拆分导致 import path 断裂，优先恢复原模块 re-export 兼容层。
- 若多个 owner 需要改同一文件，暂停对应子任务，改为主责 owner 集成。
- 若某个超大文件无法在单轮安全拆完，允许只做第一层目录化和兼容 facade，并在 `tech-done.md` 标记剩余风险。
- 本轮不得覆盖 unrelated 删除文件，不得运行 destructive git 命令。
