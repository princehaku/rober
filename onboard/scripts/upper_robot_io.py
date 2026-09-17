"""统一 API 的串口单写者；调度边界独立于 HTTP 请求的取消生命周期。"""

from __future__ import annotations

import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable


class SerialBusyError(RuntimeError):
    """普通动作不排队，避免停止后执行已经过时的运动指令。"""


class SerialCoordinator:
    """同一 API 实例只允许一个串口任务；外部 ROS 驱动仍须独占设备。"""

    def __init__(self) -> None:
        # 专用线程避免诊断子进程占满默认线程池后拖延自动停车。
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="base-serial")
        # 已完成 future 的 callback 可能在注册线程立即运行，重入锁避免自锁。
        self._lock = threading.RLock()
        self._active: threading.Event | None = None
        # Stop 的共享对象只代表一种底层停车操作，HTTP schema 在调用方分别构造。
        self._stop_future = None
        self._closed = False

    async def run(self, operation: Callable[[threading.Event], Any]) -> Any:
        # 先预约再提交，使尚未开始的旧动作同样能被 Stop 抢占。
        with self._lock:
            if self._closed or self._active is not None or self._stop_future is not None:
                raise SerialBusyError("serial_busy")
            interrupted = threading.Event()
            self._active = interrupted
            future = self._executor.submit(self._execute, operation, interrupted)
        wrapped = asyncio.wrap_future(future)
        # shield 保护线程结果，避免取消 HTTP task 时把待执行任务从 executor 撤走。
        try:
            # HTTP 取消只能请求抢占，不能取消后台 finally 中的停车。
            return await asyncio.shield(wrapped)
        except asyncio.CancelledError:
            interrupted.set()
            # 首次取消尽量等到停车完成；重复取消仍由线程 finally 保证实际收口。
            try:
                await asyncio.shield(wrapped)
            finally:
                raise

    def _execute(self, operation: Callable[[threading.Event], Any], interrupted: threading.Event) -> Any:
        try:
            return operation(interrupted)
        finally:
            # 完整动作收口后才释放预约，避免反馈与下一条运动交错。
            with self._lock:
                if self._active is interrupted:
                    self._active = None

    async def stop(self, operation: Callable[[], Any]) -> Any:
        with self._lock:
            if self._closed:
                raise SerialBusyError("serial_coordinator_closed")
            if self._active is not None:
                self._active.set()
            # 重复 Stop 共用同一写入结果；停止完成前拒绝所有普通动作。
            if self._stop_future is None:
                self._stop_future = self._executor.submit(operation)
                future = self._stop_future
                future.add_done_callback(self._stop_completed)
            else:
                future = self._stop_future
        # future 回调负责释放预约，因此等待者取消也不会遗留陈旧结果。
        wrapped = asyncio.wrap_future(future)
        try:
            return await asyncio.shield(wrapped)
        except asyncio.CancelledError:
            # 停止请求自身被取消时仍等待已提交写入，保持安全收口。
            try:
                await asyncio.shield(wrapped)
            finally:
                raise

    def _stop_completed(self, future: Any) -> None:
        # 释放预约依赖实际写入结束；多次 HTTP 取消也不会留下已完成的旧 Stop。
        with self._lock:
            if self._stop_future is future:
                self._stop_future = None

    async def close(self, stop_operation: Callable[[], Any]) -> None:
        # 只有存在未收口动作时才额外停车；空闲关闭不打开真实串口。
        with self._lock:
            active = self._active is not None or self._stop_future is not None
        # 关闭过程不通过取消线程来中止动作，必须先请求优先停车。
        if active:
            await self.stop(stop_operation)
        with self._lock:
            self._closed = True
        # 正常清理不阻塞事件循环，后台 finally 已在 stop 前完成。
        await asyncio.to_thread(self._executor.shutdown, wait=True)
