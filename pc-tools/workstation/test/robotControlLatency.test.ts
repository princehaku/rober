import { describe, expect, it } from "vitest";
import {
  buildPcLatencyTiming,
  normalizeRobotControlLatencyTrace,
  ROBOT_CONTROL_LATENCY_TRACE_SCHEMA,
} from "../src/server/robotControlLatency";

describe("robot control latency contract", () => {
  it("只保留白名单 trace 字段并兼容缺失 envelope", () => {
    // 未带 trace 的旧点动请求必须继续工作。
    expect(normalizeRobotControlLatencyTrace(undefined)).toBeNull();
    // 未知字段必须被丢弃，防止代理反射任意 body。
    const trace = normalizeRobotControlLatencyTrace({
      // 固定 schema 防止测试误接受未来未知版本。
      schema: ROBOT_CONTROL_LATENCY_TRACE_SCHEMA,
      // 短 token 覆盖正常 UUID/owner 风格字符。
      latency_trace_id: "trace-001",
      // browser 两个时间字段保持有限且非负。
      client_keydown_perf_ms: 12.5,
      client_time_origin_ms: 1_784_570_000_000,
      // hold identity 必须和已有 watchdog metadata 一起贯穿。
      hold_session_id: "keyboard-owner-1",
      hold_sequence: 7,
      // warm 样本不和首次 cold path 合并统计。
      sample_kind: "warm",
      // 这两个未知字段模拟敏感/任意数据注入。
      token: "must-not-reflect",
      base_url: "http://secret.invalid",
    });
    expect(trace).toEqual({
      schema: ROBOT_CONTROL_LATENCY_TRACE_SCHEMA,
      latency_trace_id: "trace-001",
      client_keydown_perf_ms: 12.5,
      client_time_origin_ms: 1_784_570_000_000,
      hold_session_id: "keyboard-owner-1",
      hold_sequence: 7,
      sample_kind: "warm",
    });
  });

  it("拒绝超长、恶意字符与非有限时间值", () => {
    // 这些输入不能进入 upper，更不能把控制字符或 Infinity 回显给浏览器。
    const base = {
      schema: ROBOT_CONTROL_LATENCY_TRACE_SCHEMA,
      latency_trace_id: "trace-001",
      client_keydown_perf_ms: 12.5,
      client_time_origin_ms: 1_784_570_000_000,
      hold_session_id: "keyboard-owner-1",
      hold_sequence: 7,
      sample_kind: "warm",
    } as const;
    expect(() => normalizeRobotControlLatencyTrace({ ...base, latency_trace_id: "x".repeat(97) })).toThrow("latency_trace_invalid_fields");
    expect(() => normalizeRobotControlLatencyTrace({ ...base, hold_session_id: "bad\nvalue" })).toThrow("latency_trace_invalid_fields");
    expect(() => normalizeRobotControlLatencyTrace({ ...base, client_keydown_perf_ms: Number.POSITIVE_INFINITY })).toThrow("latency_trace_invalid_fields");
  });

  it("用 fake monotonic clock 只计算 Node 本进程 span", () => {
    // 100 个 warm 样本共用确定性 clock 增量，证明统计输入不会依赖真实网络或机器人。
    const samples = Array.from({ length: 120 }, (_unused, index) => {
      // 每个样本使用独立起点，证明实现计算差值而不是依赖绝对值。
      const receive = 1_000_000_000n + BigInt(index) * 10_000_000n;
      return buildPcLatencyTiming({
        // validation 固定 0.2ms，代表同步白名单和数值 clamp。
        receive,
        validationDone: receive + 200_000n,
        // forward 紧跟 validation，不插入 summary/readback。
        forwardStart: receive + 300_000n,
        // headers 模拟固定 loopback upstream 响应窗口。
        upstreamHeaders: receive + 4_300_000n,
        // done 再增加 0.4ms JSON 读取窗口。
        responseDone: receive + 4_700_000n,
      });
    });
    // 样本数满足 Epic 对 warm software sample 的最低要求。
    expect(samples).toHaveLength(120);
    expect(samples[0]!.pc_receive_to_validation_ms).toBe(0.2);
    expect(samples[0]!.pc_forward_to_headers_ms).toBe(4);
    expect(samples[119]!.pc_proxy_total_ms).toBe(4.7);
    expect(samples.every((sample) => sample.clock_id === "node_process_hrtime")).toBe(true);
  });
});
