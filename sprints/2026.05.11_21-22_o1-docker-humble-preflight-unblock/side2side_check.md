# Sprint 2026.05.11_21-22 O1 Docker Humble Preflight Unblock - Side2Side Check

## 状态

- 阶段：side2side_check
- 时间：2026-05-11 21:14 Asia/Shanghai
- 结论：对照通过，状态为 `Blocked with precise diagnosis`。

## 对照结果

| 验收项 | 结果 | 证据 |
| --- | --- | --- |
| Docker preflight 诊断可定位 | 通过 | `scripts/docker_humble_build.sh` 输出 daemon/context/builder/base image/mirror/proxy，并在失败时输出分类。 |
| `SKIP_COLCON=1 bash scripts/docker_humble_build.sh` | 失败但可归因 | `category=registry mirror/proxy`；关键错误为 `encountered unknown type text/html; children may not be fetched`。 |
| HIL 边界不虚增 | 通过 | `--status` 输出 `source=software_proof`、`hil_ready=false`、`blocked_reason=no_serial_candidates_found`。 |
| runbook/checklist 更新 | 通过 | Docker-only host 与无 `/dev/ttyUSB*` 明确只能产生 readiness/blocked evidence。 |
| 文件范围 | 通过 | 未触碰 `.codex/config.toml`，未修改 vendor/factory firmware，未改 O2/O3 代码。 |

## 用户验收口径

- 本轮不是 `hil_pass`；没有真实硬件和串口，不能声明 WAVE ROVER 已上车通过。
- 本轮把上一轮 Docker 阻断从“metadata/unpack 失败”推进到可操作归因：Docker Desktop daemon 和 `desktop-linux` builder 可用，当前 registry mirror/proxy 对 Docker Hub base image metadata/layer 返回 HTML。
- 下一步由 operator 在 Docker Desktop/Engine 侧处理 registry mirrors/proxy/network/cache，然后重跑同一 preflight。

## 未完成项

- `ros-rbs-humble:dev` 镜像尚未在本机重建成功。
- 真实 HIL run 仍等待真实串口设备和 WAVE ROVER。
