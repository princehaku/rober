# Sprint 2026.05.10 13-14 OKR Function - PRD

## 状态

- 阶段：PRD 已完成，进入 tech-plan。
- 产品目标：推进 Objective 4，从“样本能落盘”推进到“样本 manifest 能被检查、汇总、复盘”。

## 背景

Objective 4 当前进度最低，约 63%。最近几轮已经让 route/camera 样本具备 manifest 和上下文，但缺少真实采集后的离线检查与汇总能力。没有这个能力，后续 diagnostics、人工标注、路线质量复盘只能靠人工翻目录，无法稳定判断样本链是否完整。

## 用户价值

面向最终手机用户，直接价值是售后和远程支持能更快判断“机器人这次送达失败是否有视觉/路线证据”。面向工程团队，直接价值是每次 route/camera 采集后能快速发现缺图、缺 JSON、缺 route/checkpoint 上下文、异常样本未记录等问题。

## OKR 映射与 KR 拆解

主 OKR：Objective 4，把摄像头从“捡垃圾检测”收敛为送达任务的可选感知能力。

KR 拆解：

- KR4.3-a：给 vision sample manifest 增加可运行的离线检查入口，验证 manifest 文件存在、可解析、样本字段满足最低 contract。
- KR4.3-b：输出 diagnostics/人工复盘可消费的 summary JSON 或等价结构化结果。
- KR4.3-c：对缺文件、缺字段、空样本、异常/负样本等情况给出稳定 warning/error，不静默成功。
- KR4.4-a：summary 只依赖 manifest contract，不耦合具体视觉算法或 detector 类型。

本轮不更新 `OKR.md`；实现完成并有验证证据后，由后续收口 worker 或 coordinator 更新 OKR 进度。

## 本轮核心抓手

Autonomy Algorithm Engineer 单线闭环完成 manifest 离线验证/汇总功能。建议优先在 `ros2_trashbot_vision` 或现有样本/manifest 相关模块内实现，不新增跨包依赖。

## 范围

### 必须做

- 读取现有 manifest contract 和样本写入逻辑。
- 增加一个可从命令行或纯函数调用的 manifest 检查/汇总能力。
- 产出结构化 summary，至少包含：
  - manifest path
  - sample count
  - raw image / annotated image / detection JSON 完整性统计
  - route id / task id / checkpoint / event / anomaly 上下文覆盖统计
  - negative/empty detection sample 统计
  - errors 和 warnings
- 增加 focused tests，测试只作为护栏。
- 更新本 sprint 的 `tech-done.md`，记录实际改动、验证结果和剩余风险。

### 不做

- 不训练或接入 YOLO/RT-DETR/OpenCV 新模型。
- 不默认启动散落垃圾 detector。
- 不修改硬件、底盘、串口、WAVE ROVER、Orange Pi、ESP32 相关配置。
- 不实现手机 UI 或 `/api/diagnostics` 接口接入。
- 不声称真实数据集已经完成，除非本轮确实提供实采 manifest 和验证日志。

## 优先级

P0：

- 离线 manifest parse/check/summary 能运行。
- 错误和 warning 可读，失败时非零退出或测试可判定。
- 单元测试覆盖正常与坏 manifest。

P1：

- summary 字段稳定，便于后续 diagnostics 引用。
- 样本上下文覆盖统计能帮助人工复盘 route/checkpoint 质量。

P2：

- 更漂亮的命令行输出、表格化展示、文档扩展；不影响本轮验收。

## 验收口径

本轮完成必须同时满足：

- Autonomy Engineer 返回实际改动文件列表。
- 离线入口能在无 ROS2 daemon、无硬件、无真实相机环境运行。
- 至少一个测试验证 valid manifest summary。
- 至少一个测试验证缺文件或缺字段会进入 error/warning，不静默通过。
- smoke 或目标测试通过；如果 Docker/Humble 或全量 smoke 无法跑，必须说明原因和影响。
- `sprints/2026.05.10_13-14_okr-function/tech-done.md` 记录验证证据和剩余风险。

## 责任 Engineer

- 主责：Autonomy Algorithm Engineer。
- 协作：Robot Platform Engineer 和 Full-Stack Engineer 本轮只作为后续消费者，不阻塞本轮。

## 风险和证据链

- 证据链最小要求：代码 diff、目标测试日志、summary 示例、tech-done 记录。
- 最大风险：只做了测试 fixture 汇总，没有真实 manifest 样本；可接受但必须在 final/OKR 中标为剩余风险。
- 产品风险：如果 summary 结构过度贴合当前 detector 输出，会阻碍未来算法替换；因此本轮验收强调 manifest contract，而不是 detector 内部字段。

