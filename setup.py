import sys
from cx_Freeze import setup, Executable

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(  name = "TL-DR",
        version = "0.1",
        description = "test",
        options=
        {
            "build_exe": 
            {
                "packages": ["multiprocessing", "idna"],
                "include_files": ["api_keys.txt", "html/"]
            }
            },
        executables = [Executable("TL-DR.py", base=base)])