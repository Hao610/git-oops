"""
Executable module entrypoint: enables running via 'python -m git_oops'
100% immune to Windows Smart App Control unsigned executable blocks.
"""

from git_oops.cli import main

if __name__ == "__main__":
    main()
