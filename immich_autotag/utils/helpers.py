from typeguard import typechecked

@typechecked
def print_perf(count: int, elapsed: float, total_assets: int | None = None):
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
        # Formato de tiempo: si es más de 60 minutos, mostrar en horas
        def fmt_time(minutes: float) -> str:
            if minutes >= 60:
                return f"{minutes/60:.1f} h"
            else:
                return f"{minutes:.1f} min"
        print(
            f"[PERF] {count}/{total_assets} ({percent:.1f}%) assets processed. Avg: {avg:.3f} s. Est. remaining: {fmt_time(est_remaining/60)}/{fmt_time(est_total/60)}"
        )
    else:
        print(f"[PERF] Processed {count} assets. Average per asset: {avg:.3f} s")
