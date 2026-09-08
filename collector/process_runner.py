"""可流式读取且可取消的子进程执行器。"""

import os
import subprocess
import threading
from pathlib import Path
from typing import Callable, Optional, Sequence


class ProcessExecutionError(RuntimeError):
    pass


class ProcessCancelled(RuntimeError):
    pass


class ProcessRunner:
    def __init__(self):
        self._lock = threading.Lock()
        self._process: Optional[subprocess.Popen] = None
        self._cancelled = False

    def run(self, command: Sequence[str], cwd: Path, on_output: Callable[[str], None]) -> None:
        if self._cancelled:
            raise ProcessCancelled('采集已取消')

        creationflags = 0
        if hasattr(subprocess, 'CREATE_NEW_PROCESS_GROUP'):
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

        child_env = os.environ.copy()
        child_env['PYTHONIOENCODING'] = 'utf-8'
        child_env['PYTHONUTF8'] = '1'

        process = subprocess.Popen(
            list(command),
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
            bufsize=1,
            creationflags=creationflags,
            env=child_env,
        )
        with self._lock:
            self._process = process

        try:
            if process.stdout:
                for line in process.stdout:
                    on_output(line.rstrip())
            return_code = process.wait()
        finally:
            if process.stdout:
                process.stdout.close()
            with self._lock:
                self._process = None

        if self._cancelled:
            raise ProcessCancelled('采集已取消')
        if return_code != 0:
            raise ProcessExecutionError(f'采集子进程退出码: {return_code}')

    def cancel(self) -> None:
        self._cancelled = True
        with self._lock:
            process = self._process
        if not process or process.poll() is not None:
            return

        try:
            import psutil

            parent = psutil.Process(process.pid)
            children = parent.children(recursive=True)
            for child in children:
                child.terminate()
            parent.terminate()
            _, alive = psutil.wait_procs([*children, parent], timeout=3)
            for item in alive:
                item.kill()
        except Exception:
            try:
                process.terminate()
            except OSError:
                pass
