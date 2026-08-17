"""python -m qxtrl.viz  →  Willow example figure."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

from .cli import main

if __name__ == "__main__":
    main()
