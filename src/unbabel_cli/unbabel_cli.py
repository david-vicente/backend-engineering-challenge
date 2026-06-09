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


def process_line(line):
    ob = json.loads(line)
    event = Event(
        timestamp=datetime.fromisoformat(ob["timestamp"]),
        duration=ob["duration"],
        event_name=ob["event_name"],
    )
    return event


def assign_event_to_minute(event):
    floored = event.timestamp.replace(second=0, microsecond=0)
    if event.timestamp == floored:
        return floored - timedelta(minutes=1)
    return floored


def print_window_avg(queue, current_minute, output_path):
    all_events = [e for bucket in queue for e in bucket]
    avg_duration = (
        sum(e.duration for e in all_events) / len(all_events) if all_events else 0
    )
    if isinstance(avg_duration, float) and avg_duration.is_integer():
        avg_duration = int(avg_duration)

    output = {
        "date": current_minute.strftime("%Y-%m-%d %H:%M:%S"),
        "average_delivery_time": avg_duration,
    }
    with output_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(output) + "\n")


def close_minute(
    queue, events_list, current_minute, window, starting_output_minute, output_path
):
    if current_minute >= starting_output_minute:
        print_window_avg(queue, current_minute, output_path)
    queue.append(events_list)
    if len(queue) > window:
        queue.popleft()


def process_file(input_path, output_path, window=10):
    queue = deque()
    try:
        with input_path.open("r", encoding="utf-8") as f:

            # Process the first delivered event to extract the starting minute.
            first_event = None
            for line in f:
                event = process_line(line.rstrip())
                if event.event_name != "translation_delivered":
                    continue
                first_event = event
                break

            if first_event is None:
                return

            starting_output_minute = first_event.timestamp.replace(second=0, microsecond=0)
            current_minute = assign_event_to_minute(first_event)
            events_list = [first_event]

            for line in f:
                event = process_line(line.rstrip())
                if event.event_name != "translation_delivered":
                    continue

                event_minute = assign_event_to_minute(event)
                # If the event shares the minute with the one before it, put it in the same bucket
                # if it doesn't, the minute bucket is complete so we can output its average and add it to the queue
                # and start a new minute bucket
                if event_minute == current_minute:
                    events_list.append(event)
                else:

                    close_minute(
                        queue,
                        events_list,
                        current_minute,
                        window,
                        starting_output_minute,
                        output_path,
                    )
                    current_minute += timedelta(minutes=1)

                    # Add empty minute buckets between the previous event minute and this event minute
                    while current_minute < event_minute:
                        close_minute(
                            queue,
                            [],
                            current_minute,
                            window,
                            starting_output_minute,
                            output_path,
                        )
                        current_minute += timedelta(minutes=1)

                    # Start a new minute bucket with the current event
                    events_list = [event]
            # print the queue up to the second to last minute bucket and close the last bucket
            close_minute(
                queue,
                events_list,
                current_minute,
                window,
                starting_output_minute,
                output_path,
            )
            # force printing the window, with the last added bucket to the queue as if it just closed
            print_window_avg(queue, current_minute + timedelta(minutes=1), output_path)
    except Exception as e:
        print(f"Error reading {input_path}: {e}")



def parse_args():
    parser = argparse.ArgumentParser(
        description="Compute the moving average of the translation delivery time for the last minutes."
    )
    parser.add_argument(
        "--input_file",
        required=True,
        type=Path,
        help="Path to the input file.",
    )
    parser.add_argument(
        "--window_size",
        type=int,
        default=10,
        help="Number of previous minutes to consider for computing the moving average.",
    )
    return parser.parse_args()

def main():
    args = parse_args()
    output_file = Path.cwd() / "averages.jsonl"

    process_file(args.input_file, output_file, args.window_size)

if __name__ == "__main__":
    main()
