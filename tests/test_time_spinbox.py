import tkinter as tk
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from chapters import Chapter
from chapter_editor import ChapterEditor
from time_spinbox import TimeSpinbox, format_time, parse_time, seconds_to_milliseconds, time_step


class TimeConversionTests(unittest.TestCase):
    def test_hundredths_are_stored_as_milliseconds(self):
        for text, milliseconds in [('00:00:05:10', 5100), ('00:00:05:20', 5200),
                                   ('00:00:05:30', 5300), ('00:00:05:01', 5010)]:
            with self.subTest(text=text):
                self.assertEqual(parse_time(text), milliseconds)
                self.assertEqual(format_time(milliseconds), text)

    def test_rounding_to_hundredths(self):
        for seconds, expected in [(5.104, 5100), (5.105, 5110), (5.109, 5110),
                                  (59.995, 60000), (0.005, 10), (0.004, 0)]:
            with self.subTest(seconds=seconds):
                self.assertEqual(seconds_to_milliseconds(seconds), expected)
        self.assertEqual(format_time(59995), '00:01:00:00')

    def test_hour_and_minute_rollover_and_long_times(self):
        for milliseconds in [0, 59990, 60000, 3599990, 3600000, 100 * 3600000 + 1230]:
            with self.subTest(milliseconds=milliseconds):
                self.assertEqual(parse_time(format_time(milliseconds)), milliseconds)
        self.assertEqual(format_time(3600000), '01:00:00:00')

    def test_invalid_input(self):
        for text in ['', '5.1', '-1:00:00:00', '00:60:00:00', '00:00:60:00',
                     '00:00:05:100', '00:00:05:1', 'nan']:
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_time(text)
        for value in [-1, float('nan'), float('inf')]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                seconds_to_milliseconds(value)

    def test_modifier_steps(self):
        self.assertEqual(time_step(0), 1000)
        self.assertEqual(time_step(0x0001), 60000)
        self.assertEqual(time_step(0x0004), 100)
        self.assertEqual(time_step(0x0005), 100)


class TimeSpinboxTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.root = tk.Tk()
            cls.root.withdraw()
        except tk.TclError as error:
            raise unittest.SkipTest(f'Tk display unavailable: {error}')

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def setUp(self):
        self.variable = tk.StringVar(master=self.root, value='00:00:05:10')
        self.spinbox = TimeSpinbox(self.root, textvariable=self.variable, maximum_ms=3600000)

    def tearDown(self):
        self.spinbox.destroy()

    def test_integer_storage_and_manual_edit(self):
        self.assertEqual(self.spinbox.get_milliseconds(), 5100)
        self.assertIsInstance(self.spinbox._milliseconds, int)
        self.variable.set('00:01:02:34')
        self.assertEqual(self.spinbox.get_milliseconds(), 62340)
        self.assertEqual(self.spinbox._milliseconds, 62340)

    def test_arrows_and_modifiers(self):
        self.spinbox._step(1, 0)
        self.assertEqual(self.spinbox.get_milliseconds(), 6100)
        self.spinbox._step(1, 0x0001)
        self.assertEqual(self.spinbox.get_milliseconds(), 66100)
        self.spinbox._step(-1, 0x0004)
        self.assertEqual(self.variable.get(), '00:01:06:00')
        self.assertEqual(self.spinbox.get_milliseconds(), 66000)

    def test_mouse_arrow_uses_modifier_state(self):
        self.spinbox.identify = Mock(return_value='uparrow')
        self.spinbox._arrow_clicked(SimpleNamespace(x=0, y=0, state=0x0004))
        self.assertEqual(self.spinbox.get_milliseconds(), 5200)
        self.assertEqual(self.variable.get(), '00:00:05:20')

    def test_repeated_tenth_steps_have_no_float_drift(self):
        for _ in range(100):
            self.spinbox._step(1, 0x0004)
        self.assertEqual(self.spinbox.get_milliseconds(), 15100)
        self.assertEqual(self.variable.get(), '00:00:15:10')

    def test_bounds_and_invalid_edit(self):
        self.variable.set('00:00:00:00')
        self.spinbox._step(-1, 0)
        self.assertEqual(self.spinbox.get_milliseconds(), 0)
        self.variable.set('01:00:00:00')
        self.spinbox._step(1, 0)
        self.assertEqual(self.spinbox.get_milliseconds(), 3600000)
        self.variable.set('invalid')
        self.spinbox._commit(None)
        self.assertEqual(self.variable.get(), '01:00:00:00')

    def test_locked_chapter_boundary_keeps_hundredths(self):
        changed = Mock()
        editor = ChapterEditor(self.root, changed)
        try:
            editor.set_chapters([Chapter('First', 0, 5.105), Chapter('Second', 5.105, 60.105)])
            self.assertEqual(editor.rows[0].end.get(), '00:00:05:11')
            editor.rows[0].end.set('00:00:05:12')
            self.assertEqual(editor.rows[1].start.get(), '00:00:05:12')
            self.assertEqual(editor.get_chapters()[0].end_time, 5.12)
            self.assertEqual(editor.get_chapters()[1].start_time, 5.12)
            self.assertEqual(seconds_to_milliseconds(changed.call_args.args[0][0].end_time), 5120)
        finally:
            editor.destroy()


if __name__ == '__main__':
    unittest.main()
