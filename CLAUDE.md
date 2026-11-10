# eOS – a small operating system for PenguinMod

`eOS.pmp` (repo root) is the shipped project: open it in PenguinMod and press the green flag. It is the **sprite edition**: every
app is its own sprite, every UI element is a clone of the `Element` sprite, text is rendered by the **Iris Text** extension
(`g1nxIrisText`, https://extensions.penguinmod.com/extensions/Gen1x/iris-text.js). The project is **generated** – never edit the
.pmp by hand; edit the Python in `tools/` and rebuild. (A legacy single-sprite pen edition can still be built with
`tools/build_pen.py` → `eOS-pen.pmp`; it is not shipped and not tested by default.)

```
python3 tools/build_os.py            # writes ./eOS.pmp           (needs: pip install fonttools)
python3 tools/lint_pmp.py eOS.pmp    # structural check of every sprite (ids, variables, broadcasts, procedure calls, assets)
tools/test/run_all.sh                # build + lint + all headless suites (needs: cd tools/test && npm install, playwright)
EOS_PEN=1 tools/test/run_all.sh      # ... and the pen edition too
```

## What it is
640x360 phone/tablet-style OS. Boot → lock screen (optional PIN) → Home (8 apps) → apps. Gesture bar by default (or 3 buttons),
app switcher, control centre + notification centre (pull down from the status bar), dialogs, toasts, on-screen keyboard
(+ physical a-z/0-9/space/enter), dark mode, 6 accents, 6 wallpapers, brightness, 12/24h clock, customisable navigation.
Apps: Files, Notes (shares the editor with Files), Calculator, Clock (clock/stopwatch/timer), Terminal, Paint, Snake, Settings.
Virtual FS in lists `fs_id/fs_name/fs_parent/fs_type/fs_data` (ids 1-5 = root + Documents/Notes/Pictures/System are protected).
Persistence: TurboWarp Local Storage extension (project id `eos`), autosave every 150 frames + on Home; settings + FS only.
**Everything animates** – the user insists on it: any new state change needs an enter *and* exit animation, time-based, interruptible.

## Source map (tools/)
| file | contents |
|---|---|
| `sb3.py` | compiler/DSL (Python → sb3). `V('x')`/`L('l')` globals, `VL()` sprite-locals, operators, `with If/Else/repeat/until`, `@proc` custom blocks, `P.name(...)` calls, `Script('flag'/'receive:x'/'clone')`, `unit('Sprite')`, broadcasts, clones, lib pruning, `build_multi`. |
| `assets.py` / `sp_assets.py` | costumes: UI icons, app icons, wallpapers / Element shapes (palette families, rounded-rect classes, pill). |
| `os_core.py` | shared basics: input, hit-testing, widgets (`btn/switch/slider/seg_hl`), theme, time, `notify`, easing helpers. Primitives come from `sp_prims.py` (sprite) or `pen_prims.py` (pen). |
| `os_sys.py` | boot, lock/PIN, Home, launch/close morph, gestures, app switcher, status/nav bar, keyboard, control/notification centre, dialog, toast, `frame`. |
| `os_apps.py` | file system + every app (each `with app_unit('Name')` = its own sprite), `app_init/app_back/app_draw` dispatch, `dlg_run`, `text_submit`. |
| `os_store.py` | save/load to localStorage. |
| `sp_prims.py`, `sp_element.py` | command-buffer primitives; Element clone pool + Measure sprite (Iris Text). |
| `build_os.py`, `build_pen.py`, `lint_pmp.py`, `modes.py` | entry points / mode switch (`EOS_MODE`). |

## Sprite architecture
* Shared code lives in unit `lib` and is copied *pruned* (only procedures actually called) into every sprite; `app_unit('Name')` puts an
  app's procedures into its own sprite, reached by broadcasts (`draw_N`, `init_N`, `term_run`). Cross-sprite state = globals only.
* Primitives (`sp_prims.py`) append **commands** to the `cm_*` lists; at the end of `frame`, `broadcast render` (no wait) lets pool clone *i*
  draw command *i* (slot = z-order). Kinds: 1 rect 2 circle 3 rounded rect 4 icon 5 app icon 6 pill 7 text 8 rotated line. Colours = costume
  family (white/accent) + brightness + hue effects (`pal_*` lists). Rounded rects pick one of 8 aspect × 4 radius costumes. Pool 270 (< 300 clones).
* Text: Iris renders the string onto the clone; `[`/`]` are escaped, bold = `[b]..[/b]`, the editor caret is appended as `[color=..]|[/color]`
  (`caret_u`: 2 visible, 4 transparent placeholder). `Measure` sprite gives text sizes (`P.tw`, `P.para` measure). Setters are cheap when unchanged.
* **Never `broadcast and wait` inside a warp procedure** (busy-waits ~500 ms): the sprite build compiles procedures non-warp
  (`sb3.DEFAULT_WARP`); pen loops without broadcasts (`paint_draw`) are explicitly warp. Avoid `pen_clear` each frame (ends the VM step);
  only Paint draws with the pen (`pen_dirty`). One logical frame = one VM step – keep it that way (`fpf` check in history).
* Paint's canvas is on the pen layer (below all sprites) – it is not visible inside switcher thumbnails.

## Drawing / input rules (os_core.py, os_sys.py)
* **UI space** 640x360, origin top-left, y down; stage = `(x-320, 180-y)`. Constants `W,H,SB(24),NB(28)`. Text `y` = vertical centre.
* **Immediate mode**: every frame rebuilds the UI; widgets draw *and* hit-test in the same call. `P.tap` = press, `P.tapr` = release
  (not after a drag, press began inside). Draw inner widgets before their row (first hit consumes the press).
* **Transforms**: `gs, gox, goy` applied in every primitive. `P.set_base(s,cx,cy)` = window level (absolute), `P.set_tf(s,cx,cy)` = relative to the
  window (moves the window centre to cx,cy), `P.zoom_at(s,px,py)` = scale *around a point*. Reset with `set_base(1, W/2, H/2)`.
* **Fades**: `gh` = ghost of the next shapes; `fade` (0..100) is a *group* fade multiplied into every element – use it to fade whole screens.
* **Hit-testing** maps the pointer through the inverse transform, so sliding/popping things stay tappable. Content that must be inert sets
  `no_hit=1` (thumbnails, morphing/dragged windows). Layers: `cur_layer` ≥ `act_layer` (0 normal, 1 panel open/switcher, 2 dialog, 3 dragging);
  set `cur_layer -1` to draw something visible-but-untappable (fading out). Layer 0 is clipped to `clip0..clip1` and above `kb_top`.
* **Easing**: `x += (target - x) * lkNN` then **snap** when within 0.003 (`abs_(t-x) < 0.003`) – asymptotic values never reach 1 otherwise.
* **Booleans**: never store a comparison in a variable (`S('v', a > b)` stores `true`); use `If` and set 1/0.
* **Time base**: never count frames. `fsc` = elapsed 30fps-frames; advance counters with `change(V('x'), V('fsc'))`; `lk30/lk35/lk50`
  frame-rate-independent easing factors; `fclk` for blinks. `timebase.js` checks 30/60/120 fps give equal durations.
* `frame` sets `moved=1` whenever (screen, app, view, panel, dialog, keyboard) changes so a release can't hit the new screen.
* Temps are globals prefixed `_` (not re-entrant). Adding an app: `APPS/APP_ICON` (os_core), `a_<icon>` costume, an `app_unit` section with
  `app_<name>` + `receive:draw_N`/`init_N` scripts, `app_back` entries; text fields return through `text_submit` (`ti_act`).

## Animation catalogue (where to look)
* Screens: lock wakes from black (`pg_t`); unlock = lock face lifts away (`draw_unlock_overlay`, `unl_t`) while Home's clock zooms in and icons
  rise one by one; PIN face↔pad cross-fade (`pin_a`), dots pop (`pin_pop`) / shake on a wrong PIN (`pin_sh`).
* Apps: open = icon→window morph (`open_t`, `draw_card`), close = window→icon on the closing layer (`cl_*`), interruptible both ways and
  continuing from the current size; gesture drag (`gmode 1`), spring back (`gmode 3`), sideways bar swipe slides apps (`swipe_switch`).
* Switcher (`draw_switcher`): hold-halfway card + neighbours; same layout after release; dim fades in; leaving fades cards out (`draw_rec_exit`,
  `rx_t`), swipe-up dismiss, Close all staggers then returns Home.
* Bars: status bar solidity `sb_a`, wifi icon `wifi_a`; nav bar appears `bar_a`, pill↔buttons `nm_a`, pill colour cross-fade `pc_*`.
* Panels (`panel_input`, `draw_panels`, `draw_cc`, `draw_nc`): `qs_p` follows the finger, snaps by position+direction, tap toggles; tiles
  cross-fade (`qt_a`); notification rows slide up after a dismiss (`nt_dt`), Clear all slides them away (`nt_clr`); panel height eases (`nc_h`).
* Overlays: keyboard slides + apps resize (`kb_a` → `kb_top`), dialog pop/fade (`dlg_a`), toast slides in/out, dark mode dissolves (`th_t`),
  wallpaper dip (`wp_t`).
* In-app: page slide (direction from `pg_dir`, back = from the left), list rows stagger (`stag`) and re-settle when a list changes (`_lsig`),
  switch knobs (`sw_pos`), slider knob grows (`sl_k`), choice groups slide (`seg_group` → `seg_hl`), key/button/tile/d-pad press sink,
  calculator display pulse (`cb_t`), Clock tab underline (`tab_x`) + sweeping second hand (`ssf`) + timer bar (`tm_bar`), terminal lines scroll
  in (`tl_*`), Snake glides between cells, food pulse, game-over pop (`zoom_at`), Paint colour pop + brush highlight glide (`pt_hy`).

## Settings / customisation
Saved fields (os_store.py, in order): dark, accent, wall, bright, wifi, bt, h24, pin, sn_best, navmode, anim_n, nav_col, nav_barw,
nav_barh, nav_close, nav_swipe, nav_edge, nav_hold, nav_tap. Layout constants (`W H SB NB`, sizes) are still hard-coded.

## Gotchas (all bitten already)
* **No `transform=` attributes in SVGs** (Scratch's loader mangles `h/H/V` under transforms). SVG size = viewBox; rotation centre in user space.
* `pen` must be listed in project `extensions`; `Script` bodies run eagerly, `@proc` bodies lazily (`make_main_script()` pattern); `VL()` inside a
  procedure registers on the sprite being compiled.
* Variables hold strings after `set`; `"0." == "0"` is true → compare lengths too. `stop this script` in a procedure only leaves it.
* PenguinMod-only blocks: `looks_setStretch`, `jgRuntime_setStageSize`; extensions: pen, localstorage, Iris Text. Real PenguinMod is **not**
  available here: everything is verified in stock scratch-vm + scratch-render with shims in `harness.js` (incl. an Iris Text stand-in written
  from the extension's source in PenguinMod/PenguinMod-ExtensionsGallery `static/extensions/Gen1x/iris-text.js`). The user's screenshots
  from real PenguinMod trump the harness.

## Testing
`tools/test/harness.js`: headless Chromium, real VM + WebGL renderer, fake clock (`fps` option), shims, mouse/keys, variables, screenshots
(`EOS_OUT`, default `/tmp/eos-test`). The harness forces `navmode 0` after the flag unless `open(pmp,{gesture:true})`.
Suites: `interact` (apps/keyboard/files/terminal/PIN/recents), `visual`, `persist`, `robust` (protections + timings), `gesture`, `nav`
(switcher, sideways switch, nav settings), `timebase` (fps independence), `anim` (every transition takes time + mid-animation screenshots).
Coordinates mirror layout constants – if you move a widget, update the clicks. Always *look* at the screenshots.

## Not done yet (see NEXT_PROMPT.md)
App store, back-gesture visual (edge swipe works but shows no chevron), Home icon dragging/rearranging, layout independence (any stage size),
real Iris verification, Wi-Fi/Bluetooth/battery are cosmetic, no sound, Paint not persisted, physical Backspace/Shift.
