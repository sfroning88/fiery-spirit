#!/usr/bin/env python3
"""
Author: Sean Froning
Created Date: 11.10.2026
Ops function for volcanic states
"""

import csv
import os
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv
from datasets import ClassLabel, Dataset, DatasetDict, Features, Value

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

_SOURCE_DIR = Path.home() / "Downloads" / "volcanic-states"
_OUTPUT_DIR = Path.home() / "Downloads" / "volcanic-states-hf"
_HF_REPO = "sfroning88/Volcanic-States"
_SEED = 42
_LABEL_NAMES = ["green", "yellow", "orange", "red"]
_REQUIRED = (
    "prompt",
    "reference",
    "label",
    "citation",
    "published_at",
    "chunk_index",
    "volcano_id",
)
_FEATURES = Features(
    {
        "prompt": Value("string"),
        "reference": Value("string"),
        "label": ClassLabel(names=_LABEL_NAMES),
        "citation": Value("string"),
        "published_at": Value("string"),
        "chunk_index": Value("int32"),
        "volcano_id": Value("string"),
    }
)
_DATASET_CARD = """\
---
license: cc-by-nc-3.0
task_categories:
  - text-classification
pretty_name: Volcanic states
---

# Volcanic states

Passages are one prompt and one reference sentence labeled with a technical alert
color (`green`, `yellow`, `orange`, `red`). `published_at` is the report timestamp,
`chunk_index` distinguishes sentences from the same report, and `volcano_id` is the
catalog slug. Rows come from `volcanic-states.csv`.

Cite the original reports. This Hub copy is for reproducible ingest only.
"""


def _load_rows(csv_path: Path) -> Dict[str, List[object]]:
    if not csv_path.is_file():
        raise FileNotFoundError(f"missing {csv_path}")
    prompts: List[str] = []
    references: List[str] = []
    labels: List[str] = []
    citations: List[str] = []
    published: List[str] = []
    chunks: List[int] = []
    volcanoes: List[str] = []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = [name for name in _REQUIRED if name not in (reader.fieldnames or [])]
        if missing:
            raise RuntimeError(f"{csv_path.name} missing columns {missing}")
        for line_number, row in enumerate(reader, start=2):
            label = (row.get("label") or "").strip().lower()
            if label not in _LABEL_NAMES:
                raise RuntimeError(
                    f"{csv_path.name}:{line_number} invalid label {label!r}"
                )
            prompt = (row.get("prompt") or "").strip()
            reference = (row.get("reference") or "").strip()
            citation = (row.get("citation") or "").strip()
            published_at = (row.get("published_at") or "").strip()
            if not prompt or not reference or not citation or not published_at:
                raise RuntimeError(f"{csv_path.name}:{line_number} empty required text")
            try:
                chunk_index = int((row.get("chunk_index") or "").strip())
            except ValueError as err:
                raise RuntimeError(
                    f"{csv_path.name}:{line_number} invalid chunk_index"
                ) from err
            prompts.append(prompt)
            references.append(reference)
            labels.append(label)
            citations.append(citation)
            published.append(published_at)
            chunks.append(chunk_index)
            volcanoes.append((row.get("volcano_id") or "").strip())
    if not prompts:
        raise RuntimeError(f"{csv_path.name} has no rows")
    return {
        "prompt": prompts,
        "reference": references,
        "label": labels,
        "citation": citations,
        "published_at": published,
        "chunk_index": chunks,
        "volcano_id": volcanoes,
    }


def _stratified_splits(dataset: Dataset) -> DatasetDict:
    first = dataset.train_test_split(
        test_size=0.30,
        seed=_SEED,
        stratify_by_column="label",
    )
    second = first["test"].train_test_split(
        test_size=0.50,
        seed=_SEED,
        stratify_by_column="label",
    )
    return DatasetDict(
        {
            "train": first["train"],
            "validation": second["train"],
            "test": second["test"],
        }
    )


def _can_stratify(dataset: Dataset) -> bool:
    if len(dataset) < 10:
        return False
    counts = {label: 0 for label in _LABEL_NAMES}
    for label in dataset["label"]:
        counts[_LABEL_NAMES[int(label)]] += 1
    present = [count for count in counts.values() if count]
    return bool(present) and min(present) >= 2


def _assign_splits(dataset: Dataset) -> DatasetDict:
    if _can_stratify(dataset):
        return _stratified_splits(dataset)
    ordered = dataset.shuffle(seed=_SEED)
    count = len(ordered)
    if count < 3:
        raise RuntimeError("need at least 3 rows to fill train, validation, and test")
    return DatasetDict(
        {
            "train": ordered.select(range(0, count - 2)),
            "validation": ordered.select([count - 2]),
            "test": ordered.select([count - 1]),
        }
    )


def _print_counts(splits: DatasetDict) -> None:
    for name, split in splits.items():
        counts = {label: 0 for label in _LABEL_NAMES}
        for label in split["label"]:
            counts[_LABEL_NAMES[int(label)]] += 1
        print(f"{name}: {len(split)} {counts}")


def main() -> None:
    rows = _load_rows(_SOURCE_DIR / "volcanic-states.csv")
    dataset = Dataset.from_dict(rows, features=_FEATURES)
    splits = _assign_splits(dataset)
    _print_counts(splits)
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (_OUTPUT_DIR / "README.md").write_text(_DATASET_CARD, encoding="utf-8")
    splits.save_to_disk(str(_OUTPUT_DIR / "dataset"))
    token = os.getenv("HF_TOKEN")
    if not token:
        raise RuntimeError("HF_TOKEN not configured")
    splits.push_to_hub(
        _HF_REPO,
        token=token,
        commit_message="Add risk classifications from volcanic states",
    )
    print(f"source dir {_SOURCE_DIR}")
    print(f"saved {_OUTPUT_DIR / 'dataset'}")
    print(f"pushed {_HF_REPO}")


if __name__ == "__main__":
    main()
