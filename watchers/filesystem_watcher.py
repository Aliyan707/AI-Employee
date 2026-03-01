"""File System Watcher for Silver-tier AI Employee system.

Monitors a designated drop folder for new files and creates
FILE_*.md metadata files in Needs_Action/ for processing.
"""

import shutil
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent
from base_watcher import BaseWatcher


class DropFolderHandler(FileSystemEventHandler):
    """Handles file creation events in the drop folder."""

    def __init__(self, watcher: 'FileSystemWatcher'):
        """Initialize handler with reference to parent watcher.

        Args:
            watcher: Parent FileSystemWatcher instance
        """
        self.watcher = watcher
        self.logger = watcher.logger

    def on_created(self, event: FileCreatedEvent):
        """Handle file creation event.

        Args:
            event: Watchdog file created event
        """
        if event.is_directory:
            return

        source = Path(event.src_path)

        # Ignore temporary/system files
        if source.name.startswith('.') or source.name.startswith('~'):
            return

        self.logger.info(f'Detected new file: {source.name}')

        try:
            # Create action file
            self.watcher.create_action_file(source)
        except Exception as e:
            self.logger.error(f'Error processing file {source.name}: {e}')


class FileSystemWatcher(BaseWatcher):
    """Watches a drop folder for new files.

    When a file is dropped into the monitored folder, creates:
    1. Copy of the file in vault (optional)
    2. FILE_*.md metadata file in Needs_Action/
    """

    def __init__(self, vault_path: str, drop_folder: str, copy_files: bool = True):
        """Initialize file system watcher.

        Args:
            vault_path: Path to Obsidian vault
            drop_folder: Path to folder to monitor for new files
            copy_files: Whether to copy files into vault (default True)
        """
        # Don't use check_interval for filesystem watcher (event-driven)
        super().__init__(vault_path, check_interval=0)

        self.drop_folder = Path(drop_folder)
        self.copy_files = copy_files

        # Create drop folder if it doesn't exist
        self.drop_folder.mkdir(parents=True, exist_ok=True)

        # Create Files subfolder in vault if copying files
        if self.copy_files:
            self.files_folder = self.vault_path / 'Files'
            self.files_folder.mkdir(parents=True, exist_ok=True)

        # Setup watchdog observer
        self.observer = Observer()
        self.event_handler = DropFolderHandler(self)

        self.logger.info(f'Monitoring drop folder: {self.drop_folder}')

    def check_for_updates(self):
        """Not used for filesystem watcher (event-driven).

        Returns:
            Empty list
        """
        return []

    def create_action_file(self, source: Path) -> Path:
        """Create FILE_*.md metadata file for dropped file.

        Args:
            source: Path to the dropped file

        Returns:
            Path to created metadata file
        """
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_name = self._sanitize_filename(source.stem)

        # Copy file to vault if requested
        copied_path = None
        if self.copy_files:
            dest_name = f'{timestamp}_{source.name}'
            copied_path = self.files_folder / dest_name
            shutil.copy2(source, copied_path)
            self.logger.info(f'Copied file to vault: {copied_path}')

        # Create metadata file
        metadata_filename = f'FILE_{timestamp}_{safe_name}.md'
        metadata_path = self.needs_action / metadata_filename

        # Determine file type
        file_type = self._classify_file_type(source)

        # Create markdown content
        content = f'''---
type: file_drop
original_name: {source.name}
original_path: {source.absolute()}
size_bytes: {source.stat().st_size}
file_type: {file_type}
copied_to_vault: {copied_path if copied_path else 'false'}
received: {self.format_timestamp()}
status: pending
---

## File Details
- **Original Name**: {source.name}
- **Size**: {self._format_size(source.stat().st_size)}
- **Type**: {file_type}
- **Dropped**: {self.format_timestamp()}

## Vault Location
{f'File copied to: `{copied_path.relative_to(self.vault_path)}`' if copied_path else 'File not copied to vault'}

## Suggested Actions
- [ ] Review file content
- [ ] Process or extract information
- [ ] Archive or delete original
- [ ] Update relevant project files

## Notes
Created by FileSystem Watcher
'''

        metadata_path.write_text(content, encoding='utf-8')

        return metadata_path

    def _sanitize_filename(self, name: str) -> str:
        """Sanitize filename for use in markdown filename.

        Args:
            name: Original filename (without extension)

        Returns:
            Sanitized filename safe for filesystem
        """
        # Remove/replace problematic characters
        safe = name.replace(' ', '_')
        safe = ''.join(c for c in safe if c.isalnum() or c in '_-')
        return safe[:50]  # Limit length

    def _classify_file_type(self, filepath: Path) -> str:
        """Classify file type based on extension.

        Args:
            filepath: Path to file

        Returns:
            File type category
        """
        ext = filepath.suffix.lower()

        type_map = {
            '.pdf': 'document',
            '.doc': 'document',
            '.docx': 'document',
            '.txt': 'text',
            '.md': 'markdown',
            '.csv': 'spreadsheet',
            '.xlsx': 'spreadsheet',
            '.xls': 'spreadsheet',
            '.jpg': 'image',
            '.jpeg': 'image',
            '.png': 'image',
            '.gif': 'image',
            '.zip': 'archive',
            '.tar': 'archive',
            '.gz': 'archive',
        }

        return type_map.get(ext, 'unknown')

    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format.

        Args:
            size_bytes: File size in bytes

        Returns:
            Formatted size string (e.g., "1.5 MB")
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    def run(self):
        """Start watching the drop folder for file creation events."""
        self.logger.info(f'Starting {self.__class__.__name__}')
        self.logger.info(f'Monitoring: {self.drop_folder}')

        # Schedule observer
        self.observer.schedule(
            self.event_handler,
            str(self.drop_folder),
            recursive=False
        )

        # Start observer
        self.observer.start()
        self.logger.info('Observer started, watching for files...')

        try:
            # Keep running until interrupted
            self.observer.join()
        except KeyboardInterrupt:
            self.logger.info('Received shutdown signal, stopping...')
            self.observer.stop()
            self.observer.join()

        self.logger.info(f'{self.__class__.__name__} stopped')


if __name__ == '__main__':
    """Run filesystem watcher standalone for testing."""
    import sys

    if len(sys.argv) < 3:
        print('Usage: python filesystem_watcher.py <vault_path> <drop_folder>')
        sys.exit(1)

    vault_path = sys.argv[1]
    drop_folder = sys.argv[2]

    watcher = FileSystemWatcher(vault_path, drop_folder)
    watcher.run()
