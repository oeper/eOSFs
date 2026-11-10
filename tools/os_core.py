"""eOS core: drawing primitives, text engine, input, widgets, theme.

Coordinate system for all OS code: UI space, 640x360, origin top-left, y down.
Everything is drawn with pen stamps each frame (immediate-mode UI).
"""
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
    ('cur_layer', 0), ('act_layer', 0), ('clip0', SB), ('clip1', H - NB), ('gh', 0),
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

L('gw')          # glyph widths indexed by costume number (filled in by build)
L('rec')         # recent apps (most recent last)
L('app_name', APPS)
L('app_icon', APP_ICON)
L('dow', ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'])
L('mon', ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September',
          'October', 'November', 'December'])


# ------------------------------------------------------------ primitives ---
@proc('x y w h c')
def rect(x, y, w, h, c):
    with If((w > 0) & (h > 0)):
        costume(c + 0)
        effect('GHOST', V('gh'))
        set_stretch(w, h)
        goto(x + w / 2 - 320, 180 - y - h / 2)
        stamp()


@proc('cx cy d c')
def circle(cx, cy, d, c):
    with If(d > 0):
        costume(c + NP)
        effect('GHOST', V('gh'))
        set_stretch(d, d)
        goto(cx - 320, 180 - cy)
        stamp()


@proc('x y w h r c')
def rrect(x, y, w, h, r, c):
    S('_r', r)
    with If(V('_r') * 2 > h):
        S('_r', h / 2)
    with If(V('_r') * 2 > w):
        S('_r', w / 2)
    with If(V('_r') < 0.5):
        P.rect(x, y, w, h, c)
    with Else():
        P.rect(x + V('_r'), y, w - V('_r') * 2, h, c)
        P.rect(x, y + V('_r'), w, h - V('_r') * 2, c)
        P.circle(x + V('_r'), y + V('_r'), V('_r') * 2, c)
        P.circle(x + w - V('_r'), y + V('_r'), V('_r') * 2, c)
        P.circle(x + V('_r'), y + h - V('_r'), V('_r') * 2, c)
        P.circle(x + w - V('_r'), y + h - V('_r'), V('_r') * 2, c)


@proc('x y s size bold tint maxw')
def text(x, y, s, size, bold, tint, maxw):
    """y = vertical centre of the text line.  bold 0/1.  tint = brightness (0 white, -90 near black)."""
    with If(bold == 1):
        S('_pf', 'b')
    with Else():
        S('_pf', 'g')
    effect('BRIGHTNESS', tint)
    effect('GHOST', V('gh'))
    set_stretch(size, size)
    S('_tx', x)
    S('_ti', 1)
    S('_td', 0)
    S('_tn', length(s))
    with until((V('_ti') > V('_tn')) | (V('_td') == 1)):
        S('_ch', letter(V('_ti'), s))
        with If(V('_ch') == ' '):
            change(V('_tx'), size * 0.3)
        with Else():
            costume(join(V('_pf'), V('_ch')))
            S('_tw', item(L('gw'), costume_number()) * size / 100)
            with If((maxw > 0) & (V('_tx') + V('_tw') > x + maxw)):
                S('_td', 1)
            with Else():
                goto(V('_tx') - 320, 180 - y - size * 0.36)
                stamp()
                change(V('_tx'), V('_tw'))
        inc('_ti')
    effect('BRIGHTNESS', 0)


@proc('s size bold')
def tw(s, size, bold):
    """text width -> tw_o"""
    with If(bold == 1):
        S('_wpf', 'b')
    with Else():
        S('_wpf', 'g')
    S('tw_o', 0)
    S('_wi', 1)
    S('_wn', length(s))
    with until(V('_wi') > V('_wn')):
        S('_wc', letter(V('_wi'), s))
        with If(V('_wc') == ' '):
            change(V('tw_o'), size * 0.3)
        with Else():
            costume(join(V('_wpf'), V('_wc')))
            change(V('tw_o'), item(L('gw'), costume_number()) * size / 100)
        inc('_wi')


@proc('cx y s size bold tint')
def text_c(cx, y, s, size, bold, tint):
    P.tw(s, size, bold)
    P.text(cx - V('tw_o') / 2, y, s, size, bold, tint, 0)


@proc('rx y s size bold tint')
def text_r(rx, y, s, size, bold, tint):
    P.tw(s, size, bold)
    P.text(rx - V('tw_o'), y, s, size, bold, tint, 0)


@proc('x y w s size lh tint draw')
def para(x, y, w, s, size, lh, tint, draw):
    """Word-less char wrap with \\n support.  End position -> p_x, p_y (line centre of the last line)."""
    S('_px', x)
    S('_py', y)
    S('_pi', 1)
    S('_pn', length(s))
    effect('BRIGHTNESS', tint)
    set_stretch(size, size)
    with until(V('_pi') > V('_pn')):
        S('_pc', letter(V('_pi'), s))
        with If(V('_pc') == '\n'):
            S('_px', x)
            change(V('_py'), lh)
        with Else():
            with If(V('_pc') == ' '):
                S('_pw', size * 0.3)
                S('_pcs', 0)
            with Else():
                costume(join('g', V('_pc')))
                S('_pw', item(L('gw'), costume_number()) * size / 100)
                S('_pcs', 1)
            with If(V('_px') + V('_pw') > x + w):
                S('_px', x)
                change(V('_py'), lh)
            with If((draw == 1) & (V('_pcs') == 1)):
                goto(V('_px') - 320, 180 - V('_py') - size * 0.36)
                stamp()
            change(V('_px'), V('_pw'))
        inc('_pi')
    S('p_x', V('_px'))
    S('p_y', V('_py'))
    effect('BRIGHTNESS', 0)


@proc('name cx cy size tint')
def icon(name, cx, cy, size, tint):
    costume(join('i_', name))
    effect('BRIGHTNESS', tint)
    effect('GHOST', V('gh'))
    set_stretch(size * 100 / 24, size * 100 / 24)
    goto(cx - 320, 180 - cy)
    stamp()
    effect('BRIGHTNESS', 0)


@proc('name cx cy size')
def appicon(name, cx, cy, size):
    costume(join('a_', name))
    effect('GHOST', V('gh'))
    set_stretch(size, size)
    goto(cx - 320, 180 - cy)
    stamp()


@proc('cx cy tint gh_')
def pillkey(cx, cy, tint, gh_):
    """64x38 pill, tinted + translucent (single stamp, so no alpha overlap artefacts)"""
    costume('k_pill')
    effect('BRIGHTNESS', tint)
    effect('GHOST', gh_)
    set_stretch(100, 100)
    goto(cx - 320, 180 - cy)
    stamp()
    effect('BRIGHTNESS', 0)
    effect('GHOST', 0)


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
    S('hit_o', 0)
    with If((V('mx') >= x) & (V('mx') < x + w) & (V('my') >= y) & (V('my') < y + h)):
        with If(V('cur_layer') >= V('act_layer')):
            with If(V('cur_layer') > 0):
                S('hit_o', 1)
            with Else():
                with If((V('my') >= V('clip0')) & (V('my') < V('clip1')) &
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
    with If((V('hit_o') == 1) & (V('rel') == 1) & (V('moved') == 0) &
            (V('px') >= x) & (V('px') < x + w) & (V('py') >= y) & (V('py') < y + h)):
        S('tap_o', 1)
        S('rel', 0)


@proc('max')
def scroll_update(mx_):
    """vertical drag scrolling; clamps V('scroll') to 0..max"""
    with If(V('press') == 1):
        with If((V('my') >= V('clip0')) & (V('my') < V('clip1')) & (V('cur_layer') >= V('act_layer')) &
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
    with If((V('hit_o') == 1) & (V('md') == 1) & (V('moved') == 0)):
        with If(style == 0):
            S('_bc', V('c_div'))
        with Else():
            S('gh', 25)
    P.rrect(x, y, w, h, 9, V('_bc'))
    S('gh', 0)
    P.text_c(x + w / 2, y + h / 2, label, 13, 1, V('_btx'))
    S('tap_o', V('_bt'))


@proc('x y on')
def switch(x, y, on):
    """44x24 toggle; call, then read tap_o and flip the variable yourself"""
    P.tapr(x - 4, y - 6, 52, 36)
    S('_st', V('tap_o'))
    with If(on == 1):
        P.rrect(x, y, 44, 24, 12, V('c_acc'))
        P.circle(x + 32, y + 12, 18, pal('white'))
    with Else():
        P.rrect(x, y, 44, 24, 12, V('c_div'))
        P.circle(x + 12, y + 12, 18, pal('white'))
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
        S('sl_o', clamp((V('mx') - x) / w * 100, 0, 100))
    P.rrect(x, y - 2, w, 4, 2, V('c_div'))
    P.rrect(x, y - 2, V('sl_o') / 100 * w, 4, 2, V('c_acc'))
    P.circle(x + V('sl_o') / 100 * w, y, 16, pal('white'))
    P.circle(x + V('sl_o') / 100 * w, y, 8, V('c_acc'))


# --------------------------------------------------------------- theme -----
@proc('')
def theme():
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
