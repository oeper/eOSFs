"""eOS system UI: boot, lock, home, status/nav bars, keyboard, quick settings, dialogs, recents, main loop."""
from sb3 import *
from os_core import *

KB_H = 130

for _n, _v in [('navmode', 1), ('anim_n', 10), ('gmode', 0), ('gtype', 0), ('gt', 0), ('ga_s', 1), ('ga_cx', W / 2),
               ('ga_cy', H / 2), ('gx0', 0), ('boot_t', 0), ('pin_in', ''), ('pin_show', 0), ('back_o', 0), ('kb_k', ''), ('_kbx', 0),
               ('pad_o', ''), ('rc_n', 0), ('qs_h', 0), ('lock_t', 0)]:
    V(_n, _v)


# ------------------------------------------------------------------ boot ---
@proc('')
def draw_boot():
    P.rect(0, 0, W, H, pal('black'))
    P.text_c(W / 2, 150, 'eOS', 64, 1, 0)
    P.text_c(W / 2, 196, 'PenguinMod edition', 12, 0, -45)
    P.rrect(W / 2 - 80, 250, 160, 6, 3, pal('dgray'))
    P.rrect(W / 2 - 80, 250, 160 * V('boot_t') / 70, 6, 3, pal('white'))
    inc('boot_t')
    with If(V('boot_t') > 70):
        S('screen', SCR_LOCK)
        S('lock_t', 0)
        P.theme()


# ------------------------------------------------------------------ lock ---
@proc('')
def draw_lock():
    with If(V('dark') == 1):
        S('gh', 80)
        P.rect(0, 0, W, H, pal('black'))
        S('gh', 0)
    inc('lock_t')
    with If(V('pin_show') == 0):
        P.text_c(W / 2, 112, V('tstr'), 72, 1, 0)
        P.tw(V('tstr'), 72, 1)
        P.text(W / 2 + V('tw_o') / 2 + 8, 134, V('ampm'), 16, 1, -10, 0)
        P.text_c(W / 2, 168, V('dstr'), 16, 0, 0)
        P.icon('lock', W / 2, 262, 20, 0)
        P.text_c(W / 2, 300, 'Tap to unlock', 13, 0, -20 - 25 * abs_(sin(V('lock_t') * 4)))
        P.tapr(0, SB, W, H - SB)
        with If(V('tap_o') == 1):
            with If(V('pin') == ''):
                S('screen', SCR_HOME)
            with Else():
                S('pin_show', 1)
                S('pin_in', '')
    with Else():
        P.text_c(W / 2, 54, V('tstr'), 34, 1, 0)
        P.text_c(W / 2, 86, 'Enter PIN', 13, 0, -15)
        # dots
        S('_pd', 0)
        with repeat(4):
            inc('_pd')
            with If(length(V('pin_in')) >= V('_pd')):
                P.circle(W / 2 - 54 + V('_pd') * 27 - 13.5, 112, 13, pal('white'))
            with Else():
                P.circle(W / 2 - 54 + V('_pd') * 27 - 13.5, 112, 13, pal('dgray'))
        P.pinpad(128)
        with If(V('pin_back') == 1):
            S('pin_back', 0)
            S('pin_show', 0)
            S('pin_in', '')
        with If(V('pin_ok') == 1):
            S('pin_ok', 0)
            with If(V('pin_in') == V('pin')):
                S('screen', SCR_HOME)
                S('pin_show', 0)
                S('pin_in', '')
            with Else():
                S('pin_in', '')
                P.notify('Wrong PIN')


@proc('top')
def pinpad(top):
    """digit pad (lock screen + Settings).  Edits pin_in; sets pin_ok=1 once 4 digits typed, pin_back=1 on Back."""
    S('_pk', 0)
    with repeat(12):
        inc('_pk')
        S('_pcx', W / 2 + ((V('_pk') - 1) % 3 - 1) * 76)
        S('_pcy', top + floor((V('_pk') - 1) / 3) * 46)
        S('_pl', V('_pk'))
        with If(V('_pk') == 10):
            S('_pl', 'Back')
        with If(V('_pk') == 11):
            S('_pl', 0)
        with If(V('_pk') == 12):
            S('_pl', 'Del')
        P.tap(V('_pcx') - 32, V('_pcy'), 64, 38)
        S('_pt', V('tap_o'))
        S('_pg', 50)
        with If((V('hit_o') == 1) & (V('md') == 1)):
            S('_pg', 25)
        P.pillkey(V('_pcx'), V('_pcy') + 19, -100, V('_pg'))
        P.text_c(V('_pcx'), V('_pcy') + 19, V('_pl'), 15, 1, 0)
        with If(V('_pt') == 1):
            with If(V('_pk') == 10):
                S('pin_back', 1)
            with If(V('_pk') == 12):
                P.drop_last_pin()
            with If((V('_pk') != 10) & (V('_pk') != 12) & (length(V('pin_in')) < 4)):
                with If(V('_pk') == 11):
                    S('pin_in', join(V('pin_in'), 0))
                with Else():
                    S('pin_in', join(V('pin_in'), V('_pk')))
                with If(length(V('pin_in')) == 4):
                    S('pin_ok', 1)


for _n in ('pin_ok', 'pin_back'):
    V(_n, 0)


@proc('')
def drop_last_pin():
    S('_dn', length(V('pin_in')) - 1)
    with If(V('_dn') >= 0):
        S('_ds', '')
        S('_di', 1)
        with until(V('_di') > V('_dn')):
            S('_ds', join(V('_ds'), letter(V('_di'), V('pin_in'))))
            inc('_di')
        S('pin_in', V('_ds'))


# ------------------------------------------------------------------ home ---
@proc('')
def draw_home():
    with If(V('dark') == 1):
        S('gh', 82)
        P.rect(0, 0, W, H, pal('black'))
        S('gh', 0)
    P.text_c(W / 2, 74, V('tstr'), 56, 1, 0)
    P.tw(V('tstr'), 56, 1)
    P.text(W / 2 + V('tw_o') / 2 + 6, 90, V('ampm'), 14, 1, -10, 0)
    P.text_c(W / 2, 112, V('dstr'), 14, 0, -10)
    S('_ai', 0)
    with repeat(8):
        inc('_ai')
        S('_ax', 93 + ((V('_ai') - 1) % 4) * 130)
        S('_ay', 146 + floor((V('_ai') - 1) / 4) * 98)
        P.tapr(V('_ax') - 10, V('_ay') - 6, 84, 92)
        S('_at', V('tap_o'))
        S('_asz', 62)
        with If((V('hit_o') == 1) & (V('md') == 1) & (V('moved') == 0)):
            S('_asz', 56)
        P.appicon(item(L('app_icon'), V('_ai')), V('_ax') + 32, V('_ay') + 31, V('_asz'))
        P.text_c(V('_ax') + 32, V('_ay') + 76, item(L('app_name'), V('_ai')), 12, 1, 0)
        with If(V('_at') == 1):
            P.launch(V('_ai'), V('_ax'), V('_ay'))


@proc('a ox oy')
def launch(a, ox, oy):
    S('app', a)
    S('view', 0)
    S('scroll', 0)
    S('kb_open', 0)
    S('qs_open', 0)
    S('open_x', ox)
    S('open_y', oy)
    S('open_t', 0)
    S('gmode', 0)
    with If(indexof(L('rec'), a) == 0):
        P.app_init(a)
    with Else():
        list_delete(L('rec'), indexof(L('rec'), a))
    list_add(L('rec'), a)
    S('screen', SCR_APP)


@proc('s cx cy')
def set_tf(s_, cx, cy):
    """draw everything that follows scaled by s_ and centred on (cx, cy)"""
    S('gs', s_)
    S('gox', cx - W / 2 * s_)
    S('goy', cy - H / 2 * s_)


@proc('')
def close_app_anim():
    """shrink the foreground app into its home-screen icon, then go home"""
    with If(V('gmode') != 1):
        S('ga_s', 1)
        S('ga_cx', W / 2)
        S('ga_cy', H / 2)
    S('kb_open', 0)
    S('qs_open', 0)
    S('gmode', 2)
    S('gt', 0)


@proc('')
def gesture_update():
    """gesture-bar navigation (navmode 1): drag the bar up to shrink/close the app, edge-swipe for back"""
    with If((V('navmode') == 1) & (V('dlg') == 0) & (V('screen') >= SCR_HOME) & (V('gmode') <= 1)):
        with If(V('press') == 1):
            S('gtype', 0)
            with If(V('my') >= H - NB):
                S('gtype', 1)
                S('gx0', V('mx'))
                S('press', 0)
                S('moved', 1)
            with Else():
                with If((V('mx') < 14) | (V('mx') > W - 14)):
                    S('gtype', 2)
                    S('press', 0)
                    S('moved', 1)
        with If((V('gtype') == 1) & (V('md') == 1) & (V('screen') == SCR_APP) & (V('open_t') >= V('anim_n'))):
            S('gmode', 1)
            S('kb_open', 0)
            S('qs_open', 0)
            S('_gd', clamp((H - V('my')) / H, 0, 1))
            S('ga_s', clamp(1 - V('_gd') * 0.95, 0.22, 1))
            S('ga_cx', W / 2 + (V('mx') - V('gx0')))
            S('ga_cy', V('my') - V('ga_s') * H / 2 + 10)
        with If((V('gtype') != 0) & (V('rel') == 1)):
            S('rel', 0)
            with If(V('gtype') == 1):
                with If(V('gmode') == 1):
                    with If(V('my') < H * 0.74):
                        S('gmode', 2)
                        S('gt', 0)
                    with Else():
                        with If(V('ga_s') > 0.97):
                            S('gmode', 0)
                        with Else():
                            S('gmode', 3)
                            S('gt', 0)
                S('_gs', V('screen'))
                with If((V('_gs') == SCR_HOME) & (V('py') - V('my') > 60)):
                    P.nav_recents()
                with If((V('_gs') == SCR_REC) & (V('py') - V('my') > 60)):
                    P.nav_home()
            with If((V('gtype') == 2) & (abs_(V('mx') - V('px')) > 40)):
                P.nav_back()
            S('gtype', 0)
    with If(V('md') == 0):
        S('gtype', 0)


# --------------------------------------------------------------- recents ---
@proc('')
def draw_recents():
    S('cur_layer', 1)
    S('gh', 45)
    P.rect(0, 0, W, H, pal('black'))
    S('gh', 0)
    S('rc_n', listlen(L('rec')))
    with If(V('rc_n') == 0):
        P.text_c(W / 2, 170, 'No recent apps', 16, 1, 0)
    with Else():
        P.text_c(W / 2, 54, 'Recent apps', 16, 1, 0)
    S('_ri', V('rc_n') + 1)
    S('_rk', 0)
    with repeat(V('rc_n')):
        inc('_ri', -1)
        S('_rapp', item(L('rec'), V('_ri')))
        S('_rx', 50 + (V('_rk') % 2) * 280)
        S('_ry', 76 + floor(V('_rk') / 2) * 58)
        inc('_rk')
        # close button first (sits on top of the card)
        P.tapr(V('_rx') + 214, V('_ry') + 8, 32, 32)
        S('_rcl', V('tap_o'))
        P.tapr(V('_rx'), V('_ry'), 260, 48)
        S('_rt', V('tap_o'))
        P.rrect(V('_rx'), V('_ry'), 260, 48, 12, V('c_surf'))
        P.appicon(item(L('app_icon'), V('_rapp')), V('_rx') + 26, V('_ry') + 24, 34)
        P.text(V('_rx') + 52, V('_ry') + 24, item(L('app_name'), V('_rapp')), 14, 1, V('tx'), 150)
        P.icon('close', V('_rx') + 230, V('_ry') + 24, 16, V('tx2'))
        with If(V('_rcl') == 1):
            list_delete(L('rec'), V('_ri'))
            S('_rt', 0)
        with If(V('_rt') == 1):
            P.launch(V('_rapp'), V('_rx') - 5, V('_ry') - 7)
    with If(V('rc_n') > 0):
        P.btn(W / 2 - 60, 296, 120, 30, 'Close all', 0)
        with If(V('tap_o') == 1):
            list_clear(L('rec'))


# ------------------------------------------------------------ status/nav ---
@proc('mode')
def statusbar(mode):
    S('cur_layer', 1)
    S('_st', 0)
    S('_sv', V('tx'))
    with If(mode == 0):
        S('_sv', 0)
    with Else():
        P.rect(0, 0, W, SB, V('c_bg'))
    P.text(14, SB / 2, V('tstr'), 12, 1, V('_sv'), 0)
    with If(V('h24') == 0):
        P.text(14 + 8 + 5.6 * length(V('tstr')), SB / 2, V('ampm'), 9, 1, V('_sv'), 0)
    with If(V('wifi') == 1):
        P.icon('wifi', W - 64, SB / 2, 14, V('_sv'))
    with Else():
        P.icon('wifi_off', W - 64, SB / 2, 14, V('_sv'))
    with If(mode == 0):
        P.rrect(W - 46, SB / 2 - 5.5, 24, 11, 3, pal('gray'))
        P.rrect(W - 44, SB / 2 - 3.5, 20, 7, 1.5, pal('white'))
    with Else():
        P.rrect(W - 46, SB / 2 - 5.5, 24, 11, 3, V('c_div'))
        P.rrect(W - 44, SB / 2 - 3.5, 20, 7, 1.5, pal('green'))
    P.rect(W - 21.5, SB / 2 - 2, 2, 4, pal('gray'))
    P.tapr(0, 0, W, SB)
    with If((V('tap_o') == 1) & (V('screen') != SCR_LOCK)):
        S('qs_open', 1 - V('qs_open'))
        S('kb_open', 0)


@proc('mode')
def navbar(mode):
    S('cur_layer', 1)
    S('_nv', V('tx'))
    with If(mode == 0):
        S('_nv', 0)
    with Else():
        P.rect(0, H - NB, W, NB, V('c_bg'))
    S('_ny', H - NB / 2)
    with If(V('navmode') == 1):
        S('_pc', pal('white'))
        with If((mode == 1) & (V('dark') == 0)):
            S('_pc', pal('black'))
        S('_pw', 110)
        with If(V('gtype') == 1):
            S('_pw', 140)
        P.rrect(W / 2 - V('_pw') / 2, H - 12, V('_pw'), 5, 2.5, V('_pc'))
    with Else():
        P.icon('back', W / 2 - 100, V('_ny'), 18, V('_nv'))
        P.icon('home', W / 2, V('_ny'), 18, V('_nv'))
        P.icon('recents', W / 2 + 100, V('_ny'), 18, V('_nv'))
        P.tapr(W / 2 - 150, H - NB, 100, NB)
        with If(V('tap_o') == 1):
            P.nav_back()
        P.tapr(W / 2 - 50, H - NB, 100, NB)
        with If(V('tap_o') == 1):
            P.nav_home()
        P.tapr(W / 2 + 50, H - NB, 100, NB)
        with If(V('tap_o') == 1):
            P.nav_recents()


@proc('')
def nav_home():
    P.store_save()
    S('kb_open', 0)
    S('qs_open', 0)
    with If((V('screen') == SCR_APP) & (V('gmode') == 0) & (V('open_t') >= V('anim_n'))):
        P.close_app_anim()
    with Else():
        S('screen', SCR_HOME)
        S('gmode', 0)
        S('open_t', 99)


@proc('')
def nav_recents():
    S('kb_open', 0)
    S('qs_open', 0)
    with If(V('screen') == SCR_REC):
        S('screen', SCR_HOME)
    with Else():
        S('screen', SCR_REC)


@proc('')
def nav_back():
    with If(V('kb_open') == 1):
        S('kb_open', 0)
    with Else():
        with If(V('qs_open') == 1):
            S('qs_open', 0)
        with Else():
            with If(V('screen') == SCR_REC):
                S('screen', SCR_HOME)
            with If(V('screen') == SCR_APP):
                S('back_o', 0)
                P.app_back()
                with If(V('back_o') == 0):
                    P.close_app_anim()


# --------------------------------------------------------------- keyboard --
L('kb_r1l', list('qwertyuiop'))

KB_PAGES = {
    # page: (row1, row2, row3 letters)
    0: ('qwertyuiop', 'asdfghjkl', 'zxcvbnm'),
    1: ('qwertyuiop'.upper(), 'asdfghjkl'.upper(), 'zxcvbnm'.upper()),
    2: ('1234567890', '-/:;()$&@"', ".,?!'_*"),
    3: ('[]{}#%^*+=', '_\\|~<>`@&$', ".,?!'-:"),
}


@proc('prompt init act multi maxlen')
def kb_begin(prompt, init, act, multi, maxlen):
    S('kb_prompt', prompt)
    S('ti', init)
    S('ti_act', act)
    S('ti_multi', multi)
    S('kb_max', maxlen)
    S('kb_open', 1)
    S('kb_done', 0)
    S('kb_page', 0)
    S('kb_shift', 0)
    S('qs_open', 0)


@proc('')
def drop_last():
    S('_dn', length(V('ti')) - 1)
    with If(V('_dn') >= 0):
        S('_ds', '')
        S('_di', 1)
        with until(V('_di') > V('_dn')):
            S('_ds', join(V('_ds'), letter(V('_di'), V('ti'))))
            inc('_di')
        S('ti', V('_ds'))


@proc('ch')
def kb_type(ch):
    with If(length(V('ti')) < V('kb_max')):
        S('ti', join(V('ti'), ch))
    with If(V('kb_shift') == 1):
        S('kb_shift', 0)


@proc('y chars x0')
def kb_row(y, chars, x0):
    S('_ki', 0)
    S('_kn', length(chars))
    with repeat(V('_kn')):
        inc('_ki')
        S('_kc', letter(V('_ki'), chars))
        S('_kx', x0 + (V('_ki') - 1) * 60)
        P.tap(V('_kx'), y, 56, 26)
        S('_kt', V('tap_o'))
        S('_kcol', V('c_surf'))
        with If((V('hit_o') == 1) & (V('md') == 1)):
            S('_kcol', V('c_div'))
        P.rrect(V('_kx'), y, 56, 26, 6, V('_kcol'))
        P.text_c(V('_kx') + 28, y + 13, V('_kc'), 15, 0, V('tx'))
        with If(V('_kt') == 1):
            P.kb_type(V('_kc'))


@proc('x y w h label ic')
def kb_fn(x, y, w, h, label, ic):
    """function key (shift/backspace/enter/page): draws, sets tap_o"""
    P.tap(x, y, w, h)
    S('_ft', V('tap_o'))
    S('_fcol', V('c_div'))
    with If((V('hit_o') == 1) & (V('md') == 1)):
        S('_fcol', V('c_surf'))
    P.rrect(x, y, w, h, 6, V('_fcol'))
    with If(ic != ''):
        P.icon(ic, x + w / 2, y + h / 2, 17, V('tx'))
    with Else():
        P.text_c(x + w / 2, y + h / 2, label, 12, 1, V('tx'))
    S('tap_o', V('_ft'))


@proc('')
def draw_keyboard():
    S('cur_layer', 1)
    S('kb_top', H - NB - KB_H)
    S('_ky', V('kb_top'))
    P.rect(0, V('kb_top'), W, KB_H, V('c_surf2'))
    P.rect(0, V('kb_top'), W, 1, V('c_div'))
    S('_p', V('kb_page'))
    # row 1 / 2
    def rows(page):
        P.kb_row(V('_ky') + 6, KB_PAGES[page][0], 22)
        P.kb_row(V('_ky') + 37, KB_PAGES[page][1], 52 if page < 2 else 22)
        P.kb_row(V('_ky') + 68, KB_PAGES[page][2], 102)
    with If(V('kb_page') == 0):
        with If(V('kb_shift') == 1):
            rows(1)
        with Else():
            rows(0)
    with Else():
        with If(V('kb_page') == 1):
            rows(2)
        with Else():
            rows(3)
    # row 3 function keys
    with If(V('kb_page') == 0):
        with If(V('kb_shift') == 1):
            P.kb_fn(22, V('_ky') + 68, 76, 26, '', 'shift_on')
        with Else():
            P.kb_fn(22, V('_ky') + 68, 76, 26, '', 'shift')
        with If(V('tap_o') == 1):
            S('kb_shift', 1 - V('kb_shift'))
    with Else():
        with If(V('kb_page') == 1):
            P.kb_fn(22, V('_ky') + 68, 76, 26, '#+=', '')
            with If(V('tap_o') == 1):
                S('kb_page', 2)
        with Else():
            P.kb_fn(22, V('_ky') + 68, 76, 26, '123', '')
            with If(V('tap_o') == 1):
                S('kb_page', 1)
    P.kb_fn(522, V('_ky') + 68, 96, 26, '', 'backspace')
    with If(V('tap_o') == 1):
        P.drop_last()
    # row 4
    with If(V('kb_page') == 0):
        P.kb_fn(22, V('_ky') + 99, 76, 26, '123', '')
        with If(V('tap_o') == 1):
            S('kb_page', 1)
    with Else():
        P.kb_fn(22, V('_ky') + 99, 76, 26, 'ABC', '')
        with If(V('tap_o') == 1):
            S('kb_page', 0)
    P.kb_row(V('_ky') + 99, ',', 102)
    P.kb_fn(162, V('_ky') + 99, 288, 26, '', '')
    with If(V('tap_o') == 1):
        P.kb_type(' ')
    P.kb_row(V('_ky') + 99, '.', 454)
    P.kb_fn(514, V('_ky') + 99, 104, 26, '', 'enter')
    with If(V('tap_o') == 1):
        with If(V('ti_multi') == 1):
            P.kb_type('\n')
        with Else():
            S('kb_done', 1)
    P.kb_physical()


@proc('')
def kb_physical():
    """physical keyboard: letters, digits, space, enter (edge-detected through a held-key string)"""
    S('_pk_now', '')
    S('_pi2', 0)
    with repeat(37):
        inc('_pi2')
        S('_pkc', letter(V('_pi2'), 'abcdefghijklmnopqrstuvwxyz0123456789 '))
        with If(key_pressed(V('_pkc'))):
            S('_pk_now', join(V('_pk_now'), V('_pkc')))
            with If(~contains(V('pk_held'), V('_pkc'))):
                P.kb_type(V('_pkc'))
    with If(key_pressed('enter')):
        with If(~contains(V('pk_held'), '#')):
            with If(V('ti_multi') == 1):
                P.kb_type('\n')
            with Else():
                S('kb_done', 1)
        S('_pk_now', join(V('_pk_now'), '#'))
    S('pk_held', V('_pk_now'))


V('pk_held', '')


# ------------------------------------------------------------ quick settings
@proc('')
def draw_qs():
    S('cur_layer', 1)
    S('gh', 50)
    P.rect(0, 0, W, H, pal('black'))
    S('gh', 0)
    P.tapr(0, 176, W, H - 176)
    with If(V('tap_o') == 1):
        S('qs_open', 0)
    P.rrect(20, SB + 2, W - 40, 150, 18, V('c_surf'))
    S('_qi', 0)
    with repeat(4):
        inc('_qi')
        S('_qx', 34 + (V('_qi') - 1) * 148)
        S('_qy', SB + 14)
        S('_qon', 0)
        S('_qn', '')
        S('_qic', '')
        with If(V('_qi') == 1):
            S('_qon', V('wifi'))
            S('_qn', 'Wi-Fi')
            S('_qic', 'wifi')
        with If(V('_qi') == 2):
            S('_qon', V('dark'))
            S('_qn', 'Dark mode')
            S('_qic', 'moon')
        with If(V('_qi') == 3):
            S('_qon', V('bt'))
            S('_qn', 'Bluetooth')
            S('_qic', 'bt')
        with If(V('_qi') == 4):
            S('_qon', 0)
            S('_qn', 'Lock')
            S('_qic', 'lock')
        P.tapr(V('_qx'), V('_qy'), 136, 62)
        S('_qt', V('tap_o'))
        with If(V('_qon') == 1):
            P.rrect(V('_qx'), V('_qy'), 136, 62, 14, V('c_acc'))
            P.icon(V('_qic'), V('_qx') + 68, V('_qy') + 22, 22, 0)
            P.text_c(V('_qx') + 68, V('_qy') + 47, V('_qn'), 12, 1, 0)
        with Else():
            P.rrect(V('_qx'), V('_qy'), 136, 62, 14, V('c_surf2'))
            P.icon(V('_qic'), V('_qx') + 68, V('_qy') + 22, 22, V('tx'))
            P.text_c(V('_qx') + 68, V('_qy') + 47, V('_qn'), 12, 1, V('tx'))
        with If(V('_qt') == 1):
            with If(V('_qi') == 1):
                S('wifi', 1 - V('wifi'))
            with If(V('_qi') == 2):
                S('dark', 1 - V('dark'))
                P.theme()
            with If(V('_qi') == 3):
                S('bt', 1 - V('bt'))
            with If(V('_qi') == 4):
                S('qs_open', 0)
                S('screen', SCR_LOCK)
                S('pin_show', 0)
    P.icon('sun', 52, SB + 108, 18, V('tx2'))
    P.slider(90, 76, SB + 108, W - 150, V('bright'))
    S('bright', clamp(V('sl_o'), 15, 100))


# ----------------------------------------------------------------- dialog --
@proc('')
def draw_dialog():
    S('cur_layer', 2)
    S('gh', 40)
    P.rect(0, 0, W, H, pal('black'))
    S('gh', 0)
    P.rrect(W / 2 - 150, 100, 300, 150, 18, V('c_surf'))
    P.text(W / 2 - 128, 126, V('dlg_title'), 16, 1, V('tx'), 256)
    P.para(W / 2 - 128, 156, 256, V('dlg_msg'), 13, 18, V('tx2'), 1)
    P.btn(W / 2 - 134, 204, 124, 34, 'Cancel', 0)
    with If(V('tap_o') == 1):
        S('dlg', 0)
    P.btn(W / 2 + 10, 204, 124, 34, V('dlg_ok'), 2)
    with If(V('tap_o') == 1):
        S('dlg', 0)
        P.dlg_run()


@proc('title msg ok act arg')
def ask(title, msg, ok, act, arg):
    S('dlg_title', title)
    S('dlg_msg', msg)
    S('dlg_ok', ok)
    S('dlg_act', act)
    S('dlg_arg', arg)
    S('dlg', 1)
    S('kb_open', 0)


@proc('')
def draw_toast():
    with If(V('toast_t') > 0):
        inc('toast_t', -1)
        P.tw(V('toast'), 13, 1)
        S('gh', 0)
        with If(V('toast_t') < 14):
            S('gh', 100 - V('toast_t') * 100 / 14)
        P.rrect(W / 2 - V('tw_o') / 2 - 16, SB + 8, V('tw_o') + 32, 30, 15, pal('black'))
        P.text_c(W / 2, SB + 23, V('toast'), 13, 1, 0)
        S('gh', 0)


# ------------------------------------------------------------------ frame ---
@proc('')
def draw_app():
    S('_tfm', 0)
    with If((V('open_t') < V('anim_n')) | (V('gmode') != 0)):
        S('_tfm', 1)
    with If(V('_tfm') == 1):
        S('press', 0)
        S('rel', 0)
        P.draw_home()
        S('_ix', 93 + ((V('app') - 1) % 4) * 130 + 31)
        S('_iy', 146 + floor((V('app') - 1) / 4) * 98 + 31)
        with If(V('gmode') == 1):
            P.set_tf(V('ga_s'), V('ga_cx'), V('ga_cy'))
        with Else():
            with If(V('gmode') == 2):
                S('_t', V('gt') / V('anim_n'))
                S('_e', 1 - (1 - V('_t')) * (1 - V('_t')))
                P.set_tf(V('ga_s') + (0.11 - V('ga_s')) * V('_e'), V('ga_cx') + (V('_ix') - V('ga_cx')) * V('_e'),
                         V('ga_cy') + (V('_iy') - V('ga_cy')) * V('_e'))
                inc('gt')
                with If(V('gt') > V('anim_n')):
                    S('gmode', 0)
                    S('screen', SCR_HOME)
                    S('open_t', 99)
            with Else():
                with If(V('gmode') == 3):
                    S('_t', V('gt') / 6)
                    S('_e', 1 - (1 - V('_t')) * (1 - V('_t')))
                    P.set_tf(V('ga_s') + (1 - V('ga_s')) * V('_e'), V('ga_cx') + (W / 2 - V('ga_cx')) * V('_e'),
                             V('ga_cy') + (H / 2 - V('ga_cy')) * V('_e'))
                    inc('gt')
                    with If(V('gt') > 6):
                        S('gmode', 0)
                with Else():
                    S('_t', V('open_t') / V('anim_n'))
                    S('_e', 1 - (1 - V('_t')) * (1 - V('_t')))
                    P.set_tf(0.11 + 0.89 * V('_e'), V('open_x') + 31 + (W / 2 - V('open_x') - 31) * V('_e'),
                             V('open_y') + 31 + (H / 2 - V('open_y') - 31) * V('_e'))
                    inc('open_t')
    S('clip0', SB)
    S('clip1', H - NB)
    P.rrect(0, 0, W, H, (1 - V('gs')) * 60, V('c_bg'))
    P.app_draw()
    P.set_tf(1, W / 2, H / 2)
    S('cur_layer', 0)


@proc('')
def frame():
    P.input_()
    P.set_tf(1, W / 2, H / 2)
    P.gesture_update()
    P.time_update()
    P.bg_tasks()
    inc('frame_n')
    pen_clear()
    S('gh', 0)
    effect('GHOST', 0)
    # which layer owns input this frame
    S('act_layer', 0)
    with If((V('qs_open') == 1) | (V('screen') == SCR_REC)):
        S('act_layer', 1)
    with If(V('dlg') == 1):
        S('act_layer', 2)
    with If((V('gmode') != 0) | ((V('screen') == SCR_APP) & (V('open_t') < V('anim_n')))):
        S('act_layer', 3)
    S('cur_layer', 0)
    S('clip0', SB)
    S('clip1', H - NB)
    with If(V('kb_open') == 0):
        S('kb_top', H)
    with If(V('screen') != SCR_APP):
        S('kb_open', 0)
    dispatch(V('screen'), [
        (SCR_BOOT, lambda: P.draw_boot()),
        (SCR_LOCK, lambda: P.draw_lock()),
        (SCR_HOME, lambda: P.draw_home()),
        (SCR_APP, lambda: P.draw_app()),
        (SCR_REC, lambda: P.draw_recents()),
    ])
    with If(V('screen') > SCR_LOCK):
        with If((V('screen') == SCR_APP) & (V('open_t') >= V('anim_n')) & (V('gmode') == 0)):
            S('_sm', 1)
        with Else():
            S('_sm', 0)
        with If(V('kb_open') == 1):
            P.draw_keyboard()
        P.statusbar(V('_sm'))
        P.navbar(V('_sm'))
    with If(V('screen') == SCR_LOCK):
        P.statusbar(0)
    with If(V('qs_open') == 1):
        P.draw_qs()
        P.statusbar(0)
    with If(V('dlg') == 1):
        P.draw_dialog()
    P.draw_toast()
    # a press that caused a screen/view change must not activate widgets of the new screen on release
    S('_sig', V('screen') * 100000 + V('app') * 1000 + V('view') * 100 + V('qs_open') * 10 + V('dlg') * 3 +
      V('kb_open'))
    with If(V('_sig') != V('ui_sig')):
        S('ui_sig', V('_sig'))
        S('moved', 1)
    with If((V('frame_n') % 150) == 0):
        P.store_save()
    # screen brightness
    with If(V('bright') < 100):
        S('gh', 100 - (100 - V('bright')) * 0.75)
        P.rect(0, 0, W, H, pal('black'))
        S('gh', 0)
    effect('GHOST', 0)


V('_sm', 0)
V('ui_sig', 0)
V('_sig', 0)


def make_main_script():
    """green-flag script (built after every module is imported so all procedures exist)"""
    with Script('flag'):
        hide()
        stage_size(W, H)
        rotation_all()
        S('screen', SCR_BOOT)
        S('boot_t', 0)
        S('md', 0)
        S('mdp', 0)
        S('kb_open', 0)
        S('qs_open', 0)
        S('dlg', 0)
        S('pin_show', 0)
        S('pin_in', '')
        S('open_t', 99)
        S('gmode', 0)
        S('gtype', 0)
        S('toast_t', 0)
        S('app', 0)
        list_clear(L('rec'))
        S('pk_held', '')
        P.store_load()
        P.theme()
        backdrop(7)
        with forever():
            P.frame()
