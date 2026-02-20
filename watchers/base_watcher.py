"""Base Watcher class for Silver-tier AI Employee system.

All watcher scripts inherit from this base class to ensure consistent
behavior across the perception layer.
"""

import time
import logging
from pathlib import Path
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Any


class BaseWatcher(ABC):
    """Abstract base class for all watcher implementations.

    Watchers monitor external sources (Gmail, WhatsApp, file system) and
    create actionable .md files in the vault's Needs_Action/ folder for
    Claude Code to process.
    """

    def __init__(self, vault_path: str, check_interval: int = 60):
        """Initialize the watcher.

        Args:
            vault_path: Absolute path to Obsidian vault root
            check_interval: Seconds between checks (default 60)
        """
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.check_interval = check_interval
        self.logger = logging.getLogger(self.__class__.__name__)

        # Ensure Needs_Action folder exists
        self.needs_action.mkdir(parents=True, exist_ok=True)

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.vault_path / 'Logs' / f'{self.__class__.__name__.lower()}.log'),
                logging.StreamHandler()
            ]
        )

    @abstractmethod
    def check_for_updates(self) -> List[Any]:
        """Check external source for new items.

        Returns:
            List of new items to process (format specific to watcher type)
        """
        pass

    @abstractmethod
    def create_action_file(self, item: Any) -> Path:
        """Create .md file in Needs_Action folder.

        Args:
            item: Item to convert to action file

        Returns:
            Path to created file
        """
        pass

    def run(self):
        """Main loop: continuously check for updates and create action files.

        This runs indefinitely until interrupted (Ctrl+C) or process killed.
        Use a process manager (PM2, supervisord) for production deployment.
        """
        self.logger.info(f'Starting {self.__class__.__name__}')
        self.logger.info(f'Monitoring interval: {self.check_interval} seconds')
        self.logger.info(f'Vault path: {self.vault_path}')

        while True:
            try:
                items = self.check_for_updates()

                if items:
                    self.logger.info(f'Found {len(items)} new item(s)')
                    for item in items:
                        filepath = self.create_action_file(item)
                        self.logger.info(f'Created action file: {filepath.name}')
                else:
                    self.logger.debug('No new items found')

            except KeyboardInterrupt:
                self.logger.info('Received shutdown signal, stopping...')
                break
            except Exception as e:
                self.logger.error(f'Error in watch loop: {e}', exc_info=True)
                # Continue running despite errors (resilience)

            time.sleep(self.check_interval)

        self.logger.info(f'{self.__class__.__name__} stopped')

    def format_timestamp(self) -> str:
        """Generate ISO 8601 timestamp in PKT timezone.

        Returns:
            Timestamp string like '2026-02-15T10:30:00+05:00'
        """
        # PKT is UTC+5
        from datetime import timezone, timedelta
        pkt = timezone(timedelta(hours=5))
        return datetime.now(pkt).isoformat()
