# Install the integrated toolkit

Native decomposition is opt-in while the toolkit release criteria remain pending.
From a checkout, run `bash install.sh --toolkit --target /path/to/project`.
This installs the CLI, matching TaskMesh helper, four harness skills, and a private
Python 3.11+ environment. Core gate operations retain the Bash 3.2 floor.
Existing `--copy`, `--symlink`, `--global`, `--no-bin`, and `--with-mesh` modes remain.
`--toolkit --no-bin` is invalid because managed recipes require the CLI and Mesh.

For an existing checkout, use `taskspec setup decompose`. Dependencies and all
accepted package hashes are pinned in `src/decompose/requirements.lock`; no global
Python packages are installed. Interrupted replacement retains the previous runtime.
Inspect it before removing a failed staging directory. `taskspec --dry-run setup
decompose` reports the exact destination and dependency-lock digest.

Verify `taskspec doctor`, `taskspec mesh doctor`, `taskspec recipe list`, and
`taskspec guide decomposition`. Set up repository signing separately with
`taskspec setup signing`; installation never creates provider credentials.
