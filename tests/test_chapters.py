import copy
import json
import unittest

from chapters import Chapter, ChapterParseError, parse_chapters


class ChapterParserTests(unittest.TestCase):
    def test_full_metadata_preserves_titles_and_fractional_seconds(self):
        info = {
            'id': 'example',
            'duration': 60.5,
            'chapters': [
                {'title': 'Вступление', 'start_time': 0, 'end_time': 10.25},
                {'title': 'Main', 'start_time': 10.25, 'end_time': 60.5},
            ],
        }
        expected = [Chapter('Вступление', 0, 10.25), Chapter('Main', 10.25, 60.5)]
        for data in [info, json.dumps(info), json.dumps(info, ensure_ascii=False).encode('utf-8')]:
            with self.subTest(input_type=type(data)):
                self.assertEqual(parse_chapters(data), expected)

    def test_chapters_only_json(self):
        chapters = [{'title': 'Intro', 'start_time': 2, 'end_time': 5}]
        self.assertEqual(parse_chapters(json.dumps(chapters)), [Chapter('Intro', 2, 5)])

    def test_no_chapters(self):
        for data in [{}, {'chapters': None}, {'chapters': []}, [], '{}', '[]']:
            with self.subTest(data=data):
                self.assertEqual(parse_chapters(data), [])

    def test_infers_ends_without_mutating_metadata(self):
        info = {'duration': 30, 'chapters': [
            {'title': 'First', 'start_time': 0},
            {'title': 'Last', 'start_time': 12.5, 'end_time': None},
        ]}
        original = copy.deepcopy(info)
        self.assertEqual(parse_chapters(info), [Chapter('First', 0, 12.5), Chapter('Last', 12.5, 30)])
        self.assertEqual(info, original)

    def test_infers_next_start_without_video_duration(self):
        chapters = [{'start_time': 0}, {'start_time': 5, 'end_time': 10}]
        self.assertEqual(parse_chapters(chapters), [Chapter('Chapter 1', 0, 5), Chapter('Chapter 2', 5, 10)])

    def test_missing_and_blank_titles_get_numbered_names(self):
        chapters = [{'start_time': 0}, {'title': '  ', 'start_time': 1},
                    {'title': None, 'start_time': 2, 'end_time': 3}]
        self.assertEqual([c.title for c in parse_chapters(chapters)], ['Chapter 1', 'Chapter 2', 'Chapter 3'])

    def test_explicit_gaps_and_overlaps_are_preserved(self):
        chapters = [{'start_time': 0, 'end_time': 5},
                    {'start_time': 3, 'end_time': 7},
                    {'start_time': 9, 'end_time': 10}]
        self.assertEqual([(c.start_time, c.end_time) for c in parse_chapters(chapters)], [(0, 5), (3, 7), (9, 10)])

    def test_invalid_json_or_root(self):
        for data in ['{', b'\xff', 'null', '42', '"text"', None, True, 42]:
            with self.subTest(data=data), self.assertRaises(ChapterParseError):
                parse_chapters(data)

    def test_rejects_playlists(self):
        for data in [{'entries': []}, {'_type': 'playlist'}, {'_type': 'multi_video'}]:
            with self.subTest(data=data), self.assertRaises(ChapterParseError):
                parse_chapters(data)

    def test_invalid_chapter_array_or_entry(self):
        for data in [{'chapters': {}}, {'chapters': 'bad'}, [None], ['bad']]:
            with self.subTest(data=data), self.assertRaises(ChapterParseError):
                parse_chapters(data)

    def test_invalid_timestamps(self):
        for field in ['start_time', 'end_time']:
            for value in [None, True, False, '2', -1, float('nan'), float('inf'), 10**400]:
                chapter = {'start_time': 0, 'end_time': 10}
                chapter[field] = value
                with self.subTest(field=field, value=value), self.assertRaises(ChapterParseError):
                    parse_chapters([chapter])

    def test_invalid_video_duration(self):
        for duration in [-1, True, '10', float('nan'), float('inf')]:
            with self.subTest(duration=duration), self.assertRaises(ChapterParseError):
                parse_chapters({'duration': duration, 'chapters': [{'start_time': 0, 'end_time': 5}]})

    def test_end_must_follow_start(self):
        for end in [4, 5]:
            with self.subTest(end=end), self.assertRaises(ChapterParseError):
                parse_chapters([{'start_time': 5, 'end_time': end}])

    def test_rejects_unsorted_or_duplicate_starts(self):
        for start in [0, 1]:
            with self.subTest(start=start), self.assertRaises(ChapterParseError):
                parse_chapters([{'start_time': 1, 'end_time': 3}, {'start_time': start, 'end_time': 4}])

    def test_rejects_end_beyond_duration(self):
        with self.assertRaises(ChapterParseError):
            parse_chapters({'duration': 5, 'chapters': [{'start_time': 0, 'end_time': 6}]})

    def test_rejects_incomplete_last_chapter(self):
        with self.assertRaises(ChapterParseError):
            parse_chapters([{'start_time': 0}])

    def test_rejects_non_string_title(self):
        with self.assertRaises(ChapterParseError):
            parse_chapters([{'title': 123, 'start_time': 0, 'end_time': 1}])


if __name__ == '__main__':
    unittest.main()
