import sys
from pathlib import Path

# tools/ の中のモジュール（build_images・voice）をテストから import できるようにする
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
