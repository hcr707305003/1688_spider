#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PyInstaller 便携版的后台工作进程入口。"""

import sys


def _configure_output() -> None:
    """冻结后的控制台启动器不会可靠继承 PYTHONIOENCODING。"""
    for stream in (sys.stdout, sys.stderr):
        if stream is not None and hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)


def main() -> int:
    _configure_output()
    if len(sys.argv) < 2:
        print('缺少工作模式', flush=True)
        return 2

    mode = sys.argv[1]
    sys.argv = [sys.argv[0], *sys.argv[2:]]
    if mode == 'auto':
        from utils.auto_collector import main as auto_main

        return auto_main()
    if mode == 'parse':
        from main import main as parser_main

        return parser_main()

    print(f'未知工作模式：{mode}', flush=True)
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
