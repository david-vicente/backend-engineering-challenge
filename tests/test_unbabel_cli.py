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
                duration=20
            ),
        )


if __name__ == "__main__":
    unittest.main()
