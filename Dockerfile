FROM python:3.7-slim

WORKDIR /app

# 1. Upgrade system pip to a version that properly handles PEP 517
# and pin setuptools globally to a safe Python 3.7 variant.
RUN pip install --no-cache-dir --upgrade "pip>=22.0" "setuptools>=61.0.0,<=68.0.0" "wheel"

# 2. Copy project metadata first (better layer caching)
COPY pyproject.toml README.md ./

# 3. Copy source tree
COPY src/ ./src/

# 4. Create an output directory that can be bind-mounted from the host.
RUN mkdir -p /output

# 5. Install the CLI in editable mode.
# --no-build-isolation forces pip to use the safe setuptools we pinned in step 1
# instead of trying to spin up a temporary, unpredictable build container.
RUN pip install --no-cache-dir --no-build-isolation -e .

VOLUME ["/output"]

WORKDIR /output

ENTRYPOINT ["unbabel_cli"]
CMD ["--help"]
