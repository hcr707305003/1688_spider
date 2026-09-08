import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from collector import runtime_paths


class RuntimePathTests(unittest.TestCase):
    def test_source_commands_keep_python_entry_points(self):
        with patch.object(runtime_paths.sys, 'frozen', False, create=True):
            auto = runtime_paths.build_auto_collector_command(
                'https://detail.1688.com/offer/1.html',
                Path('products'),
            )
            parser = runtime_paths.build_parser_command(Path('products/1.html'))

        self.assertEqual(auto[0], runtime_paths.sys.executable)
        self.assertIn('utils.auto_collector', auto)
        self.assertEqual(parser[0], runtime_paths.sys.executable)
        self.assertIn('--no-rebuild', parser)

    def test_frozen_command_uses_bundled_browser_and_portable_data(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            executable = root / '1688商品采集工具.exe'
            worker = root / '_collector_worker.exe'
            browser = root / 'browser' / 'chrome' / 'chrome.exe'
            driver = root / 'browser' / 'chromedriver.exe'
            for path in (executable, worker, browser, driver):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()

            with (
                patch.object(runtime_paths.sys, 'frozen', True, create=True),
                patch.object(runtime_paths.sys, 'executable', str(executable)),
            ):
                command = runtime_paths.build_auto_collector_command(
                    'https://detail.1688.com/offer/1.html',
                    runtime_paths.products_root(),
                )

            self.assertEqual(Path(command[0]), worker.resolve())
            self.assertEqual(command[1], 'auto')
            command_paths = {
                Path(value)
                for value in command
                if ':\\' in value
            }
            self.assertIn(browser.resolve(), command_paths)
            self.assertIn(driver.resolve(), command_paths)
            self.assertIn((root / 'data' / 'browser_data').resolve(), command_paths)
            self.assertIn((root / 'data' / 'products').resolve(), command_paths)

    def test_frozen_command_reports_incomplete_package(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            executable = Path(temp_dir) / '1688商品采集工具.exe'
            executable.touch()
            with (
                patch.object(runtime_paths.sys, 'frozen', True, create=True),
                patch.object(runtime_paths.sys, 'executable', str(executable)),
            ):
                with self.assertRaisesRegex(RuntimeError, '重新解压完整便携版'):
                    runtime_paths.build_auto_collector_command('https://example.test', Path('out'))


if __name__ == '__main__':
    unittest.main()
