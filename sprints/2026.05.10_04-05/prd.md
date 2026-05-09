# Sprint 2026.05.10 04-05 PRD

## 需求

让远程诊断包从“只给视觉样本 manifest 路径”升级为“能说明 manifest 是否存在、样本数量、最近样本、检测数量和上下文”的最小支持包。

## OKR 对齐

- Objective 4：视觉样本 manifest 进入可复盘数据链路。
- Objective 5：手机/远程支持诊断包能直接判断是否有视觉证据。

## 验收

- `/api/diagnostics` payload 增加视觉样本摘要。
- manifest 缺失或损坏时不影响诊断包返回。
- 目标测试和 smoke 测试通过。
