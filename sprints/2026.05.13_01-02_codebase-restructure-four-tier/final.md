# Sprint 2026.05.13_01-02 Codebase Restructure Four-Tier — final

## sprint_type

`epic`

## 结论

本轮完成 **monorepo 四分层目录落地**（`onboard/`、`cloud-relay/`、`mobile/`、`pc-tools/`）及配套文档、`.codex` 路径、部分测试/脚本的路径适配；**未实施 tech-plan 中的 P5**（operator_gateway 与 relay 源码迁入 cloud-relay 并集成）。

## 验证与 CEO 指令

按 CEO 指示：**本轮跳过全部测试与构建验证**，未收集 `run_smoke_tests` / `colcon` / `docker compose` 日志。收口依据为代码与文档变更清单（见 `tech-done.md`）。

## OKR

本轮为 **结构治理**，**不调整**任何 Objective 完成度数字与 KR 文字。

## OKR 最低优先级核对（回顾）

本 sprint 不推进最低 Objective 的理由仍成立：本轮仅为目录与路径治理；功能与证据链未增加。下轮若启动 P5 或补跑验证，再在对应 sprint `final.md` 回顾。

## 遗留与下一 sprint 建议

1. **必做**：在可用环境补跑 `bash onboard/scripts/run_smoke_tests.sh` 与 Docker Humble build，修复暴露问题。
2. **可选 epic**：执行 tech-plan **P5**（cloud-relay 自包含源码 + 缩小 build context + bringup 调整）。
3. **可选**：P4 将 `route_debug_web` / `route_csv_to_yaml` 抽到 `pc-tools/route/` 并更新 `setup.py` entry_points。

## side2side_check

本轮按流程可写 `side2side_check.md` 为 **N/A（用户明确跳过验证）**；若需 CEO 书面签字跳过，可补一句引用本 `final.md` 本节。
