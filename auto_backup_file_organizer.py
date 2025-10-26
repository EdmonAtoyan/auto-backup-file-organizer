
"""
Auto-backup File Organizer
- Scans a source directory
- Detects file type by extension
- Moves or copies files into category folders (and optional date folders)
- Prints a clear summary
"""

import argparse
import datetime as dt
import hashlib
import shutil
from pathlib import Path
from typing import Dict, Tuple, Optional

DEFAULT_CATEGORIES: Dict[str, str] = {
    # Images
    ".jpg": "Images", ".jpeg": "Images", ".png": "Images", ".gif": "Images",
    ".webp": "Images", ".tif": "Images", ".tiff": "Images", ".svg": "Images",
    # Documents
    ".pdf": "Documents", ".doc": "Documents", ".docx": "Documents",
    ".xls": "Documents", ".xlsx": "Documents", ".ppt": "Documents",
    ".pptx": "Documents", ".txt": "Documents", ".md": "Documents",
    ".rtf": "Documents",
    # Audio
    ".mp3": "Audio", ".wav": "Audio", ".flac": "Audio", ".aac": "Audio",
    # Video
    ".mp4": "Video", ".mov": "Video", ".avi": "Video", ".mkv": "Video", ".webm": "Video",
    # Archives
    ".zip": "Archives", ".rar": "Archives", ".7z": "Archives",
    ".tar": "Archives", ".gz": "Archives", ".bz2": "Archives",
    # Code / Config
    ".py": "Code", ".js": "Code", ".ts": "Code", ".java": "Code",
    ".cpp": "Code", ".c": "Code", ".cs": "Code", ".go": "Code",
    ".rb": "Code", ".php": "Code", ".sh": "Code", ".bat": "Code",
    ".ps1": "Code", ".json": "Code", ".yaml": "Code", ".yml": "Code",
    ".xml": "Code", ".html": "Code", ".css": "Code",
    # 3D / CAD / BIM
    ".dwg": "CAD", ".dxf": "CAD", ".rvt": "CAD", ".skp": "CAD",
    ".obj": "CAD", ".fbx": "CAD", ".dae": "CAD",
}

def file_sha1(path: Path, chunk_size: int = 1 << 20) -> str:
    """Return SHA1 of a file (used to avoid duplicate copies)."""
    h = hashlib.sha1()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()

def category_for(path: Path, categories: Dict[str, str]) -> str:
    """Infer category from extension; unknown -> 'Other'."""
    return categories.get(path.suffix.lower(), "Other")

def safe_destination(dest_root: Path, rel_dir: Path, name: str) -> Path:
    """
    Create a non-colliding destination path by suffixing '(1)', '(2)', ...
    if needed.
    """
    base = dest_root / rel_dir
    base.mkdir(parents=True, exist_ok=True)
    candidate = base / name
    if not candidate.exists():
        return candidate

    stem = candidate.stem
    suffix = candidate.suffix
    i = 1
    while True:
        alt = base / f"{stem} ({i}){suffix}"
        if not alt.exists():
            return alt
        i += 1

def move_or_copy(
    src: Path,
    dst: Path,
    copy_mode: bool,
    dry_run: bool
) -> None:
    action = "COPY" if copy_mode else "MOVE"
    if dry_run:
        print(f"[DRY-RUN] {action}: {src}  ->  {dst}")
        return
    if copy_mode:
        shutil.copy2(src, dst)
    else:
        shutil.move(str(src), str(dst))
    print(f"[OK] {action}: {src.name} -> {dst.relative_to(dst.parents[2]) if len(dst.parents) >= 2 else dst}")

def plan_rel_dir(category: str, use_date: bool, ext: str) -> Path:
    """
    Build relative destination subpath like:
    - 'Images/JPG/' or
    - 'Images/2025-10-26/JPG/' if use_date enabled
    """
    parts = [category]
    if use_date:
        parts.append(dt.date.today().isoformat())
      
    parts.append(ext.lstrip(".").upper() if ext else "MISC")
    return Path(*parts)

def organize(
    source: Path,
    dest: Path,
    copy_mode: bool,
    dry_run: bool,
    use_date: bool,
    skip_duplicates: bool,
    categories: Dict[str, str],
) -> Dict[str, int]:
    """
    Iterate source dir (non-recursive or recursive?), here we do recursive.
    """
    if not source.exists() or not source.is_dir():
        raise SystemExit(f"Source directory does not exist or is not a directory: {source}")

    counts = {"processed": 0, "moved": 0, "copied": 0, "skipped": 0}
    seen_hashes = set()

    for path in source.rglob("*"):
        if path.is_dir():
            continue
        try:
            path.relative_to(dest)
            counts["skipped"] += 1
            continue
        except ValueError:
            pass

        counts["processed"] += 1
        category = category_for(path, categories)
        rel_dir = plan_rel_dir(category, use_date, path.suffix.lower())
        final = safe_destination(dest, rel_dir, path.name)

        if skip_duplicates:
            try:
                digest = file_sha1(path)
            except Exception:
                digest = ""
            if digest and digest in seen_hashes:
                print(f"[SKIP] duplicate (sha1={digest[:8]}…): {path}")
                counts["skipped"] += 1
                continue
            if digest:
                seen_hashes.add(digest)

        move_or_copy(path, final, copy_mode, dry_run)
        if not dry_run:
            if copy_mode:
                counts["copied"] += 1
            else:
                counts["moved"] += 1

    return counts

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Organize and backup files by category (and date)."
    )
    p.add_argument("-s", "--source", type=Path, required=True, help="Source directory to scan (recursive).")
    p.add_argument("-d", "--dest", type=Path, required=True, help="Destination root directory.")
    p.add_argument("--copy", action="store_true", help="Copy files instead of moving them.")
    p.add_argument("--dry-run", action="store_true", help="Show what would happen without changing files.")
    p.add_argument("--by-date", action="store_true", help="Create date folder (YYYY-MM-DD) under each category.")
    p.add_argument("--skip-duplicates", action="store_true", help="Skip files that are byte-identical (by SHA1).")
    return p.parse_args()

def main() -> None:
    args = parse_args()
    counts = organize(
        source=args.source,
        dest=args.dest,
        copy_mode=args.copy,
        dry_run=args.dry_run,
        use_date=args.by_date,
        skip_duplicates=args.skip_duplicates,
        categories=DEFAULT_CATEGORIES,
    )
    print("\n--- Summary ---")
    for k, v in counts.items():
        print(f"{k}: {v}")

if __name__ == "__main__":
    main()
