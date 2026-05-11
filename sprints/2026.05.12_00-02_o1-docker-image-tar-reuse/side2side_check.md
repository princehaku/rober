# Sprint 2026.05.12_00-02 O1 Docker Image Tar Reuse - Side2Side Check

## 状态

- 阶段：side2side_check
- 时间：2026-05-12 00:42 Asia/Shanghai
- Product Owner：Product Manager / OKR Owner
- Engineering Owner：`robot-software-engineer`
- 证据范围：`software_proof_docker_only`
- 验收结论：有条件通过；仅通过 Docker-only 软件围栏，不构成 `hil_pass`

## 用户价值和产品北极星

北极星仍是低成本 ROS2 自主垃圾投递机器人：普通手机用户交付垃圾后，小车可验证地完成固定路线送达。

本轮验收的用户价值不是证明小车已经能上车运行，而是把上一轮被 registry mirror/proxy 阻断后的人工镜像复用动作收敛进 `scripts/docker_humble_build.sh`。这给后续 O1 真实 HIL 准备提供一条可重复的 Docker/Humble 环境恢复路径。

## OKR 映射

- O1：直接支撑 Docker/Humble readiness 和后续硬件桥验证准备；当前仍约 75%，blocked on real HIL。
- O2：间接支撑后续 task record / failure recovery 复盘环境；本轮不更新完成度。
- O3：间接支撑后续 fixed-route replay 环境；本轮不更新完成度。
- O4/O5：本轮不涉及视觉、手机、语音或用户触点。

## KR 对照

| Sprint KR | 验收结果 | 证据 |
| --- | --- | --- |
| KR-O1-Docker-1：支持 `ROS_HUMBLE_IMAGE_TAR` 显式 tar 入口 | 通过软件验收 | `tech-done.md` 记录 tar provided 路径会先 `docker load -i`，再沿用目标镜像可运行校验 |
| KR-O1-Docker-2：空 tar / 缺失 tar 快速失败 | 通过 | 空 tar exit 2；缺失 tar exit 2；均输出 `evidence_scope=software_proof_docker_only`，不进 Docker build |
| KR-O1-Docker-3：`SKIP_DOCKER_BUILD=1` 仍校验目标镜像可运行 | 通过 blocked 语义验收 | 本地 `ros-rbs-humble:dev` tag 不可运行，exit 4，错误为 `descriptor is neither a manifest or index` |
| KR-O1-Docker-4：不冒充 `hil_pass` | 通过 | `tech-done.md` 和本验收均标注 `software_proof_docker_only` |

## 做什么 / 不做什么对照

已做：

- 将可信 Docker image tar 导入入口产品化为脚本参数。
- 保持默认 build 路径不变；tar 复用被限定在显式 `SKIP_DOCKER_BUILD=1` 路径。
- 对空 tar、缺失 tar、tar provided 但未 skip build、本地目标镜像不可运行做快速失败或 blocked 分类。
- 记录工程验证结果和剩余风险。

未做且不应算缺口：

- 未修改 ROS2 产品代码、测试代码、硬件配置、launch 参数或 vendor 文件。
- 未执行真实 WAVE ROVER move-test、串口 smoke、`T=1001` 反馈采集或 evidence packet 归档。
- 未更新 `OKR.md` 完成度。

## 优先级和验收口径

- P0：脚本入口、错误路径和复用校验已满足。
- P1：operator 输出能够说明 tar 可信来源、tag 匹配和 Docker daemon 风险。
- P2：本 sprint 的实现留档已创建，验收和最终复盘由当前两个收口文档补齐。

产品验收口径是：后续 Engineer 能在 registry mirror/proxy broken 时使用可信 tar 恢复本地目标镜像复用路径；如果 tar 缺失、为空、不可信或目标镜像不可运行，脚本必须失败而不是给出假阳性。本轮没有可信 tar，因此不要求证明成功 `docker load` + colcon。

## 责任 Engineer

- 已执行：`robot-software-engineer`
- Product 验收：确认范围、OKR 映射、证据边界和 sprint 链路
- 不需要介入：`hardware-engineer`、`autonomy-engineer`、`full-stack-software-engineer`

## 证据链和阻塞

已形成证据：

- `bash -n scripts/docker_humble_build.sh` exit 0。
- 空 `ROS_HUMBLE_IMAGE_TAR` exit 2，快速失败。
- 缺失 tar path exit 2，快速失败。
- `SKIP_DOCKER_BUILD=1` exit 4，保留本地目标镜像不可运行的 blocked evidence。
- `ROS_HUMBLE_IMAGE_TAR=/etc/hosts` 且未设置 `SKIP_DOCKER_BUILD=1` exit 2，防止 load 后继续 build 的语义混乱。
- scoped `git diff --check` 通过。

仍缺证据：

- 可信 `ros-rbs-humble:dev` tar 来源。
- 成功 `docker load` 后的可运行目标镜像探针和完整 colcon build。
- 真实 WAVE ROVER、串口、Orange Pi、`T=1001`、`command.txt`、`serial.log`、`feedback_T1001.log`、同一 `evidence_ref` evidence packet。

## 验收结论

本轮按 `software_proof_docker_only` 收口。它证明脚本级 tar 复用入口和失败围栏已经具备，但未证明成功 Docker load 后的完整构建，也未证明任何真实硬件、串口、WAVE ROVER、`T=1001` 或 HIL evidence packet。

因此不更新 `OKR.md` 完成度；O1 仍约 75%，继续 blocked on real HIL。
