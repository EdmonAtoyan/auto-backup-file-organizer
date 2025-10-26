# Auto-backup File Organizer

A simple, job-ready Python tool that organizes files from a source directory into a destination backup folder, grouped by **category** (Images, Documents, Audio, Video, Archives, Code, CAD, Other) and optionally by **date (YYYY-MM-DD)**. It can **move** or **copy** files and prints a clear summary at the end.

## Features
- Recursive scan of a source directory
- Category-based sorting by file extension
- Optional per-day folders (`--by-date`)
- Move (default) or copy mode (`--copy`)
- Dry-run simulation (`--dry-run`)
- Optional duplicate skipping via SHA1 (`--skip-duplicates`)
- Collision-safe filenames: adds `(1)`, `(2)`, … if needed

## Quick Start

```bash
python3 auto_backup_file_organizer.py \
  --source /path/to/Downloads \
  --dest   /path/to/Backup \
  --by-date \
  --skip-duplicates
