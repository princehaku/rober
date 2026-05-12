# Sprint 2026.05.13_01-02 Codebase Restructure Four-Tier — tech-done

## sprint_type

`epic`

## CEO 本轮指令（验证范围）

**本轮跳过测试与验证**，不执行 `bash onboard/scripts/run_smoke_tests.sh`、`docker compose` / `docker_humble_build` 等；直接进入 sprint 收口留档。证据边界仍为 **`structural_refactor_only`**，不声明任何 Objective 完成度变化。

## 实际改动（摘要）

### 仓库分层（monorepo 四目录）

- **`onboard/`**：`git mv` 原 `src/` → `onboard/src/`；`docker/humble` → `onboard/docker/humble`；`docker-compose.humble.yml` → `onboard/docker-compose.humble.yml`；上车脚本迁入 `onboard/scripts/`（`docker_humble_*`、`run_smoke_tests.sh`、`hardware_smoke_*`、`hil_evidence_packet_gate.py`、`setup_wsl_*.sh`）。
- **`cloud-relay/`**：`docker-compose.remote-cloud-relay.yml` → `cloud-relay/docker-compose.yml`；`docker/remote-cloud-relay/Dockerfile` → `cloud-relay/docker/Dockerfile`；`scripts/remote_cloud_relay_docker_smoke.sh` → `cloud-relay/scripts/docker_smoke.sh`；compose **build context = 仓库根 `..`**，Dockerfile `COPY onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/...`。
- **`mobile/`、`pc-tools/`**：README 与目录脚手架；`scripts/evidence_crosscheck.py`、`scripts/phone_browser_acceptance_gate.py` → **`pc-tools/evidence/`**。
- **仓库根 `scripts/`**：仅保留 `README.md` 说明新路径入口。

### 文档与 Agent 配置

- `README.md`、`AGENTS.md`：构建/Compose 路径改为 `onboard/...`。
- `.codex/agents/*.toml`、`.codex/agents/registry.toml`：`owner_paths` 更新为 `onboard/src/...`、`pc-tools/`、`cloud-relay/` 等。

### 为布局与跨平台适配的代码/测试调整（未在本轮跑测确认）

- `onboard/scripts/run_smoke_tests.sh`：`cd "$repo_root"` 后再 `compileall`。
- `onboard/src/ros2_trashbot_interfaces/test/`：`docs` 契约路径向上查找仓库根；CMake 注册列表用 `as_posix()` 兼容 Windows。
- `onboard/src/ros2_trashbot_behavior/test/`：`test_task_record.py` 仓库根解析、`evidence_crosscheck` 指向 `pc-tools/evidence/`；`test_legacy_*` 的 `ROS_CONTRACTS` 路径；`test_remote_cloud_relay.py` 不可写 state 路径跨平台 helper；`test_task_orchestrator_static.py` 与 `fixed_route` 期望值；gateway 诊断里 hardware smoke 路径；`test_perception_docs_static.py` 仓库根。
- `onboard/scripts/hardware_smoke_wave_rover.py`、`hardware_diagnostics_proof.py`：文案中的脚本路径更新为 `onboard/scripts/...`。

## 验证结果

| 项 | 状态 |
| --- | --- |
| `bash onboard/scripts/run_smoke_tests.sh` | **本轮跳过（CEO 指令）** |
| `SKIP_COLCON=1 bash onboard/scripts/docker_humble_build.sh` | **本轮跳过** |
| `cd cloud-relay && docker compose build` | **本轮跳过** |

## 未完成 / 下阶段（tech-plan 原 P5+）

- **P5**：`operator_gateway*`、`remote_cloud_relay` 迁入 `cloud-relay/src/` 并与 HTTP server 集成；bringup 移除 `operator_gateway` 节点等——**未在本轮实施**。
- **P4 剩余**：`route_debug_web.py`、`route_csv_to_yaml.py` 仍留在 `onboard/src/ros2_trashbot_nav/`（未抽到 `pc-tools/route/`）。
- **回归验证**：下一轮应优先补跑 `onboard/scripts/run_smoke_tests.sh` 与（如环境可用）Docker build，再推进 P5。

## 剩余风险

1. **未验证合并**：路径与测试修改未经 CI/本地 smoke 确认，存在漏改路径或 Windows/Linux 差异风险。
2. **历史 sprint 文档**仍引用旧路径 `src/`、`scripts/docker_*`，属留档不追溯；以当前 `README.md` / `AGENTS.md` / 各 tier `README.md` 为准。
3. **`OKR.md` 若有 §6 等仍写旧命令**：若发现不一致需单独 micro sprint 对齐（本轮未系统性 grep `OKR.md`）。
