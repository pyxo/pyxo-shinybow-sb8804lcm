"""Serialized V2 transport. Receiving is deliberately separate from routing state."""
import asyncio
import re

import serial


def encode_command(command: str) -> bytes:
    """Accept exactly one ASCII command; normalize its terminator."""
    command = command.strip()
    if not re.fullmatch(r"[A-Za-z0-9 ?]+;?", command):
        raise ValueError("Enter one ASCII command without embedded terminators")
    return (command.rstrip(";") + ";\r\n").encode("ascii")


def route_command(output: int | None, source: int) -> str:
    if type(source) is not int or not 0 <= source <= 8:
        raise ValueError("Input must be 0 (off) through 8")
    if output is not None and (type(output) is not int or not 1 <= output <= 8):
        raise ValueError("Output must be 1 through 8")
    return f"OUTPUT{'ALL' if output is None else f'{output:03d}'} {source:03d};"


class SerialClient:
    """Keep the port open, link once per connection, and serialize operations."""

    def __init__(self, path: str):
        self.path = path
        self._port = None
        self._lock = asyncio.Lock()

    async def _run(self, func, *args):
        # A cancelled caller must not release the lock while serial I/O still runs.
        task = asyncio.create_task(asyncio.to_thread(func, *args))
        try:
            return await asyncio.shield(task)
        except asyncio.CancelledError:
            await task
            raise

    def _open(self):
        if self._port is None:
            self._port = serial.Serial(
                self.path, baudrate=9600, bytesize=8, parity="N", stopbits=1,
                timeout=0, write_timeout=2, xonxoff=False, rtscts=False,
                dsrdtr=False, exclusive=True,
            )

    def _write(self, payload):
        if self._port.write(payload) != len(payload):
            raise serial.SerialTimeoutException("Incomplete serial write")

    def _close(self):
        if self._port is not None:
            port, self._port = self._port, None
            port.close()

    async def _connect(self):
        if self._port is None:
            await self._run(self._open)
            await self._run(self._write, b"LINK 001;\r\n")
            await asyncio.sleep(1)

    async def connect(self):
        async with self._lock:
            try:
                await self._connect()
            except BaseException:
                await self._run(self._close)
                raise

    async def send_command(self, command: str):
        payload = encode_command(command)
        async with self._lock:
            try:
                await self._connect()
                await self._run(self._write, payload)
            except BaseException:
                await self._run(self._close)
                raise

    async def read_available(self) -> bytes:
        """Future RX/debug hook; no unverified response parsing."""
        async with self._lock:
            if self._port is None:
                return b""
            return await self._run(self._port.read, 4096)

    async def close(self):
        async with self._lock:
            await self._run(self._close)
