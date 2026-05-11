# Sprint 2026.05.12_00-02 O1 Docker Image Tar Reuse - Pre Start

## 状态

- 阶段：pre_start
- 时间：2026-05-12 00:02 Asia/Shanghai
- Owner：Product Manager / OKR Owner
- 执行主责：`robot-software-engineer`
- 证据范围：`software_proof_docker_only`
- 本轮边界：Docker-only 主机可执行的镜像 tar 导入与复用校验；不声明真实硬件 `hil_pass`

## 用户价值和产品北极星

北极星仍是让普通手机用户最终能把垃圾交给小车后，由小车可靠完成低成本固定路线送达。当前最低完成度和最高优先级仍在 O1：可信底盘控制层的 HIL 边界与补齐。

本机没有真实 WAVE ROVER、串口和 Orange Pi 运行环境，所以上车 `hil_pass` 不能在本轮完成。本轮用户价值是把上一轮手工 operator 动作产品化：当 Docker registry mirror/proxy broken 时，工程师可以从可信机器导入可运行的 `ros-rbs-humble:dev` tar，并用同一构建脚本验证镜像可复用，再继续 Docker/Humble 软件围栏验证。这样可以减少环境阻断对 O1 后续 HIL 准备的影响，但不把 Docker 证据冒充真实硬件证据。

## OKR 映射

- O1 当前约 75%，仍是最高优先级。上一轮已证明 Docker daemon/builder 可用，但默认 build blocked 在 registry mirror/proxy 返回 `text/html`，本地 `ros-rbs-humble:dev` tag 也不可运行。
- O2/O3 当前约 77%，依赖 O1 的真实 evidence packet 与同一 `evidence_ref` 复账。本轮不直接推进 O2/O3 实机闭环。
- O4 当前约 76%，本轮不涉及视觉或电梯感知。
- O5 当前约 80%，本轮不涉及手机/Web 触点。

## 近期证据

- `sprints/2026.05.12_00-01_o1-docker-humble-base-image-fallback/final.md`：Docker daemon 与 `desktop-linux` builder 可用；默认 Docker build blocked 于 `docker.io/osrf/ros:humble-desktop` metadata/layer 返回 `text/html`；本地 `ros-rbs-humble:dev` tag 存在但 `docker run` 返回 `descriptor is neither a manifest or index`。
- 同一 final 的下一步 operator 动作：修复或更换 registry mirror/proxy 后 build，或从可信机器导出可运行 `ros-rbs-humble:dev` 后 `docker load`，再执行 `SKIP_DOCKER_BUILD=1 bash scripts/docker_humble_build.sh`。
- `sprints/2026.05.11_23-24_hil-packet-crosscheck-bridge/final.md`：HIL packet gate 与 crosscheck 已能区分 `hil_pass`、`blocked`、`software_proof`，但真实 WAVE ROVER 串口和同一 `evidence_ref` run 仍缺。
- `OKR.md` 当前快照：O1 约 75%，O2/O3 约 77%，O4 约 76%，O5 约 80%；当前最高优先顺序仍是 `O1 -> O2 -> O3`。

## 上轮未完成项和阻塞

- 未完成：registry mirror/proxy broken 时，可信镜像 tar 的导入与复用仍是人工说明，不是脚本级入口。
- 阻塞：默认 Docker build 仍依赖可用 registry path；本机已有目标 tag 但 manifest 不可运行。
- 真实硬件缺口：无 WAVE ROVER、无真实串口、无 `command.txt`、`serial.log`、`feedback_T1001.log` packet，不允许升级为 `hil_pass`。

## KR 拆解

- KR-O1-Docker-1：`scripts/docker_humble_build.sh` 支持显式 `ROS_HUMBLE_IMAGE_TAR=/path/to/ros-rbs-humble-dev.tar`，在复用前自动 `docker load`。
- KR-O1-Docker-2：当 tar 路径为空或不存在时快速失败，输出 operator 可读原因，不进入误导性的后续构建。
- KR-O1-Docker-3：`SKIP_DOCKER_BUILD=1` 仍必须验证目标镜像可运行，不能只信任 tag 存在。
- KR-O1-Docker-4：输出继续标注 `evidence_scope=software_proof_docker_only`，并保留不会冒充 `hil_pass` 的边界。

## 做什么 / 不做什么

做：

- 把可信机器导出的 Docker image tar 导入动作收敛为脚本入口。
- 在 registry mirror/proxy broken 时给 Docker-only 主机一条可执行、可验证的下一步。
- 保持验证围栏为 shell 语法、缺失输入快速失败、本地镜像复用校验和 scoped diff check。

不做：

- 不修改 ROS2 产品代码、测试代码、硬件配置、launch 参数或 vendor 文件。
- 不设计真实 move-test，不接触 WAVE ROVER 串口，不声明 `hil_pass`。
- 不更新 `OKR.md` 完成度；只有真实 HIL evidence packet 或可复账实机证据出现后再更新。
- 不扩大为全量测试或广泛 Docker 清理。

## 优先级和验收口径

P0：实现 `ROS_HUMBLE_IMAGE_TAR` 入口并在 `SKIP_DOCKER_BUILD=1` 前完成 tar load 与目标镜像可运行校验。

P1：错误路径必须短、明确、可操作：空 tar、缺失 tar、load 后目标镜像不可运行都要返回非 0 并说明下一步。

P2：执行留档必须写入当前 sprint 的 `tech-done.md`，后续阶段再补 `side2side_check.md` 和 `final.md`，不得一次性预生成。

## 责任 Engineer

- 主责：`robot-software-engineer`
- 咨询：Product Manager / OKR Owner 只验收范围、证据边界和 sprint 留档
- 不需要：`hardware-engineer`，因为本轮不涉及真实串口、WAVE ROVER、电气、波特率或 vendor 参数
- 不需要：`autonomy-engineer`、`full-stack-software-engineer`

## 风险、阻塞和证据链

- 风险：可信 tar 本身可能来自错误平台、损坏镜像或不含 `/opt/ros/humble/setup.bash`；必须通过 `docker run` 探针拦住。
- 风险：`docker load` 输出的 tag 可能与 `ROS_HUMBLE_IMAGE` 不一致；实现需要明确目标镜像仍按 `ROS_HUMBLE_IMAGE` 校验。
- 阻塞：如果 Docker daemon 不可用，脚本仍应按既有 preflight 分类失败，本轮不解决 Docker Desktop 本身故障。
- 证据链：本轮最多形成 `software_proof_docker_only`，只证明 Docker/Humble 构建环境复用入口可用；真实 O1 `hil_pass` 仍需 WAVE ROVER 串口 evidence packet。

## Sprint 文档

本轮只创建并填写：

- `sprints/2026.05.12_00-02_o1-docker-image-tar-reuse/pre_start.md`
- `sprints/2026.05.12_00-02_o1-docker-image-tar-reuse/prd.md`
- `sprints/2026.05.12_00-02_o1-docker-image-tar-reuse/tech-plan.md`

不得在 planning 阶段预生成：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
