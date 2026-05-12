# Sprint 2026.05.13_01-02 Codebase Restructure Four-Tier - PRD

## 状态

- 阶段：prd
- sprint_type: epic
- 时间：2026-05-13 01:xx Asia/Shanghai
- 主集成 Owner：product-okr-owner（PRD 审定）+ robot-software-engineer（技术可行性背书）
- 证据边界：`structural_refactor_only`

## 1. 背景与北极星对齐

当前 `ros_rbs` monorepo 把上车 ROS2 代码、手机 Web UI、PC 开发工具、独立云中转服务全部混在 `src/` + `scripts/` + `docker/` 顶层目录里。`ros2_trashbot_behavior` 包内同时承载：

- 上车决策（`task_orchestrator.py`、`delivery_*.py`、`dropoff_*.py`、`task_record.py`）
- 手机后端（`operator_gateway*.py` × 4）
- 远程桥客户端（`remote_bridge*.py` × 2）
- 独立云中转 HTTP 服务（`remote_cloud_relay.py`，5106 行，已有独立 Dockerfile）

这违反了：北极星「用户只用手机 / 上车跑 ROS2 / 4G 走云端中转」的清晰分层；以及战略 §5「4G 数据通路走云端中转，不走手机直连 WiFi」。

本轮把代码库按部署目标切成 4 块，让后续 sprint 在各自部署面里专注推进，不再因为"看起来 behavior 包改了"被迫跨面回归。

## 2. 用户价值与不做什么

### 做什么

- 让上车 Orange Pi（Ubuntu 22 + ROS2 Humble）的 build/deploy/test 与手机 PWA、PC 工具、云中转服务**完全解耦目录**。
- 让 4G 走云端中转的产品定位**在代码结构上落地**（cloud-relay 独立子目录、独立 Dockerfile、独立 compose、独立 entry，**与上车 ROS2 build 无任何 `colcon` / setup.py 耦合**）。
- 让 PC 端打标 / 路径学习 / debug web / 评估证据交叉检查工具集中到 `pc-tools/`，不再混在 `scripts/` 根目录或散落在 `src/ros2_trashbot_nav/` 的 ROS2 entry_points 里。
- 给手机端 PWA 一个独立目录 `mobile/`，让后续设计资源、HTML/CSS/JS、service worker、manifest 可以单独迭代而不污染 ROS2 build。

### 不做什么

- 不重命名任何 ROS2 包（包名仍是 `ros2_trashbot_interfaces` / `_hardware` / `_nav` / `_vision` / `_behavior` / `_bringup`），只搬目录位置到 `onboard/src/`。
- 不修改任何 ROS2 接口契约（`msg`/`srv`/`action` 不动）。
- 不修改任何 KR 文字、任何 Objective 完成度数字。
- 不删除 `sprints/` 历史 sprint 文档（即使其中路径已过时）。
- 不在本轮新增功能或新增 ROS2 节点。
- 不实施真实云、真实 4G、真实手机设备、真实 HIL、真实送达；本轮不影响 O1-O6 任何完成度。

## 3. 顶层结构（CEO 已拍板）

```
e:\rober\
├── onboard/                     # Orange Pi 上车（Ubuntu 22 + ROS2 Humble）
│   ├── src/
│   │   ├── ros2_trashbot_interfaces/   # 不动
│   │   ├── ros2_trashbot_hardware/     # 不动
│   │   ├── ros2_trashbot_nav/          # 移除 route_debug_web / route_csv_to_yaml entry_points
│   │   ├── ros2_trashbot_vision/       # 不动
│   │   ├── ros2_trashbot_behavior/     # 瘦身：移除 operator_gateway*、保留 task_orchestrator/remote_bridge
│   │   └── ros2_trashbot_bringup/      # 不动主体，launch 引用更新
│   ├── docker/humble/Dockerfile
│   ├── docker-compose.humble.yml
│   └── scripts/
│       ├── docker_humble_build.sh
│       ├── docker_humble_dev.sh
│       ├── hardware_smoke_wave_rover.py
│       └── run_smoke_tests.sh
│
├── mobile/                      # 用户手机 PWA / 设计资源
│   ├── web/                     # 后续承接 HTML/CSS/JS、manifest、service worker
│   ├── design/                  # 配色 token、字号、间距、按钮态
│   ├── fixtures/                # 离线 mock 数据（可选）
│   └── README.md
│
├── pc-tools/                    # PC 工作站（macOS/Win/Linux）开发工具
│   ├── route/                   # 路径学习 / debug
│   │   ├── route_debug_web.py
│   │   └── route_csv_to_yaml.py
│   ├── labeling/                # 视觉样本标注 / 复核 GUI 占位
│   │   └── README.md
│   ├── evidence/                # 证据交叉检查
│   │   ├── evidence_crosscheck.py
│   │   └── phone_browser_acceptance_gate.py
│   ├── training/                # 未来 YOLO/RT-DETR 训练占位
│   │   └── README.md
│   └── README.md
│
├── cloud-relay/                 # 4G 云中转服务（4C8G 公网部署单位）
│   ├── src/
│   │   ├── remote_cloud_relay.py
│   │   ├── operator_gateway*.py（P5 搬入后）
│   │   └── ...
│   ├── docker/Dockerfile
│   ├── docker-compose.yml
│   ├── test/
│   └── README.md
│
├── docs/                        # 不动
├── sprints/                     # 不动
├── AGENTS.md / OKR.md / README.md  # 内容引用路径更新
└── .env.example / .gitignore / .dockerignore
```

## 4. 关键功能契约（不变）

| 契约 | 现状 | 本轮处理 |
| --- | --- | --- |
| `ros2_trashbot_interfaces` msg/srv/action | 由 6 个包共同消费 | 不动 |
| `trashbot.remote.v1` command/status/ack envelope | 由 `remote_bridge_protocol.py` 定义 | 不动；只是协议文件搬迁路径 |
| `trashbot.phone_readiness.v1` 等 phone-safe schema | 由 `operator_gateway_http.py` 与 `remote_cloud_relay.py` 产出 | P5 改造时保持 schema 字段、值域、phone-safe 边界不变 |
| WAVE ROVER UART JSON 协议 | 由 `ros2_trashbot_hardware` 实现 | 不动 |
| Nav2 / fixed-route 行为 | 由 `ros2_trashbot_nav` + behavior 配合 | 不动 |

## 5. 验收口径（CEO 视角，对应 final.md 复核）

- [ ] `colcon build --symlink-install` 在 `onboard/` 目录下 OK（不在仓库根，避免 Docker 误带 mobile/pc-tools）
- [ ] `cloud-relay/` 下 `docker compose up` 可独立启动云中转，`/healthz` `/readyz` 通过
- [ ] `pc-tools/route/route_debug_web.py` 可独立 `python3` 启动（脱离 colcon 也行；如仍依赖 ROS2 runtime 则在 README 写清楚）
- [ ] `mobile/` 有 README 解释后续 P5 之后这里承接哪些资产
- [ ] 上车不再有 `operator_gateway` ROS2 node（P5 完成后）
- [ ] 所有 sprint 之前定义的 phone-safe schema / API contract 在 cloud-relay 侧仍可工作；Task A 类 `Ran N tests in T OK` 仍能输出
- [ ] OKR.md 任何 Objective % / KR 文字未改
- [ ] AGENTS.md / OKR.md / README.md 顶层路径引用更新到新结构

## 6. 进度边界声明

本轮证据边界：**`structural_refactor_only`**。不声明：
- 任何 OKR 完成度变化（O1-O6 保持上轮数字）
- 任何 HIL / 真实云 / 真实 4G / 真实手机设备 / 真实送达 通过
- 任何新功能、新 API、新 schema、新 KR

允许声明：
- 目录结构 + build/test 通过
- 现有 tests 在新结构下 `Ran N tests in T OK` 不退化
- Docker build/up smoke 通过

## 7. 是否分多 sprint

tech-plan 将提出 Phase 1-5 划分。如果 Phase 5（operator_gateway → cloud-relay 改造为 HTTP client）评估超出本轮风险预算，**建议拆到下一个独立 sprint**（届时由 product-okr-owner + full-stack-software-engineer 收口）。本轮 PRD 接受这种"P1-P4 本轮完成 + P5 下轮"的退路方案，前提是 final.md 写清退路理由与下一轮 sprint 名。
