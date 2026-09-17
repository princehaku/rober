# CPU 差分采样修复证据

- owner: robot-software-engineer / camera_cpu_sampling
- 验证时间：2026-09-18，Asia/Shanghai。
- 证据边界：Windows 本地 Python 离线 fake psutil / 单元测试；无摄像头、串口、远端部署或控车。

## 实际改动

- `onboard/scripts/local_webrtc_camera_smoke.py`：新增服务级 `CpuPercentSampler`，复用进程 `Process`；首次、故障恢复、依赖恢复及 PID 变化均重新预热。系统 CPU 使用线程独立窗口；采样锁非阻塞获取，竞争请求返回 `sampling_in_progress`。
- `onboard/scripts/test_local_webrtc_camera_smoke.py`：增加可导入的 `FakeCpuPsutil` 和 7 项 CPU 回归。原有缺 psutil 健康回归保持通过。
- `docs/interfaces/o7_local_webrtc_camera_smoke.md`：同步字段、预热/争用语义、线程差异及验证范围。
- 本证据文件归入现有 Epic，由上级 owner 集成到 `tech-done.md`。

保留已有 `available/value` 有效读数结构；预热读数为 `available=false, reason=warming_up` 并省略 `value`。新增 `sample_window_ms`、`sampled_monotonic_s`；进程 CPU 不截断至 100%。异常保持 `psutil_runtime_error`，缺依赖保持 `psutil_not_installed`，健康接口 fail-open。

依据：[psutil Process.cpu_percent](https://psutil.readthedocs.io/stable/#psutil.Process.cpu_percent)、[psutil.cpu_percent](https://psutil.readthedocs.io/stable/#psutil.cpu_percent)。前者在同一对象上维护差分基线；后者按线程维护基线。调用均使用 `interval=None`。

## 验证结果

命令：

```text
python -m unittest onboard.scripts.test_local_webrtc_camera_smoke
..............
----------------------------------------------------------------------
Ran 14 tests in 0.312s

OK
```

新增 7 项覆盖：连续采样复用和窗口、零长度窗口、进程/系统异常恢复、缺依赖与 PID 切换、线程独立系统预热、锁争用立即返回、实际 collector 复用服务实例。争用测试用事件依赖证明竞争请求在持锁请求释放之前完成，不以机器速度作为判定阈值。

使用 fake 单调时间 `1.0s -> 1.25s -> 1.75s` 的结构性探针结果：

```json
{
  "process_creations": 1,
  "process_sample_calls": 3,
  "system_sample_calls": 3,
  "warmup_count": 1,
  "valid_samples": 2,
  "valid_window_ms": [250.0, 500.0],
  "valid_process_values": [125.0, 125.0]
}
```

复用方式：从 `onboard.scripts.local_webrtc_camera_smoke` 导入 `CpuPercentSampler`，从 `onboard.scripts.test_local_webrtc_camera_smoke` 导入 `FakeCpuPsutil`，创建 sampler/fake 后调用 `sampler.sample(fake)`。fake 暴露 `process_creations`、`process_sample_calls`、`system_sample_calls`、`intervals`；可按返回字段统计预热和有效样本。每次成功 sample 读取两次 `time.monotonic()`，顺序为进程、系统，探针注入时钟应配对提供时间值。

`git diff --check` 对三个被修改文件通过。新增非空代码行中的中文注释及 docstring 占比：实现 `16/72 = 22.2%`，测试 `34/165 = 20.6%`（未计行末注释）。

## 失败定位与剩余风险

- 本轮验收无失败，未改编码、摄像头参数、硬件或控制安全字段，未提交或切换分支。
- 本结果证明采样正确性与结构性对象复用，未测量真实视频 CPU 降幅、板端内核查询耗时、HIL 或端到端控车时延。
- 无正数 interval 等待、无锁等待；psutil 的瞬时内核查询本身仍有运行时间，异常会 fail-open。
- 推荐采样间隔至少 100 ms。极短但为正的窗口保留真实数值与窗口长度，消费方需结合计时精度解读。
- aiohttp 的同线程连续采样可形成两类有效窗口；降级 `ThreadingHTTPServer` 每个新请求线程的系统 CPU 读数需单独预热，进程指标可复用共享基线。
- 本探针只计 CPU 路径；内存诊断仍独立创建 `Process`，此次范围未修改内存采样。
- 无新增 KR 或 Objective 完成度调整；上级 Robot owner 负责性能探针和整体集成验收。
