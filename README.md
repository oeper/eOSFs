# eOS for PenguinMod

A functional mini operating system built as a PenguinMod project.

**Use it:** open `eOS.pmp` in PenguinMod and click the green flag (every app and UI element is a sprite; text uses the Iris Text extension) (File → Load from your computer) and click the green flag.

* Lock screen → Home with 8 apps: **Files, Notes, Calculator, Clock** (clock / stopwatch / timer), **Terminal**, **Paint**, **Snake**, **Settings**
* Gesture bar (or 3 buttons), app switcher, pull-down control centre (right) and notification centre (left), dialogs, notifications
* Everything is animated: unlocking, opening/closing apps (they morph from/into their icons), panels, keyboard, dialogs, lists
* On-screen keyboard (shift, numbers/symbols) plus physical keyboard typing
* Virtual file system shared by Files, Notes and the Terminal (`ls cd cat echo > mkdir touch rm mv open theme …`)
* Dark mode, 6 accent colours, 6 wallpapers, brightness, 12/24h clock, screen-lock PIN, factory reset
* Notes, files and settings are saved automatically to the browser (TurboWarp *Local Storage* extension)

Developer notes live in [CLAUDE.md](CLAUDE.md). Rebuild with `python3 tools/build_os.py`.
