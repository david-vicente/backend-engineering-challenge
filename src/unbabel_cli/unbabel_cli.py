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


def process_line(line):
    ob = json.loads(line)
    event = Event(
        timestamp=datetime.fromisoformat(ob["timestamp"]),
        duration=ob["duration"]
    )
    return event

def assign_event_to_minute(event):
    floored = event.timestamp.replace(second=0, microsecond=0)
    if event.timestamp == floored:
        return floored - timedelta(minutes=1)
    return floored

def print_queue(queue, current_minute, output_path):
    with output_path.open("a", encoding="utf-8") as f:
        print(queue, file=f)


def process_file(input_path, output_path, window=10):
    queue = deque()
    try:
        with input_path.open("r", encoding="utf-8") as f:

            # process the first event to extract the starting minute.
            first_event = process_line(next(f).rstrip())

            starting_output_minute = first_event.timestamp.replace(second=0, microsecond=0)
            current_minute = assign_event_to_minute(first_event)
            events_list = [first_event]

            for line in f:
                event = process_line(line.rstrip())
                event_minute = assign_event_to_minute(event)
                # If the event shares the minute with the one before it, put it in the same bucket
                # if it doesn't, the minute bucket is complete so we can output its average and add it to the queue
                # and start a new minute bucket
                if event_minute == current_minute:
                    events_list.append(event)
                else:

                    if current_minute >= starting_output_minute:
                         print_queue(queue, current_minute, output_path)

                    queue.append(events_list)

                    if len(queue) > window:
                        queue.popleft()
                    current_minute += timedelta(minutes=1)

                    # Add empty minute buckets between the previous event minute and this event minute
                    while current_minute < event_minute:
                        if current_minute >= starting_output_minute:
                             print_queue(queue, current_minute, output_path)
                        queue.append([])
                        if len(queue) > window:
                            queue.popleft()
                        current_minute += timedelta(minutes=1)

                    # Start a new minute bucket with the current event
                    events_list = [event]
            # print window before closing the final bucket
            if current_minute >= starting_output_minute:
                print_queue(queue, current_minute, output_path)
            # add the last event bucket to the queue
            queue.append(events_list)
            if len(queue) > window:
                queue.popleft()
            # force printing the window, with the last added bucket to the queue
            print_queue(queue, current_minute, output_path)
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