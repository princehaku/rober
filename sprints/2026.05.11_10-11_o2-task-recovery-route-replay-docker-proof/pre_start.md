# Sprint Pre-start: O2 Task Recovery Route Replay Docker Proof

时间：2026-05-11 20:18 Asia/Shanghai

## 背景

上一个 `10-11_hil-docker-preflight-to-real-run` 切片仍 blocked 在 O1 Docker/HIL 环境：`osrf/ros:humble-desktop` 拉取/解包异常，且本机没有真实串口设备。因此本轮不继续扩大硬件范围，只补齐 O2/O3 软件证据链，让 fixed-route status、task record、operator diagnostics 和 crosscheck 在同一个 `evidence_ref` 下可复账。

## Owner

- Robot Platform Engineer：主责行为层、operator gateway、diagnostics、crosscheck 和 sprint docs。

## 范围

- 允许改动：`OKR.md`、behavior 相关模块/测试、`scripts/evidence_crosscheck.py`、本 sprint 目录。
- 禁止改动：`.codex/config.toml`、硬件 docs/scripts、`sprints/2026.05.11_10-11_hil-docker-preflight-to-real-run/*`。

## 验收口径

- `task_orchestrator` 从 fixed-route `route_progress` 透传/提升 evidence 字段。
- `task_record` 顶层持久化 `route_progress`，未显式传入时从最新 nav evidence 抽取。
- operator gateway 和 diagnostics 透传 `route_progress`，空 `{}` 不阻断 nav fallback。
- `scripts/evidence_crosscheck.py --task-record-dir` 能自动找同 `evidence_ref` 的 task record；找不到或缺 route-progress evidence 时返回非 0。
- 只做 software proof，不声明 `hil_pass`。

## 风险

- 本轮不触碰真实硬件，O1 仍保持 blocked。
- 复账样例是本地软件 JSON/JSONL proof，不等于真实 Nav2/fixed-route 上车运行。
