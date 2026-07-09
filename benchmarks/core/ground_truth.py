"""Dataset manifest + ground-truth JSON loading, with suite-gating.

Format: plain JSON files under `datasets/<repo>/ground_truth/<kind>.json`,
gated by `datasets/<repo>/manifest.json`'s `suites` list. No schema library --
stdlib `json` load + a required-keys check.
"""

import json
from pathlib import Path

REQUIRED_MANIFEST_KEYS = ("repo", "commit", "schema_version", "suites")


class GroundTruthError(Exception):
    """Raised on a malformed manifest, missing ground-truth file, or ungated suite."""


def load_manifest(dataset_dir: Path) -> dict:
    """Load and validate `<dataset_dir>/manifest.json`.

    Raises GroundTruthError with a clear message if the file is missing, is
    not valid JSON, or is missing a required key. No silent empty-dict fallback.
    """
    path = Path(dataset_dir) / "manifest.json"
    if not path.exists():
        raise GroundTruthError(f"manifest.json not found in {dataset_dir}")
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise GroundTruthError(f"manifest.json in {dataset_dir} is not valid JSON: {e}") from e

    missing = [k for k in REQUIRED_MANIFEST_KEYS if k not in manifest]
    if missing:
        raise GroundTruthError(
            f"manifest.json in {dataset_dir} missing required keys: {missing}"
        )
    return manifest


def load_ground_truth(dataset_dir: Path, kind: str) -> dict | list:
    """Load `<dataset_dir>/ground_truth/<kind>.json`, gated by the manifest's `suites`.

    Raises GroundTruthError if:
    - the manifest doesn't list `kind` in its `suites` array (fail loud, not
      silent-empty -- a suite must be explicitly declared supported)
    - the ground-truth file doesn't exist
    - the ground-truth file isn't valid JSON
    """
    dataset_dir = Path(dataset_dir)
    manifest = load_manifest(dataset_dir)

    if kind not in manifest["suites"]:
        raise GroundTruthError(
            f"suite '{kind}' is not listed in {dataset_dir}/manifest.json's "
            f"'suites' ({manifest['suites']}) -- refusing to load ground truth "
            "for an ungated suite"
        )

    gt_path = dataset_dir / "ground_truth" / f"{kind}.json"
    if not gt_path.exists():
        raise GroundTruthError(
            f"suite '{kind}' is listed in manifest.json but "
            f"{gt_path} does not exist"
        )
    try:
        return json.loads(gt_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise GroundTruthError(f"{gt_path} is not valid JSON: {e}") from e
