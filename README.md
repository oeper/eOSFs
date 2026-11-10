# eOS for PenguinMod

A functional mini operating system built as a PenguinMod project.

**Use it:** open `eOS.pmp` (pen edition) or `eOS-sprites.pmp` (every app and UI element is a sprite; needs the Iris Text extension) in PenguinMod (File → Load from your computer) and click the green flag.

* Lock screen → Home with 8 apps: **Files, Notes, Calculator, Clock** (clock / stopwatch / timer), **Terminal**, **Paint**, **Snake**, **Settings**
* Status bar (tap it for quick settings), Back / Home / Recents navigation, app switcher, dialogs, notifications
* On-screen keyboard (shift, numbers/symbols) plus physical keyboard typing
* Virtual file system shared by Files, Notes and the Terminal (`ls cd cat echo > mkdir touch rm mv open theme …`)
* Dark mode, 6 accent colours, 6 wallpapers, brightness, 12/24h clock, screen-lock PIN, factory reset
* Notes, files and settings are saved automatically to the browser (TurboWarp *Local Storage* extension)

Developer notes live in [CLAUDE.md](CLAUDE.md). Rebuild with `python3 tools/build_os.py`.
