# Sprint 2026.05.12_00-02 O1 Docker Image Tar Reuse - Tech Plan

## 状态

- 阶段：tech-plan
- 时间：2026-05-12 00:02 Asia/Shanghai
- Product Owner：Product Manager / OKR Owner
- Engineering Owner：`robot-software-engineer`
- 证据范围：`software_proof_docker_only`

## 目标

在 `scripts/docker_humble_build.sh` 中增加可信 Docker image tar 的显式导入入口，让 Docker-only 主机在 registry mirror/proxy broken 时可以执行：

```bash
ROS_HUMBLE_IMAGE_TAR=/path/to/ros-rbs-humble-dev.tar SKIP_DOCKER_BUILD=1 bash scripts/docker_humble_build.sh
```

脚本应先导入 tar，再沿用现有 `SKIP_DOCKER_BUILD=1` 的本地目标镜像可运行校验。通过条件仍是目标镜像可以启动并找到 `/opt/ros/humble/setup.bash`，不是 tag 存在。

## 证据依据

- 上一轮 `sprints/2026.05.12_00-01_o1-docker-humble-base-image-fallback/final.md` 已证明 Docker daemon 和 `desktop-linux` builder 可用，但默认 build blocked 于 registry mirror/proxy 返回 `text/html`。
- 同一 final 已证明本地 `ros-rbs-humble:dev` tag 存在但不可运行，`docker run` 返回 `descriptor is neither a manifest or index`。
- `sprints/2026.05.11_23-24_hil-packet-crosscheck-bridge/final.md` 已建立 HIL packet gate 与 crosscheck 的证据边界；本轮必须继续区分 `software_proof`、`blocked`、`hil_pass`。

## 文件范围

后续实现允许改动：

- `scripts/docker_humble_build.sh`
- `sprints/2026.05.12_00-02_o1-docker-image-tar-reuse/tech-done.md`

后续验收或收口阶段允许按 sprint 链路改动：

- `sprints/2026.05.12_00-02_o1-docker-image-tar-reuse/side2side_check.md`
- `sprints/2026.05.12_00-02_o1-docker-image-tar-reuse/final.md`

禁止改动：

- ROS2 产品代码
- 测试代码
- 硬件配置
- launch 参数
- vendor 文件
- `OKR.md`
- 其他 sprint 目录

## 接口影响

- 新增环境变量：`ROS_HUMBLE_IMAGE_TAR`
- 默认行为不变：未设置 `ROS_HUMBLE_IMAGE_TAR` 时，脚本按现有 build 或 skip-build 路径执行。
- `ROS_HUMBLE_IMAGE` 仍是目标镜像名；导入 tar 后仍必须校验该目标镜像，而不是盲目信任 `docker load` 输出。
- `SKIP_DOCKER_BUILD=1` 语义不变：不执行 Docker build，只复用本地目标镜像；若设置 tar，则先补一次 `docker load`。

## 实现建议

1. 在变量区新增：

```bash
image_tar="${ROS_HUMBLE_IMAGE_TAR:-}"
image_tar_state="unset"
```

2. 若 `ROS_HUMBLE_IMAGE_TAR` 被设置但为空，快速失败：

```bash
if [ -n "${ROS_HUMBLE_IMAGE_TAR+x}" ] && [ -z "$ROS_HUMBLE_IMAGE_TAR" ]; then
    echo "ERROR: ROS_HUMBLE_IMAGE_TAR is set but empty. Provide a Docker image tar path, or unset it." >&2
    echo "evidence_scope=software_proof_docker_only" >&2
    exit 2
fi
```

3. 若路径非空但不是普通文件，快速失败：

```bash
if [ -n "$image_tar" ] && [ ! -f "$image_tar" ]; then
    echo "ERROR: ROS_HUMBLE_IMAGE_TAR does not point to an existing file: $image_tar" >&2
    echo "evidence_scope=software_proof_docker_only" >&2
    exit 2
fi
```

4. 在 preflight 输出中增加：

```bash
echo "image_tar_state=$image_tar_state"
```

建议状态值：

- `unset`
- `provided`
- `empty_error`
- `missing_error`

5. 在 `SKIP_DOCKER_BUILD=1` 分支校验目标镜像之前执行导入：

```bash
if [ -n "$image_tar" ]; then
    echo "ROS_HUMBLE_IMAGE_TAR: loading Docker image tar before local image reuse: $image_tar"
    docker load -i "$image_tar"
fi
```

6. 保留现有 `target_image_present` 和 `validate_target_image_for_reuse`。即使 `docker load` 成功，只要 `$image` 不存在或不可运行，仍应走现有 missing/unusable help 并非 0 退出。

7. 错误提示应建议 operator 检查：

- tar 是否来自可信机器导出的可运行 `ros-rbs-humble:dev`
- tar 内 tag 是否匹配 `ROS_HUMBLE_IMAGE`
- Docker daemon 是否可用
- 是否需要取消 `SKIP_DOCKER_BUILD` 并修复 registry mirror/proxy 后重建

## 验收命令

后续 `robot-software-engineer` 必须运行：

```bash
bash -n scripts/docker_humble_build.sh
```

预期：exit 0。

```bash
ROS_HUMBLE_IMAGE_TAR= SKIP_DOCKER_BUILD=1 bash scripts/docker_humble_build.sh
```

预期：快速失败，非 0 退出；提示 `ROS_HUMBLE_IMAGE_TAR` 为空或无效；不得进入 Docker build。

```bash
ROS_HUMBLE_IMAGE_TAR=/tmp/does-not-exist.tar SKIP_DOCKER_BUILD=1 bash scripts/docker_humble_build.sh
```

预期：快速失败，非 0 退出；提示文件不存在；不得进入 Docker build。

```bash
SKIP_DOCKER_BUILD=1 bash scripts/docker_humble_build.sh
```

预期：仍校验本地目标镜像是否可运行。若本机仍是上一轮不可运行 tag，应快速失败并提示替换本地镜像；这属于预期 blocked evidence。

```bash
git diff --check -- scripts/docker_humble_build.sh sprints/2026.05.12_00-02_o1-docker-image-tar-reuse/tech-done.md
```

预期：无输出，exit 0。后续若已创建 `side2side_check.md` 或 `final.md`，把它们加入 scoped diff check；不要跑广泛测试。

## 风险边界

- 本轮不要求有真实 tar；没有 tar 时可通过空值、缺失路径和既有 skip-build 复用校验形成围栏证据。
- Docker daemon 不可用时，仍按既有 preflight 暴露环境问题；不要把 Docker daemon 故障写成脚本逻辑失败。
- `docker load` 成功不等于镜像可运行；必须保留容器探针。
- 本轮不触碰 WAVE ROVER、ESP32、Orange Pi、UART、波特率、JSON 指令、速度映射、反馈协议、引脚、电压、固件或机械尺寸，因此不需要 vendor 文件变更，也不能声称硬件验证。
- 本轮最多产生 `software_proof_docker_only`，不能升级 `OKR.md` 完成度。

## 子 Agent 执行 Prompt

后续进入实现阶段时，主节点应派发 1 个 `spawn_agent(agent_type=worker)`，角色为 `robot-software-engineer`，并包含 `.codex/agents/robot-software-engineer.toml` 的完整 prompt。

执行任务摘要：

- 在 `scripts/docker_humble_build.sh` 增加 `ROS_HUMBLE_IMAGE_TAR` 支持。
- 只允许改动 `scripts/docker_humble_build.sh` 和本 sprint 的执行留档文件。
- 按本文件验收命令运行最小围栏验证。
- 实际改动完成后创建 `tech-done.md`，记录改动、验证结果、失败定位和剩余风险。

输出要求：

1. 实际改动的文件列表
2. 验证命令输出结果或关键日志片段
3. 失败定位
4. 剩余风险
5. 是否仍为 `software_proof_docker_only`
