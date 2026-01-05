"""
Checkpoint utilities (deprecated): now use statistics system.
All functions are redirected to the new statistics manager for backward compatibility.
"""

from immich_autotag.statistics.checkpoint_compat import (delete_checkpoint,
                                                         load_checkpoint,
                                                         save_checkpoint)
