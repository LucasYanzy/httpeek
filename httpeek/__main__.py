"""支持 `python -m httpeek ...` 免安装运行。"""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
