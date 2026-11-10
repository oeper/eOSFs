# eOS – a small operating system for PenguinMod

`eOS.pmp` (repo root) is the shippable project: open it in PenguinMod and press the green flag.
It is **generated** – never edit the .pmp by hand. Edit the Python in `tools/` and rebuild.

```
python3 tools/build_os.py            # writes ./eOS.pmp           (needs: pip install fonttools)
python3 tools/lint_pmp.py eOS.pmp    # structural sanity check
tools/test/run_all.sh                # build + all headless tests (needs: cd tools/test && npm install, playwright)
```

## What it is
640x360 phone/tablet-style OS drawn entirely with pen stamps (one hidden sprite `eOS`, everything global on the Stage).
Boot → lock screen (optional PIN) → home (8 apps) → apps. Status bar, navigation (**gesture bar by default**, or 3 buttons – Settings → Navigation), quick settings
(tap status bar), recents, dialogs, toasts, on-screen QWERTY keyboard (+ physical a-z/0-9/space/enter), dark mode,
6 accents, 6 wallpapers, brightness, 12/24h clock.
Apps: Files, Notes (shares the editor with Files), Calculator, Clock (clock/stopwatch/timer), Terminal, Paint, Snake, Settings.
Virtual FS lives in lists `fs_id/fs_name/fs_parent/fs_type/fs_data` (ids 1-5 = root + Documents/Notes/Pictures/System are protected).
Persistence: TurboWarp Local Storage extension (`localstorage_*`, project id `eos`), autosave every 150 frames + on Home;
settings + FS only (not Paint/terminal history).

## Source map (tools/)
| file | contents |
|---|---|
| `sb3.py` | the compiler/DSL (Python → sb3 blocks). `V('x')`/`L('l')` globals, operator overloading, `with If/Else/repeat/until`, `@proc('args')` custom blocks (warp), `P.name(...)` calls, `Script('flag')`. |
| `assets.py` | all costumes: palette rect/circle stamps, UI icons, app icons, Inter glyphs (via fontTools), wallpapers. |
| `os_core.py` | primitives (`rect/rrect/circle/text/icon/para`), input, hit-testing, widgets (`btn/switch/slider`), theme, time. |
| `os_sys.py` | boot, lock/PIN, home, launch animation, recents, status/nav bar, keyboard, quick settings, dialog, toast, `frame`. |
| `os_apps.py` | file system + every app, `app_init/app_back/app_draw` dispatch, `dlg_run`, `text_submit`, `bg_tasks`. |
| `os_store.py` | save/load to localStorage. |
| `build_os.py`, `lint_pmp.py` | entry points. `test/` = headless Scratch VM + WebGL harness and suites. |

## Navigation / animations (os_sys.py)
* **Global draw transform** `gs, gox, goy` is applied inside every primitive (`rect/circle/text/para/icon/appicon/pillkey/hand` and Paint's replay);
  `P.set_tf(scale, cx, cy)` draws the next things scaled around a centre. Reset to identity at the start of `frame` and after `draw_app`.
  Anything new that stamps or pen-draws directly must apply it too.
* `navmode` 1 = gesture bar, 0 = 3 buttons. `gesture_update` (runs first in `frame`): press in the bottom `NB` px = `gtype 1`
  (drag up in an app → `gmode 1`: app shrinks with `ga_s`, follows the finger via `ga_cx/ga_cy`; release above 74% of the height → `gmode 2`
  close animation into its icon, else `gmode 3` snap back; on Home it opens Recents, in Recents it goes Home); press within 14 px of a
  side edge = `gtype 2` edge-swipe back. Back/Home buttons and `nav_back` also use `close_app_anim`.
* Opening an app (`launch`) animates from the icon (or recents card) for `anim_n` frames (Settings: Fast 6 / Normal 10 / Slow 16).
  While any transform animation runs `act_layer` is 3, so no widget reacts.
* **In-app animation helpers** (os_core.py): `P.ease(t)` → `ez_o`; `P.stag(k)` → `stag_o` (list-row entrance offset). Counters that restart on a
  change and are advanced per frame: `pg_t` (page slide-in/row stagger; reset when screen/app/view/folder/clock tab changes), `kb_t` (keyboard rise),
  `qs_t` (quick-settings drop), `dlg_t` (dialog pop), `cb_t` (calculator display pulse), `pt_pop` (Paint colour), `sn_pop` (Snake game-over).
  Switch knobs glide via list `sw_pos` (each `P.switch` call needs a unique id 1-8); Clock tab underline glides via `tab_x`; the second hand
  sweeps using `ssf`. Speeds scale with `anim_n` where noted. Reuse these when adding animations; apply them with `P.set_tf`.
* Customisable state (saved by `os_store.py`, fields in order): dark, accent, wall, bright, wifi, bt, h24, pin, sn_best, navmode, anim_n.
  Layout constants (`W H SB NB`, sizes in code) are still hard-coded – see "Ideas".

* **UI space**: 640x360, origin top-left, y down. Stage coords are `(x-320, 180-y)`. Constants `W,H,SB(24),NB(28)` in `os_core.py`.
* **Immediate mode**: `frame` clears the pen and redraws everything every frame; widgets draw *and* hit-test in the same call.
  `P.tap` = press-activated (keys, d-pad), `P.tapr` = release-activated, only if not dragged and the press began inside (lists, buttons).
  Both set `tap_o`; `P.btn` leaves its result in `tap_o` too. Draw inner widgets before the row that contains them (first hit consumes the press).
* **Layers**: `cur_layer` (set by the code drawing) must be >= `act_layer` (set at the start of `frame`: 0 normal, 1 quick-settings/recents, 2 dialog)
  for a hit to count. Layer-0 hits are also limited to `clip0..clip1` rows and blocked below `kb_top` while the keyboard is open.
  Scrolled content is drawn *first* and the opaque header/nav drawn over it (there is no clipping); set `clip0=SB+37` for scrolling views.
* `frame` sets `moved=1` whenever (screen, app, view, qs, dialog, keyboard) changes so the release of a press that caused a transition
  can't activate a widget of the new screen.
* **Text**: costume `g<char>` (medium) / `b<char>` (bold); widths in list `gw` indexed by costume number. Tint = brightness effect
  (0 white, -90 near-black) – glyphs/icons are white. Only ASCII 33-126 plus `×÷−±•°…`. `y` for text is the *vertical centre*.
* **Colours**: palette = costume numbers (`pal('name')`; rect stamp = number, circle = number + `NPAL`). Theme variables
  `c_bg c_surf c_surf2 c_div c_acc tx tx2` are set by `P.theme`. Translucent shapes (`gh` = ghost) show overlap artefacts for `rrect`;
  use single-stamp costumes (`k_pill`) for those.
* Temp variables in procedures are globals prefixed `_` (not re-entrant – don't recurse). Proc args are real args.
* Adding an app: add name/icon to `APPS/APP_ICON` (os_core), an `a_<icon>` costume (assets), `app_<name>` proc, entries in `app_draw`,
  `app_init`, `app_back` (os_apps). Text-field results arrive in `text_submit` keyed by `ti_act` (10-12 files, 20 editor, 30 terminal).

## Gotchas (all bitten already)
* **No `transform=` attributes in SVGs**: Scratch's loader rewrites paths under transforms and mangles `h/H/V`. Bake coordinates.
* SVG costume size = **viewBox**, not width/height; rotation centre is in user-space coordinates (keep viewBox origin 0,0).
* `pen` must be listed in project `extensions`; `Script` bodies run eagerly while `@proc` bodies are lazy (use `make_main_script()` pattern).
* Variables hold strings after `set`; `"0." == "0"` is true in Scratch → compare lengths too. `stop this script` inside a procedure only leaves the procedure.
* PenguinMod-only blocks used: `looks_setStretch` (all stamps), `jgRuntime_setStageSize` (flag script). Everything else is core Scratch + pen
  + `localstorage`. Real PenguinMod was **not** available when this was built; behaviour was verified in the stock scratch-vm + scratch-render
  with `harness.js` shimming those blocks. The harness forces `navmode 0` after the flag unless `open(pmp,{gesture:true})`.

## Testing
`tools/test/harness.js` loads a .pmp in headless Chromium (real VM + WebGL renderer), shims setStretch/setStageSize/localstorage,
steps frames, injects mouse/keys, reads variables, takes screenshots (`EOS_OUT`, default `/tmp/eos-test`).
Suites: `gesture.js` (gesture bar, animations, edge swipe; runs with the gesture bar), `interact.js` (apps, keyboard, files, terminal, PIN, recents…), `visual.js` (shift/physical keys/dark mode/animation),
`persist.js` (save/load/corruption), `robust.js` (protections + per-frame timings). Coordinates in tests mirror the layout constants;
if you move a widget, update the click positions.

## Ideas not done
Make every layout constant a variable (stage size, bar heights, icon size, corner radius, font, fps) – only nav mode and animation speed are done;
Wi-Fi/Bluetooth are cosmetic; battery is static; no sound; Paint isn't persisted; editor has no caret positioning (append-only);
no notifications centre; physical Backspace/Shift aren't available in stock key menus.
