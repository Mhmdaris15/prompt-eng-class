"""Generate the English Lab 2 report from a saved run."""

import sys

from lab2.report import main


if __name__ == "__main__":
    sys.argv.extend(["--language", "en"])
    main()
