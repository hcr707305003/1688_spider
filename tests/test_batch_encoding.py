import tempfile
import unittest
from pathlib import Path

import config
from utils.file_handler import FileHandler


def assert_utf8_crlf_batch(test_case: unittest.TestCase, path: Path) -> None:
    raw = path.read_bytes()
    test_case.assertFalse(raw.startswith(b'\xef\xbb\xbf'), f'{path} 含 UTF-8 BOM')
    text = raw.decode('utf-8')
    test_case.assertNotIn('\ufffd', text, f'{path} 含 Unicode 替换字符')
    test_case.assertNotRegex(raw, rb'(?<!\r)\n', f'{path} 含非 CRLF 换行')
    lines = text.splitlines()
    test_case.assertGreaterEqual(len(lines), 2)
    test_case.assertEqual(lines[0].lower(), '@echo off')
    test_case.assertEqual(lines[1].lower(), 'chcp 65001 >nul')


class BatchEncodingTests(unittest.TestCase):
    def test_static_batch_files_are_utf8_crlf(self):
        root = Path(__file__).resolve().parents[1]
        for name in ('start1688.bat', 'bp1688html.bat', 'start_collector_gui.bat'):
            with self.subTest(name=name):
                assert_utf8_crlf_batch(self, root / name)

    def test_generated_rebuild_script_is_utf8_crlf(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            FileHandler({
                'DOWNLOAD_CONF': config.DOWNLOAD_CONF,
                'FILE_NAMING': config.FILE_NAMING,
            }).create_rebuild_script(temp_dir)
            assert_utf8_crlf_batch(self, Path(temp_dir) / 'rebuild.bat')

    def test_windows_powershell_build_script_has_utf8_bom(self):
        root = Path(__file__).resolve().parents[1]
        raw = (root / 'build_portable.ps1').read_bytes()
        self.assertTrue(raw.startswith(b'\xef\xbb\xbf'))
        self.assertNotIn('\ufffd', raw.decode('utf-8-sig'))


if __name__ == '__main__':
    unittest.main()
