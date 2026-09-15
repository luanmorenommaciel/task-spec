#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" == --version ]]; then echo chat-fixture/1; exit 0; fi
exit 1
