from datetime import datetime
import unittest
import unbabel_cli


class UnbabelCliTests(unittest.TestCase):
    def test_process_line_builds_event_from_json(self):
        line = (
            '{"timestamp": "2018-12-26 18:11:08.509654",'
            '"translation_id": "5aa5b2f39f7254a75aa5",'
            '"source_language": "en",'
            '"target_language": "fr",'
            '"client_name": "airliberty",'
            '"event_name": "translation_delivered",'
            '"nr_words": 30,'
            ' "duration": 20}')
        event = unbabel_cli.process_line(line)

        self.assertEqual(
            event,
            unbabel_cli.Event(
                timestamp=datetime(2018, 12, 26, 18, 11, 8, 509654),
                duration=20,
                event_name="translation_delivered",
            ),
        )

    def test_event_minute_assigns_event_to_floored_minute(self):

        inside_minute_ev = unbabel_cli.Event(
            timestamp=datetime(2018, 12, 26, 18, 11, 8, 509654),
            duration=20,
            event_name="translation_delivered",
        )
        self.assertEqual(
            unbabel_cli.assign_event_to_minute(inside_minute_ev),
            datetime(2018, 12, 26, 18, 11),
        )

    def test_event_minute_assigns_event_at_exact_minute_to_previous_minute(self):
        exact_minute_ev = unbabel_cli.Event(
            timestamp=datetime(2018, 12, 26, 18, 11),
            duration=20,
            event_name="translation_delivered",
        )

        self.assertEqual(
            unbabel_cli.assign_event_to_minute(exact_minute_ev),
            datetime(2018, 12, 26, 18, 10),
        )





if __name__ == "__main__":
    unittest.main()
