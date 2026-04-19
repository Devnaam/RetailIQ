"""Dataset download helpers for RetailIQ."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from retailiq.config import DATA_DIR
from retailiq.pipeline.ingest import REQUIRED_FILES


@dataclass(frozen=True)
class DownloadResult:
    """Summary of a Kaggle dataset download."""

    source_path: Path
    data_dir: Path
    copied_files: list[str]


def download_olist_with_kagglehub(data_dir: Path = DATA_DIR) -> DownloadResult:
    """Download the Olist dataset with KaggleHub and copy required CSVs into data_dir."""

    try:
        import kagglehub
    except ImportError as exc:
        raise RuntimeError("Install kagglehub first: pip install kagglehub") from exc

    source_path = Path(kagglehub.dataset_download("olistbr/brazilian-ecommerce"))
    data_dir.mkdir(parents=True, exist_ok=True)

    copied: list[str] = []
    for file_name in REQUIRED_FILES.values():
        source_file = source_path / file_name
        if not source_file.exists():
            matches = list(source_path.rglob(file_name))
            if not matches:
                raise FileNotFoundError(f"KaggleHub download did not include {file_name}")
            source_file = matches[0]
        shutil.copy2(source_file, data_dir / file_name)
        copied.append(file_name)

    return DownloadResult(source_path=source_path, data_dir=data_dir, copied_files=copied)


if __name__ == "__main__":
    result = download_olist_with_kagglehub()
    print(f"Downloaded from: {result.source_path}")
    print(f"Copied to: {result.data_dir}")
    print("Files:")
    for file_name in result.copied_files:
        print(f"- {file_name}")
