# Sprint 2026.05.13_01-02 Codebase Restructure Four-Tier - Tech Plan

## 状态

- 阶段：tech-plan
- sprint_type: epic
- 时间：2026-05-13 01:xx Asia/Shanghai
- 主集成 Owner：robot-software-engineer（ROS2 主链路 + 集成验收）
- 并行 Owner：full-stack-software-engineer / autonomy-engineer / hardware-engineer
- 留档 Owner：product-okr-owner
- 证据边界：`structural_refactor_only`

## 0. 并行 / 串行依赖总图

```
                                ┌──────────────────────────────────────┐
                                │   Phase 1 (P1) 顶层 4 子目录脚手架      │
                                │   Owner: product-okr-owner (主节点写) │
                                │   依赖: 无                            │
                                └──────────────────────────────────────┘
                                                  │
                ┌─────────────────────────────────┼─────────────────────────────────┐
                ▼                                 ▼                                 ▼
   ┌──────────────────────┐         ┌──────────────────────┐         ┌──────────────────────┐
   │ Phase 2A             │         │ Phase 2B             │         │ Phase 2C             │
   │ cloud-relay 独立     │         │ mobile/ 脚手架       │         │ docker compose 拆分  │
   │ Owner: full-stack    │         │ Owner: full-stack    │         │ Owner: full-stack    │
   │ 依赖: P1             │         │ 依赖: P1             │         │ 依赖: P2A            │
   │ 并行: 与 2B/3        │         │ 并行: 与 2A/3        │         │ 并行: 与 2B/3        │
   └──────────────────────┘         └──────────────────────┘         └──────────────────────┘
                                                  │
                                                  ▼
                                ┌──────────────────────────────────────┐
                                │   Phase 3 ROS2 包整体迁到 onboard/    │
                                │   Owner: robot-software-engineer 主责│
                                │   配合: hardware-engineer            │
                                │   依赖: P1（不依赖 P2A/B/C，可同时）  │
                                │   阻塞: P4, P5 必须等 P3 完成        │
                                └──────────────────────────────────────┘
                                                  │
                              ┌───────────────────┴───────────────────┐
                              ▼                                       ▼
              ┌──────────────────────────────┐         ┌──────────────────────────────────┐
              │ Phase 4 pc-tools 工具搬迁    │         │ Phase 5 operator_gateway 拆到    │
              │ Owner: autonomy-engineer     │         │ cloud-relay（HTTP client 改造）   │
              │ 依赖: P3                     │         │ Owner: full-stack-software-       │
              │ 并行: 与 P5                  │         │ engineer                          │
              │                              │         │ 依赖: P3                          │
              │                              │         │ 风险: ★★★★（最高）              │
              │                              │         │ 退路: 拆到下一个 sprint            │
              └──────────────────────────────┘         └──────────────────────────────────┘
                                                  │
                                                  ▼
                                ┌──────────────────────────────────────┐
                                │   Phase 6 集成验收 + sprint 收口      │
                                │   Owner: robot-software-engineer +   │
                                │            product-okr-owner          │
                                │   依赖: P1, P2A/B/C, P3, P4, [P5]    │
                                └──────────────────────────────────────┘
```

并行启动规则：
- 主节点完成 P1 后，同一条消息里**并行**派 P2A、P2B（full-stack 一个 agent 串两个 task）+ P3（robot-software-engineer）。
- P3 完成 → 主节点验收 → 同一条消息里并行派 P4（autonomy-engineer）+ P5（full-stack-software-engineer）。
- 默认 2-4 并行 agent；P3 单 owner 单线是因为接口耦合（路径迁移必须由 1 个 agent 一口气完成才能给后续 phase 当基础），符合 `iteration_velocity.md` § 3.2 豁免条件 1。

## 1. Phase 详述

### Phase 1（P1）顶层 4 子目录脚手架｜主节点完成

**Owner**：主节点（product-okr-owner 角色，sprint 留档允许）

**做什么**：

```
git mkdir onboard mobile pc-tools cloud-relay
git mkdir onboard/src onboard/docker onboard/scripts
git mkdir mobile/web mobile/design mobile/fixtures
git mkdir pc-tools/route pc-tools/labeling pc-tools/evidence pc-tools/training
git mkdir cloud-relay/src cloud-relay/docker cloud-relay/test
```

为每个顶层目录写 `README.md`，说明：
- 用途
- 部署目标
- 后续 phase 会承接的内容
- 与其他目录的契约

**不做**：任何 git mv，任何代码改动。

**验收**：

```bash
test -d onboard && test -d mobile && test -d pc-tools && test -d cloud-relay
test -f onboard/README.md && test -f mobile/README.md && test -f pc-tools/README.md && test -f cloud-relay/README.md
```

### Phase 2A（P2A）cloud-relay 独立部署单位｜full-stack-software-engineer

**Owner**：full-stack-software-engineer

**做什么**：
- `git mv docker/remote-cloud-relay/Dockerfile cloud-relay/docker/Dockerfile`
- `git mv docker-compose.remote-cloud-relay.yml cloud-relay/docker-compose.yml`
- 修改 `cloud-relay/docker-compose.yml` 的 `build.context` 从 `.` 改为 `..` 或 `cloud-relay/`，`dockerfile` 路径相应调整
- 修改 `cloud-relay/docker/Dockerfile`：把 `COPY src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py /app/` 改为 `COPY src/remote_cloud_relay.py /app/`（即在 cloud-relay 本地 src 下的引用；本 Phase 还不动 `remote_cloud_relay.py` 本身位置，先建一个 symlink 或临时 copy 给 docker build 用）
- 实际**不**搬动 `remote_cloud_relay.py` 源码本身（仍在 `src/ros2_trashbot_behavior/...`），只是把 Dockerfile + compose 搬到 cloud-relay/；`remote_cloud_relay.py` 在 P3 完成后由 P5 一并搬迁，避免和 P3 的 ROS2 包迁移撞路径
- `scripts/remote_cloud_relay_docker_smoke.sh` → `cloud-relay/scripts/docker_smoke.sh`，更新内部路径引用
- 在 `cloud-relay/README.md` 写明：当前 `src/` 占位空，源码在 P3 完成后由 P5 搬入

**验收**：
- `git diff --check -- cloud-relay/ docker-compose.remote-cloud-relay.yml docker/remote-cloud-relay/ scripts/remote_cloud_relay_docker_smoke.sh` exit 0
- 文件存在性：`cloud-relay/docker/Dockerfile`、`cloud-relay/docker-compose.yml`、`cloud-relay/scripts/docker_smoke.sh`
- 老路径不存在：`! test -f docker-compose.remote-cloud-relay.yml`、`! test -d docker/remote-cloud-relay`
- Docker 构建：本 phase **跳过** docker build smoke（P5 完成后再跑），因为 Dockerfile 现在引用未来路径

### Phase 2B（P2B）mobile/ 脚手架｜full-stack-software-engineer

**Owner**：full-stack-software-engineer（与 P2A 同一 agent，串行做完两个 task）

**做什么**：
- `mobile/README.md` 写清楚 P5 之后承接：
  - `operator_gateway_static.py` 内嵌的 HTML/CSS/JS（抽出为独立文件）
  - `manifest.webmanifest`、`service-worker.js`、`offline.html`、icons（来自 PWA gate sprint）
  - phone-safe 中文文案 contract
- `mobile/design/README.md`：占位
- `mobile/fixtures/README.md`：占位
- **本 phase 不搬任何文件**，只建 README 框架；P5 之后由 full-stack-software-engineer 把 HTML/JS/CSS 从 `operator_gateway_static.py` 内嵌字符串抽出来搬到 `mobile/web/`

**验收**：
- `test -f mobile/README.md && test -f mobile/design/README.md && test -f mobile/fixtures/README.md`

### Phase 2C（P2C）docker compose 顶层分布｜full-stack-software-engineer（合并入 P2A 同 owner）

**做什么**：
- `git mv docker-compose.humble.yml onboard/docker-compose.humble.yml`（注意：与 P3 协调；如果 P3 还没完成，本 Phase 不动 `docker-compose.humble.yml`，P3 包内一并 mv）
- 选择：**本 Phase 不做 `docker-compose.humble.yml` 搬迁**，留给 P3 robot-software-engineer 在迁 ROS2 主链路时一并搬，因为 `docker-compose.humble.yml` 的 build context、卷挂载、`/ws` 工作目录都强耦合于 ROS2 源码位置。
- `.dockerignore` 视情况复制到 `onboard/` 和 `cloud-relay/` 各一份（避免 docker build context 误包含其他子目录）

**验收**：
- `test -f onboard/.dockerignore && test -f cloud-relay/.dockerignore`
- 仓库根 `.dockerignore` 可保留作 fallback

### Phase 3（P3）ROS2 包整体迁到 onboard/｜robot-software-engineer ★ 关键路径

**Owner**：robot-software-engineer（单线，强接口耦合，必须单 agent 一口气完成）

**做什么**：

1. **整体 `git mv`**：
   ```bash
   git mv src onboard/src
   git mv docker/humble onboard/docker/humble
   git mv docker-compose.humble.yml onboard/docker-compose.humble.yml
   git mv scripts/docker_humble_build.sh onboard/scripts/docker_humble_build.sh
   git mv scripts/docker_humble_dev.sh onboard/scripts/docker_humble_dev.sh
   git mv scripts/hardware_smoke_wave_rover.py onboard/scripts/hardware_smoke_wave_rover.py
   git mv scripts/hil_evidence_packet_gate.py onboard/scripts/hil_evidence_packet_gate.py
   git mv scripts/run_smoke_tests.sh onboard/scripts/run_smoke_tests.sh
   git mv scripts/setup_wsl_docker_mirrors.sh onboard/scripts/setup_wsl_docker_mirrors.sh
   git mv scripts/setup_wsl_ros2_humble.sh onboard/scripts/setup_wsl_ros2_humble.sh
   ```

2. **路径引用修复**：
   - `onboard/docker/humble/Dockerfile`：`WORKDIR /ws` 不变；如有 `COPY src/` 改为 `COPY onboard/src/` 或调整 `docker compose` 的 `build.context`
   - `onboard/docker-compose.humble.yml`：`build.context` 从 `.` 改为 `..` 或 `./`（视实际 compose 调用位置）；`volumes` 把 `./` 换成 `../`（如果挂载仓库到 `/ws`）
   - `onboard/scripts/docker_humble_build.sh`：`colcon build --symlink-install` 调用位置不变（容器内 `/ws`），但脚本里的 `docker compose build` 路径要更新
   - `onboard/scripts/run_smoke_tests.sh`：测试目录 `src/ros2_trashbot_*/test` → `onboard/src/ros2_trashbot_*/test`
   - 所有 launch 文件内的 `package='ros2_trashbot_*'` 不需要改（ROS2 包名解析与文件位置无关）；只要 colcon build OK 即可
   - 所有 `package.xml` 不动
   - 所有 `setup.py` 不动（包名仍是 `ros2_trashbot_*`）
   - 所有 `CMakeLists.txt` 不动
   - bringup `learn.launch.py`、`autonomous.launch.py`、`bringup.launch.py` 不动主体；但其中 `Node(package='ros2_trashbot_behavior', executable='operator_gateway', ...)` 暂时保留（P5 时再移除）

3. **新建 onboard/README.md**：写明 `cd onboard/ && colcon build --symlink-install` 的标准入口

4. **`onboard/scripts/run_smoke_tests.sh` 全部 tests 通过验证**：
   - `bash onboard/scripts/run_smoke_tests.sh` 输出所有包 `Ran N tests in T OK`，无 import 错误、无 path not found 错误

**验收命令**：

```bash
# 仓库根没有 src/ 也没有 docker-compose.humble.yml
! test -d src && ! test -f docker-compose.humble.yml && echo "old paths gone"

# 新路径
test -d onboard/src/ros2_trashbot_interfaces
test -d onboard/src/ros2_trashbot_behavior
test -d onboard/src/ros2_trashbot_bringup
test -f onboard/docker-compose.humble.yml
test -f onboard/scripts/run_smoke_tests.sh

# Docker build smoke
cd onboard && SKIP_COLCON=1 bash scripts/docker_humble_build.sh
# 预期：Docker build OK，输出包含 "ros-rbs-humble:dev Built"

# colcon build full
cd onboard && bash scripts/docker_humble_build.sh
# 预期：6 packages finished

# Python smoke tests
cd onboard && PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh
# 预期：interfaces / hardware / nav / bringup / behavior / vision 全部 Ran N tests OK

# git diff --check on onboard/
cd onboard && git diff --check -- .
# 预期：exit 0

# 没有遗漏的旧路径引用
grep -rn "^src/ros2_trashbot" --include="*.py" --include="*.sh" --include="*.yml" --include="*.md" onboard/ pc-tools/ cloud-relay/ mobile/ 2>/dev/null | grep -v sprints/
# 预期：无输出（sprints/ 历史文档允许保留旧路径）
```

### Phase 4（P4）pc-tools 工具搬迁｜autonomy-engineer

**Owner**：autonomy-engineer（依赖 P3 完成）

**做什么**：

1. **从 `onboard/src/ros2_trashbot_nav/` 抽出纯工具**：
   - `git mv onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/route_debug_web.py pc-tools/route/route_debug_web.py`
   - `git mv onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/route_csv_to_yaml.py pc-tools/route/route_csv_to_yaml.py`
   - `git mv onboard/src/ros2_trashbot_nav/test/test_route_debug_web.py pc-tools/route/test/test_route_debug_web.py`
2. **改 `onboard/src/ros2_trashbot_nav/setup.py`**：移除 `route_debug_web` 和 `route_csv_to_yaml` 的 `console_scripts` entry_point（如有）
3. **`onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/route_data_recorder.py` 是 ROS2 节点（订阅 `/odom` `/camera/image_raw`），必须留在 onboard**，不搬
4. **从 `scripts/` 抽出**：
   - `git mv scripts/evidence_crosscheck.py pc-tools/evidence/evidence_crosscheck.py`
   - `git mv scripts/phone_browser_acceptance_gate.py pc-tools/evidence/phone_browser_acceptance_gate.py`
5. **新建 labeling GUI 占位**（不实现真实 GUI）：
   - `pc-tools/labeling/README.md` 写明：未来承接 `operator_gateway_diagnostics.review_queue` 拆出来后的样本复核 GUI；可选 Web app（FastAPI + 简单 HTML） 或 desktop（PyQt/Tkinter）；本 Phase 不实现
   - `pc-tools/labeling/CONTRACT.md` 写明：从 `trashbot.vision_samples.v1` manifest 消费 raw image / annotated image / JSON / decision metadata；产出 `trashbot.vision_review_decisions.v1`（占位 schema）
6. **新建 training/ 占位**：
   - `pc-tools/training/README.md` 写明：未来承接 YOLO/RT-DETR 训练入口、数据集组织规范；本 Phase 不实现
7. **pc-tools/README.md 总入口**：写各子目录用途、运行环境（Python 3.10+，可选 ROS2 dev container）、与 onboard/ 的契约边界

**验收命令**：

```bash
# 文件搬过来了
test -f pc-tools/route/route_debug_web.py
test -f pc-tools/route/route_csv_to_yaml.py
test -f pc-tools/evidence/evidence_crosscheck.py
test -f pc-tools/evidence/phone_browser_acceptance_gate.py
test -f pc-tools/labeling/README.md
test -f pc-tools/labeling/CONTRACT.md
test -f pc-tools/training/README.md

# 老路径不存在
! test -f onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/route_debug_web.py
! test -f onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/route_csv_to_yaml.py
! test -f scripts/evidence_crosscheck.py
! test -f scripts/phone_browser_acceptance_gate.py

# route_data_recorder 仍在 onboard
test -f onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/route_data_recorder.py

# pc-tools/route/route_debug_web.py 可独立运行（dry run）
python3 -c "import sys; sys.path.insert(0, 'pc-tools/route'); import route_debug_web; print('import ok')"

# route_debug_web 测试搬过来后仍能跑
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=pc-tools/route python3 -m unittest pc-tools/route/test/test_route_debug_web.py
# 预期：Ran N tests OK

# evidence_crosscheck 仍可独立调用
python3 pc-tools/evidence/evidence_crosscheck.py --help
# 预期：打印 --help 信息

# nav 包测试不退化
cd onboard && PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_nav/test -p "test_*.py"
# 预期：Ran N tests OK（N 比 P3 完成后少几个，因为 route_debug_web 测试搬走了）

# onboard 完整 smoke 不退化
cd onboard && PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh
# 预期：Ran N tests OK
```

### Phase 5（P5）operator_gateway 拆到 cloud-relay｜full-stack-software-engineer ★ 最高风险

**Owner**：full-stack-software-engineer（依赖 P3 完成，与 P4 并行）

**风险等级**：★★★★（最高）

**做什么**：

1. **整体 git mv**：
   ```bash
   git mv onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py            cloud-relay/src/operator_gateway.py
   git mv onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py       cloud-relay/src/operator_gateway_http.py
   git mv onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_static.py     cloud-relay/src/operator_gateway_static.py
   git mv onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py cloud-relay/src/operator_gateway_diagnostics.py
   git mv onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py         cloud-relay/src/remote_cloud_relay.py
   git mv onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_http.py                   cloud-relay/test/test_operator_gateway_http.py
   git mv onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_static.py                 cloud-relay/test/test_operator_gateway_static.py
   git mv onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py            cloud-relay/test/test_operator_gateway_diagnostics.py
   git mv onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py                      cloud-relay/test/test_remote_cloud_relay.py
   ```

2. **改 `onboard/src/ros2_trashbot_behavior/setup.py`**：移除 `operator_gateway = ... entry_point`

3. **改 `operator_gateway.py`（原 ROS2 节点）**：
   - **删除 ROS2 节点逻辑**（rclpy.Node、subscribe、publish）
   - **改为 HTTP client**：通过 `remote_cloud_relay` 的内部 API 直接拿数据（in-process），不再依赖 ROS2 topic
   - 或者：让 `operator_gateway_http.py` 直接成为 cloud-relay 的一个 HTTP handler，与 `remote_cloud_relay` 共用 store
   - **建议方案**：把 `operator_gateway_http.py` 的 handlers 集成到 `remote_cloud_relay.py` 的 ThreadingHTTPServer 上（同一 server，同一 store），不再分两个独立 HTTP server

4. **改所有 `operator_gateway*` 的 import 路径**：
   - 旧：`from ros2_trashbot_behavior.operator_gateway_http import ...`
   - 新：`from operator_gateway_http import ...`（cloud-relay/src/ 加入 PYTHONPATH）

5. **改测试**：
   - 旧：`PYTHONPATH=src/ros2_trashbot_behavior python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_*.py`
   - 新：`PYTHONPATH=cloud-relay/src python3 -m unittest cloud-relay/test/test_operator_gateway_*.py`
   - 测试代码内 mock ROS2 topic 的部分改成 mock cloud_relay store

6. **改 `onboard/src/ros2_trashbot_bringup/launch/*.launch.py`**：移除 `Node(package='ros2_trashbot_behavior', executable='operator_gateway', ...)` 行

7. **改 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`**：
   - 当前：会订阅本地 ROS2 topic 并 POST 到云中转
   - 改造：不变，仍 POST 到云中转；只是被订阅的 topic 由 task_orchestrator 发布（task_orchestrator 不变）
   - 关键：`remote_bridge` 仍在 onboard 上车跑，不搬

8. **新建 `cloud-relay/scripts/run_tests.sh`**：替代 onboard 上的 operator_gateway 测试入口

9. **保持 phone-safe schema 字段完全不变**：`trashbot.phone_readiness.v1`、`trashbot.command_safety.v1`、`trashbot.phone_offline_resume_readiness.v1` 等所有已经存在的 schema 在 cloud-relay 输出端字段、值域、`evidence_boundary` 不变；不重新设计字段、不重新设计 phone-safe 文案。

**验收命令**：

```bash
# 文件搬迁
test -f cloud-relay/src/operator_gateway_http.py
test -f cloud-relay/src/operator_gateway_static.py
test -f cloud-relay/src/operator_gateway_diagnostics.py
test -f cloud-relay/src/remote_cloud_relay.py
test -f cloud-relay/test/test_operator_gateway_http.py

# onboard 不再有 operator_gateway
! test -f onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py
! test -f onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py
! test -f onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py

# onboard behavior 包测试不退化（剩余 task_orchestrator / remote_bridge / delivery_* 类测试）
cd onboard && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src/ros2_trashbot_behavior python3 -m unittest discover -s src/ros2_trashbot_behavior/test -p "test_*.py"
# 预期：除 operator_gateway 类外，原 task_orchestrator / remote_bridge / delivery_* 测试 Ran N tests OK

# cloud-relay 测试全部 OK
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=cloud-relay/src python3 -m unittest discover -s cloud-relay/test -p "test_*.py"
# 预期：Ran N tests OK，N >= 之前的 operator_gateway + remote_cloud_relay tests 总数

# cloud-relay Docker compose up 主路径
cd cloud-relay && TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=test-token docker compose up -d
sleep 3
curl http://127.0.0.1:8088/healthz
curl http://127.0.0.1:8088/readyz
cd cloud-relay && docker compose down
# 预期：healthz/readyz 返回 200，docker compose up OK

# onboard colcon build 仍 OK（移除 operator_gateway entry 后 behavior 包仍可 build）
cd onboard && bash scripts/docker_humble_build.sh
# 预期：6 packages finished

# bringup launch 不再启动 operator_gateway 节点
grep -rn "operator_gateway" onboard/src/ros2_trashbot_bringup/launch/ 2>/dev/null
# 预期：无输出
```

**退路方案**：如果 P5 的"把 operator_gateway_http.py 集成到 remote_cloud_relay HTTP server"在 sprint 时间内无法完成，本轮可以**只搬文件不改造**：
- git mv 完成（文件位置变了）
- onboard 上 operator_gateway entry_point 移除（不再有 ROS2 节点）
- cloud-relay/src/operator_gateway_http.py 保持原 in-process Python ROS2 节点逻辑暂时不可运行，但测试可独立跑（因测试本来就 mock 了 ROS2）
- HTTP server 真正接管 phone API 留到下一个 sprint
- final.md 写清楚这是 P5 部分完成、HTTP 集成留下一个 sprint

### Phase 6（P6）集成验收 + sprint 收口｜主节点 + product-okr-owner

**Owner**：主节点（运行集成命令）+ product-okr-owner（写 tech-done / side2side_check / final）

**做什么**：

1. **完整集成验收**（主节点跑所有 P1-P5 验收命令）
2. **更新 `AGENTS.md`**：把"5 个核心包"描述更新为"6 个 ROS2 包，全部在 onboard/src/，加上 mobile/ pc-tools/ cloud-relay/ 三个非 ROS2 子目录"
3. **更新 `OKR.md` §6"当前最高优先级"**：路径引用从 `src/ros2_trashbot_*` 更新为 `onboard/src/ros2_trashbot_*`
4. **更新 `README.md`**：顶层结构图、构建步骤
5. **更新 `docs/process/iteration_velocity.md`**：如有引用旧路径，同步更新
6. **写 sprint 6 文档剩余**：tech-done.md（实际改动 + 验证结果 + 偏差）、side2side_check.md（CEO 验收口径对比）、final.md（复盘 + OKR 进度声明 + 剩余风险）
7. **同步 `docs/process/okr_progress_log.md`**：在 2026-05-13 系列下追加本 sprint 的进度段
8. **commit + push**

**集成验收命令汇总**：

```bash
# 1. 顶层结构
test -d onboard && test -d mobile && test -d pc-tools && test -d cloud-relay
test -f onboard/README.md && test -f mobile/README.md && test -f pc-tools/README.md && test -f cloud-relay/README.md

# 2. 旧路径全部清空（仓库根不再有 src/ docker-compose.humble.yml docker/）
! test -d src && ! test -f docker-compose.humble.yml && ! test -f docker-compose.remote-cloud-relay.yml
! test -d docker

# 3. onboard 主链路
cd onboard && bash scripts/docker_humble_build.sh
cd onboard && PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh

# 4. cloud-relay 独立部署
cd cloud-relay && TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=test-token docker compose up -d
sleep 3 && curl http://127.0.0.1:8088/readyz | grep '"ok":true'
cd cloud-relay && docker compose down

# 5. pc-tools 独立运行
python3 pc-tools/evidence/evidence_crosscheck.py --help

# 6. mobile 占位
test -f mobile/README.md

# 7. AGENTS.md / OKR.md / README.md 路径引用同步
grep -c "onboard/src/ros2_trashbot" AGENTS.md OKR.md README.md
# 预期：每个 ≥ 1

# 8. sprint 留档完整
test -f sprints/2026.05.13_01-02_codebase-restructure-four-tier/pre_start.md
test -f sprints/2026.05.13_01-02_codebase-restructure-four-tier/prd.md
test -f sprints/2026.05.13_01-02_codebase-restructure-four-tier/tech-plan.md
test -f sprints/2026.05.13_01-02_codebase-restructure-four-tier/tech-done.md
test -f sprints/2026.05.13_01-02_codebase-restructure-four-tier/side2side_check.md
test -f sprints/2026.05.13_01-02_codebase-restructure-four-tier/final.md

# 9. okr_progress_log 同步
grep -c "2026.05.13_01-02_codebase-restructure-four-tier" docs/process/okr_progress_log.md
# 预期：≥ 1

# 10. OKR.md % 数字未改
grep -E "Objective [1-6].*约 [0-9]+%" OKR.md
# 预期：6 行，O1=75, O2=74, O3=76, O4=75, O5=54, O6=53
```

## 2. 风险与缓解

| 风险 | 等级 | 缓解 |
| --- | --- | --- |
| P3 完成后 colcon build 失败（path 引用未全修复） | ★★★ | robot-software-engineer 在 P3 内反复 build 直到 OK；如 30 min 内未 OK，主节点介入 patch |
| P5 operator_gateway 改造 HTTP client 超时 | ★★★★ | 退路方案：本轮只搬文件不改造 HTTP server 集成，集成留到下一个 sprint；final.md 写清退路 |
| docker-compose context 改变后 build context 包含 onboard/ pc-tools/ 全部文件，build 时间显著上升 | ★★ | 各 docker-compose 改 context 为对应子目录而非仓库根；加 `.dockerignore` 排除 sprints/、docs/ |
| sprint 历史文档（`sprints/*/tech-done.md`）内 `src/ros2_trashbot_*` 路径过时 | ★ | 不改历史 sprint 文档（按 sprint 留档原则）；只在 README / AGENTS.md / OKR.md / `docs/process/iteration_velocity.md` 更新引用 |
| 子 agent 之间路径冲突（P3 在改 src/，P4 同时也想改 src/route_*） | ★★★ | P4/P5 必须等 P3 完成；只有 P2A/P2B 可与 P3 并行（因不动 src/） |
| Windows + LF/CRLF 文件 mode 在 git mv 后丢失 | ★ | 各 agent 在 PowerShell 下用 `git mv`（git 处理换行符），不用 `Move-Item` 系统命令 |
| 远端 origin/master 期间有新 commit 进来 | ★★ | sprint 收口前 `git pull --rebase`；若冲突，按本次 OKR.md auto-merge 类似策略处理 |
| Phase 5 之后 bringup launch 移除 operator_gateway 节点，可能让 patrol/collect 流程缺少状态聚合 | ★★★ | task_orchestrator 仍写 `task_record.json`、remote_bridge 仍向云中转 POST，cloud-relay 来聚合状态；不需要 onboard 自己跑 HTTP UI |

## 3. 子 Agent Prompt 框架（主节点派发时使用）

每个子 agent prompt 必须按 AGENTS.md SOP 含五段：

```
[角色 System Prompt]
（从 .codex/agents/<role>.toml prompt 字段完整复制）

[本轮任务]
本轮是 sprint 2026.05.13_01-02_codebase-restructure-four-tier 的 Phase {N}：{phase 名}。
依赖：{前置 phase}。并行：{并行 phase}。

[文件范围]
{允许改动的路径列表，本 phase 之外的文件一律不动}

[验收命令]
{从 tech-plan.md Phase {N} 验收段复制}

[输出要求]
1. git status --short（只允许出现授权路径）
2. 所有验收命令的输出
3. 失败定位（如有）
4. 剩余风险
5. 是否仍为 structural_refactor_only
```

## 4. 进度边界与 OKR 影响

本轮 sprint 是结构治理 sprint，**不影响任何 Objective 完成度数字**：
- O1 保持约 75%
- O2 保持约 74%
- O3 保持约 76%
- O4 保持约 75%
- O5 保持约 54%（software_proof_docker_phone_offline_resume_gate）
- O6 保持约 53%（software_proof_docker_production_recovery_gate）

证据边界：`structural_refactor_only`。

final.md 验收时需复核：所有 OKR % 数字、KR 文字、`evidence_boundary` 字段未变。

## 5. 是否本轮一次性做 P1-P5

CEO 选了"本轮一次性全迁完"。tech-plan 默认按这条路径推进；但保留 P5 退路方案（"只搬文件不改造"）。

**主节点本轮判断**：建议把 P5 完整改造作为本轮"努力目标"，但不强求；如 P5 改造无法在合理时间内完成，按退路方案收口本轮，下一个 sprint 由 full-stack-software-engineer 专责完成 HTTP server 集成。这样既满足 CEO 一次性迁完的意图（文件位置全到位），又控制风险。

待 CEO 在 PRD/tech-plan 上签字确认后，主节点立即派子 agent 并行启动 P1 + P2A/P2B + P3，按依赖图推进。
