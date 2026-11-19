import unittest
from types import SimpleNamespace as Point

from gesture import GestureEngine, Settings, pointer_target


def hand(thumb=(0.4, 0.4), index=(0.6, 0.4)):
    points = [Point(x=0.5, y=0.6) for _ in range(21)]
    points[0] = Point(x=0.5, y=0.8)
    points[9] = Point(x=0.5, y=0.5)
    points[4] = Point(x=thumb[0], y=thumb[1])
    points[8] = Point(x=index[0], y=index[1])
    return points


class GestureTests(unittest.TestCase):
    def test_pointer_movement_modes(self):
        screen = (0, 0, 1000, 800)
        relative = pointer_target(.6, .5, (.5, .5), (300, 250), screen,
                                  Settings(movement_mode="손 이동량", sensitivity=1))
        absolute = pointer_target(.6, .5, (.5, .5), (300, 250), screen,
                                  Settings(movement_mode="화면 위치", sensitivity=1))
        self.assertAlmostEqual(relative[0], 300 + .1 * 1000 / .76)
        self.assertAlmostEqual(absolute[0], (.6 - .12) / .76 * 999)
        self.assertNotEqual(relative, absolute)

    def test_pointer_choices(self):
        middle = GestureEngine(Settings()).update(hand(), 0)[0]
        thumb = GestureEngine(Settings(pointer_mode="엄지 끝")).update(hand(), 0)[0]
        self.assertEqual(middle, ("move", 0.5, 0.4))
        self.assertEqual(thumb, ("move", 0.4, 0.4))

    def test_small_jitter_still_clicks_before_release_move(self):
        engine = GestureEngine(Settings())
        engine.update(hand(index=(0.41, 0.4)), 0)
        engine.update(hand(thumb=(0.402, 0.415), index=(0.412, 0.415)), 0.1)
        actions = engine.update(hand(), 0.2)
        self.assertEqual(actions[0], ("left_click",))
        self.assertEqual(actions[1], ("move", 0.5, 0.4))

    def test_deliberate_vertical_move_scrolls_without_click(self):
        engine = GestureEngine(Settings())
        engine.update(hand(index=(0.41, 0.4)), 0)
        engine.update(hand(thumb=(0.4, 0.29), index=(0.41, 0.29)), 0.1)
        actions = engine.update(hand(thumb=(0.4, 0.23), index=(0.41, 0.23)), 0.2)
        self.assertIn(("scroll", 2), actions)
        self.assertNotIn(("left_click",), engine.update(hand(), 0.3))

    def test_one_missing_frame_keeps_pinch(self):
        engine = GestureEngine(Settings())
        engine.update(hand(index=(0.41, 0.4)), 0)
        self.assertEqual(engine.update(None, 0.05), [])
        self.assertEqual(engine.update(hand(), 0.1)[0], ("left_click",))

    def test_scroll_direction_and_sensitivity(self):
        settings = Settings(scroll_direction="손과 반대 방향", scroll_sensitivity=2.0)
        engine = GestureEngine(settings)
        engine.update(hand(index=(0.41, 0.4)), 0)
        engine.update(hand(thumb=(0.4, 0.29), index=(0.41, 0.29)), 0.1)
        actions = engine.update(hand(thumb=(0.4, 0.26), index=(0.41, 0.26)), 0.2)
        self.assertIn(("scroll", -2), actions)

    def test_held_pinch_clicks_once(self):
        engine = GestureEngine(Settings())
        pinched = hand(index=(0.41, 0.4))
        engine.update(pinched, 0)
        self.assertIn(("left_click",), engine.update(pinched, 0.21))
        self.assertNotIn(("left_click",), engine.update(pinched, 0.31))
        self.assertNotIn(("left_click",), engine.update(hand(), 0.4))


if __name__ == "__main__":
    unittest.main()

