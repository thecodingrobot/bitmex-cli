#/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

docker build -t bitmex:latest $SCRIPT_DIR && \
docker run --rm \
  -it bitmex:latest \
  $*
