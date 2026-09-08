import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from utils.auto_collector import AutoCollector


class AutoCollectorPortableTests(unittest.TestCase):
    def test_portable_mode_uses_only_explicit_browser_and_driver(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            browser = root / 'browser' / 'chrome.exe'
            driver = root / 'browser' / 'chromedriver.exe'
            profile = root / 'data' / 'browser_data'
            output = root / 'data' / 'products'
            browser.parent.mkdir(parents=True)
            browser.touch()
            driver.touch()
            collector = AutoCollector(
                output_dir=str(output),
                browser_binary=str(browser),
                driver_path=str(driver),
                user_data_dir=str(profile),
                portable=True,
            )

            with patch('utils.auto_collector.webdriver.Chrome') as chrome:
                collector.start_browser(load_default_extensions=False)

            kwargs = chrome.call_args.kwargs
            self.assertEqual(kwargs['options'].binary_location, str(browser))
            self.assertEqual(kwargs['service'].path, str(driver))
            self.assertTrue(profile.is_dir())


if __name__ == '__main__':
    unittest.main()
