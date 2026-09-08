"""面向 GUI 的后台采集服务。"""

import queue
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Sequence

from .platforms.alibaba1688 import Alibaba1688Adapter
from .platforms.base import CollectionTarget
from .platforms.registry import PlatformRegistry
from .process_runner import ProcessCancelled, ProcessRunner
from .runtime_paths import data_root as default_data_root


@dataclass(frozen=True)
class CollectionEvent:
    kind: str
    message: str = ''
    progress: int = 0
    data: Dict[str, Any] = field(default_factory=dict)


class _Runtime:
    def __init__(
        self,
        project_root: Path,
        data_root: Path,
        runner: ProcessRunner,
        emit: Callable[[CollectionEvent], None],
    ):
        self.project_root = project_root
        self.data_root = data_root
        self._runner = runner
        self._emit = emit

    def stage(self, name: str, progress: int, message: str) -> None:
        self._emit(CollectionEvent('stage', message, progress, {'stage': name}))

    def log(self, message: str) -> None:
        self._emit(CollectionEvent('log', message))

    def run_process(self, command: Sequence[str]) -> None:
        self._runner.run(command, self.project_root, self.log)


class CollectionService:
    def __init__(
        self,
        project_root: Optional[Path] = None,
        registry: Optional[PlatformRegistry] = None,
        runner_factory: Callable[[], ProcessRunner] = ProcessRunner,
        data_root: Optional[Path] = None,
    ):
        self.project_root = (project_root or Path(__file__).resolve().parents[1]).resolve()
        self.data_root = (data_root or (
            self.project_root if project_root is not None else default_data_root()
        )).resolve()
        self.registry = registry or PlatformRegistry([Alibaba1688Adapter()])
        self.runner_factory = runner_factory
        self.events: queue.Queue[CollectionEvent] = queue.Queue()
        self._thread: Optional[threading.Thread] = None
        self._runner: Optional[ProcessRunner] = None

    @property
    def running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def prepare(self, url: str) -> CollectionTarget:
        return self.registry.prepare(url)

    def start(self, url: str) -> CollectionTarget:
        if self.running:
            raise RuntimeError('已有采集任务正在运行')
        target = self.prepare(url)
        self._runner = self.runner_factory()
        self._thread = threading.Thread(
            target=self._collect,
            args=(target,),
            name='product-collector',
            daemon=True,
        )
        self._thread.start()
        return target

    def _collect(self, target: CollectionTarget) -> None:
        self.events.put(CollectionEvent('started', f'已识别平台：{target.platform}', 5, {
            'platform': target.platform,
            'product_id': target.product_id,
        }))
        runtime = _Runtime(self.project_root, self.data_root, self._runner, self.events.put)
        try:
            adapter = self.registry.match(target.normalized_url)
            result = adapter.collect(target, runtime)
            self.events.put(CollectionEvent('success', '采集完成', 100, result))
        except ProcessCancelled:
            self.events.put(CollectionEvent('cancelled', '采集已取消'))
        except Exception as exc:
            self.events.put(CollectionEvent('error', str(exc)))

    def cancel(self) -> None:
        if self._runner:
            self._runner.cancel()
