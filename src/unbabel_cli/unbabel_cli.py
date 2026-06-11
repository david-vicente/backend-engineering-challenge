import argparse
import json
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import deque

@dataclass
class Event:
    timestamp: datetime
    duration: int
    event_name: str


@dataclass
class MinuteStats:
    total: int  # sum of event durations in this minute
    count: int  # number of events in this minute


@dataclass
class WindowStats:
    buckets: deque
    total: int = 0  # rolling sum of durations across buckets in the window
    count: int = 0  # rolling number of events across buckets in the window

    # Close minute and update sliding window statistics.
    def append(self, bucket: MinuteStats, window: int):

        self.buckets.append(bucket)
        self.total += bucket.total
        self.count += bucket.count

        # remove old buckets
        if len(self.buckets) > window:
            removed = self.buckets.popleft()
            self.total -= removed.total
            self.count -= removed.count

    def average(self):
        return self.total / self.count if self.count else 0

def event_stats(event):
    return MinuteStats(
        total=event.duration,
        count=1,
    )


def add_event_to_stats(minute_stats, event):
    minute_stats.total += event.duration
    minute_stats.count += 1


def process_line(line):
    try:
        ob = json.loads(line)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}") from e

    try:
        return Event(
            timestamp=datetime.fromisoformat(ob["timestamp"]),
            duration=ob["duration"],
            event_name=ob["event_name"],
        )
    except KeyError as e:
        raise ValueError(f"Missing field: {e}") from e
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid field value: {e}") from e

# Yield translation_delivered events from an open file
def iter_delivered_events(f):
    for line in f:
        event = process_line(line.rstrip())
        if event.event_name == "translation_delivered":
            yield event


def assign_event_to_minute(event):
    floored = event.timestamp.replace(second=0, microsecond=0)
    if event.timestamp == floored:
        return floored - timedelta(minutes=1)
    return floored


def print_window_avg(window_stats, current_minute, out_f):
    avg_duration = window_stats.average()

    average_delivery_time = avg_duration
    if (
        isinstance(average_delivery_time, float)
        and average_delivery_time.is_integer()
    ):
        average_delivery_time = int(average_delivery_time)

    output = {
        "date": current_minute.strftime("%Y-%m-%d %H:%M:%S"),
        "average_delivery_time": average_delivery_time,
    }
    out_f.write(json.dumps(output) + "\n")


def close_minute(
    window_stats, minute_stats, current_minute, window, starting_output_minute, out_f,
):
    if current_minute >= starting_output_minute:
        print_window_avg(window_stats, current_minute, out_f)

    window_stats.append(minute_stats, window)


def process_file(input_path, output_path, window_size=10):
    if input_path.stat().st_size == 0:
        print(f"Error reading {input_path}: file is empty")
        return

    window_stats = WindowStats(buckets=deque())
    try:
        with input_path.open("r", encoding="utf-8") as f, output_path.open("w", encoding="utf-8") as out_f:
            events = iter_delivered_events(f)

            first_event = next(events, None)
            if first_event is None:
                print(f"Error reading {input_path}: no translation_delivered events found")
                return

            starting_output_minute = first_event.timestamp.replace(second=0, microsecond=0)

            current_minute = assign_event_to_minute(first_event)
            current_minute_stats = event_stats(first_event)

            for event in events:
                event_minute = assign_event_to_minute(event)
                # If the event shares the minute with the one before it, put it in the same bucket
                # if it doesn't, the minute bucket is complete so we can output its average and add it to the queue
                # and start a new minute bucket
                if event_minute == current_minute:
                    add_event_to_stats(current_minute_stats, event)
                else:
                    close_minute(
                        window_stats,
                        current_minute_stats,
                        current_minute,
                        window_size,
                        starting_output_minute,
                        out_f,
                    )
                    current_minute += timedelta(minutes=1)

                    # Add empty minute buckets between the previous event minute and this event minute
                    while current_minute < event_minute:
                        close_minute(
                            window_stats,
                            MinuteStats(total=0, count=0),
                            current_minute,
                            window_size,
                            starting_output_minute,
                            out_f,
                        )
                        current_minute += timedelta(minutes=1)

                    # Start the new event's minute bucket.
                    current_minute_stats = event_stats(event)

            # print the queue up to the second to last minute bucket and close the last bucket
            close_minute(
                window_stats,
                current_minute_stats,
                current_minute,
                window_size,
                starting_output_minute,
                out_f,
            )
            # force printing the window, with the last added bucket to the queue as if it just closed
            print_window_avg(window_stats, current_minute + timedelta(minutes=1), out_f)

    except Exception as e:
        print(f"Error reading {input_path}: {e}")


def positive_int(value):
    n = int(value)
    if n <= 0:
        raise argparse.ArgumentTypeError(f"window_size must be a positive integer, got {n}")
    return n


def existing_file(value):
    path = Path(value)
    if not path.exists():
        raise argparse.ArgumentTypeError(f"file not found: {value}")
    if not path.is_file():
        raise argparse.ArgumentTypeError(f"not a file: {value}")
    return path

def is_a_file(value):
    path = Path(value)
    if path.exists() and not path.is_file():
        raise argparse.ArgumentTypeError(f"not a file: {value}")

    return path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Compute the moving average of the translation delivery time for the last minutes. By default outputs a file named 'averages.jsonl'"
    )
    parser.add_argument(
        "--input_file",
        required=True,
        type=existing_file,
        help="Path to the input file.",
    )
    parser.add_argument(
        "--window_size",
        type=positive_int,
        default=10,
        help="Number of previous minutes to consider for computing the moving average (must be positive).",
    )

    parser.add_argument(
        "--output_file",
        type=is_a_file,
        default=None,
        help="Optional path to the output file",
    )

    return parser.parse_args()

def main():
    args = parse_args()

    if args.output_file is not None:
        output_file = args.output_file
    else:
        output_file = Path.cwd() / "averages.jsonl"
        if output_file.exists():
            random_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = Path.cwd() / f"averages_{random_suffix}.jsonl"

    process_file(args.input_file, output_file, args.window_size)

if __name__ == "__main__":
    main()