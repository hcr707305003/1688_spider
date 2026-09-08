import queue
import tempfile
import threading
import time
import unittest
from pathlib import Path

from collector.platforms.base import CollectionTarget, PlatformAdapter
from collector.platforms.registry import PlatformRegistry
from collector.process_runner import ProcessCancelled
from collector.service import CollectionService


class FakeAdapter(PlatformAdapter):
    platform = 'fake'
    display_name = '测试平台'

    def __init__(self, fail=False, run_process=False):
        self.fail = fail
        self.should_run_process = run_process

    def matches(self, url):
        return url.startswith('https://fake.test/')

    def prepare(self, url):
        return CollectionTarget('fake', '1', url, 'https://fake.test/item/1')

    def collect(self, target, runtime):
        runtime.stage('测试阶段', 50, '处理中')
        runtime.log('一条日志')
        if self.should_run_process:
            runtime.run_process(['fake'])
        if self.fail:
            raise RuntimeError('模拟失败')
        return {'title': '测试商品', 'output_dir': str(runtime.project_root / 'out')}


class FakeRunner:
    def __init__(self):
        self.cancelled = threading.Event()

    def run(self, command, cwd, on_output):
        while not self.cancelled.wait(0.01):
            pass
        raise ProcessCancelled('采集已取消')

    def cancel(self):
        self.cancelled.set()


class CollectionServiceTests(unittest.TestCase):
    def _events_until_terminal(self, service):
        events = []
        while True:
            event = service.events.get(timeout=2)
            events.append(event)
            if event.kind in {'success', 'error', 'cancelled'}:
                return events

    def test_emits_ordered_success_events(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            service = CollectionService(
                Path(temp_dir),
                PlatformRegistry([FakeAdapter()]),
            )
            service.start('https://fake.test/item/1')
            events = self._events_until_terminal(service)

        self.assertEqual([event.kind for event in events], ['started', 'stage', 'log', 'success'])
        self.assertEqual(events[-1].data['title'], '测试商品')

    def test_emits_recoverable_error_event(self):
        service = CollectionService(
            registry=PlatformRegistry([FakeAdapter(fail=True)]),
        )
        service.start('https://fake.test/item/1')
        events = self._events_until_terminal(service)
        self.assertEqual(events[-1].kind, 'error')
        self.assertIn('模拟失败', events[-1].message)

    def test_cancel_stops_active_runner(self):
        service = CollectionService(
            registry=PlatformRegistry([FakeAdapter(run_process=True)]),
            runner_factory=FakeRunner,
        )
        service.start('https://fake.test/item/1')
        deadline = time.monotonic() + 2
        while not service.running and time.monotonic() < deadline:
            time.sleep(0.01)
        service.cancel()
        events = self._events_until_terminal(service)
        self.assertEqual(events[-1].kind, 'cancelled')


if __name__ == '__main__':
    unittest.main()
