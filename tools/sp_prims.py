# Sprite-mode drawing primitives - exec'd into os_core's namespace.
# Nothing is drawn here: every call appends one *command* (final stage geometry + look) to the cm_* lists.
# The Element clone pool (sp_element.py) turns slot i of that buffer into clone i, in draw order = z-order.
import colorsys
import math

CM_LISTS = ['cm_k', 'cm_x', 'cm_y', 'cm_w', 'cm_h', 'cm_a', 'cm_s', 'cm_g', 'cm_t', 'cm_e', 'cm_u', 'cm_p', 'cm_m', 'cm_l']
for _n in CM_LISTS:
    L(_n)
V('cm_n', 0)
V('fade', 0)
V('caret_u', 0)       # editor caret: 2 = visible, 4 = invisible placeholder (keeps wrapping stable)
for _n in ('ms_s', 'ms_size', 'ms_bold', 'ms_maxw', 'ms_lh', 'ms_w', 'ms_h'):
    V(_n, 0)

# --- colours: palette index -> (costume family, brightness effect, hue effect)
_BASE_HUE = colorsys.rgb_to_hsv(0x2F / 255, 0x6B / 255, 0xFF / 255)[0] * 360
_fam, _bri, _hue = [], [], []
for _name, _hx in assets.PAL:
    _r, _g, _b = (int(_hx[i:i + 2], 16) / 255 for i in (0, 2, 4))
    _h, _s, _v = colorsys.rgb_to_hsv(_r, _g, _b)
    if _s < 0.3:
        _fam.append(1)
        _bri.append(round((_v - 1) * 100, 1))
        _hue.append(0)
    else:
        _fam.append(2)
        _bri.append(round(min(0, (_v - 1) * 100), 1))
        _hue.append(round((((_h * 360 - _BASE_HUE) % 360) / 360) * 200, 1))
L('pal_fam', _fam)
L('pal_bri', _bri)
L('pal_hue', _hue)
# rounded-rect costume classes
from sp_prims_data import RR_ASPECT, RR_RATIO
L('rr_nw', [40 * a for a in RR_ASPECT])


def gx(x):
    return V('gox') + x * V('gs') - 320


def gy(y):
    return 180 - V('goy') - y * V('gs')


@proc('k x y w h a s g t e u p m l')
def cmd(k, x, y, w, h, a, s, g, t, e, u, p, m, l):
    list_add(L('cm_k'), k)
    list_add(L('cm_x'), x)
    list_add(L('cm_y'), y)
    list_add(L('cm_w'), w)
    list_add(L('cm_h'), h)
    list_add(L('cm_a'), a)
    list_add(L('cm_s'), s)
    list_add(L('cm_g'), g + (100 - g) * V('fade') / 100)     # group fade multiplies into every element's ghost
    list_add(L('cm_t'), t)
    list_add(L('cm_e'), e)
    list_add(L('cm_u'), u)
    list_add(L('cm_p'), p)
    list_add(L('cm_m'), m)
    list_add(L('cm_l'), l)
    inc('cm_n')


@proc('x y w h c')
def rect(x, y, w, h, c):
    with If((w > 0) & (h > 0) & vis(y, y + h)):
        P.cmd(1, gx(x + w / 2), gy(y + h / 2), w * V('gs'), h * V('gs'), join('sq_', item(L('pal_fam'), c)), 0, V('gh'),
              item(L('pal_bri'), c), item(L('pal_hue'), c), 0, 100, 100, 0)


@proc('cx cy d c')
def circle(cx, cy, d, c):
    with If((d > 0) & vis(cy - d / 2, cy + d / 2)):
        P.cmd(2, gx(cx), gy(cy), d * V('gs'), d * V('gs'), join('ci_', item(L('pal_fam'), c)), 0, V('gh'),
              item(L('pal_bri'), c), item(L('pal_hue'), c), 0, 100, 100, 0)


@proc('x y w h r c')
def rrect(x, y, w, h, r, c):
    with If((w > 0) & (h > 0) & vis(y, y + h)):
        with If(r < 0.5):
            P.rect(x, y, w, h, c)
        with Else():
            S('_ra', w / h)
            S('_ai', 1 + (V('_ra') > 1.26) + (V('_ra') > 2) + (V('_ra') > 3.2) + (V('_ra') > 4.9) + (V('_ra') > 7.7) +
              (V('_ra') > 12.6) + (V('_ra') > 22))
            S('_rr', clamp(r, 0, clamp(w, 0, h) / 2) / h)
            S('_ri', 1 + (V('_rr') > 0.16) + (V('_rr') > 0.25) + (V('_rr') > 0.4))
            P.cmd(3, gx(x + w / 2), gy(y + h / 2), w * V('gs'), h * V('gs'),
                  join('rr_', item(L('pal_fam'), c), '_', V('_ai'), '_', V('_ri')), 0, V('gh'),
                  item(L('pal_bri'), c), item(L('pal_hue'), c), 0, item(L('rr_nw'), V('_ai')), 40, 0)


@proc('name cx cy size tint')
def icon(name, cx, cy, size, tint):
    with If(vis(cy - size / 2, cy + size / 2)):
        P.cmd(4, gx(cx), gy(cy), size * V('gs'), size * V('gs'), join('i_', name), 0, V('gh'), tint, 0, 0, 24, 24, 0)


@proc('name cx cy size')
def appicon(name, cx, cy, size):
    with If(vis(cy - size / 2, cy + size / 2)):
        P.cmd(5, gx(cx), gy(cy), size * V('gs'), size * V('gs'), join('a_', name), 0, V('gh'), 0, 0, 0, 100, 100, 0)


@proc('cx cy tint gh_')
def pillkey(cx, cy, tint, gh_):
    P.cmd(6, gx(cx), gy(cy), 64 * V('gs'), 38 * V('gs'), 'k_pill', 0, gh_, tint, 0, 0, 64, 38, 0)


@proc('x y s size bold tint maxw anchor lh')
def textcmd(x, y, s, size, bold, tint, maxw, anchor, lh):
    with If(vis(y - size * 0.7, y + size * 0.7) | (anchor == 3)):
        P.cmd(7, gx(x), gy(y), V('gs'), 0, s, size, V('gh'), tint, 0, bold + V('caret_u'), anchor, maxw, lh)


@proc('x y s size bold tint maxw')
def text(x, y, s, size, bold, tint, maxw):
    P.textcmd(x, y, s, size, bold, tint, maxw, 0, 0)


@proc('cx y s size bold tint')
def text_c(cx, y, s, size, bold, tint):
    P.textcmd(cx, y, s, size, bold, tint, 0, 1, 0)


@proc('rx y s size bold tint')
def text_r(rx, y, s, size, bold, tint):
    P.textcmd(rx, y, s, size, bold, tint, 0, 2, 0)


@proc('s size bold maxw lh')
def measure(s, size, bold, maxw, lh):
    """text size via the Measure sprite -> ms_w, ms_h (cached while the arguments stay the same)"""
    with If((V('ms_s') != s) | (V('ms_size') != size) | (V('ms_bold') != bold) | (V('ms_maxw') != maxw) |
            (V('ms_lh') != lh) | (V('ms_w') == 0)):
        S('ms_s', s)
        S('ms_size', size)
        S('ms_bold', bold)
        S('ms_maxw', maxw)
        S('ms_lh', lh)
        broadcast_wait('measure')


@proc('s size bold')
def tw(s, size, bold):
    P.measure(s, size, bold, 0, 0)
    S('tw_o', V('ms_w'))


@proc('x y w s size lh tint draw')
def para(x, y, w, s, size, lh, tint, draw):
    """wrapped multi-line text, (x, y) = centre of the first line.  draw 0 = only measure -> p_y (centre of last line)"""
    with If(draw == 1):
        P.textcmd(x, y - lh / 2, s, size, 0, tint, w, 3, lh)
    with Else():
        P.measure(s, size, 0, w, lh)
        S('p_y', y + V('ms_h') - lh / 2 - (lh - size) * 0)
        S('p_x', x)


@proc('x1 y1 x2 y2 w color')
def hand(x1, y1, x2, y2, w, color):
    """line (clock hands/ticks): a thin rotated rectangle element"""
    with If(vis(y1 - w, y1 + w) & vis(y2 - w, y2 + w)):
        S('_dx', x2 - x1)
        S('_dy', y1 - y2)                       # up is positive
        S('_hl', sqrt(V('_dx') * V('_dx') + V('_dy') * V('_dy')))
        with If(V('_dy') == 0):
            S('_hb', 90 + (V('_dx') < 0) * 180)
        with Else():
            S('_hb', mathop('atan', V('_dx') / V('_dy')) + (V('_dy') < 0) * 180)
        P.cmd(8, gx((x1 + x2) / 2), gy((y1 + y2) / 2), w * V('gs'), V('_hl') * V('gs'),
              join('sq_', item(L('pal_fam'), color)), 0, V('gh'), item(L('pal_bri'), color),
              item(L('pal_hue'), color), V('_hb'), 100, 100, 0)
