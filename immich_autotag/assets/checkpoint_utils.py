import os

from typeguard import typechecked

CHECKPOINT_FILE = ".autotag_checkpoint"


@typechecked
def load_checkpoint() -> tuple[str | None, int]:
    """
    Returns (last_processed_id, count) or (None, 0) if no checkpoint.
    """
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r") as f:
            line = f.read().strip()
            if not line:
                return None, 0
            if "," in line:
                asset_id, count = line.split(",", 1)
                try:
                    return asset_id, int(count)
                except Exception:
                    return asset_id, 0
            else:
                # legacy: only id stored
                return line, 0
    return None, 0


@typechecked
def save_checkpoint(asset_id: str, count: int) -> None:
    with open(CHECKPOINT_FILE, "w") as f:
        f.write(f"{asset_id},{count}")


@typechecked
def delete_checkpoint() -> None:
    if os.path.exists(CHECKPOINT_FILE):
        try:
            os.remove(CHECKPOINT_FILE)
            print(
                f"[CHECKPOINT] Checkpoint file '{CHECKPOINT_FILE}' deleted after successful run."
            )
        except Exception as e:
            print(f"[WARN] Could not delete checkpoint file '{CHECKPOINT_FILE}': {e}")
