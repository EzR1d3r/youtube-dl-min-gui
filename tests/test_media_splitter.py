import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from chapters import Chapter
from media_splitter import _executable, split_media


class MediaSplitterIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.location = os.environ.get('TEST_FFMPEG_DIR', '')
        try:
            cls.ffmpeg = _executable(cls.location, 'ffmpeg')
            cls.ffprobe = _executable(cls.location, 'ffprobe')
        except ValueError as error:
            raise unittest.SkipTest(str(error))

    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory(prefix='mingui-test-')
        self.addCleanup(self.workspace.cleanup)
        self.folder = Path(self.workspace.name)
        self.logs = []

    def run_ffmpeg(self, *arguments):
        result = subprocess.run([self.ffmpeg, '-hide_banner', '-nostdin', '-v', 'error', *arguments],
                                capture_output=True, text=True, encoding='utf-8', errors='replace')
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def assert_media(self, path, duration, codecs):
        result = subprocess.run([self.ffprobe, '-v', 'error', '-show_format', '-show_streams',
                                 '-of', 'json', str(path)], capture_output=True, text=True,
                                encoding='utf-8', errors='replace', check=True)
        info = json.loads(result.stdout)
        self.assertAlmostEqual(float(info['format']['duration']), duration, delta=0.08)
        self.assertEqual([stream['codec_name'] for stream in info['streams']], codecs)
        self.run_ffmpeg('-xerror', '-i', str(path), '-f', 'null', '-')

    def test_video_ranges_are_decodable_and_original_is_kept(self):
        source = self.folder / 'source.mp4'
        self.run_ffmpeg('-f', 'lavfi', '-i', 'testsrc2=size=160x90:rate=25',
                        '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=48000',
                        '-t', '3', '-c:v', 'libx264', '-c:a', 'aac', str(source))
        original = source.read_bytes()
        chapters = [Chapter('First / part', 0.30, 1.40), Chapter('Second', 1.40, 2.30)]
        split_media(str(source), str(self.folder), chapters, self.location, self.logs.append)
        outputs = sorted(self.folder.glob('source - *.mp4'))
        self.assertEqual(len(outputs), 2)
        self.assert_media(outputs[0], 1.10, ['h264', 'aac'])
        self.assert_media(outputs[1], 0.90, ['h264', 'aac'])
        self.assertEqual(source.read_bytes(), original)
        with self.assertRaisesRegex(ValueError, 'already exists'):
            split_media(str(source), str(self.folder), chapters, self.location, self.logs.append)
        self.assertFalse(list(self.folder.glob('.mingui-chapters-*')))
        self.assertIn('Finished', ''.join(self.logs))

    def test_single_range_without_source_chapters_trims_mp3(self):
        source = self.folder / 'audio.mp3'
        self.run_ffmpeg('-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=48000',
                        '-t', '3', '-c:a', 'libmp3lame', str(source))
        split_media(str(source), str(self.folder), [Chapter('Trimmed', 0.30, 1.40)],
                    self.location, self.logs.append)
        outputs = list(self.folder.glob('audio - *.mp3'))
        self.assertEqual(len(outputs), 1)
        self.assert_media(outputs[0], 1.10, ['mp3'])

    def test_other_audio_is_encoded_as_m4a_and_bad_range_is_rejected(self):
        source = self.folder / 'audio.wav'
        self.run_ffmpeg('-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=48000',
                        '-t', '3', str(source))
        split_media(str(source), str(self.folder), [Chapter('Trimmed', 0.30, 1.40)],
                    self.location, self.logs.append)
        outputs = list(self.folder.glob('audio - *.m4a'))
        self.assertEqual(len(outputs), 1)
        self.assert_media(outputs[0], 1.10, ['aac'])
        with self.assertRaisesRegex(ValueError, 'beyond'):
            split_media(str(source), str(self.folder), [Chapter('Bad', 0, 8)],
                        self.location, self.logs.append)
