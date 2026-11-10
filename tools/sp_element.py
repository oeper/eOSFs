"""The Element sprite: a pool of clones, one per slot of the command buffer, plus the Measure sprite.

Every UI element on screen is one clone.  `when I receive render` each clone reads its slot of the cm_* lists:
 kinds 1-6, 8 = shapes (rect, circle, rounded rect, icon, app icon, pill, rotated line) -> costume + stretch + effects
 kind 7 = text -> Iris Text renders the string onto the clone itself.
Slot order is z-order (clones are sent to the front in slot order at start-up).
"""
from sb3 import *

POOL = 270                        # < 300 (stock Scratch clone limit)
HEX = ['%02X' % i for i in range(256)]
IRIS = 'g1nxIrisText'


def _escape(src):
    """proc body: esc_o = src with [ and ] escaped for Iris markup"""
    S_ = set_
    esc_o, i, ch = VL('esc_o', ''), VL('esc_i', 1), VL('esc_c', '')
    S_(esc_o, src)
    with If(contains(src, '[') | contains(src, ']')):
        S_(esc_o, '')
        S_(i, 1)
        with repeat(length(src)):
            S_(ch, letter(i, src))
            with If((ch == '[') | (ch == ']')):
                S_(esc_o, join(esc_o, '\\'))
            S_(esc_o, join(esc_o, ch))
            change(i, 1)
    return esc_o


_set = set_


def _text_setup(size, tint, bold, maxw, lh, src):
    """configure the Iris state of *this sprite* and render the string; leaves width/height in tx_w/tx_h"""
    tx_w, tx_h = VL('tx_w', 0), VL('tx_h', 0)
    gray = VL('gray', 255)
    call_ext(IRIS + '_setBaseSize', SIZE=size)
    _set(gray, clamp(round_(255 * (1 + tint / 100)), 0, 255))
    emit(St(IRIS + '_setBaseColor', {'COLOR': ColorIn(join('#', item(L('hx'), gray + 1), item(L('hx'), gray + 1),
                                                        item(L('hx'), gray + 1)))}))
    emit(St(IRIS + '_setAlign', {'ALIGN': Menu(IRIS + '_menu_ALIGN', 'ALIGN', 'left')}))
    with If(maxw > 0):
        call_ext(IRIS + '_setMaxWidth', WIDTH=maxw)
    with Else():
        emit(St(IRIS + '_clearMaxDimensions'))
    with If(lh > 0):
        call_ext(IRIS + '_setLineHeight', HEIGHT=lh / size)
    with Else():
        call_ext(IRIS + '_setLineHeight', HEIGHT=1.2)
    esc = _escape(src)
    car = VL('car_s', '')
    _set(car, '')
    with If(floor(bold / 2) == 1):
        _set(car, join('[color=', item(L('pal_hex'), V('c_acc')), ']|[/color]'))
    with If(floor(bold / 2) == 2):
        _set(car, '[color=rgba(0,0,0,0)]|[/color]')
    with If(bold % 2 == 1):
        call_ext(IRIS + '_setText', TEXT=join('[b]', esc, '[/b]', car))
    with Else():
        call_ext(IRIS + '_setText', TEXT=join(esc, car))
    emit(St(IRIS + '_renderNow'))
    _set(tx_w, ext_reporter(IRIS + '_getExactTextWidth'))
    _set(tx_h, ext_reporter(IRIS + '_getExactTextHeight'))


def define():
    L('hx', HEX)
    with unit('Element', uselib=False):
        slot, shown, k_last, a_last, dir_on = VL('slot', 0), VL('shown', 0), VL('k_last', 0), VL('a_last', ''), VL('dir_on', 0)
        z_cur = V('z_cur', 0)

        @proc('')
        def el_shape():
            k = item(L('cm_k'), slot)
            with If(k_last == 7):
                emit(St(IRIS + '_clearText'))
                _set(a_last, '')
            with If(item(L('cm_a'), slot) != a_last):
                _set(a_last, item(L('cm_a'), slot))
                costume(a_last)
            set_stretch(item(L('cm_w'), slot) / item(L('cm_p'), slot) * 100,
                        item(L('cm_h'), slot) / item(L('cm_m'), slot) * 100)
            effect('COLOR', item(L('cm_e'), slot))
            effect('BRIGHTNESS', item(L('cm_t'), slot))
            effect('GHOST', item(L('cm_g'), slot))
            with If(k == 8):
                point(90 + item(L('cm_u'), slot))
                _set(dir_on, 1)
            with Else():
                with If(dir_on == 1):
                    point(90)
                    _set(dir_on, 0)
            goto(item(L('cm_x'), slot), item(L('cm_y'), slot))
            _set(k_last, k)

        @proc('')
        def el_text():
            sc = item(L('cm_w'), slot)
            anchor = item(L('cm_p'), slot)
            _text_setup(item(L('cm_s'), slot), item(L('cm_t'), slot), item(L('cm_u'), slot), item(L('cm_m'), slot),
                        item(L('cm_l'), slot), item(L('cm_a'), slot))
            tx_w, tx_h = VL('tx_w'), VL('tx_h')
            set_stretch(sc * 100, sc * 100)
            effect('COLOR', 0)
            effect('BRIGHTNESS', 0)
            effect('GHOST', item(L('cm_g'), slot))
            point(90)
            _set(dir_on, 0)
            goto(item(L('cm_x'), slot) + ((anchor == 0) | (anchor == 3)) * (tx_w * sc / 2) - (anchor == 2) * (tx_w * sc / 2),
                 item(L('cm_y'), slot) - (anchor == 3) * (tx_h * sc / 2))
            _set(k_last, 7)

        with Script('receive:init_pool'):
            hide()
            _set(slot, 0)
            with repeat(POOL):
                _set(slot, slot + 1)
                create_clone('_myself_')
            _set(slot, 0)
            _set(z_cur, 0)
            with repeat(POOL):                    # z-order: slot 1 at the back ... slot POOL in front
                _set(z_cur, z_cur + 1)
                broadcast_wait('z_front')

        with Script('receive:z_front'):
            with If(slot == z_cur):
                go_front()

        with Script('receive:render'):
            with If(slot > 0):
                with If(slot <= V('cm_n')):
                    with If(item(L('cm_k'), slot) == 7):
                        P.el_text()
                    with Else():
                        P.el_shape()
                    with If(shown == 0):
                        show()
                        _set(shown, 1)
                with Else():
                    with If(shown == 1):
                        hide()
                        _set(shown, 0)

    with unit('Measure', uselib=False):
        with Script('receive:measure'):
            hide()
            _text_setup(V('ms_size'), 0, V('ms_bold'), V('ms_maxw'), V('ms_lh'), V('ms_s'))
            _set(V('ms_w'), VL('tx_w'))
            _set(V('ms_h'), VL('tx_h'))
