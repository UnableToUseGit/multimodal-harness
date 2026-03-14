#!/usr/bin/env bash
set -euo pipefail

PYTHONPATH=src python3 -m compileall src/video_atlas
PYTHONPATH=src python3 -m video_atlas.cli check-import
PYTHONPATH=src python3 -m unittest discover -s tests
