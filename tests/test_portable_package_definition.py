import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class PortablePackageDefinitionTests(unittest.TestCase):
    def test_package_has_gui_worker_and_shared_runtime(self):
        spec = (PROJECT_ROOT / 'portable_collector.spec').read_text(encoding='utf-8')
        self.assertIn("name='1688商品采集工具'", spec)
        self.assertIn("name='_collector_worker'", spec)
        self.assertIn("contents_directory='runtime'", spec)
        self.assertIn('selenium.webdriver.chrome.webdriver', spec)
        self.assertIn("'assets' / 'app-icon.ico'", spec)
        self.assertIn('icon=str(app_icon)', spec)

        icon = PROJECT_ROOT / 'assets' / 'app-icon.ico'
        self.assertTrue(icon.is_file())
        self.assertEqual(icon.read_bytes()[:4], b'\x00\x00\x01\x00')

    def test_build_script_bundles_browser_driver_and_empty_data_dirs(self):
        script = (PROJECT_ROOT / 'build_portable.ps1').read_text(encoding='utf-8-sig')
        self.assertIn('last-known-good-versions-with-downloads.json', script)
        self.assertIn('$ariaVersion = "1.37.0"', script)
        self.assertIn('aria2-$ariaVersion-win-64bit-build1.zip', script)
        self.assertIn('browser\\chrome', script)
        self.assertIn('browser\\chromedriver.exe', script)
        self.assertIn('data\\browser_data', script)
        self.assertIn('data\\products', script)
        self.assertIn('Compress-Archive', script)


if __name__ == '__main__':
    unittest.main()
