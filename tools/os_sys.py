import math
"""eOS system UI: boot, lock, home, status/nav bars, keyboard, quick settings, dialogs, recents, main loop."""
from sb3 import *
from os_core import *

KB_H = 130

for _n, _v in [('rscroll', 0), ('rs_on', 0), ('rs_x0', 0), ('rs_s0', 0), ('rc_dis_app', 0), ('rc_dis_t', 0), ('fsc', 1), ('last_t', 0), ('fclk', 0), ('last_save', 0), ('lk30', 0.3), ('lk35', 0.35), ('lk50', 0.5),
               ('op_x0', 0), ('op_y0', 0), ('op_w0', 62), ('op_h0', 62), ('op_p0', 0), ('cl_cw', 62), ('cl_ch', 62),
               ('cl_ccx', 0), ('cl_ccy', 0), ('cl_cp', 0), ('g_still', 0), ('g_rec', 0), ('g_px', 0), ('g_py', 0), ('cl_w0', W), ('cl_h0', H), ('cl_p0', 1), ('cur_w', W), ('cur_h', H), ('cur_p', 1), ('cl_on', 0), ('cl_app', 0), ('cl_t', 0), ('cl_full', 1), ('cl_s0', 1), ('cl_x0', W / 2), ('cl_y0', H / 2),
               ('cur_s', 1), ('cur_cx', W / 2), ('cur_cy', H / 2), ('navmode', 1), ('anim_n', 10), ('gmode', 0), ('gtype', 0), ('gt', 0), ('ga_s', 1), ('ga_cx', W / 2),
               ('ga_cy', H / 2), ('gx0', 0), ('boot_t', 0), ('pin_in', ''), ('pin_show', 0), ('back_o', 0), ('kb_k', ''), ('_kbx', 0),
               ('pad_o', ''), ('rc_n', 0), ('qs_h', 0), ('lock_t', 0)]:
    V(_n, _v)


# ------------------------------------------------------------------ boot ---
@proc('')
def draw_boot():
    P.rect(0, 0, W, H, pal('black'))
    P.ease(V('boot_t') / 20)
    S('gh', 100 - V('ez_o') * 100)
    P.text_c(W / 2, 150, 'eOS', 56 + 8 * V('ez_o'), 1, 0)
    S('gh', 0)
    P.text_c(W / 2, 196, 'PenguinMod edition', 12, 0, -45)
    P.rrect(W / 2 - 80, 250, 160, 6, 3, pal('dgray'))
    P.rrect(W / 2 - 80, 250, 160 * V('boot_t') / 70, 6, 3, pal('white'))
    change(V('boot_t'), V('fsc'))
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
    change(V('lock_t'), V('fsc'))
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
    S('view', 0)
    S('scroll', 0)
    S('kb_open', 0)
    S('qs_open', 0)
    S('open_x', ox)
    S('open_y', oy)
    with If((V('screen') == SCR_APP) & (V('open_t') < V('anim_n')) & (V('app') != a)):
        P.start_close(V('app'), V('cur_w'), V('cur_h'), V('cur_cx'), V('cur_cy'), V('cur_p'))      # previous app was still opening: let it shrink away
    S('app', a)
    S('op_x0', ox + 31)
    S('op_y0', oy + 31)
    S('op_w0', 62)
    S('op_h0', 62)
    S('op_p0', 0)
    with If(V('cl_on') == 1):
        with If((V('cl_app') == a) & (V('cl_full') == 1)):
            S('op_x0', V('cl_ccx'))                  # re-opening an app that is still closing: continue from its window
            S('op_y0', V('cl_ccy'))
            S('op_w0', V('cl_cw'))
            S('op_h0', V('cl_ch'))
            S('op_p0', V('cl_cp'))
            S('cl_on', 0)
        with Else():
            with If(V('cl_app') == a):
                S('cl_on', 0)
            with Else():
                S('cl_full', 0)
    S('open_t', 0)
    S('gmode', 0)
    with If(indexof(L('rec'), a) == 0):
        P.app_init(a)
    with Else():
        list_delete(L('rec'), indexof(L('rec'), a))
        S('view', item(L('app_view'), a))
        S('scroll', item(L('app_scroll'), a))
    list_add(L('rec'), a)
    S('screen', SCR_APP)


@proc('s cx cy')
def set_tf(s_, cx, cy):
    """draw everything that follows scaled by s_ and centred on (cx, cy)"""
    S('gs', s_)
    S('gox', cx - W / 2 * s_)
    S('goy', cy - H / 2 * s_)


@proc('a w h cx cy p')
def start_close(a, w, h, cx, cy, p):
    """move app `a` (drawn as a w x h window at centre cx,cy, `p` = how app-like it still is) onto the closing layer
    and go Home at once; the window keeps morphing into its icon while Home is already usable"""
    S('cl_app', a)
    S('cl_w0', w)
    S('cl_h0', h)
    S('cl_x0', cx)
    S('cl_y0', cy)
    S('cl_p0', p)
    S('cl_t', 0)
    S('cl_full', 1)
    S('cl_on', 1)
    S('kb_open', 0)
    S('qs_open', 0)
    S('gmode', 0)
    S('open_t', 99)
    S('screen', SCR_HOME)


@proc('')
def close_app_anim():
    """close the foreground app (also while it is still opening: starts from the window's current shape)"""
    with If(V('gmode') == 1):
        P.start_close(V('app'), V('ga_s') * W, V('ga_s') * H, V('ga_cx'), V('ga_cy'), 1)
    with Else():
        P.start_close(V('app'), V('cur_w'), V('cur_h'), V('cur_cx'), V('cur_cy'), V('cur_p'))


@proc('w h cx cy fa ia r')
def draw_card(w, h, cx, cy, fa, ia, r):
    """an app window of any shape: bg + app content (alpha fa, scaled to fit) + app icon (alpha ia)"""
    P.rrect(cx - w / 2, cy - h / 2, w, h, r, V('c_bg'))
    with If(fa > 0.03):
        S('gh', 100 - fa * 100)
        P.set_tf(clamp(w / W, 0, h / H), cx, cy)          # fit the content inside the (morphing) window
        S('clip0', SB)
        S('clip1', H - NB)
        P.app_draw()
        P.rect(0, 0, W, SB, V('c_bg'))
        P.rect(0, H - NB, W, NB, V('c_bg'))
        P.set_tf(1, W / 2, H / 2)
        S('gh', 0)
        S('cur_layer', 0)
    with If(ia > 0.03):
        S('gh', 100 - ia * 100)
        P.appicon(item(L('app_icon'), V('card_app')), cx, cy, clamp(w, 0, h))
        S('gh', 0)


V('card_app', 1)


@proc('')
def draw_closing():
    """the closing window (own layer so another app can open meanwhile)"""
    with If(V('cl_on') == 1):
        S('_ce', 1 - (1 - V('cl_t') / V('anim_n')) * (1 - V('cl_t') / V('anim_n')))
        S('_cix', 93 + ((V('cl_app') - 1) % 4) * 130 + 31)
        S('_ciy', 146 + floor((V('cl_app') - 1) / 4) * 98 + 31)
        S('_cp', V('cl_p0') * (1 - V('_ce')))
        S('_cfa', clamp((V('_cp') - 0.35) / 0.65, 0, 1))
        S('_cia', clamp((0.65 - V('_cp')) / 0.65, 0, 1))
        with If(V('cl_full') == 0):
            S('_cfa', 0)
            S('_cia', 1)
        S('card_app', V('cl_app'))
        S('cl_cw', V('cl_w0') + (62 - V('cl_w0')) * V('_ce'))
        S('cl_ch', V('cl_h0') + (62 - V('cl_h0')) * V('_ce'))
        S('cl_ccx', V('cl_x0') + (V('_cix') - V('cl_x0')) * V('_ce'))
        S('cl_ccy', V('cl_y0') + (V('_ciy') - V('cl_y0')) * V('_ce'))
        S('cl_cp', V('_cp'))
        P.draw_card(V('cl_cw'), V('cl_ch'), V('cl_ccx'), V('cl_ccy'), V('_cfa'), V('_cia'),
                    16 * (1 - V('_cp') * V('_cp') * V('_cp')))
        change(V('cl_t'), V('fsc'))
        with If(V('cl_t') > V('anim_n')):
            S('cl_on', 0)


@proc('')
def gesture_update():
    """gesture-bar navigation (navmode 1): drag the bar up to shrink/close the app, edge-swipe for back"""
    with If((V('navmode') == 1) & (V('dlg') == 0) & (V('screen') >= SCR_HOME)):
        with If(V('press') == 1):
            S('gtype', 0)
            with If(V('gmode') == 3):
                S('gmode', 0)                      # a new touch interrupts the snap-back
            with If(V('my') >= H - NB):
                S('gtype', 1)
                S('g_still', 0)
                S('g_rec', 0)
                S('g_px', V('mx'))
                S('g_py', V('my'))
                S('gx0', V('mx'))
                S('press', 0)
                S('moved', 1)
            with Else():
                with If((V('mx') < 14) | (V('mx') > W - 14)):
                    S('gtype', 2)
                    S('press', 0)
                    S('moved', 1)
        with If((V('gtype') == 1) & (V('md') == 1) & (V('screen') == SCR_APP)):
            with If(V('gmode') != 1):
                S('ga_s', V('cur_w') / W)             # grab the window exactly where it currently is
                S('ga_cx', V('cur_cx'))
                S('ga_cy', V('cur_cy'))
            S('open_t', 99)
            S('gmode', 1)
            S('kb_open', 0)
            S('qs_open', 0)
            with If(abs_(V('mx') - V('g_px')) + abs_(V('my') - V('g_py')) <= 3):
                change(V('g_still'), V('fsc'))
            with Else():
                S('g_still', 0)
                S('g_rec', 0)
            S('g_px', V('mx'))
            S('g_py', V('my'))
            with If((V('g_still') >= 7) & (V('my') > H * 0.42) & (V('my') < H * 0.82)):
                S('g_rec', 1)                      # held halfway: show the other open apps
            with If(V('g_rec') == 1):
                S('ga_s', V('ga_s') + (0.5 - V('ga_s')) * V('lk30'))
                S('ga_cx', V('ga_cx') + (W / 2 - V('ga_cx')) * V('lk30'))
                S('ga_cy', V('ga_cy') + (H / 2 - 14 - V('ga_cy')) * V('lk30'))
            with Else():
                S('_gd', clamp((H - V('my')) / H, 0, 1))
                S('_gts', clamp(1 - V('_gd') * 0.95, 0.22, 1))
                S('ga_s', V('ga_s') + (V('_gts') - V('ga_s')) * V('lk50'))       # ease toward the finger (no jump)
                S('ga_cx', V('ga_cx') + (W / 2 + (V('mx') - V('gx0')) - V('ga_cx')) * V('lk50'))
                S('ga_cy', V('ga_cy') + (V('my') - V('_gts') * H / 2 + 10 - V('ga_cy')) * V('lk50'))
        with If((V('gtype') != 0) & (V('rel') == 1)):
            S('rel', 0)
            S('_gs', V('screen'))
            with If(V('gtype') == 1):
                with If(V('gmode') == 1):
                    with If(V('g_rec') == 1):
                        S('g_rec', 0)
                        S('gmode', 0)
                        S('open_t', 99)
                        P.nav_recents()
                    with Else():
                      with If(V('my') < H * 0.74):
                        P.close_app_anim()
                      with Else():
                        with If(V('ga_s') > 0.9):
                            S('gmode', 0)
                        with Else():
                            S('gmode', 3)
                            S('gt', 0)
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
@proc('a cx cy w h fa')
def draw_thumb(a, cx, cy, w, h, fa):
    """live window of app `a` (its saved view/scroll) for the app switcher"""
    S('_ta', V('app'))
    S('_tv', V('view'))
    S('_ts', V('scroll'))
    S('app', a)
    S('view', item(L('app_view'), a))
    S('scroll', item(L('app_scroll'), a))
    S('card_app', a)
    P.draw_card(w, h, cx, cy, fa, 0, 12)
    S('app', V('_ta'))
    S('view', V('_tv'))
    S('scroll', V('_ts'))


@proc('')
def draw_recents():
    S('cur_layer', 1)
    S('gh', 45)
    P.rect(0, 0, W, H, pal('black'))
    S('gh', 0)
    S('_rcn', listlen(L('rec')))
    with If(V('_rcn') == 0):
        P.text_c(W / 2, 170, 'No recent apps', 16, 1, 0)
    # horizontal drag scroll
    with If((V('press') == 1) & (V('my') > 60) & (V('my') < H - NB)):
        S('rs_on', 1)
        S('rs_x0', V('mx'))
        S('rs_s0', V('rscroll'))
    with If(V('md') == 0):
        S('rs_on', 0)
    with If((V('rs_on') == 1) & (V('moved') == 1)):
        S('rscroll', V('rs_s0') - (V('mx') - V('rs_x0')))
    S('_rmax', V('_rcn') * 250 - 210)
    S('rscroll', clamp(V('rscroll'), 0, (V('_rmax') + abs_(V('_rmax'))) / 2))
    S('_rcI', V('_rcn') + 1)
    S('_rcK', 0)
    with repeat(V('_rcn')):
        inc('_rcI', -1)
        S('_rcApp', item(L('rec'), V('_rcI')))
        S('_rcX', 40 - V('rscroll') + V('_rcK') * 250)
        S('_rcY', 104)
        P.stag(V('_rcK'))
        S('_rcOff', V('stag_o'))
        S('_rcFa', 1)
        with If((V('rc_dis_app') == V('_rcApp')) | (V('rc_dis_app') == -1)):
            P.ease((V('rc_dis_t') - (V('_rcK') * 1.5) * (V('rc_dis_app') == -1)) / 8)
            S('_rcOff', 0 - V('ez_o') * 150)
            S('_rcFa', 1 - V('ez_o'))
        inc('_rcK')
        with If((V('_rcX') > -240) & (V('_rcX') < W)):
            P.tapr(V('_rcX') + 198, V('_rcY') - 36 + V('_rcOff'), 32, 30)
            S('_rcCl', V('tap_o'))
            P.tapr(V('_rcX'), V('_rcY') + V('_rcOff'), 230, 129)
            S('_rcT', V('tap_o'))
            S('gh', 100 - V('_rcFa') * 100)
            P.appicon(item(L('app_icon'), V('_rcApp')), V('_rcX') + 14, V('_rcY') - 20 + V('_rcOff'), 22)
            P.text(V('_rcX') + 32, V('_rcY') - 20 + V('_rcOff'), item(L('app_name'), V('_rcApp')), 13, 1, 0, 150)
            P.icon('close', V('_rcX') + 214, V('_rcY') - 20 + V('_rcOff'), 14, 0)
            P.draw_thumb(V('_rcApp'), V('_rcX') + 115, V('_rcY') + 64.5 + V('_rcOff'), 230, 129, V('_rcFa'))
            S('gh', 0)
            with If((V('_rcCl') == 1) & (V('rc_dis_app') == 0)):
                S('rc_dis_app', V('_rcApp'))
                S('rc_dis_t', 0)
                S('_rcT', 0)
            with If((V('_rcT') == 1) & (V('rc_dis_app') == 0)):
                P.launch(V('_rcApp'), V('_rcX') + 115 - 31, V('_rcY') + 64.5 - 31)
                S('op_w0', 230)
                S('op_h0', 129)
                S('op_p0', 1)
    with If(V('rc_dis_app') != 0):
        change(V('rc_dis_t'), V('fsc'))
        with If(V('rc_dis_t') > 8 + V('_rcn') * 1.5):
            with If(V('rc_dis_app') == -1):
                list_clear(L('rec'))
            with Else():
                with If(indexof(L('rec'), V('rc_dis_app')) > 0):
                    list_delete(L('rec'), indexof(L('rec'), V('rc_dis_app')))
            S('rc_dis_app', 0)
    with If((V('_rcn') > 0) & (V('rc_dis_app') == 0)):
        P.btn(W / 2 - 60, 288, 120, 30, 'Close all', 0)
        with If(V('tap_o') == 1):
            S('rc_dis_app', -1)
            S('rc_dis_t', 0)


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
L('app_view', [0] * 8)
L('app_scroll', [0] * 8)

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
    with If(V('kb_open') == 0):
        S('kb_t', 0)
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
    change(V('kb_t'), V('fsc'))
    P.ease(V('kb_t') / 6)
    S('kb_top', H - NB - KB_H)
    S('_ky', V('kb_top'))
    P.set_tf(1, W / 2, H / 2 + (1 - V('ez_o')) * 60)
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
    P.set_tf(1, W / 2, H / 2)


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
    change(V('qs_t'), V('fsc'))
    P.ease(V('qs_t') / 7)
    S('gh', 100 - 50 * V('ez_o'))
    P.rect(0, 0, W, H, pal('black'))
    S('gh', 0)
    P.tapr(0, 176, W, H - 176)
    with If(V('tap_o') == 1):
        S('qs_open', 0)
    P.set_tf(1, W / 2, H / 2 - (1 - V('ez_o')) * 170)
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
    P.set_tf(1, W / 2, H / 2)


# ----------------------------------------------------------------- dialog --
@proc('')
def draw_dialog():
    S('cur_layer', 2)
    S('gh', 40)
    P.rect(0, 0, W, H, pal('black'))
    S('gh', 0)
    change(V('dlg_t'), V('fsc'))
    P.ease(V('dlg_t') / 6)
    P.set_tf(0.8 + 0.2 * V('ez_o'), W / 2, H / 2)
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
    P.set_tf(1, W / 2, H / 2)


@proc('title msg ok act arg')
def ask(title, msg, ok, act, arg):
    S('dlg_title', title)
    S('dlg_msg', msg)
    S('dlg_ok', ok)
    S('dlg_act', act)
    S('dlg_arg', arg)
    S('dlg', 1)
    S('dlg_t', 0)
    S('kb_open', 0)


@proc('')
def draw_toast():
    with If(V('toast_t') > 0):
        change(V('toast_t'), 0 - V('fsc'))
        P.tw(V('toast'), 13, 1)
        S('gh', 0)
        with If(V('toast_t') < 14):
            S('gh', 100 - V('toast_t') * 100 / 14)
        P.ease((100 - V('toast_t')) / 8)
        P.set_tf(1, W / 2, H / 2 - (1 - V('ez_o')) * 34)
        P.rrect(W / 2 - V('tw_o') / 2 - 16, SB + 8, V('tw_o') + 32, 30, 15, pal('black'))
        P.text_c(W / 2, SB + 23, V('toast'), 13, 1, 0)
        P.set_tf(1, W / 2, H / 2)
        S('gh', 0)


# ------------------------------------------------------------------ frame ---
@proc('')
def draw_switcher_preview():
    """swipe-and-hold: the other open apps appear around the shrunken current app"""
    S('gh', 55)
    P.rect(0, 0, W, H, pal('black'))
    S('gh', 0)
    S('_sj', 0)
    S('_sk', listlen(L('rec')) + 1)
    with repeat(listlen(L('rec'))):
        inc('_sk', -1)
        S('_sa', item(L('rec'), V('_sk')))
        with If((V('_sa') != V('app')) & (V('_sj') < 4)):
            inc('_sj')
            S('_sx', W / 2 + (255 + (floor((V('_sj') + 1) / 2) - 1) * 166) * (1 - (V('_sj') % 2) * 2))
            P.rrect(V('_sx') - 75, H / 2 - 14 - 45, 150, 90, 14, V('c_surf'))
            P.appicon(item(L('app_icon'), V('_sa')), V('_sx'), H / 2 - 14 - 8, 44)
            P.text_c(V('_sx'), H / 2 - 14 + 30, item(L('app_name'), V('_sa')), 12, 1, V('tx'))
    P.text_c(W / 2, H / 2 + 100, 'Release to open the app switcher', 12, 1, 0)


@proc('')
def draw_app():
    S('_tfm', 0)
    with If((V('open_t') < V('anim_n')) | (V('gmode') != 0)):
        S('_tfm', 1)
    S('cur_s', 1)
    S('cur_w', W)
    S('cur_h', H)
    S('cur_cx', W / 2)
    S('cur_cy', H / 2)
    S('cur_p', 1)
    S('_opening', 0)
    with If(V('_tfm') == 1):
        P.draw_home()
        P.draw_closing()
        with If((V('gmode') == 1) & (V('g_rec') == 1)):
            P.draw_switcher_preview()
        with If(V('gmode') == 1):
            S('cur_s', V('ga_s'))
            S('cur_cx', V('ga_cx'))
            S('cur_cy', V('ga_cy'))
        with Else():
            with If(V('gmode') == 3):
                S('_t', V('gt') / 6)
                S('_e', 1 - (1 - V('_t')) * (1 - V('_t')))
                S('cur_s', V('ga_s') + (1 - V('ga_s')) * V('_e'))
                S('cur_cx', V('ga_cx') + (W / 2 - V('ga_cx')) * V('_e'))
                S('cur_cy', V('ga_cy') + (H / 2 - V('ga_cy')) * V('_e'))
                change(V('gt'), V('fsc'))
                with If(V('gt') > 6):
                    S('gmode', 0)
            with Else():
                # opening: the icon turns into the app (inverse of closing)
                S('_opening', 1)
                S('_e', 1 - (1 - V('open_t') / V('anim_n')) * (1 - V('open_t') / V('anim_n')))
                S('cur_p', V('op_p0') + (1 - V('op_p0')) * V('_e'))
                S('cur_cx', V('op_x0') + (W / 2 - V('op_x0')) * V('_e'))
                S('cur_cy', V('op_y0') + (H / 2 - V('op_y0')) * V('_e'))
                S('cur_w', V('op_w0') + (W - V('op_w0')) * V('_e'))
                S('cur_h', V('op_h0') + (H - V('op_h0')) * V('_e'))
                S('cur_s', V('cur_w') / W)
                S('card_app', V('app'))
                P.draw_card(V('cur_w'), V('cur_h'), V('cur_cx'), V('cur_cy'), clamp((V('cur_p') - 0.35) / 0.65, 0, 1),
                            clamp((0.65 - V('cur_p')) / 0.65, 0, 1), 16 * (1 - V('cur_p') * V('cur_p') * V('cur_p')))
                change(V('open_t'), V('fsc'))
        with If(V('_opening') == 0):
            S('cur_w', V('cur_s') * W)
            S('cur_h', V('cur_s') * H)
            P.set_tf(V('cur_s'), V('cur_cx'), V('cur_cy'))
    with If(V('_opening') == 0):
        S('clip0', SB)
        S('clip1', H - NB)
        P.rrect(0, 0, W, H, (1 - V('gs')) * 60, V('c_bg'))
        with If(V('_tfm') == 0):
            P.ease(V('pg_t') / V('anim_n'))                       # page transition: slide in from the right
            P.set_tf(1, W / 2 + (1 - V('ez_o')) * 36, H / 2)
        P.app_draw()
        with If(V('gs') != 1):
            # shrunken window: bars drawn in window space hide anything that overlaps them (no clipping exists)
            P.rect(0, 0, W, SB, V('c_bg'))
            P.rect(0, H - NB, W, NB, V('c_bg'))
        P.set_tf(1, W / 2, H / 2)
    S('cur_layer', 0)
    list_replace(L('app_view'), V('app'), V('view'))
    list_replace(L('app_scroll'), V('app'), V('scroll'))


@proc('')
def frame():
    # time base: fsc = elapsed time in 30fps-frames, so animations take the same wall time at any refresh rate
    S('_now', timer())
    S('fsc', clamp((V('_now') - V('last_t')) * 30, 0, 4))
    S('last_t', V('_now'))
    change(V('fclk'), V('fsc'))
    S('lk30', 1 - mathop('e ^', V('fsc') * math.log(0.7)))
    S('lk35', 1 - mathop('e ^', V('fsc') * math.log(0.65)))
    S('lk50', 1 - mathop('e ^', V('fsc') * math.log(0.5)))
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
    with If(V('gmode') == 1):
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
        (SCR_HOME, lambda: (P.draw_home(), P.draw_closing())),
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
    S('_psig', V('screen') * 10000000 + V('app') * 1000000 + V('view') * 100000 + V('clk_tab') * 10000 + V('f_dir'))
    with If(V('_psig') != V('pg_sig')):
        S('pg_sig', V('_psig'))
        S('pg_t', 0)
    with If(V('pg_t') < 99):
        change(V('pg_t'), V('fsc'))
    with If(V('qs_open') == 0):
        S('qs_t', 0)
    # a press that caused a screen/view change must not activate widgets of the new screen on release
    S('_sig', V('screen') * 100000 + V('app') * 1000 + V('view') * 100 + V('qs_open') * 10 + V('dlg') * 3 +
      V('kb_open'))
    with If(V('_sig') != V('ui_sig')):
        S('ui_sig', V('_sig'))
        S('moved', 1)
    with If(V('fclk') - V('last_save') >= 150):
        S('last_save', V('fclk'))
        P.store_save()
    # screen brightness
    with If(V('bright') < 100):
        S('gh', 100 - (100 - V('bright')) * 0.75)
        P.rect(0, 0, W, H, pal('black'))
        S('gh', 0)
    effect('GHOST', 0)


V('_sm', 0)
V('ui_sig', 0)
V('pg_sig', 0)
V('_psig', 0)
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
        S('cl_on', 0)
        S('toast_t', 0)
        S('app', 0)
        list_clear(L('rec'))
        S('pk_held', '')
        P.store_load()
        P.theme()
        backdrop(7)
        with forever():
            P.frame()
