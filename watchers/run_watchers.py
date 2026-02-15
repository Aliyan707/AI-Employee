#!/usr/bin/env python3
"""Launcher script for Silver-tier AI Employee watchers.

Starts both Gmail and FileSystem watchers using configuration from config.env
"""

import os
import sys
import subprocess
import multiprocessing
from pathlib import Path
from dotenv import load_dotenv


def run_gmail_watcher(vault_path: str, credentials_path: str):
    """Run Gmail watcher in subprocess.

    Args:
        vault_path: Path to Obsidian vault
        credentials_path: Path to Gmail credentials
    """
    from gmail_watcher import GmailWatcher

    print(f"[Gmail Watcher] Starting...")
    watcher = GmailWatcher(vault_path, credentials_path)
    watcher.run()


def run_filesystem_watcher(vault_path: str, drop_folder: str):
    """Run filesystem watcher in subprocess.

    Args:
        vault_path: Path to Obsidian vault
        drop_folder: Path to drop folder
    """
    from filesystem_watcher import FileSystemWatcher

    print(f"[FileSystem Watcher] Starting...")
    watcher = FileSystemWatcher(vault_path, drop_folder)
    watcher.run()


def main():
    """Main launcher: load config and start all watchers."""
    # Load environment variables
    env_file = Path(__file__).parent / 'config.env'

    if not env_file.exists():
        print(f"ERROR: Configuration file not found: {env_file}")
        print("Copy config.env.example to config.env and fill in your settings")
        sys.exit(1)

    load_dotenv(env_file)

    # Get configuration
    vault_path = os.getenv('VAULT_PATH')
    gmail_credentials = os.getenv('GMAIL_CREDENTIALS_PATH')
    drop_folder = os.getenv('DROP_FOLDER_PATH')

    # Validate required settings
    if not vault_path:
        print("ERROR: VAULT_PATH not set in config.env")
        sys.exit(1)

    if not Path(vault_path).exists():
        print(f"ERROR: Vault path does not exist: {vault_path}")
        sys.exit(1)

    print("=" * 60)
    print("Silver-tier AI Employee - Watcher Launcher")
    print("=" * 60)
    print(f"Vault Path: {vault_path}")
    print(f"Gmail Credentials: {gmail_credentials or 'Not configured'}")
    print(f"Drop Folder: {drop_folder or 'Not configured'}")
    print("=" * 60)

    # Create process list
    processes = []

    # Start Gmail watcher if configured
    if gmail_credentials and Path(gmail_credentials).exists():
        print("\n[1/2] Starting Gmail Watcher...")
        p = multiprocessing.Process(
            target=run_gmail_watcher,
            args=(vault_path, gmail_credentials),
            name="GmailWatcher"
        )
        p.start()
        processes.append(p)
        print(f"✓ Gmail Watcher started (PID: {p.pid})")
    else:
        print("\n[1/2] Gmail Watcher: SKIPPED (credentials not configured)")

    # Start filesystem watcher if configured
    if drop_folder:
        # Create drop folder if it doesn't exist
        Path(drop_folder).mkdir(parents=True, exist_ok=True)

        print("\n[2/2] Starting FileSystem Watcher...")
        p = multiprocessing.Process(
            target=run_filesystem_watcher,
            args=(vault_path, drop_folder),
            name="FileSystemWatcher"
        )
        p.start()
        processes.append(p)
        print(f"✓ FileSystem Watcher started (PID: {p.pid})")
    else:
        print("\n[2/2] FileSystem Watcher: SKIPPED (drop folder not configured)")

    if not processes:
        print("\nERROR: No watchers configured. Check config.env settings.")
        sys.exit(1)

    print("\n" + "=" * 60)
    print(f"✓ All watchers running ({len(processes)} active)")
    print("=" * 60)
    print("\nPress Ctrl+C to stop all watchers")
    print("\nLogs are being written to:")
    print(f"  - {vault_path}/Logs/gmail_watcher.log")
    print(f"  - {vault_path}/Logs/filesystem_watcher.log")
    print()

    # Wait for all processes
    try:
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        print("\n\nShutting down watchers...")
        for p in processes:
            p.terminate()
            p.join(timeout=5)
            if p.is_alive():
                print(f"Force killing {p.name}...")
                p.kill()
        print("All watchers stopped.")


if __name__ == '__main__':
    # Ensure we're in the right directory
    os.chdir(Path(__file__).parent)
    main()
