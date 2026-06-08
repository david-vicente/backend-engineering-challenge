import argparse
import json
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

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


def process_file(input_path, output_path, window=10):
    try:
        with input_path.open("r", encoding="utf-8") as f:
            for line in f:
                event = process_line(line.rstrip())
                print(event)
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