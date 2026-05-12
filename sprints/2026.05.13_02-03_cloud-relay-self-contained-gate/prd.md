# Sprint 2026.05.13_02-03 Cloud Relay Self-Contained Gate - PRD

## 用户价值

普通手机用户最终只应该面对一个云端入口，而不是依赖开发者知道 `onboard/src/...` 里的 ROS2 包路径。上一轮已经把仓库分成 `onboard/`、`cloud-relay/`、`mobile/`、`pc-tools/`，但云中转仍从 onboard behavior 源码复制模块，部署边界不够清楚。

本轮把云中转部署入口收敛到 `cloud-relay/`，让后续真实云、4G、生产 DB/queue、OSS/CDN 证据可以围绕这个目录继续推进。

## OKR 对齐

- 主线：Objective 5 云中转 + OSS/CDN 数据通路产品化。
- 直接支撑：
  - KR1：云中转服务端最小契约 `trashbot.remote.v1` 的独立部署入口更清晰。
  - KR2：4C 8G 公网服务端部署文档与目录入口一致。
  - KR5：凭证仍只通过环境变量注入，`.env.example` / compose 只保留占位。
  - KR6：Docker/local recovery gate 仍可在 cloud-relay 入口复跑。
- 边界：本轮只证明 `software_proof_docker_cloud_relay_self_contained_gate`，不提升到真实生产云或真实 4G。

## 需求

1. `cloud-relay/` 必须能表达自身的服务入口和部署入口，减少对仓库根旧路径的耦合。
2. Dockerfile、compose、smoke 脚本和产品文档必须使用当前四分层目录后的路径。
3. `remote_bridge` / 本地 `operator_gateway` 的 ROS2 fallback 语义不得被破坏；ACK 仍只能表示 command envelope accepted / processing / failed。
4. 验证必须围栏化：目标 unittest、`py_compile`、scoped diff check、一个 Docker/local smoke；不做 broad regression。

## 非目标

- 不抽离完整生产应用框架。
- 不实现公网 TLS、域名、防火墙、真实云账号、生产数据库、队列、对象存储、CDN 回源。
- 不承诺真实手机浏览器验收、WAVE ROVER、HIL 或真实送达。

## 责任分工

- `full-stack-software-engineer`：实现 cloud-relay 自包含入口、Docker/smoke/docs。
- `robot-software-engineer`：核对 onboard behavior / remote_bridge / bringup fallback 不被破坏，运行兼容性围栏。
- `product-okr-owner`：收口 `tech-done.md`、`side2side_check.md`、`final.md` 与 `OKR.md` 保守进度。
