# Sprint 2026.05.12_01-02 Mac Docker Humble Env - Tech Plan

## 状态

- 阶段：tech-plan
- 时间：2026-05-12 01:02 Asia/Shanghai
- Product Owner：Product Manager / OKR Owner
- Engineering Owner：`robot-software-engineer`
- 计划类型：产品口径 + 工程并行执行边界

## 技术目标

把本地开发和 Docker/Humble 验证入口切到 macOS + Docker Desktop/Engine。Product 负责文档和验收口径，Engineer 负责 Compose、脚本和 README 的实际工程修正。

## 文件范围

Product 允许改动：

- `AGENTS.md`
- `sprints/2026.05.12_01-02_mac-docker-humble-env/pre_start.md`
- `sprints/2026.05.12_01-02_mac-docker-humble-env/prd.md`
- `sprints/2026.05.12_01-02_mac-docker-humble-env/tech-plan.md`
- `sprints/2026.05.12_01-02_mac-docker-humble-env/side2side_check.md`
- `sprints/2026.05.12_01-02_mac-docker-humble-env/final.md`

Product 禁止改动：

- `docker-compose.humble.yml`
- `scripts/*`
- `README.md`
- ROS2 产品代码、测试代码、硬件配置、vendor 文件、`OKR.md`

## 责任拆分

- Product Manager / OKR Owner：更新 Mac-first 本地环境记忆，定义验收口径和风险边界，收口 sprint。
- `robot-software-engineer`：并行处理 Docker Compose、脚本、README，验证 Mac 本机 Docker/Humble 入口。

## 接口影响

- 不变更 ROS2 topic/action/service。
- 不变更硬件协议、串口参数、launch 参数或 vendor 事实。
- 不变更 `OKR.md` 完成度。

## 验收命令

Product 围栏：

```bash
git diff --check -- AGENTS.md sprints/2026.05.12_01-02_mac-docker-humble-env/pre_start.md sprints/2026.05.12_01-02_mac-docker-humble-env/prd.md sprints/2026.05.12_01-02_mac-docker-humble-env/tech-plan.md sprints/2026.05.12_01-02_mac-docker-humble-env/side2side_check.md sprints/2026.05.12_01-02_mac-docker-humble-env/final.md
```

工程侧预期由 `robot-software-engineer` 在自己的范围内运行并记录：

```bash
docker compose -f docker-compose.humble.yml config
docker compose -f docker-compose.humble.yml up
```

工程验收关键不是 Product 代跑，而是确认输出不再出现 `/run/desktop/mnt/host/wsl/docker-desktop-bind-mounts/Ubuntu-24.04/...`。

## 风险边界

- 如果工程侧 Docker daemon、registry mirror/proxy 或本地镜像仍异常，应记录为 Docker 环境 blocked，不得写成 HIL blocked。
- 如果仍出现 WSL bind mount 路径，本轮 Mac-first 环境切换未完成。
- 如果只通过 `git diff --check`，只能证明 Product 文档无 whitespace error，不能证明 Docker/Humble 或 colcon 成功。

## 收口标准

- `AGENTS.md` 已改为 Mac-first 本地环境记忆。
- 本 sprint 文档链路写清目标、OKR 映射、范围、不做事项、责任 owner、验收命令和风险。
- Product scoped `git diff --check` 通过。
- `final.md` 明确不更新 OKR 完成度、不声明 HIL。
