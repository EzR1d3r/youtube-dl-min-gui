import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from chapters import Chapter
from download import build_download_plan


class DownloadPlanTests(unittest.TestCase):
    def test_default_chapter_output_uses_selected_folder(self):
        plan = build_download_plan('', 'downloads', '%(title)s.%(ext)s', '', 'Default')
        self.assertIn('--split-chapters', plan.options)
        chapter_output = next(value for value in plan.options if value.startswith('chapter:'))
        self.assertTrue(chapter_output.startswith('chapter:' + os.path.abspath('downloads')))

    def test_multiple_spaces_do_not_produce_empty_urls(self):
        plan = build_download_plan(' --extract-audio  --audio-format mp3  ', '.', 'x', 'ffmpeg')
        self.assertNotIn('', plan.options)

    def test_extended_uses_final_path_and_keeps_snapshot_of_ranges(self):
        chapters = [Chapter('Whole file', 0.1, 1.2)]
        plan = build_download_plan('', '.', 'x', '', 'Extended', chapters)
        workspace = plan.workspace.name
        try:
            result_file = plan.options[-1]
            Path(result_file).write_text(json.dumps('converted.mp3') + '\n', encoding='utf-8')
            chapters.clear()
            with patch('download.split_media') as split:
                plan.postprocess()
            self.assertEqual(split.call_args.args[0], 'converted.mp3')
            self.assertEqual(split.call_args.args[2], (Chapter('Whole file', 0.1, 1.2),))
            self.assertIn('--no-split-chapters', plan.options)
        finally:
            plan.cleanup()
        self.assertFalse(os.path.exists(workspace))

    def test_extended_rejects_missing_ranges_and_timeline_changes(self):
        for options, chapters in [('', []), ('--download-sections=*0-1', [Chapter('x', 0, 1)]),
                                  ('--remove-chapters x', [Chapter('x', 0, 1)])]:
            with self.subTest(options=options), self.assertRaises(ValueError):
                build_download_plan(options, '.', 'x', '', 'Extended', chapters)

    def test_extended_rejects_missing_or_multiple_final_files(self):
        plan = build_download_plan('', '.', 'x', '', 'Extended', [Chapter('x', 0, 1)])
        try:
            with self.assertRaisesRegex(ValueError, 'did not report'):
                plan.postprocess()
            Path(plan.options[-1]).write_text('"a.mp4"\n"b.mp4"\n', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'single'):
                plan.postprocess()
        finally:
            plan.cleanup()
