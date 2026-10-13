"""Double-click bootstrap: report startup errors without requiring a terminal."""
from pathlib import Path
import sys
import traceback

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / 'scripts'))
try:
    if len(sys.argv) == 3 and sys.argv[1] == '--diagnose':
        import json
        import tkinter
        import requests
        import bs4
        from runtime_paths import RESOURCE_DIR, VERSION, FROZEN
        window = tkinter.Tk()
        window.withdraw()
        info = {'version': VERSION, 'frozen': FROZEN, 'tk': window.tk.call('info', 'patchlevel'),
                'template': (RESOURCE_DIR / 'templates/collector.html').is_file()}
        window.destroy()
        Path(sys.argv[2]).write_text(json.dumps(info), encoding='utf-8')
    else:
        from collector_ui import main
        main()
except Exception:
    error = traceback.format_exc()
    from runtime_paths import DATA_DIR
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / 'collector-startup-error.log').write_text(error, encoding='utf-8')
    import tkinter
    from tkinter import messagebox
    window = tkinter.Tk()
    window.withdraw()
    messagebox.showerror('GroundSignal 启动失败', '界面未能启动。错误日志：\n' + str(DATA_DIR / 'collector-startup-error.log') + '\n\n' + error.splitlines()[-1])
    window.destroy()
