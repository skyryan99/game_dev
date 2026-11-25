import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import screenconfig as sc


class FitTests(unittest.TestCase):
    def test_identity_at_native_size(self):
        self.assertEqual(sc.fit((1920, 1080)), (1.0, 0, 0))

    def test_smaller_16_9_window_scales_without_bars(self):
        scale, ox, oy = sc.fit((1280, 720))
        self.assertAlmostEqual(scale, 2 / 3)
        self.assertEqual((ox, oy), (0, 0))

    def test_ultrawide_gets_side_bars(self):
        scale, ox, oy = sc.fit((2560, 1080))
        self.assertEqual((scale, ox, oy), (1.0, 320, 0))

    def test_tall_window_gets_top_and_bottom_bars(self):
        scale, ox, oy = sc.fit((1920, 1200))
        self.assertEqual((scale, ox, oy), (1.0, 0, 60))

    def test_mouse_mapping_round_trips(self):
        window = (2560, 1440 + 200)
        scale, ox, oy = sc.fit(window)
        for base_pos in [(0, 0), (960, 540), (1919, 1079)]:
            win_pos = (base_pos[0] * scale + ox, base_pos[1] * scale + oy)
            x, y = sc.window_to_base(win_pos, window)
            self.assertAlmostEqual(x, base_pos[0]); self.assertAlmostEqual(y, base_pos[1])

    def test_click_in_a_bar_lands_outside_the_canvas(self):
        x, _ = sc.window_to_base((10, 500), (2560, 1080))
        self.assertLess(x, 0)

    def test_zero_sized_window_does_not_divide_by_zero(self):
        sc.window_to_base((0, 0), (0, 0))


class ResolutionTests(unittest.TestCase):
    def test_only_presets_that_fit_the_desktop(self):
        self.assertEqual(sc.available_resolutions((1920, 1080)), [(1280, 720), (1366, 768), (1600, 900), (1920, 1080)])
        self.assertEqual(sc.available_resolutions((800, 600)), [sc.MIN_SIZE])

    def test_stepping(self):
        opts = sc.available_resolutions((2560, 1440))
        self.assertEqual(sc.step_resolution((1920, 1080), 1, opts), (2560, 1440))
        self.assertEqual(sc.step_resolution((1920, 1080), -1, opts), (1600, 900))
        self.assertEqual(sc.step_resolution((2560, 1440), 1, opts), (2560, 1440))      # already max
        self.assertEqual(sc.step_resolution((1280, 720), -1, opts), (1280, 720))       # already min

    def test_stepping_from_a_dragged_out_size(self):
        opts = sc.available_resolutions((2560, 1440))
        self.assertEqual(sc.step_resolution((1700, 950), 1, opts), (1920, 1080))
        self.assertEqual(sc.step_resolution((1700, 950), -1, opts), (1600, 900))

    def test_oversized_saved_window_falls_back(self):
        opts = sc.available_resolutions((1366, 768))
        self.assertEqual(sc.fit_to_desktop((1920, 1080), (1366, 768), opts), (1366, 768))
        self.assertEqual(sc.fit_to_desktop((1280, 720), (1366, 768), opts), (1280, 720))


class PersistenceTests(unittest.TestCase):
    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "settings.json")
            self.assertTrue(sc.save(sc.Settings(True, 1600, 900), path))
            self.assertEqual(sc.load(path), sc.Settings(True, 1600, 900))

    def test_missing_corrupt_and_silly_files_give_defaults(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "settings.json")
            self.assertEqual(sc.load(path), sc.Settings())                       # missing
            for junk in ("{not json", "[]", '{"width": "wide"}', '{"width": 3, "height": 3}'):
                with open(path, "w") as handle:
                    handle.write(junk)
                self.assertEqual(sc.load(path).size, (1920, 1080), junk)

    def test_unwritable_location_is_not_fatal(self):
        self.assertFalse(sc.save(sc.Settings(), os.path.join("no_such_folder_xyz", "s.json")))


if __name__ == "__main__":
    unittest.main()
