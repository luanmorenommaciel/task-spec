# Experimental mutation packs

These opt-in `MutationMatrix/v1` manifests exercise stack-specific falsifiers
through `taskspec eval-audit --mutations`. A pack is an experiment until its
patches apply to the target repository; it never changes the core acceptance
policy or grants authority.

The checked-in Python, JavaScript, Go, and Bash manifests are validated shape
examples. Copy the relevant manifest into the target repository and supply a
repository-specific patch at each declared path before running it. Paths are
relative to the manifest, may not traverse outside that directory, and IDs must
be unique. A missing or non-applicable patch makes the audit fail; it never
silently counts as a successful falsifier.
