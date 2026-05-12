# Sprint 2026.05.13_01-02 Codebase Restructure Four-Tier - Pre-Start

## 状态

- 阶段：pre-start
- sprint_type: **epic**（跨 4 个部署面 / 6 个 ROS2 包 / 数十文件 git mv / build & test pipeline 重建）
- 时间：2026-05-13 01:xx Asia/Shanghai
- 主集成 Owner：`product-okr-owner`（sprint 收口）+ `robot-software-engineer`（ROS2 主链路集成）
- 并行 Owner：`full-stack-software-engineer`、`autonomy-engineer`、`hardware-engineer`
- 证据边界：`structural_refactor_only`（不声明任何 OKR 完成度变化）

## 上一轮未完成项与阻塞

- 上一轮 sprint：`2026.05.13_00-01_okr-progress-log-extraction`（OKR.md 瘦身 + 进度日志外迁），已 commit + push（`1c97b65`）。
- 上一轮治理 sprint：`2026.05.12_23-24_iteration-velocity-fence-tuning`（Epic/Micro 分层、2-4 并行、最低 Objective 软提醒、blocker 红线），已 commit + push（`7792696`）。
- 远端 master 与 origin/master 同步。
- 无遗留阻塞。

## 本轮触发

CEO 原话：「代码库也要整理一下。一个是给 orange pi 上位机用的（ubuntu22）/ 一个是给用户手机的 / 一个是 PC 端 ros2 打标 路径学习 展示 训练 用的。应该够了？」

CEO 决策（AskQuestion 5 题）：
- 4 块结构：`onboard/` + `mobile/` + `pc-tools/` + `cloud-relay/`（额外加 cloud-relay，因为它本来就是独立公网部署单位）
- 同一 monorepo，顶层 4 子目录
- `operator_gateway` 整体搬到 `cloud-relay/`，上车不再保留 HTTP fallback
- 本轮**一次性全迁完**：git mv + 修 import/launch + 重建 build/install + tests pass
- `pc-tools/` 含现有工具 + 新建视觉样本标注/复核 GUI 占位

## OKR 最低优先级核对

按当前 OKR §4.1：O5≈54%、O6≈53% 为最低；O1≈75%、O2≈74%、O3≈76%、O4≈75% 居中或较高。

**本轮不直接推进任何 Objective**：
- 本轮是结构治理 sprint（结构重构 + 路径迁移 + build/test 重建），不引入新功能、不变 KR、不变完成度数字。
- 不针对最低 Objective 也合理：当前 4G 云中转 / 手机 / 上车真实硬件相关推进都受真实硬件、真实云、真实 4G 等外部条件约束（属于「最低 Objective 当前无可推进的软件工作」）；先把代码库切清楚，再让后续 sprint 在各自部署面里专注推进相应 KR，提高未来迭代效率。
- 软提醒规则要求 `final.md` 复核此理由是否仍成立。

## 主集成 Owner 与并行 Owner 分工初步

| Owner | Phase | 文件范围 |
| --- | --- | --- |
| robot-software-engineer | P3 / 集成验收 | onboard/ ROS2 包整体目录迁移、setup.py / package.xml / CMakeLists 路径修正、bringup launch 路径修正、`colcon build --symlink-install` 重建、smoke tests |
| full-stack-software-engineer | P1B / P2 / P5 | cloud-relay/ 拆分（含 `remote_cloud_relay.py` 与 docker/compose）、mobile/ 脚手架、operator_gateway 整体搬到 cloud-relay 并改造为 HTTP client 模式 |
| autonomy-engineer | P4 | pc-tools/ 工具搬迁（`route_debug_web.py`、`route_csv_to_yaml.py`、`evidence_crosscheck.py`、`phone_browser_acceptance_gate.py`）、新建 labeling GUI 占位 |
| hardware-engineer | P3 配套 | onboard/scripts/hardware_smoke_wave_rover.py、onboard/docker/humble 路径修正、`docs/vendor/VENDOR_INDEX.md` 引用更新 |
| product-okr-owner | sprint 留档 | sprint 6 文档、OKR.md §6 引用更新、迁移完成后的 README/AGENTS.md 同步 |

完整 phase 划分、并行边界、依赖关系、风险等级、验收命令见 `tech-plan.md`。

## 风险预判（详见 tech-plan §风险）

1. **Phase 5（operator_gateway → cloud-relay）风险最高**：当前 `operator_gateway*.py` 4 个文件 + 100+ 个相关 tests，要从 ROS2 in-process subscriber 改成 HTTP client；如果本轮无法在 sprint 时间内完成，建议把 P5 拆到独立下一个 sprint。
2. **包间 import 强耦合**：`src/` 整体迁到 `onboard/src/` 会破坏所有 launch 文件、setup.py、CMakeLists.txt、smoke scripts、docker-compose context 的路径引用，需要 robot-software-engineer 单线串行做基础迁移，其他 Owner 后续 phase 才能并行。
3. **Docker context 变化**：现有 `docker-compose.humble.yml` 和 `docker-compose.remote-cloud-relay.yml` 在仓库根，迁到各自子目录后 `context: .` 含义改变。
4. **sprint 文档/历史路径**：本轮迁移会让所有 `sprints/*/tech-done.md` 里的 `src/ros2_trashbot_*` 路径引用过时，但不应回头改历史 sprint 文档（按 sprint 留档原则，历史是历史）。
