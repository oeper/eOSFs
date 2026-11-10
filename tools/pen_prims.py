V('fade', 0)
# Pen (stamp) drawing primitives - exec'd into os_core's namespace in pen mode.
@proc('x y w h c')
def rect(x, y, w, h, c):
    with If((w > 0) & (h > 0) & vis(y, y + h)):
        costume(c + 0)
        effect('GHOST', V('gh') + (100 - V('gh')) * V('fade') / 100)
        set_stretch(w * V('gs'), h * V('gs'))
        goto(V('gox') + (x + w / 2) * V('gs') - 320, 180 - V('goy') - (y + h / 2) * V('gs'))
        stamp()


@proc('cx cy d c')
def circle(cx, cy, d, c):
    with If((d > 0) & vis(cy - d / 2, cy + d / 2)):
        costume(c + NP)
        effect('GHOST', V('gh') + (100 - V('gh')) * V('fade') / 100)
        set_stretch(d * V('gs'), d * V('gs'))
        goto(V('gox') + cx * V('gs') - 320, 180 - V('goy') - cy * V('gs'))
        stamp()


@proc('x y w h r c')
def rrect(x, y, w, h, r, c):
    with If(vis(y, y + h)):
        P.rrect_raw(x, y, w, h, r, c)


@proc('x y w h r c', name='rrect_raw')
def _rrect_raw(x, y, w, h, r, c):
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
    with If(vis(y - size * 0.7, y + size * 0.7)):
        P.text_raw(x, y, s, size, bold, tint, maxw)


@proc('x y s size bold tint maxw', name='text_raw')
def _text_raw(x, y, s, size, bold, tint, maxw):
    """y = vertical centre of the text line.  bold 0/1.  tint = brightness (0 white, -90 near black)."""
    with If(bold == 1):
        S('_pf', 'b')
    with Else():
        S('_pf', 'g')
    effect('BRIGHTNESS', tint)
    effect('GHOST', V('gh') + (100 - V('gh')) * V('fade') / 100)
    set_stretch(size * V('gs'), size * V('gs'))
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
                goto(V('gox') + V('_tx') * V('gs') - 320, 180 - V('goy') - (y + size * 0.36) * V('gs'))
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
    set_stretch(size * V('gs'), size * V('gs'))
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
            with If((draw == 1) & (V('_pcs') == 1) & vis(V('_py') - size * 0.7, V('_py') + size * 0.7)):
                goto(V('gox') + V('_px') * V('gs') - 320, 180 - V('goy') - (V('_py') + size * 0.36) * V('gs'))
                stamp()
            change(V('_px'), V('_pw'))
        inc('_pi')
    S('p_x', V('_px'))
    S('p_y', V('_py'))
    effect('BRIGHTNESS', 0)


@proc('name cx cy size tint')
def icon(name, cx, cy, size, tint):
    with If(vis(cy - size / 2, cy + size / 2)):
        P.icon_raw(name, cx, cy, size, tint)


@proc('name cx cy size tint', name='icon_raw')
def _icon_raw(name, cx, cy, size, tint):
    costume(join('i_', name))
    effect('BRIGHTNESS', tint)
    effect('GHOST', V('gh') + (100 - V('gh')) * V('fade') / 100)
    set_stretch(size * 100 / 24 * V('gs'), size * 100 / 24 * V('gs'))
    goto(V('gox') + cx * V('gs') - 320, 180 - V('goy') - cy * V('gs'))
    stamp()
    effect('BRIGHTNESS', 0)


@proc('name cx cy size')
def appicon(name, cx, cy, size):
    with If(vis(cy - size / 2, cy + size / 2)):
        P.appicon_raw(name, cx, cy, size)


@proc('name cx cy size', name='appicon_raw')
def _appicon_raw(name, cx, cy, size):
    costume(join('a_', name))
    effect('GHOST', V('gh') + (100 - V('gh')) * V('fade') / 100)
    set_stretch(size * V('gs'), size * V('gs'))
    goto(V('gox') + cx * V('gs') - 320, 180 - V('goy') - cy * V('gs'))
    stamp()


@proc('cx cy tint gh_')
def pillkey(cx, cy, tint, gh_):
    """64x38 pill, tinted + translucent (single stamp, so no alpha overlap artefacts)"""
    costume('k_pill')
    effect('BRIGHTNESS', tint)
    effect('GHOST', gh_)
    set_stretch(100 * V('gs'), 100 * V('gs'))
    goto(V('gox') + cx * V('gs') - 320, 180 - V('goy') - cy * V('gs'))
    stamp()
    effect('BRIGHTNESS', 0)
    effect('GHOST', 0)




@proc('x1 y1 x2 y2 w color')
def hand(x1, y1, x2, y2, w, color):
    """round-capped pen line in UI coordinates (clock hands/ticks)"""
    with If(vis(y1 - w, y1 + w) & vis(y2 - w, y2 + w)):
        P.hand_raw(x1, y1, x2, y2, w, color)


@proc('x1 y1 x2 y2 w color', name='hand_raw')
def _hand_raw(x1, y1, x2, y2, w, color):
    pen_up()
    pen_color(item(L('pal_hex'), color))
    pen_size(w * V('gs'))
    goto(V('gox') + x1 * V('gs') - 320, 180 - V('goy') - y1 * V('gs'))
    pen_down()
    goto(V('gox') + x2 * V('gs') - 320, 180 - V('goy') - y2 * V('gs'))
    pen_up()


