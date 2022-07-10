import cx_Freeze
import sys

base = None
if sys.platform == 'win32':
    base = 'Win32GUI'

executables = [cx_Freeze.Executable("filelocker.py", base=base),
               cx_Freeze.Executable("crypto.py", base=base),
               cx_Freeze.Executable("path_to_tree.py", base=base)]

cx_Freeze.setup(
    name="FileLocker",
    options={"build_exe": {"packages": [
        "tkinter", "functools", "tkdnd", "tkinterdnd2", "pyotp",
        "threading", "time", "requests", "os", "json", "Crypto", "base64", "collections"],
        "include_files": ["assets/"]}
    },
    executables=executables)
