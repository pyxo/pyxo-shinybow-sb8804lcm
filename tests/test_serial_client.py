"""Isolated transport tests; intentionally no Home Assistant or serial hardware."""
import asyncio
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

serial_stub = types.ModuleType('serial')
serial_stub.SerialTimeoutException = type('SerialTimeoutException', (OSError,), {})
serial_stub.Serial = None
spec = importlib.util.spec_from_file_location('serial_client', Path(__file__).parents[1] / 'custom_components/shinybow_sb8804lcm/serial_client.py')
client = importlib.util.module_from_spec(spec)
with patch.dict(sys.modules, {'serial': serial_stub}):
    spec.loader.exec_module(client)


class FakePort:
    def __init__(self):
        self.writes = []
        self.closed = False
        self.fail = False
    def write(self, value):
        if self.fail:
            raise OSError('disconnected')
        self.writes.append(value)
        return len(value)
    def close(self):
        self.closed = True
    def read(self, size):
        return b''


class ProtocolTests(unittest.TestCase):
    def test_exact_wire_bytes(self):
        self.assertEqual(client.encode_command(client.route_command(1, 3)), b'OUTPUT001 003;\r\n')
        self.assertEqual(client.encode_command(client.route_command(None, 0)), b'OUTPUTALL 000;\r\n')
    def test_reject_invalid_routes(self):
        for output, source in [(0, 1), (9, 1), (1, -1), (1, 9), (True, 1)]:
            with self.assertRaises(ValueError):
                client.route_command(output, source)
    def test_single_command_only(self):
        for command in ['OUTPUT001 003;LINK 001;', 'A\r\nB', '', 'é']:
            with self.assertRaises(ValueError):
                client.encode_command(command)
        self.assertEqual(client.encode_command('LINK 001'), b'LINK 001;\r\n')


class TransportTests(unittest.IsolatedAsyncioTestCase):
    async def test_link_once_and_close(self):
        port = FakePort()
        with patch.object(serial_stub, 'Serial', return_value=port) as factory:
            transport = client.SerialClient('/dev/test')
            await transport.connect()
            await asyncio.gather(transport.send_command('OUTPUT001 003;'), transport.send_command('OUTPUT002 004;'))
            self.assertEqual(port.writes, [b'LINK 001;\r\n', b'OUTPUT001 003;\r\n', b'OUTPUT002 004;\r\n'])
            self.assertEqual(factory.call_count, 1)
            self.assertEqual(factory.call_args.kwargs['baudrate'], 9600)
            self.assertFalse(factory.call_args.kwargs['rtscts'])
            await transport.close()
            self.assertTrue(port.closed)
    async def test_failure_closes_and_next_action_relinks(self):
        first, second = FakePort(), FakePort()
        with patch.object(serial_stub, 'Serial', side_effect=[first, second]):
            transport = client.SerialClient('/dev/test')
            await transport.connect()
            first.fail = True
            with self.assertRaises(OSError):
                await transport.send_command('OUTPUT001 003;')
            self.assertTrue(first.closed)
            await transport.send_command('OUTPUTALL 000;')
            self.assertEqual(second.writes, [b'LINK 001;\r\n', b'OUTPUTALL 000;\r\n'])
            await transport.close()
    async def test_cancel_handshake_closes_port(self):
        port = FakePort()
        with patch.object(serial_stub, 'Serial', return_value=port):
            transport = client.SerialClient('/dev/test')
            task = asyncio.create_task(transport.connect())
            while not port.writes:
                await asyncio.sleep(.001)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task
            self.assertTrue(port.closed)
    async def test_short_write_fails(self):
        port = FakePort()
        with patch.object(serial_stub, 'Serial', return_value=port), patch.object(port, 'write', return_value=1):
            transport = client.SerialClient('/dev/test')
            with self.assertRaises(OSError):
                await transport.connect()
            self.assertTrue(port.closed)
