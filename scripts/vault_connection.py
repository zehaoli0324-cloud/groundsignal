"""Local Obsidian discovery and an explicit writable-vault connection check."""
import json
import os
from pathlib import Path
import tempfile
import threading

PICKER_LOCK = threading.Lock()


def installed():
    if os.name != 'nt':
        return False
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r'obsidian\shell\open\command'):
            return True
    except OSError:
        return False


def discover(registry_path=None):
    registry_path = Path(registry_path) if registry_path else Path(os.environ.get('APPDATA', '')) / 'obsidian/obsidian.json'
    try:
        registry = json.loads(registry_path.read_text(encoding='utf-8'))
        found = []
        for item in registry.get('vaults', {}).values():
            path = Path(item.get('path', ''))
            if path.is_absolute() and (path / '.obsidian').is_dir():
                found.append({'name': path.name, 'path': str(path.resolve())})
        return list({item['path']: item for item in found}.values())
    except (ValueError, TypeError, AttributeError, OSError):
        return []


def check_vault(value, write_test=False):
    if not isinstance(value, str) or not value.strip() or not Path(value).is_absolute():
        raise ValueError('请点击“选择文件夹”，选择你的 Obsidian 笔记库')
    path = Path(value).resolve()
    if not path.is_dir():
        raise ValueError('找不到这个文件夹，请重新选择笔记库')
    if not (path / '.obsidian').is_dir():
        children = [p for p in path.iterdir() if p.is_dir() and (p / '.obsidian').is_dir()]
        hint = f' 检测到下一级笔记库：{children[0].name}，请进入该文件夹后选择。' if children else ''
        raise ValueError('这个文件夹不是 Obsidian 笔记库（没有找到 .obsidian 配置）。请先在 Obsidian 中创建或打开笔记库。' + hint)
    if write_test:
        # Only this uniquely created file is removed; existing notes are untouched.
        fd, name = tempfile.mkstemp(prefix='.groundsignal-check-', suffix='.tmp', dir=path)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                stream.write('GroundSignal connection check')
        finally:
            Path(name).unlink(missing_ok=True)
    return {'vault': str(path), 'name': path.name, 'is_vault': True, 'writable': write_test}


def choose_folder(initial=''):
    if not PICKER_LOCK.acquire(blocking=False):
        raise ValueError('选择窗口已打开，请先完成选择')
    root = None
    try:
        import tkinter
        from tkinter import filedialog
        root = tkinter.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        return filedialog.askdirectory(parent=root, title='选择 Obsidian 笔记库文件夹',
                                       initialdir=initial if initial and Path(initial).is_dir() else str(Path.home()),
                                       mustexist=True)
    finally:
        if root is not None:
            root.destroy()
        PICKER_LOCK.release()
