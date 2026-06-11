from datetime import datetime
from collections import deque
import json
from pathlib import Path
import tempfile
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

    def test_add_Event_to_MinuteStats_accumulates(self):
        stats = unbabel_cli.MinuteStats(total=10, count=1)
        unbabel_cli.add_event_to_stats(
            stats,
            unbabel_cli.Event(
                timestamp=datetime(2018, 12, 26, 18, 11, 8, 509654),
                duration=30,
                event_name="translation_delivered")
        )
        self.assertEqual(stats.total, 40)
        self.assertEqual(stats.count, 2)

    def test_accumulates_totals(self):
        ws = unbabel_cli.WindowStats(buckets=deque(), window_size = 10)
        ws.append(unbabel_cli.MinuteStats(total=20, count=1))
        ws.append(unbabel_cli.MinuteStats(total=30, count=2))
        self.assertEqual(ws.total, 50)
        self.assertEqual(ws.count, 3)
        self.assertAlmostEqual(ws.average(), 50 / 3)

    def test_evicts_oldest_bucket_when_full(self):
        ws = unbabel_cli.WindowStats(buckets=deque(), window_size = 3)
        for i in range(1, 5):  # push 4 buckets into a window of 3
            ws.append(unbabel_cli.MinuteStats(total=i * 10, count=1))
        self.assertEqual(ws.count, 3)
        self.assertEqual(ws.total, 20 + 30 + 40)

    def test_process_file_writes_window_averages_from_input_file(self):
        input_path = Path(__file__).parent / "data" / "test-input.jsonl"

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "averages.jsonl"

            unbabel_cli.process_file(input_path, output_path)

            computed_averages = [
                json.loads(line)
                for line in output_path.read_text(encoding="utf-8").splitlines()
            ]

        self.assertEqual(
            computed_averages,
            [
                {"date": "2018-12-26 18:11:00", "average_delivery_time": 0},
                {"date": "2018-12-26 18:12:00", "average_delivery_time": 20},
                {"date": "2018-12-26 18:13:00", "average_delivery_time": 20},
                {"date": "2018-12-26 18:14:00", "average_delivery_time": 20},
                {"date": "2018-12-26 18:15:00", "average_delivery_time": 20},
                {"date": "2018-12-26 18:16:00", "average_delivery_time": 25.5},
                {"date": "2018-12-26 18:17:00", "average_delivery_time": 25.5},
                {"date": "2018-12-26 18:18:00", "average_delivery_time": 25.5},
                {"date": "2018-12-26 18:19:00", "average_delivery_time": 25.5},
                {"date": "2018-12-26 18:20:00", "average_delivery_time": 25.5},
                {"date": "2018-12-26 18:21:00", "average_delivery_time": 25.5},
                {"date": "2018-12-26 18:22:00", "average_delivery_time": 31},
                {"date": "2018-12-26 18:23:00", "average_delivery_time": 31},
                {"date": "2018-12-26 18:24:00", "average_delivery_time": 42.5},
            ],
        )

if __name__ == "__main__":
    unittest.main()
