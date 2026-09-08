import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from collector.process_runner import ProcessRunner


class ProcessRunnerTests(unittest.TestCase):
    def test_python_child_logs_are_forced_to_utf8(self):
        lines = []
        with patch.dict(os.environ, {
            'PYTHONIOENCODING': 'gbk',
            'PYTHONUTF8': '0',
        }):
            ProcessRunner().run(
                [sys.executable, '-c', "print('正在访问商品页面')"],
                Path.cwd(),
                lines.append,
            )

        self.assertEqual(lines, ['正在访问商品页面'])
        self.assertNotIn('\ufffd', ''.join(lines))


if __name__ == '__main__':
    unittest.main()
