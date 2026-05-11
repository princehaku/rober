# Sprint 2026.05.12_00-02 O1 Docker Image Tar Reuse - Final

## 状态

- 阶段：final
- 时间：2026-05-12 00:45 Asia/Shanghai
- Product Owner：Product Manager / OKR Owner
- Engineering Owner：`robot-software-engineer`
- 证据范围：`software_proof_docker_only`
- 收口结论：完成 sprint 内软件验收；不更新 `OKR.md` 完成度

## 用户价值和产品北极星

北极星仍是让普通手机用户把垃圾交给小车后，小车能以低成本、可验证、可复盘的方式完成固定路线送达。O1 的可信底盘控制层仍是当前主线，因为真实底盘控制、反馈和 evidence packet 还没有完成 HIL 证明。

本轮把“从可信机器导入可运行 Docker/Humble 镜像 tar”从人工说明变成脚本入口，减少 registry mirror/proxy broken 对后续 HIL 准备的阻断。它是环境恢复抓手，不是业务闭环或硬件闭环。

## OKR 映射

- O1：直接支撑后续硬件桥上车验证的 Docker/Humble 环境准备；状态仍约 75%，blocked on real HIL。
- O2：未更新。真实任务恢复闭环仍需要同一 `evidence_ref` 的实机任务记录。
- O3：未更新。fixed-route replay 仍需要与 O1 real HIL packet 对齐的真实或可复账 evidence。
- O4/O5：未更新。本轮没有视觉、手机、语音或量产用户触点交付。

## KR 拆解结果

完成：

- 支持 `ROS_HUMBLE_IMAGE_TAR` 作为显式 Docker image tar 入口。
- 空 tar、缺失 tar 和 tar provided 但未 `SKIP_DOCKER_BUILD=1` 均快速失败。
- `SKIP_DOCKER_BUILD=1` 继续验证 `ros-rbs-humble:dev` 目标镜像是否可运行，而不是只看 tag 是否存在。
- 文档和输出保持 `software_proof_docker_only`，没有写成 `hil_pass`。

未完成且留到后续：

- 没有可信 tar，未证明成功 `docker load` 后可运行镜像和完整 colcon build。
- 没有真实 WAVE ROVER、串口、Orange Pi 或 `T=1001` 反馈，未形成 HIL evidence packet。
- 没有同一 `evidence_ref` 下的 O2/O3 route replay / task record 实机复账。

## 本轮核心抓手

核心抓手是将上一轮 final 的 operator 下一步动作变成可执行脚本路径：

```bash
ROS_HUMBLE_IMAGE_TAR=/path/to/ros-rbs-humble-dev.tar SKIP_DOCKER_BUILD=1 bash scripts/docker_humble_build.sh
```

脚本策略选择是保守的：tar 复用只允许出现在 explicit local-image reuse 路径中。`docker load` 成功也不等于验收通过，目标镜像仍必须通过既有 Docker run 探针。

## 做什么 / 不做什么

做了：

- 由 `robot-software-engineer` 修改 `scripts/docker_humble_build.sh`。
- 创建 `tech-done.md` 记录实现、验证、失败定位和剩余风险。
- Product 创建本 `side2side_check.md` 与 `final.md`，完成 sprint 收口。

没有做：

- 未改 `OKR.md`。
- 未改 ROS2 产品代码、测试代码、硬件配置、launch 参数、vendor 文件或其他 sprint 目录。
- 未做真实硬件验证、串口验证、WAVE ROVER move-test、`T=1001` 反馈采集或 HIL packet 归档。

## 验收结果

工程验证摘要：

```text
bash -n scripts/docker_humble_build.sh -> exit 0
ROS_HUMBLE_IMAGE_TAR= SKIP_DOCKER_BUILD=1 bash scripts/docker_humble_build.sh -> exit 2
ROS_HUMBLE_IMAGE_TAR=/tmp/does-not-exist.tar SKIP_DOCKER_BUILD=1 bash scripts/docker_humble_build.sh -> exit 2
SKIP_DOCKER_BUILD=1 bash scripts/docker_humble_build.sh -> exit 4
ROS_HUMBLE_IMAGE_TAR=/etc/hosts bash scripts/docker_humble_build.sh -> exit 2
git diff --check -- scripts/docker_humble_build.sh sprints/2026.05.12_00-02_o1-docker-image-tar-reuse/tech-done.md -> exit 0
```

Product 收口验证：

```bash
git diff --check -- sprints/2026.05.12_00-02_o1-docker-image-tar-reuse/side2side_check.md sprints/2026.05.12_00-02_o1-docker-image-tar-reuse/final.md
```

结果：exit 0，无输出。

## 失败定位

当前唯一保留的 blocked evidence 是本地 `ros-rbs-humble:dev` tag 不可运行：

```text
descriptor is neither a manifest or index
```

这不是本轮 `ROS_HUMBLE_IMAGE_TAR` 脚本逻辑失败，而是 Docker 本地目标镜像状态不可用。脚本已经正确把该状态拦截为 exit 4，避免把不可运行 tag 当成可用构建环境。

## 剩余风险和证据链

- 可信 tar 仍需 operator 从可信机器导出，并确保 tar 内 tag 匹配 `ROS_HUMBLE_IMAGE=ros-rbs-humble:dev`。
- 需要用真实 tar 重新跑 `ROS_HUMBLE_IMAGE_TAR=... SKIP_DOCKER_BUILD=1 bash scripts/docker_humble_build.sh`，证明 docker load 后目标镜像可运行并能进入 colcon。
- O1 完成度不能提升；真实 HIL 仍需要 WAVE ROVER、串口、Orange Pi、`T=1001` 反馈和 archived evidence packet。
- O2/O3 不能借本轮 Docker 证据升级；它们仍依赖同一 `evidence_ref` 的实机任务记录和 fixed-route replay 复账。

## 下一步

1. 从可信机器导出可运行 `ros-rbs-humble:dev` tar，并在当前主机用本轮入口验证 `docker load` + local-image reuse。
2. 恢复 Docker/Humble colcon 围栏后，回到 O1 real HIL：接入真实串口设备，生成 `command.txt`、`serial.log`、`feedback_T1001.log` 和对应 ROS topic 样本。
3. 只有真实 HIL packet 可复账后，再更新 `OKR.md` 并推进 O3 same-`evidence_ref` route replay。

## 最终结论

本轮完成 sprint 内软件收口，结论为 `software_proof_docker_only`。没有可信 tar，所以未证明成功 docker load + colcon；没有真实硬件、串口、WAVE ROVER、`T=1001` 或 evidence packet；不更新 `OKR.md` 完成度。O1 仍约 75%，继续 blocked on real HIL。
