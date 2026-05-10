# Sprint 2026.05.10 19-20 Hardware Proof Diagnostics - Side2Side Check

## 状态

- 阶段：side2side_check completed。
- 时间：2026-05-10 19:58 Asia/Shanghai。
- Product Owner：`product-okr-owner`。
- 实现 owner：`full-stack-software-engineer`。
- 验收结论：通过软件侧产品验收；真实 WAVE ROVER HIL 未发生，不能声明硬件通过。

## 用户价值和产品北极星

本轮把硬件 proof 从工程师手动阅读 artifact，推进到手机/operator diagnostics 可以消费的诊断状态。普通用户和售后同学不需要理解 UART、JSON、轮速映射或 ROS2 日志，就能看到当前是 software proof、需要 HIL、invalid config，还是 read error。

这符合北极星：低成本自主垃圾投递机器人必须让普通手机用户完成核心操作和失败诊断；但硬件可信度必须保守表达，不能把软件证据包装成实车证据。

## OKR 映射

- Objective 5：远程/手机诊断最小数据包明显推进。`/api/diagnostics` 总是包含 `hardware_proof`，operator 页面新增 Hardware proof 诊断卡，能向手机/售后展示底盘软件 proof 状态和下一步动作。
- Objective 1：硬件协议可信底盘小幅推进。上一轮 software proof 现在已被产品化消费，但真实 WAVE ROVER HIL、真实 UART、真实轮向、IMU、电池和反馈频率证据仍缺，不能大幅上调。
- Objective 2/3/4：本轮无直接交付，只通过 full smoke 证明现有行为、导航、视觉软件测试未回归。

## KR 拆解或更新

- O5 KR4：新增 `hardware_proof` 远程诊断字段，覆盖 status、artifact ref、source status、read error、summary、next step、vendor sources、risk flags 和 HIL recipe。
- O5 KR5：operator 页面新增硬件 proof 卡片，普通用户看到的是保守状态和下一步，而不是命令行和底层协议。
- O1 KR4：硬件 proof 的软件证据通过 behavior/http/static tests 和 full smoke 被保护，但这仍是 software proof 消费链，不是 HIL pass。

## 本轮核心抓手

核心抓手是“把硬件 proof 产品化为可读诊断”，不是新增硬件能力。验收重点放在四类保守状态：

- `software_proof`：软件 proof 可读，但仍不等于实车通过。
- `needs_hil`：明确需要真实 WAVE ROVER HIL。
- `invalid_config`：配置问题可被页面和 API 表达。
- `read_error`：未配置、缺失、坏 JSON、schema 不符合预期时，API 仍稳定返回结构化诊断。

## 做什么 / 不做什么

已做：

- `/api/diagnostics` 总是包含 `hardware_proof`。
- operator 页面新增 Hardware proof 诊断卡。
- 接口文档和 `tech-done.md` 已记录字段 contract、验证输出和剩余风险。
- targeted diagnostics/http/static tests、py_compile、full smoke、git diff check 均通过。

未做：

- 没有真实 WAVE ROVER HIL。
- 没有真实 UART、IMU、电池、轮向、速度单位或反馈频率证据。
- 没有修改硬件配置、launch 默认值、vendor 文件或产品代码以外的硬件事实。
- 没有给 `operator_gateway.py` 新增 `hardware_proof_ref` ROS 参数入口。

## 优先级和验收口径

| 验收项 | 结果 | 证据 |
| --- | --- | --- |
| `/api/diagnostics` 包含 `hardware_proof` | 通过 | `tech-done.md` 记录 HTTP tests 16 tests OK |
| 页面有独立 Hardware proof 卡片 | 通过 | `tech-done.md` 记录 static tests 8 tests OK |
| 四类状态保守表达 | 通过 | diagnostics tests 覆盖 `needs_hil`、`software_proof`、`invalid_config`、`read_error` |
| 读取失败不打崩 diagnostics | 通过 | diagnostics tests 覆盖 missing/corrupt/non-dict/missing status |
| 不宣称 hardware/HIL passed | 通过 | 首轮发现并修复禁用文案，static tests 重跑通过 |
| 完整 smoke 护栏 | 通过 | interfaces 6、hardware 24、nav 39、bringup 9、behavior 118、vision 13 tests OK |
| 真实硬件验收 | 未覆盖 | 本轮明确不接 UART/WAVE ROVER，不采集真实 IMU/电池/轮向证据 |

## 对应责任 Engineer

- 已完成实现和验证：`full-stack-software-engineer`。
- 下一轮建议主责：
  - `robot-software-engineer`：为 `operator_gateway.py` 接入 `hardware_proof_ref` ROS 参数或配置入口，并做 bringup 集成验证。
  - `full-stack-software-engineer`：补 operator 页面/网关参数接线后的 HTTP 回归。
  - `hardware-engineer`：后续真实 WAVE ROVER HIL、UART、轮向、IMU、电池、反馈频率证据采集。

## 风险、阻塞和需要补齐的证据链

- `operator_gateway.py` 还没有 `hardware_proof_ref` ROS 参数入口；未配置时会显示 `read_error`。下一轮应由 Robot/Full-Stack 补参数接线。
- 本轮没有真实 HIL；O1 仍缺真实 WAVE ROVER、真实 UART、轮向、速度单位、反馈频率、IMU、电池证据。
- 当前页面能展示 hardware proof 状态，但用户实际手机浏览器截图和上车售后流程仍缺。
- software proof 被产品化消费只能证明证据链可见，不能证明底盘硬件已经可靠。

## 需要创建或更新的 sprint 文档

- 已更新：`side2side_check.md`。
- 待本轮收口同步：`final.md`、`OKR.md`。
