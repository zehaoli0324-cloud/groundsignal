"""Separate bundled resources from per-user writable settings and search cache."""
import os
from pathlib import Path
import sys

VERSION = '0.3.0-beta'
FROZEN = bool(getattr(sys, 'frozen', False))
RESOURCE_DIR = Path(sys._MEIPASS) if FROZEN else Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.environ['GROUNDSIGNAL_DATA_DIR']) if os.environ.get('GROUNDSIGNAL_DATA_DIR') else (
    Path(os.environ.get('LOCALAPPDATA', str(Path.home() / 'AppData/Local'))) / 'GroundSignal'
    if FROZEN else RESOURCE_DIR)
CONFIG_PATH = DATA_DIR / 'collector-config.json'
CACHE_DIR = DATA_DIR / '.collector-cache'
