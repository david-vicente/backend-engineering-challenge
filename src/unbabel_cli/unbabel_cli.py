import argparse
from pathlib import Path


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
    print(args.input_file, args.window_size)

if __name__ == "__main__":
    main()