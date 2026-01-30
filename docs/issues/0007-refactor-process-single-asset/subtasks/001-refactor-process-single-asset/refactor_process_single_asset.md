# Refactor: process_single_asset

Este documento describe la primera refactorización registrada sobre el proceso de asset en el sistema. Aquí se documentan los objetivos, el diseño y los cambios realizados para mejorar la mantenibilidad y robustez del flujo principal de procesamiento de assets.

---

# Proposed Refactoring: `immich_autotag/assets/process_single_asset.py`

# Mapping table: symbol, current file and destination

| Class/Method/Function                  | Current File                                      | Proposed Destination File                                 | Private? |
|---------------------------------------|-----------------------------------------------------|----------------------------------------------------------|-----------|
| DuplicateAlbumsInfo                   | assets/process_single_asset.py                      | assets/duplicates/_duplicate_albums_info.py               | Yes        |
| get_album_from_duplicates             | assets/process_single_asset.py                      | assets/duplicates/_get_album_from_duplicates.py           | Yes        |
| AlbumDecision                         | assets/process_single_asset.py                      | assets/albums/album_decision.py                           | No        |
| decide_album_for_asset                | assets/process_single_asset.py                      | assets/albums/decide_album_for_asset.py                   | No        |
| analyze_and_assign_album              | assets/process_single_asset.py                      | assets/albums/analyze_and_assign_album.py                 | No        |
| _process_album_detection              | assets/process_single_asset.py                      | assets/albums/_process_album_detection.py                 | Yes        |
| analyze_duplicate_classification_tags  | assets/duplicate_tag_logic/analyze_duplicate_classification_tags.py | (no change)                                 | No        |
| process_single_asset                  | assets/process_single_asset.py                      | assets/process/process_single_asset.py                    | No        |
| validate_and_update_asset_classification | assets/asset_validation.py                        | assets/validation/validate_and_update_asset_classification.py | No        |
| log_execution_parameters              | assets/process_assets.py                            | assets/process/log_execution_parameters.py                | No        |
| fetch_total_assets                    | assets/process_assets.py                            | assets/process/fetch_total_assets.py                      | No        |
| resolve_checkpoint                    | assets/process_assets.py                            | assets/process/resolve_checkpoint.py                      | No        |
| register_execution_parameters         | assets/process_assets.py                            | assets/process/register_execution_parameters.py            | No        |
| perf_log                              | assets/process_assets.py                            | assets/process/perf_log.py                                | No        |
| process_assets_threadpool             | assets/process_assets.py                            | assets/process/process_assets_threadpool.py                | No        |
| process_assets_sequential             | assets/process_assets.py                            | assets/process/process_assets_sequential.py                | No        |
| log_final_summary                     | assets/process_assets.py                            | assets/process/log_final_summary.py                        | No        |
| process_assets                        | assets/process_assets.py                            | assets/process/process_assets.py                           | No        |

# Execution plan for progressive asset refactoring

The goal is to move symbols one by one, testing after each move to minimize conflicts and ensure everything continues to work. The proposed order prioritizes dependencies and minimizes the risk of breakage.

## Table of symbols to refactor

| Order | Symbol/File                       | Action                                                                 |
|-------|----------------------------------------|------------------------------------------------------------------------|
| 1     | DuplicateAlbumsInfo                    | Move class to _duplicate_albums_info.py and update imports           |
| 2     | get_album_from_duplicates              | Move function to _get_album_from_duplicates.py and update imports     |
| 3     | AlbumDecision                          | Move class to album_decision.py and update imports                   |
| 4     | decide_album_for_asset                 | Move function to decide_album_for_asset.py and update imports         |
| 5     | analyze_and_assign_album               | Move function to analyze_and_assign_album.py and update imports       |
| 6     | _process_album_detection               | Move function to _process_album_detection.py and update imports       |
| 7     | process_single_asset                   | Move function to process_single_asset.py and update imports           |
| 8     | validate_and_update_asset_classification | Move function to validate_and_update_asset_classification.py and update imports |
| 9     | log_execution_parameters               | Move function to log_execution_parameters.py and update imports       |
| 10    | fetch_total_assets                     | Move function to fetch_total_assets.py and update imports             |
| 11    | resolve_checkpoint                     | Move function to resolve_checkpoint.py and update imports             |
| 12    | register_execution_parameters          | Move function to register_execution_parameters.py and update imports  |
| 13    | perf_log                               | Move function to perf_log.py and update imports                       |
| 14    | process_assets_threadpool              | Move function to process_assets_threadpool.py and update imports      |
| 15    | process_assets_sequential              | Move function to process_assets_sequential.py and update imports      |
| 16    | log_final_summary                      | Move function to log_final_summary.py and update imports              |
| 17    | process_assets                         | Move function to process_assets.py and update imports                 |

**Recommendations:**
- After each move, run the tests or test the relevant functionality.
- Update imports in all affected modules after each step.
- If a function depends on another that hasn't been moved yet, move the dependency first.
- Keep the original files until everything is tested, then clean up.

**Order strategy:**
- First move classes and functions that don't depend on others (private and utility).

---

Then, move functions that depend on the previous ones.
Finally, move the main functions (`process_single_asset`, `process_assets_sequential`, `process_assets_threadpool`, `process_assets`).
Test after each step to ensure the application never stops working.

**Notes:**
- Files marked as "Yes" in the "Private?" column should have an initial underscore in the file name and in the function/class name.
- The rest are part of the public API of the package or subpackage.
- You can adjust based on actual usage in the project.

# Execution plan for process_single_asset.py refactor

The goal is to move symbols one by one, testing after each move to minimize conflicts and ensure everything continues to work.

| Order | Symbol/File                       | Action                                                                 |
|-------|----------------------------------------|------------------------------------------------------------------------|
| 1     | DuplicateAlbumsInfo                    | Move class to _duplicate_albums_info.py and update imports           |
| 2     | get_album_from_duplicates              | Move function to _get_album_from_duplicates.py and update imports     |
| 3     | AlbumDecision                          | Move class to album_decision.py and update imports                   |
| 4     | decide_album_for_asset                 | Move function to decide_album_for_asset.py and update imports         |
| 5     | analyze_and_assign_album               | Move function to analyze_and_assign_album.py and update imports       |
| 6     | _process_album_detection               | Move function to _process_album_detection.py and update imports       |
| 7     | process_single_asset                   | Move function to process_single_asset.py and update imports           |
| 8     | validate_and_update_asset_classification | Move function to validate_and_update_asset_classification.py and update imports |

**Recommendations:**
- After each move, run the tests or test the relevant functionality.
- Update imports in all affected modules after each step.
- If a function depends on another that hasn't been moved yet, move the dependency first.
- Keep the original files until everything is tested, then clean up.

Do you want me to prepare the first move (DuplicateAlbumsInfo) and its import updates?

# Complementary refactoring: simplification of process_assets

The `process_assets` method in `assets/process_assets.py` is too large and difficult to maintain. It is proposed to divide it into sub-functions with clear responsibilities:

| Suggested sub-function                | Main responsibility                                                                 |
|-------------------------------------|------------------------------------------------------------------------------------------|
| `log_execution_parameters`          | Log execution and configuration parameters                                      |
| `fetch_total_assets`                | Query and record the total available assets                                     |
| `resolve_checkpoint`                | Calculate `last_processed_id` and `skip_n` according to resume mode                     |
| `register_execution_parameters`     | Save to statistics: total_assets, max_assets, skip_n                                |
| `process_assets_threadpool`         | Process assets using ThreadPoolExecutor                                                |
| `process_assets_sequential`         | Process assets sequentially (with checkpoint/resume and statistics)                   |
| `log_final_summary`                 | Log final summary, total time, and flush reports                                 |

### Suggested structure

```python
def process_assets(context: ImmichContext, max_assets: int | None = None) -> None:
	log_execution_parameters()
	total_assets = fetch_total_assets(context)
	last_processed_id, skip_n = resolve_checkpoint()
	register_execution_parameters(total_assets, max_assets, skip_n)
	if USE_THREADPOOL:
		process_assets_threadpool(context, max_assets)
	else:
		process_assets_sequential(context, max_assets, skip_n, last_processed_id)
	log_final_summary()
```

- Each sub-function can be defined as internal or external as appropriate.
- The main body is reduced to a clear sequence of steps.
- Logging, statistics, and error control code is encapsulated in small, reusable functions.

**Recommendation:**
- This refactor is complementary to the modularization plan for process_single_asset.py and can be addressed in parallel.
- After applying both, the asset processing flow will be much more maintainable and scalable.

