"""The Element sprite: a pool of clones, one per slot of the command buffer, plus the Measure sprite.

Every UI element on screen is one clone.  `when I receive render` each clone reads its slot of the cm_* lists:
 kinds 1-6, 8 = shapes (rect, circle, rounded rect, icon, app icon, pill, rotated line) -> costume + stretch + effects
 kind 7 = text -> Iris Text renders the string onto the clone itself.
Slot order is z-order (clones are sent to the front in slot order at start-up).
"""
from sb3 import *

POOL = 420                        # clones in the pool; the clone limit is raised with jgRuntime "set max clones"
HEX = ['%02X' % i for i in range(256)]
IRIS = 'g1nxIrisText'
FONT = 'Sans Serif'

_set = set_


def onoff(v):
    return Menu(IRIS + '_menu_ONOFF', 'ONOFF', v)


def exact(a, b):
    """case-sensitive string equality (Scratch's = ignores case) using PenguinMod's `index of text in text`"""
    return (length(a) == length(b)) & (Op('operator_indexOfTextInText', {'TEXT1': lit(a), 'TEXT2': lit(b)}) == 1)


def iris_escape(src):
    """[ and ] start Iris markup -> escape them"""
    r = Op('operator_replaceAll', {'text': lit(src), 'term': Lit('['), 'res': Lit('\\[')})
    return Op('operator_replaceAll', {'text': r, 'term': Lit(']'), 'res': Lit('\\]')})


def iris_configure(size, tint, bold, maxw, lh, src, align_expr):
    """Push style + string to Iris for *this sprite*.  Never yields: `refresh text` returns a promise (the script would
    resume a frame later, after the command buffer has been rebuilt), so it is not used - Iris repaints by itself before
    the next draw, and the width reporter lays the text out synchronously."""
    gray = VL('gray', 255)
    emit(St(IRIS + '_setFont', {'FONT': Menu(IRIS + '_menu_FONT', 'FONT', FONT)}))
    emit(St(IRIS + '_setGrowDownwardOnly', {'ENABLED': onoff('on')}))       # sprite position = centre of the FIRST line
    call_ext(IRIS + '_setBaseSize', SIZE=size)
    _set(gray, clamp(round_(255 * (1 + tint / 100)), 0, 255))
    emit(St(IRIS + '_setBaseColor', {'COLOR': ColorIn(join('#', item(L('hx'), gray + 1), item(L('hx'), gray + 1),
                                                        item(L('hx'), gray + 1)))}))
    emit(St(IRIS + '_setAlign', {'ALIGN': Menu(IRIS + '_menu_ALIGN', 'ALIGN', align_expr)}))
    with If(maxw > 0):
        call_ext(IRIS + '_setMaxWidth', WIDTH=maxw)       # NOTE: Iris makes the text box this wide (text aligned inside it)
    with Else():
        emit(St(IRIS + '_clearMaxDimensions'))
    with If(lh > 0):
        call_ext(IRIS + '_setLineHeight', HEIGHT=lh / size)
    with Else():
        call_ext(IRIS + '_setLineHeight', HEIGHT=1.2)
    car = VL('car_s', '')
    _set(car, '')
    with If(floor(bold / 2) == 1):
        _set(car, join('[color=', item(L('pal_hex'), V('c_acc')), ']|[/color]'))
    with If(floor(bold / 2) == 2):
        _set(car, '[color=rgba(0,0,0,0)]|[/color]')
    with If(bold % 2 == 1):
        call_ext(IRIS + '_setText', TEXT=join('[b]', iris_escape(src), '[/b]', car))
    with Else():
        call_ext(IRIS + '_setText', TEXT=join(iris_escape(src), car))


def define():
    L('hx', HEX)
    with unit('Element', uselib=False):
        slot, shown, k_last, a_last, dir_on = VL('slot', 0), VL('shown', 0), VL('k_last', 0), VL('a_last', ''), VL('dir_on', 0)
        z_cur = V('z_cur', 0)
        # per-clone copies of the command (read once, before anything else, so the clone never mixes two frames)
        e = {n: VL('e_' + n, 0) for n in ('k', 'x', 'y', 'w', 'h', 'a', 's', 'g', 't', 'e', 'u', 'p', 'm', 'l')}
        key, key_last, tx_w, al = VL('t_key', ''), VL('t_key_last', ''), VL('tx_w', 0), VL('t_al', 'left')

        @proc('', warp=True)
        def el_read():
            for n in e:
                _set(e[n], item(L('cm_' + n), slot))

        @proc('', warp=True)
        def el_shape():
            with If(k_last == 7):
                emit(St(IRIS + '_clearText'))
                _set(a_last, '')
                _set(key_last, '')
            with If(~exact(e['a'], a_last)):
                _set(a_last, e['a'])
                costume(a_last)
            set_stretch(e['w'] / e['p'] * 100, e['h'] / e['m'] * 100)
            effect('COLOR', e['e'])
            effect('BRIGHTNESS', e['t'])
            effect('GHOST', e['g'])
            with If(e['k'] == 8):
                point(90 + e['u'])
                _set(dir_on, 1)
            with Else():
                with If(dir_on == 1):
                    point(90)
                    _set(dir_on, 0)
            goto(e['x'], e['y'])
            _set(k_last, e['k'])

        @proc('', warp=True)
        def el_text():
            """anchor (e_p): 0 = x is the left edge, 1 = centre, 2 = right edge, 3 = wrapped paragraph (x = left, box e_m wide).
            y is always the centre of the first line."""
            _set(key, join('k', e['s'], '|', e['t'], '|', e['u'], '|', e['p'], '|', e['m'], '|', e['l'], '|',
                           V('c_acc'), '|', e['a']))
            with If((k_last != 7) | ~exact(key, key_last)):
                _set(al, 'left')
                with If(e['p'] == 1):
                    _set(al, 'center')
                with If(e['p'] == 2):
                    _set(al, 'right')
                with If(e['p'] == 3):
                    iris_configure(e['s'], e['t'], e['u'], e['m'], e['l'], e['a'], al)
                with Else():
                    iris_configure(e['s'], e['t'], e['u'], 0, e['l'], e['a'], al)
                    _set(tx_w, ext_reporter(IRIS + '_getExactTextWidth'))
                _set(key_last, key)
            set_stretch(e['w'] * 100, e['w'] * 100)
            effect('COLOR', 0)
            effect('BRIGHTNESS', 0)
            effect('GHOST', e['g'])
            with If(dir_on == 1):
                point(90)
                _set(dir_on, 0)
            # Iris centres the text box on the sprite: shift by half the box so the anchor lands on x
            goto(e['x'] + (e['p'] == 0) * (tx_w * e['w'] / 2) - (e['p'] == 2) * (tx_w * e['w'] / 2) +
                 (e['p'] == 3) * (e['m'] * e['w'] / 2), e['y'])
            _set(k_last, 7)

        with Script('receive:init_pool'):
            hide()
            emit(St('jgRuntime_setMaxClones', {'MAX': Menu('jgRuntime_menu_cloneLimit', 'cloneLimit', 1000)}))
            # paint text synchronously: with the glyph worker a changed text shows up a few frames late (flicker)
            emit(St(IRIS + '_setGlyphWorkerEnabledBlock', {'ENABLED': onoff('off')}))
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
                    P.el_read()
                    with If(e['k'] == 7):
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
            iris_configure(V('ms_size'), 0, V('ms_bold'), V('ms_maxw'), V('ms_lh'), V('ms_s'), 'left')
            _set(V('ms_w'), ext_reporter(IRIS + '_getExactTextWidth'))
            _set(V('ms_h'), ext_reporter(IRIS + '_getExactTextHeight'))
