# Unbabel CLI

Small command line app that reads translation events from a JSONL file and writes the moving average delivery time per minute.

The CLI command is:

```sh
unbabel_cli --input_file <events.jsonl> --window_size <minutes>
```

By default, the app writes `averages.jsonl` in the current directory. Use `--output_file` to choose a different file.

## Requirements

The CLI has no runtime dependencies other than Python 3.7 or newer.

There are no required development dependencies. The test suite runs with Python's built-in `unittest` module. `pytest` is optional if you prefer that test runner.

## Install on Linux

From the project root:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

## Run on Linux

```sh
source .venv/bin/activate
unbabel_cli --input_file tests/data/test-input.jsonl --window_size 10
```

## Run as a Standalone Script on Linux

The CLI is a single Python file and has no runtime dependencies other than Python 3.7 or newer, so it can also be copied and run without installing the package:

```sh
cp src/unbabel_cli/unbabel_cli.py ./unbabel_cli
chmod +x ./unbabel_cli
./unbabel_cli --input_file tests/data/test-input.jsonl --window_size 10
```

## Run Tests on Linux

```sh
source .venv/bin/activate
python -m unittest discover -s tests
```

If you prefer `pytest`, install it in the virtual environment and run:

```sh
source .venv/bin/activate
python -m pip install pytest
pytest
```

## Docker on Linux

Build the image:

```sh
docker build -f Dockerfile -t unbabel-cli .
```

Create an output directory:

```sh
mkdir -p output
```

Run the CLI:

```sh
docker run --rm \
  --mount "type=bind,source=$(pwd)/tests/data,target=/input,readonly" \
  --mount "type=bind,source=$(pwd)/output,target=/output" \
  unbabel-cli --input_file /input/test-input.jsonl --window_size 10
```

The output file is written to `output/averages.jsonl`.

## Docker on Windows

Run these commands in PowerShell from the project root.

Build the image:

```powershell
docker build -f Dockerfile -t unbabel-cli .
```

Create an output directory:

```powershell
New-Item -ItemType Directory -Force -Path output
```

Run the CLI:

```powershell
docker run --rm `
  --mount "type=bind,source=${PWD}\tests\data,target=/input,readonly" `
  --mount "type=bind,source=${PWD}\output,target=/output" `
  unbabel-cli --input_file /input/test-input.jsonl --window_size 10
```

The output file is written to `output\averages.jsonl`.
