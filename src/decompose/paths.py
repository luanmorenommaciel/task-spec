"""One validated initiative namespace per CLI process."""
import os
import re
INITIATIVE = os.environ.get("TASKSPEC_INITIATIVE", "default")
if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}", INITIATIVE):
    raise ValueError("initiative must be a lowercase identifier, at most 80 characters")
PLAN_DIR = "tasks/.plans/" + INITIATIVE
