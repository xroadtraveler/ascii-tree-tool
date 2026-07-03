# [10000] Constants and defaults

"""Application-level configuration persistence for ascii-tree-tool.

Loads and saves user preferences (Phase 2: filter checkbox state) to a
platform-appropriate config directory. Uses platformdirs to resolve
%LOCALAPPDATA%\\ascii-tree-tool\\ on Windows and ~/.config/ascii-tree-tool/
on Linux. Fail-soft: I/O errors and schema mismatches log a warning and
return defaults; never raises.
"""

import copy
import json
import logging
from pathlib import Path
from typing import Any

from platformdirs import user_config_dir


logger = logging.getLogger(__name__)


# [100] Schema constants

APP_NAME = "ascii-tree-tool"
CONFIG_FILENAME = "config.json"
SCHEMA_VERSION = 1

DEFAULT_CONFIG: dict[str, Any] = {
    "schema_version": SCHEMA_VERSION,
    "filters": {
        "exclude_git": True,
        "exclude_pycache": True,
        "exclude_venv": True,
    },
}

# [-----END [100]-----]


# [20000] Internal helpers

# [010] resolve_config_path
# [SCOPE] returns the full Path to config.json in the platform-appropriate config 
#         directory; does not create directories or files
# [OUT-OF-SCOPE] file I/O, directory creation, config parsing

def resolve_config_path() -> Path:

    # [001] delegate to platformdirs with appauthor=False for flat layout
    config_dir = Path(user_config_dir(APP_NAME, appauthor=False))
    return config_dir / CONFIG_FILENAME
    # [-----END [001]-----]

# [-----END [010]-----]


# [020] _copy_defaults
# [SCOPE] returns an independent deep copy of DEFAULT_CONFIG for caller mutation
# [OUT-OF-SCOPE] I/O, mutation of DEFAULT_CONFIG

def _copy_defaults() -> dict[str, Any]:

    # [001] deepcopy to protect DEFAULT_CONFIG from downstream mutation
    return copy.deepcopy(DEFAULT_CONFIG)
    # [-----END [001]-----]

# [-----END [020]-----]


# [030] _merge_with_defaults
# [SCOPE] returns a config dict where any missing top-level keys and any missing 
#         sub-keys in dict-valued top-level fields are filled from DEFAULT_CONFIG
# [OUT-OF-SCOPE] I/O, deep-nested merging beyond one level, schema validation

def _merge_with_defaults(loaded: dict[str, Any]) -> dict[str, Any]:

    # [001] start from defaults so any missing top-level keys are present
    result = _copy_defaults()
    # [-----END [001]-----]

    # [002] overlay loaded values, dict-merging one level deep for dict-valued keys
    for key, value in loaded.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            merged = dict(result[key])
            merged.update(value)
            result[key] = merged
        else:
            result[key] = value
    # [-----END [002]-----]

    return result

# [-----END [030]-----]


# [30000] Public load/save API

# [010] load_config
# [SCOPE] reads config.json from the platform config directory, validates schema 
#         version, merges with defaults, returns a complete config dict; fail-soft 
#         on all I/O and parse errors
# [OUT-OF-SCOPE] writing to disk, network I/O, mutating DEFAULT_CONFIG, raising 
#                exceptions

def load_config() -> dict[str, Any]:

    config_path = resolve_config_path()

    # [001] fresh-install path: no file yet, return defaults silently
    if not config_path.exists():
        return _copy_defaults()
    # [-----END [001]-----]

    # [002] read and parse; fall back to defaults on any I/O or parse error
    try:
        raw = config_path.read_text(encoding="utf-8")
        parsed = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning(
            "Failed to load config from %s: %s. Using defaults.",
            config_path, exc,
        )
        return _copy_defaults()
    # [-----END [002]-----]

    # [003] reject non-dict roots
    if not isinstance(parsed, dict):
        logger.warning(
            "Config at %s is not a JSON object (got %s). Using defaults.",
            config_path, type(parsed).__name__,
        )
        return _copy_defaults()
    # [-----END [003]-----]

    # [004] validate schema version
    if parsed.get("schema_version") != SCHEMA_VERSION:
        logger.warning(
            "Config at %s has unsupported schema_version=%r (expected %d). Using defaults.",
            config_path, parsed.get("schema_version"), SCHEMA_VERSION,
        )
        return _copy_defaults()
    # [-----END [004]-----]

    # [005] merge with defaults so any missing keys get default values
    return _merge_with_defaults(parsed)
    # [-----END [005]-----]

# [-----END [010]-----]


# [020] save_config
# [SCOPE] serializes the given config dict as JSON and writes it to the platform 
#         config directory, creating parent directories as needed; fail-soft on 
#         all I/O errors
# [OUT-OF-SCOPE] validation of config contents, migration, backup, raising exceptions

def save_config(config: dict[str, Any]) -> None:

    config_path = resolve_config_path()

    # [001] ensure parent directory exists
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        logger.warning(
            "Failed to create config directory %s: %s. Config not saved.",
            config_path.parent, exc,
        )
        return
    # [-----END [001]-----]

    # [002] serialize and write
    try:
        serialized = json.dumps(config, indent=2, sort_keys=True)
        config_path.write_text(serialized, encoding="utf-8")
        logger.info("Saved config to %s", config_path)
    except (OSError, TypeError, ValueError) as exc:
        logger.warning(
            "Failed to save config to %s: %s. Config not saved.",
            config_path, exc,
        )
    # [-----END [002]-----]

# [-----END [020]-----]