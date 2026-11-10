# Prompt: continue building eOS (paste this into a new session)

You are continuing **eOS**, a mini operating system for PenguinMod, in this repo (`oeper/eOSFs`, branch `ccr-c1288d6f-wtjt0k`).
Read `CLAUDE.md` first – it is the source of truth for architecture, conventions and gotchas. `eOS.pmp` is generated: edit `tools/*.py`, rebuild with
`python3 tools/build_os.py`, verify with `tools/test/run_all.sh` (headless Scratch VM + WebGL; screenshots in `$EOS_OUT`). Look at screenshots – never ship UI
you haven't seen. Keep every suite green, add tests for each feature, commit + push after each finished feature, and update `CLAUDE.md`.

## How the user wants me to work
* Fix every problem mentioned; pay attention to detail. Message the user only with what they must do or know (decisions, risks, things not verified).
* **Everything must animate**, time-based (`fsc`; must look identical at 30/60/120 fps). Animations must be interruptible and continue from the current
  state (no jumps). Gesture feel matters a lot (the user iterates on it).
* The user runs this in **real PenguinMod** (stage can be any size), I can't – I only have stock scratch-vm. Be explicit about anything that depends on
  PenguinMod-only blocks. The user has screenshots from the real thing; trust them over my harness.

## Status (update this when you finish things)
Done: sprite edition is the shipped `eOS.pmp` (apps = sprites, UI = Element clones, Iris Text); gesture bar (resize, morph, interruptible,
swipe-hold switcher carousel, sideways app switching, customisable navigation); everything animated (screens, unlock, PIN, panels, bars,
keyboard, dialog, toasts, theme, in-app widgets); draggable control centre + notification centre; time-based animations; live recents.
Still open below. Verify in real PenguinMod (Iris Text especially) and fix whatever the user's screenshots show first.

## Backlog (the user asked for all of these; do them in this order, one commit each)
1. **Gesture completeness**
   * *Back gesture animation*: edge swipe shows the app following the finger (shifts/scales a little, a back chevron pill appears at the edge); release past
     the threshold plays the "back" transition (page slides out right / app closes at root), otherwise springs back. Left and right edges.
   * *App dragging*: long-press an icon on Home → jiggle/lift animation; drag to rearrange icons (other icons slide aside with easing, drop snaps with a
     spring); persist the order (`app order` list in storage). Optionally drag an app card out of recents to dismiss.
   * Finish "everything animates": exit animations for dialogs/keyboard/quick settings, lock→home unlock transition, home icon entrance after
     lock/recents, key/tile/row press feedback, selection pops (accent, wallpaper, segmented buttons), list insert/delete, terminal line fade-in, smooth
     Snake movement, timer progress bar, slider knob grow, page *back* slides left (forward slides right), wallpaper cross-fade, status icon changes.
2. ~~Control center + notification center~~ (done: drag-down panels; remaining: swipe-to-dismiss notification rows, more tiles)
   * Pull down from the top-right/anywhere on the status bar → Control Center (tiles: Wi-Fi, Bluetooth, dark mode, rotation lock, flashlight-style toggle,
     airplane, do-not-disturb, brightness + volume sliders, now-playing/timer shortcuts, lock/power); from the top-left/centre → Notification Center
     (list of notifications with app icon, title, time, swipe to dismiss, "Clear all"). Drag-to-reveal with the finger, release to snap open/closed,
     fully animated and interruptible. Toasts become real notifications (`P.notify` also appends to the notification list; apps like Clock timer post one).
3. **App Store + more apps**: an App Store app that "installs"/"uninstalls" additional built-in apps (install progress animation, icons appear on Home,
   persisted). Candidate apps: Music player (generated tones/visual), Weather (fake), Calendar, Contacts, Photos (Paint exports), Calculator history,
   Browser (offline pages from the file system), Sticky notes, Tic-tac-toe/2048, System monitor.
4. **Layout independence**: nothing may assume 640×360. Derive every position/size from stage width/height (variables, not Python constants); support
   portrait, landscape and tablet aspect ratios, safe areas, and resizing at runtime (`jgRuntime_getStageWidth/Height`). Make the layout constants
   (`W H SB NB`, icon size, grid columns, radius, font, fps, nav mode, animation speed) real variables exposed in Settings and saved.
5. **Sprite architecture** (the user's requirement): each app is a **sprite** and every UI element is a **sprite** (clones of a UI-element sprite:
   button, switch, slider, icon, text…), like the original template (`dsys`, `apptest`, `nav`, `statusBar`). Text uses the **Display Text** extension
   (SharkPool, `SPdisText_*`; URL https://sharkpools-extensions.vercel.app/extension-code/Display-Text.js – the sandbox proxy blocked it, so ask the user for
   the file/block list or write a stand-in from the four blocks in the template: `printTxt TXT ID`, `setTextFont ID FONT`, `setTextPosition ID X Y`,
   `setFontSize ID SIZE`). The user chose: Display Text extension, replace the pen version. Keep gesture/animation behaviour identical to the pen version
   (port the transform/morph logic to sprite scale/position/ghost). This is a rewrite – plan it, keep the headless harness working with shims.
6. **Customisation**: every tunable value is a documented variable; Settings exposes them; a "developer" settings page edits raw variables.

## Known issues / things to double-check
* Verify in real PenguinMod: `looks_setStretch`, `jgRuntime_setStageSize`, pen stamping while the sprite is hidden, the `localstorage` extension loading.
* Variable palette is cluttered (≈400 temp variables) – consider namespacing or hiding.
* Recents: horizontal scroll feel, swipe-up-to-dismiss on cards (not done).
* Wi-Fi/Bluetooth/battery are cosmetic.

## Definition of done for each item
Implemented, animated, interruptible, time-based; screenshots reviewed; tests added and all suites green (`tools/test/run_all.sh`); `CLAUDE.md` updated;
committed and pushed; final message to the user lists only decisions needed and anything unverified.
