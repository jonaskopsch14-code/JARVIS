import unittest

from jarvis.core.router import Route, route


class TestRouter(unittest.TestCase):
    def test_web_task_goes_cloud(self):
        self.assertEqual(route("Bitte buche mir online einen Termin").route, Route.CLOUD)
        self.assertEqual(route("Recherchiere das im Internet").route, Route.CLOUD)

    def test_normal_chat_stays_local(self):
        self.assertEqual(route("Wie ist das Wetter gefühlt heute?").route, Route.LOCAL)
        self.assertEqual(route("merke dir bitte diesen Termin").route, Route.LOCAL)

    def test_very_long_input_goes_cloud(self):
        long_text = "wort " * 250
        self.assertEqual(route(long_text).route, Route.CLOUD)


if __name__ == "__main__":
    unittest.main()
