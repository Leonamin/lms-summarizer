"""Desktop entrypoint; frozen subprocess dispatch precedes GUI imports."""
import multiprocessing
import os
import sys


def main():
    # Windowed bundles have no streams, including spawned stage workers.
    if sys.stdout is None:
        sys.stdout = open(os.devnull, 'w')
    if sys.stderr is None:
        sys.stderr = open(os.devnull, 'w')
    multiprocessing.freeze_support()
    if '--core-smoke' in sys.argv:
        from src.desktop.smoke import run
        run()
        return
    from src.gui.main import main as gui_main
    gui_main()


if __name__ == '__main__':
    main()
