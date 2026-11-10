"""eOS core: drawing primitives, text engine, input, widgets, theme.

Coordinate system for all OS code: UI space, 640x360, origin top-left, y down.
Everything is drawn with pen stamps each frame (immediate-mode UI).
"""
import os
from sb3 import *
import assets

W, H = 640, 360
SB, NB = 24, 28            # status-bar / nav-bar heights
NP = assets.NPAL
PX = assets.PIDX


def pal(name):
    return PX[name]


def S(name, val):
    return set_(V(name), val)


def inc(name, d=1):
    return change(V(name), d)


def dispatch(expr, cases, default=None):
    """Nested if/else chain: cases = [(value, callable)]."""
    def build(i):
        if i >= len(cases):
            if default:
                default()
            return
        val, fn = cases[i]
        with If(expr == val):
            fn()
        if i + 1 < len(cases) or default:
            with Else():
                build(i + 1)
    build(0)


# ---------------------------------------------------------------- state ----
# screens
SCR_BOOT, SCR_LOCK, SCR_HOME, SCR_APP, SCR_REC = 0, 1, 2, 3, 4
APPS = ['Files', 'Notes', 'Calculator', 'Clock', 'Terminal', 'Paint', 'Snake', 'Settings']
APP_ICON = ['files', 'notes', 'calc', 'clock', 'term', 'paint', 'snake', 'settings']
APP_FILES, APP_NOTES, APP_CALC, APP_CLOCK, APP_TERM, APP_PAINT, APP_SNAKE, APP_SET = range(1, 9)

for _n, _v in [
    ('screen', 0), ('app', 0), ('view', 0), ('frame_n', 0),
    ('mx', 0), ('my', 0), ('md', 0), ('mdp', 0), ('press', 0), ('rel', 0), ('px', 0), ('py', 0), ('moved', 0),
    ('pg_t', 99), ('kb_t', 99), ('qs_t', 99), ('dlg_t', 99), ('cb_t', 99), ('pt_pop', 99), ('sn_pop', 99),
    ('ez_o', 1), ('stag_o', 0), ('tab_x', 0), ('ss_prev', -1), ('ss_t0', 0), ('ssf', 0), ('gs', 1), ('gox', 0), ('goy', 0), ('no_hit', 0), ('cur_layer', 0), ('act_layer', 0), ('clip0', SB), ('clip1', H - NB), ('gh', 0),
    ('hit_o', 0), ('tap_o', 0), ('tw_o', 0), ('sl_o', 0), ('drag_id', 0),
    ('scroll', 0), ('sc_on', 0), ('sc_y0', 0), ('sc_s0', 0),
    # settings (persist inside the project)
    ('dark', 0), ('accent', 0), ('wall', 1), ('bright', 100), ('wifi', 1), ('bt', 0), ('h24', 0), ('pin', ''),
    ('c_bg', 0), ('c_surf', 0), ('c_surf2', 0), ('c_div', 0), ('c_acc', 0), ('tx', 0), ('tx2', 0),
    ('hh', 0), ('mm', 0), ('ss', 0), ('tstr', ''), ('ampm', ''), ('dstr', ''), ('tsec', ''),
    ('toast', ''), ('toast_t', 0), ('qs_open', 0), ('qs_a', 0),
    ('dlg', 0), ('dlg_title', ''), ('dlg_msg', ''), ('dlg_ok', ''), ('dlg_act', 0), ('dlg_arg', 0),
    ('kb_open', 0), ('kb_top', H), ('ti', ''), ('ti_act', 0), ('ti_multi', 0), ('kb_done', 0), ('kb_shift', 0),
    ('kb_page', 0), ('kb_max', 200), ('kb_prompt', ''),
    ('open_t', 99), ('open_x', 0), ('open_y', 0), ('open_c', 0),
]:
    V(_n, _v)

L('sw_pos', [0] * 8)
L('gw')          # glyph widths indexed by costume number (filled in by build)
L('nt_txt')
L('nt_time')
L('rec')         # recent apps (most recent last)
L('app_name', APPS)
L('app_icon', APP_ICON)
L('dow', ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'])
L('mon', ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September',
          'October', 'November', 'December'])


def vis(top, bottom):
    """True when unscaled, or - while an app is drawn shrunken (gesture/animation) - only if fully inside the window.
    There is no clipping, so partially visible elements would spill out of the shrunken window."""
    return (V('gs') == 1) | (~(top < 0) & ~(bottom > H))


@proc('t')
def ease(t):
    """ease-out quad of t (clamped 0..1) -> ez_o"""
    S('_et0', clamp(t, 0, 1))
    S('ez_o', 1 - (1 - V('_et0')) * (1 - V('_et0')))


@proc('k')
def stag(k):
    """entrance offset (px, 26 -> 0) for list item k, driven by pg_t -> stag_o"""
    P.ease((V('pg_t') - k * 2) / (V('anim_n') * 0.8))
    S('stag_o', (1 - V('ez_o')) * 26)


# ------------------------------------------------------------ primitives ---
# --- drawing primitives: pen stamps (pen build) or draw commands for the Element clone pool (sprite build)
import modes
exec(compile(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               'pen_prims.py' if modes.MODE == 'pen' else 'sp_prims.py')).read(), 'prims', 'exec'), globals())


# ------------------------------------------------------------- input -------
@proc('', warp=True)
def input_():
    S('mdp', V('md'))
    with If(mouse_down()):
        S('md', 1)
    with Else():
        S('md', 0)
    S('mx', mouse_x() + 320)
    S('my', 180 - mouse_y())
    S('press', 0)
    S('rel', 0)
    with If((V('md') == 1) & (V('mdp') == 0)):
        S('press', 1)
        S('px', V('mx'))
        S('py', V('my'))
        S('moved', 0)
    with If((V('md') == 0) & (V('mdp') == 1)):
        S('rel', 1)
    with If(V('md') == 1):
        with If(abs_(V('mx') - V('px')) + abs_(V('my') - V('py')) > 8):
            S('moved', 1)
    with Else():
        S('drag_id', 0)
        S('sc_on', 0)


@proc('x y w h')
def hit(x, y, w, h):
    """pointer inside the rect, measured through the current draw transform (so anything that is sliding, popping
    or zooming stays tappable); content drawn with no_hit = 1 (thumbnails, morphing windows) never reacts"""
    S('hit_o', 0)
    S('_hx', (V('mx') - V('gox')) / V('gs'))
    S('_hy', (V('my') - V('goy')) / V('gs'))
    with If((V('_hx') >= x) & (V('_hx') < x + w) & (V('_hy') >= y) & (V('_hy') < y + h) & (V('no_hit') == 0)):
        with If(V('cur_layer') >= V('act_layer')):
            with If(V('cur_layer') > 0):
                S('hit_o', 1)
            with Else():
                with If((V('_hy') >= V('clip0')) & (V('_hy') < V('clip1')) &
                        ((V('kb_open') == 0) | (V('my') < V('kb_top')))):
                    S('hit_o', 1)


@proc('x y w h')
def tap(x, y, w, h):
    """press-activated tap (immediate)"""
    S('tap_o', 0)
    P.hit(x, y, w, h)
    with If((V('hit_o') == 1) & (V('press') == 1)):
        S('tap_o', 1)
        S('press', 0)


@proc('x y w h')
def tapr(x, y, w, h):
    """release-activated tap (not after a drag; press must have started inside)"""
    S('tap_o', 0)
    P.hit(x, y, w, h)
    S('_hpx', (V('px') - V('gox')) / V('gs'))
    S('_hpy', (V('py') - V('goy')) / V('gs'))
    with If((V('hit_o') == 1) & (V('rel') == 1) & (V('moved') == 0) &
            (V('_hpx') >= x) & (V('_hpx') < x + w) & (V('_hpy') >= y) & (V('_hpy') < y + h)):
        S('tap_o', 1)
        S('rel', 0)


@proc('max')
def scroll_update(mx_):
    """vertical drag scrolling; clamps V('scroll') to 0..max"""
    with If(V('press') == 1):
        with If((V('no_hit') == 0) & (V('my') >= V('clip0')) & (V('my') < V('clip1')) & (V('cur_layer') >= V('act_layer')) &
                ((V('kb_open') == 0) | (V('my') < V('kb_top')))):
            S('sc_on', 1)
            S('sc_y0', V('my'))
            S('sc_s0', V('scroll'))
    with If((V('sc_on') == 1) & (V('md') == 1) & (V('moved') == 1)):
        S('scroll', V('sc_s0') - (V('my') - V('sc_y0')))
    S('scroll', clamp(V('scroll'), 0, (mx_ + abs_(mx_)) / 2))


# ------------------------------------------------------------- widgets -----
@proc('x y w h label style')
def btn(x, y, w, h, label, style):
    """style 0 neutral, 1 accent, 2 danger.  -> tap_o"""
    P.tapr(x, y, w, h)
    S('_bt', V('tap_o'))
    S('_bc', V('c_surf2'))
    S('_btx', V('tx'))
    with If(style == 1):
        S('_bc', V('c_acc'))
        S('_btx', 0)
    with If(style == 2):
        S('_bc', pal('red'))
        S('_btx', 0)
    S('_bi', 0)
    with If((V('hit_o') == 1) & (V('md') == 1) & (V('moved') == 0)):
        S('_bi', 2)
        with If(style == 0):
            S('_bc', V('c_div'))
    P.rrect(x + V('_bi'), y + V('_bi'), w - V('_bi') * 2, h - V('_bi') * 2, 9, V('_bc'))
    P.text_c(x + w / 2, y + h / 2, label, 13 - V('_bi') * 0.25, 1, V('_btx'))
    S('tap_o', V('_bt'))


@proc('id x y on')
def switch(id_, x, y, on):
    """44x24 toggle with a sliding knob; call, then read tap_o and flip the variable yourself"""
    P.tapr(x - 4, y - 6, 52, 36)
    S('_st', V('tap_o'))
    S('_sp', item(L('sw_pos'), id_))
    S('_sp', V('_sp') + (on - V('_sp')) * V('lk35'))
    list_replace(L('sw_pos'), id_, V('_sp'))
    with If(V('_sp') > 0.5):
        P.rrect(x, y, 44, 24, 12, V('c_acc'))
    with Else():
        P.rrect(x, y, 44, 24, 12, V('c_div'))
    P.circle(x + 12 + 20 * V('_sp'), y + 12, 18 + 2 * sin(V('_sp') * 180), pal('white'))
    S('tap_o', V('_st'))


@proc('id x y w v')
def slider(id_, x, y, w, v):
    """horizontal slider 0..100 -> sl_o"""
    P.hit(x - 10, y - 12, w + 20, 28)
    with If((V('hit_o') == 1) & (V('press') == 1)):
        S('drag_id', id_)
        S('press', 0)
    S('sl_o', v)
    with If((V('drag_id') == id_) & (V('md') == 1)):
        S('sl_o', clamp(((V('mx') - V('gox')) / V('gs') - x) / w * 100, 0, 100))
    S('_slk', item(L('sl_k'), id_ % 16 + 1))                   # knob grows while it is held
    S('_slt', 0)
    with If((V('drag_id') == id_) & (V('md') == 1)):
        S('_slt', 1)
    S('_slk', V('_slk') + (V('_slt') - V('_slk')) * V('lk50'))
    list_replace(L('sl_k'), id_ % 16 + 1, V('_slk'))
    P.rrect(x, y - 2, w, 4, 2, V('c_div'))
    P.rrect(x, y - 2, V('sl_o') / 100 * w, 4, 2, V('c_acc'))
    P.circle(x + V('sl_o') / 100 * w, y, 16 + 6 * V('_slk'), pal('white'))
    P.circle(x + V('sl_o') / 100 * w, y, 8 + 2 * V('_slk'), V('c_acc'))


L('sl_k', [0] * 16)
L('seg_x', [0] * 8)
L('seg_w', [0] * 8)
L('pal_hex', ['#' + h for _, h in assets.PAL])


@proc('id x y w h')
def seg_hl(id_, x, y, w, h):
    """sliding highlight of a choice group: eases from the previous choice to (x, w)"""
    S('_sgx', item(L('seg_x'), id_))
    S('_sgw', item(L('seg_w'), id_))
    with If(V('_sgw') == 0):
        S('_sgx', x)
        S('_sgw', w)
    S('_sgx', V('_sgx') + (x - V('_sgx')) * V('lk35'))
    S('_sgw', V('_sgw') + (w - V('_sgw')) * V('lk35'))
    list_replace(L('seg_x'), id_, V('_sgx'))
    list_replace(L('seg_w'), id_, V('_sgw'))
    P.rrect(V('_sgx'), y, V('_sgw'), h, 9, V('c_acc'))


# --------------------------------------------------------------- theme -----
@proc('')
def theme():
    with If(V('dark') != V('th_dark')):              # remember the old background so frame can dissolve it
        S('th_prev', V('c_bg'))
        S('th_t', 0)
        S('th_dark', V('dark'))
    with If(V('wall') != V('wp_prev')):
        S('wp_t', 0)
        S('wp_prev', V('wall'))
    with If(V('dark') == 1):
        S('c_bg', pal('d_bg'))
        S('c_surf', pal('d_surf'))
        S('c_surf2', pal('d_surf2'))
        S('c_div', pal('d_div'))
        S('tx', 0)
        S('tx2', -40)
    with Else():
        S('c_bg', pal('l_bg'))
        S('c_surf', pal('l_surf'))
        S('c_surf2', pal('l_surf2'))
        S('c_div', pal('l_div'))
        S('tx', -90)
        S('tx2', -52)
    S('c_acc', pal('a_blue') + V('accent'))
    backdrop(V('wall') + 0)


# --------------------------------------------------------------- time ------
@proc('n')
def pad2(n):
    with If(n < 10):
        S('pad_o', join('0', n))
    with Else():
        S('pad_o', n)


@proc('')
def time_update():
    S('hh', current('HOUR'))
    S('mm', current('MINUTE'))
    S('ss', current('SECOND'))
    with If(V('ss') != V('ss_prev')):
        S('ss_prev', V('ss'))
        S('ss_t0', timer())
    S('ssf', V('ss') + clamp(timer() - V('ss_t0'), 0, 1))
    S('_h', V('hh'))
    S('ampm', '')
    with If(V('h24') == 0):
        S('ampm', 'AM')
        with If(V('hh') > 11):
            S('ampm', 'PM')
        S('_h', (V('hh') + 11) % 12 + 1)
    P.pad2(V('mm'))
    S('_m2', V('pad_o'))
    P.pad2(V('ss'))
    S('_s2', V('pad_o'))
    with If(V('h24') == 1):
        P.pad2(V('_h'))
        S('tstr', join(V('pad_o'), ':', V('_m2')))
    with Else():
        S('tstr', join(V('_h'), ':', V('_m2')))
    S('tsec', join(V('tstr'), ':', V('_s2')))
    S('dstr', join(item(L('dow'), current('DAYOFWEEK')), ', ', item(L('mon'), current('MONTH')), ' ',
                   current('DATE')))


@proc('msg')
def notify(msg):
    S('toast', msg)
    S('toast_t', 100)
    list_insert(L('nt_txt'), 1, msg)             # also kept in the notification centre
    list_insert(L('nt_time'), 1, V('tstr'))
    with If(listlen(L('nt_txt')) > 30):
        list_delete(L('nt_txt'), 31)
        list_delete(L('nt_time'), 31)
