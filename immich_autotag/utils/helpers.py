def print_perf(count, elapsed, total_assets=None):
    """
    Print performance statistics for asset processing.
    Args:
        count (int): Number of assets processed.
        elapsed (float): Elapsed time in seconds.
        total_assets (int, optional): Total number of assets to process.
    """
    avg = elapsed / count if count else 0
    if total_assets and count > 0:
        remaining = total_assets - count
        est_total = avg * total_assets
        est_remaining = est_total - elapsed
        percent = (count / total_assets) * 100
        print(
            f"[PERF] {count}/{total_assets} ({percent:.1f}%) assets processed. Avg: {avg:.3f} s. Est. remaining: {est_remaining/60:.1f}/{est_total/60:.1f} min"
        )
    else:
        print(f"[PERF] Processed {count} assets. Average per asset: {avg:.3f} s")
