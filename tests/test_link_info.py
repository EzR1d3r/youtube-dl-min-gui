import json
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from link_info import format_formats, read_link_info
from chapters import Chapter
from main_window import MainWindow
import utils


class LinkInfoTests(unittest.TestCase):
    def test_video_audio_and_incomplete_formats(self):
        table = format_formats({'title': 'Видео', 'formats': [
            {'format_id': '137', 'ext': 'mp4', 'width': 1920, 'height': 1080,
             'fps': 30, 'vcodec': 'avc1', 'acodec': 'none'},
            {'format_id': '140', 'ext': 'm4a', 'vcodec': 'none', 'acodec': 'aac'},
            {'format_id': 'other', 'resolution': 'storyboard', 'format_note': 'images'},
        ]})
        for value in ['Видео', '137', '1920x1080', '140', 'audio only', 'storyboard', 'images']:
            self.assertIn(value, table)

    def test_no_formats(self):
        self.assertEqual(format_formats({}), 'No formats available.\n')

    def test_json_is_displayed_as_table_and_chapters_are_not_parsed(self):
        metadata = {'title': 'Видео', 'formats': [{'format_id': '140', 'ext': 'm4a'}],
                    'chapters': [{'invalid': 'not used yet'}]}
        process = Mock(returncode=0)
        process.communicate.return_value = (json.dumps(metadata, ensure_ascii=False).encode('utf-8'), b'warning\n')
        output = []
        read_link_info(process, output.append)
        self.assertEqual(''.join(output), 'warning\n' + format_formats(metadata))
        process.communicate.assert_called_once_with()

    def test_bad_json_or_metadata_is_reported(self):
        for data in [b'bad JSON', b'[]', b'{"entries":[]}', b'{"formats":[null]}']:
            with self.subTest(data=data):
                process = Mock(returncode=0)
                process.communicate.return_value = (data, b'')
                output = []
                read_link_info(process, output.append)
                self.assertIn('ERROR:', ''.join(output))

    def test_downloader_failure_preserves_stderr(self):
        process = Mock(returncode=1)
        process.communicate.return_value = (b'', b'network error\n')
        output = []
        read_link_info(process, output.append)
        self.assertIn('network error', ''.join(output))
        self.assertIn('exit code 1', ''.join(output))

    def test_callback_receives_only_parsed_chapters(self):
        metadata = {'duration': 10, 'formats': [], 'chapters': [{'title': 'Intro', 'start_time': 0}]}
        process = Mock(returncode=0)
        process.communicate.return_value = (json.dumps(metadata).encode(), b'')
        callback = Mock()
        read_link_info(process, Mock(), callback)
        callback.assert_called_once_with([Chapter('Intro', 0, 10)])

    def test_bad_chapters_preserve_formats(self):
        metadata = {'formats': [{'format_id': '140'}], 'chapters': [{'start_time': 0}]}
        process = Mock(returncode=0)
        process.communicate.return_value = (json.dumps(metadata).encode(), b'')
        output = []
        callback = Mock()
        read_link_info(process, output.append, callback)
        self.assertIn('140', ''.join(output))
        self.assertIn('Could not parse chapters', ''.join(output))
        callback.assert_called_once_with([])

    def test_one_json_command_without_download(self):
        with patch('utils.exec_youtube_dl') as execute:
            utils.exec_get_info('yt-dlp.exe', 'url')
        args = execute.call_args.args
        for flag in ['--skip-download', '--no-playlist', '--dump-single-json']:
            self.assertIn(flag, args)
        self.assertNotIn('-F', args)
        self.assertEqual(args[-2:], ('--', 'url'))

    def test_each_click_starts_a_request_without_disabling_button(self):
        window = MainWindow.__new__(MainWindow)
        window.settings = SimpleNamespace(youtube_dl_path='yt-dlp.exe')
        window.append_console_line = Mock()
        window.btnInfo = Mock()
        window.chapter_editor = Mock()
        window.link_var = Mock()
        window.link_var.get.return_value = 'url'
        with patch('utils.exec_get_info') as execute, patch('main_window.Thread') as thread:
            window.get_info('url')
            window.get_info('url')
        self.assertEqual(execute.call_count, 2)
        self.assertEqual(thread.return_value.start.call_count, 2)
        window.btnInfo.configure.assert_not_called()

    def test_chapter_data_is_cleared_when_link_changes(self):
        window = MainWindow.__new__(MainWindow)
        window.chapter_editor = Mock()
        window.show_chapters = Mock()
        window.show_chapters.get.return_value = True
        window.link_var = Mock()
        window.link_var.get.return_value = 'new-url'
        window.chapters = [Chapter('Intro', 0, 10)]
        window._clear_link_info()
        window._set_chapters('old-url', [Chapter('Intro', 0, 10)])
        self.assertEqual(window.chapters, [])
        window._set_chapters('new-url', [Chapter('New', 0, 20)])
        self.assertEqual(window.chapters, [Chapter('New', 0, 20)])


if __name__ == '__main__':
    unittest.main()
