import math
"""eOS system UI: boot, lock, home, status/nav bars, keyboard, quick settings, dialogs, recents, main loop."""
from sb3 import *
from os_core import *
from modes import MODE

KB_H = 130

for _n, _v in [('qs_p', 0), ('qs_kind', 1), ('qs_drag', 0), ('qs_cand', 0), ('qs_tapc', 0), ('qs_y0', 0), ('qs_p0', 0),
               ('nt_dt', 99), ('nt_di', 0), ('nt_clr', 99), ('unl_t', 99), ('pin_a', 0), ('pin_pop', 99), ('pin_sh', 99), ('pin_lp', 0), ('lock_ex', 0), ('fade_b', 0),
               ('rx_t', 99), ('rx_skip', 0), ('prev_scr', 0), ('bar_a', 0), ('nm_a', 1), ('pc_prev', 0), ('pc_cur', 0), ('pc_mix', 1),
               ('sb_a', 0), ('kb_a', 0), ('dlg_a', 0), ('th_t', 99), ('th_prev', 0), ('th_dark', 0), ('wp_t', 99), ('wp_prev', 1),
               ('wifi_a', 1), ('sw_off', 0), ('sw_focus', 0), ('rs_axis', 0), ('rs_vo', 0), ('rs_app', 0), ('rs_y0', 0), ('bs', 1), ('bx', 0), ('by', 0), ('nav_col', 0), ('nav_barw', 110), ('nav_barh', 5), ('nav_close', 74), ('nav_swipe', 1), ('nav_edge', 1),
               ('nav_hold', 1), ('nav_tap', 0), ('cl_mode', 0), ('cl_dir', 1), ('launch_keep', 0), ('rscroll', 0), ('rs_on', 0), ('rs_x0', 0), ('rs_s0', 0), ('rc_dis_app', 0), ('rc_dis_t', 0), ('fsc', 1), ('last_t', 0), ('fclk', 0), ('last_save', 0), ('lk30', 0.3), ('lk35', 0.35), ('lk50', 0.5),
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
def do_unlock():
    """go Home; the lock face keeps animating away on top of it (frame -> unlock overlay)"""
    S('screen', SCR_HOME)
    S('unl_t', 0)


@proc('')
def draw_lock():
    """lock face (clock) and PIN pad cross-fade via pin_a.  Entering (pg_t) wakes from black and drops the face in.
    lock_ex = 1: drawn as the unlock overlay (no input, full visibility, frame supplies the exit transform/fade)."""
    S('_lin', 1)
    with If(V('lock_ex') == 0):
        P.ease(V('pg_t') / (V('anim_n') * 1.4))
        S('_lin', V('ez_o'))
    with If(V('dark') == 1):
        S('gh', 80)
        S('fade', V('fade_b'))
        P.rect(0, 0, W, H, pal('black'))
        S('gh', 0)
    change(V('lock_t'), V('fsc'))
    S('pin_a', V('pin_a') + (V('pin_show') - V('pin_a')) * V('lk35'))
    with If(abs_(V('pin_show') - V('pin_a')) < 0.003):
        S('pin_a', V('pin_show'))
    S('_lcl', V('cur_layer'))
    # --- face
    with If(V('pin_a') < 0.99):
        S('fade', 100 - (100 - V('fade_b')) * clamp(1 - V('pin_a') * 1.8, 0, 1) * V('_lin'))
        P.set_tf(1 - 0.06 * V('pin_a'), W / 2, H / 2 - V('pin_a') * 46 - (1 - V('_lin')) * 36)
        P.text_c(W / 2, 112, V('tstr'), 72, 1, 0)
        P.tw(V('tstr'), 72, 1)
        P.text(W / 2 + V('tw_o') / 2 + 8, 134, V('ampm'), 16, 1, -10, 0)
        P.text_c(W / 2, 168, V('dstr'), 16, 0, 0)
        P.icon('lock', W / 2, 262, 20, 0)
        P.text_c(W / 2, 300, 'Tap to unlock', 13, 0, -20 - 25 * abs_(sin(V('lock_t') * 4)))
        P.set_tf(1, W / 2, H / 2)
        S('fade', 0)
        with If(V('pin_show') == 0):
            P.tapr(0, SB, W, H - SB)
            with If(V('tap_o') == 1):
                with If(V('pin') == ''):
                    P.do_unlock()
                with Else():
                    S('pin_show', 1)
                    S('pin_in', '')
    # --- PIN pad
    with If(V('pin_a') > 0.01):
        S('fade', 100 - (100 - V('fade_b')) * clamp((V('pin_a') - 0.35) / 0.65, 0, 1) * V('_lin'))
        P.set_tf(0.92 + 0.08 * V('pin_a'), W / 2, H / 2 + (1 - V('pin_a')) * 30)
        P.text_c(W / 2, 54, V('tstr'), 34, 1, 0)
        P.text_c(W / 2, 86, 'Enter PIN', 13, 0, -15)
        # dots: the newest one pops, a wrong PIN shakes them
        with If(length(V('pin_in')) > V('pin_lp')):
            S('pin_pop', 0)
        S('pin_lp', length(V('pin_in')))
        change(V('pin_pop'), V('fsc'))
        change(V('pin_sh'), V('fsc'))
        S('_psx', 0)
        with If(V('pin_sh') < 12):
            S('_psx', sin(V('pin_sh') * 90) * 12 * (1 - V('pin_sh') / 12))
        S('_pd', 0)
        with repeat(4):
            inc('_pd')
            S('_pdx', W / 2 - 54 + V('_pd') * 27 - 13.5 + V('_psx'))
            with If(length(V('pin_in')) >= V('_pd')):
                S('_pds', 13)
                with If(V('_pd') == length(V('pin_in'))):
                    P.ease(V('pin_pop') / 5)
                    S('_pds', 13 * (1.5 - 0.5 * V('ez_o')))
                P.circle(V('_pdx'), 112, V('_pds'), pal('white'))
            with Else():
                P.circle(V('_pdx'), 112, 13, pal('dgray'))
        with If(V('pin_show') == 0):
            S('cur_layer', -1)                       # fading out: visible but not tappable
        P.pinpad(128)
        S('cur_layer', V('_lcl'))
        P.set_tf(1, W / 2, H / 2)
        S('fade', 0)
        with If(V('pin_back') == 1):
            S('pin_back', 0)
            S('pin_show', 0)
            S('pin_in', '')
        with If(V('pin_ok') == 1):
            S('pin_ok', 0)
            with If(V('pin_in') == V('pin')):
                P.do_unlock()
            with Else():
                S('pin_in', '')
                S('pin_lp', 0)
                S('pin_sh', 0)
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
    S('_hin', 1)                                  # unlocking: clock and icons rise in, one after another
    with If(V('unl_t') < 40):
        P.ease((V('unl_t') - V('anim_n') * 0.25) / V('anim_n'))
        S('_hin', V('ez_o'))
    S('fade', (1 - V('_hin')) * 100)
    P.zoom_at(1.08 - 0.08 * V('_hin'), W / 2, 90)
    P.text_c(W / 2, 74, V('tstr'), 56, 1, 0)
    P.tw(V('tstr'), 56, 1)
    P.text(W / 2 + V('tw_o') / 2 + 6, 90, V('ampm'), 14, 1, -10, 0)
    P.text_c(W / 2, 112, V('dstr'), 14, 0, -10)
    P.set_tf(1, W / 2, H / 2)
    S('fade', 0)
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
        S('_aie', 1)
        with If(V('unl_t') < 40):
            P.ease((V('unl_t') - V('anim_n') * 0.2 - V('_ai') * 0.6) / V('anim_n'))
            S('_aie', V('ez_o'))
        S('fade', (1 - V('_aie')) * 100)
        P.appicon(item(L('app_icon'), V('_ai')), V('_ax') + 32, V('_ay') + 31 + (1 - V('_aie')) * 26,
                  V('_asz') * (0.8 + 0.2 * V('_aie')))
        P.text_c(V('_ax') + 32, V('_ay') + 76 + (1 - V('_aie')) * 26, item(L('app_name'), V('_ai')), 12, 1, 0)
        S('fade', 0)
        with If(V('_at') == 1):
            P.launch(V('_ai'), V('_ax'), V('_ay'))


@proc('a ox oy')
def launch(a, ox, oy):
    # tapping the icon of the app that is already opening must not restart its animation
    with If((V('screen') == SCR_APP) & (V('app') == a) & (V('open_t') < V('anim_n'))):
        stop_this()
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
                with If(V('cl_mode') == 0):
                    S('cl_full', 0)
    S('open_t', 0)
    S('gmode', 0)
    with If(indexof(L('rec'), a) == 0):
        P.app_init(a)
    with Else():
        S('view', item(L('app_view'), a))
        S('scroll', item(L('app_scroll'), a))
        with If(V('launch_keep') == 0):
            list_delete(L('rec'), indexof(L('rec'), a))
    with If((V('launch_keep') == 0) | (indexof(L('rec'), a) == 0)):
        list_add(L('rec'), a)
    S('screen', SCR_APP)


@proc('s cx cy')
def set_base(s_, cx, cy):
    """window level: map the whole 640x360 UI onto a window of scale s_ centred on (cx, cy) - sets the base transform"""
    S('bs', s_)
    S('bx', cx - W / 2 * s_)
    S('by', cy - H / 2 * s_)
    S('gs', V('bs'))
    S('gox', V('bx'))
    S('goy', V('by'))


@proc('s px py')
def zoom_at(s_, px, py):
    """in-app effect: scale by s_ around the point (px, py) - that point stays where it is"""
    P.set_tf(s_, px + (W / 2 - px) * s_, py + (H / 2 - py) * s_)


@proc('s cx cy')
def set_tf(s_, cx, cy):
    """in-app effect (pop, slide...): scale s_ about a centre *inside the current window*; nests with set_base"""
    S('gs', V('bs') * s_)
    S('gox', V('bx') + (cx - W / 2 * s_) * V('bs'))
    S('goy', V('by') + (cy - H / 2 * s_) * V('bs'))


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
    S('cl_mode', 0)
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
        P.set_base(clamp(w / W, 0, h / H), cx, cy)          # fit the content inside the (morphing) window
        S('clip0', SB)
        S('clip1', H - NB)
        S('no_hit', 1)                                      # a window being animated / a thumbnail never reacts
        P.app_draw()
        S('no_hit', 0)
        P.rect(0, 0, W, SB, V('c_bg'))
        P.rect(0, H - NB, W, NB, V('c_bg'))
        P.set_base(1, W / 2, H / 2)
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
        with If(V('cl_mode') == 1):
            # sideways app switch: the old window slides off, drawn from its own saved view state
            S('cl_ccx', V('cl_x0') + (W / 2 + V('cl_dir') * W - V('cl_x0')) * V('_ce'))
            S('cl_ccy', V('cl_y0') + (H / 2 - V('cl_y0')) * V('_ce'))
            S('cl_cw', V('cl_w0') + (W - V('cl_w0')) * V('_ce'))
            S('cl_ch', V('cl_h0') + (H - V('cl_h0')) * V('_ce'))
            P.draw_thumb(V('cl_app'), V('cl_ccx'), V('cl_ccy'), V('cl_cw'), V('cl_ch'), 1)
        with Else():
            P.draw_card(V('cl_cw'), V('cl_ch'), V('cl_ccx'), V('cl_ccy'), V('_cfa'), V('_cia'),
                        16 * (1 - V('_cp') * V('_cp') * V('_cp')))
        change(V('cl_t'), V('fsc'))
        with If(V('cl_t') > V('anim_n')):
            S('cl_on', 0)


@proc('')
def bar_tap():
    """what a plain tap on the gesture bar does (Settings → Navigation)"""
    with If(V('nav_tap') == 1):
        S('qs_open', 0)
        S('kb_open', 0)
        S('screen', SCR_LOCK)
        S('pin_show', 0)
    with If(V('nav_tap') == 2):
        P.nav_recents()
    with If(V('nav_tap') == 3):
        P.nav_home()


@proc('dir')
def swipe_switch(dir_):
    """swipe the gesture bar sideways: dir_ +1 (right) = previous app, -1 (left) = next app; the current app slides out,
    the other slides in (the recents list is not reordered, so repeated swipes walk through it)"""
    S('_si', indexof(L('rec'), V('app')) - dir_)
    with If((V('_si') >= 1) & (V('_si') <= listlen(L('rec')))):
        S('_sa', item(L('rec'), V('_si')))
        S('cl_app', V('app'))
        S('cl_w0', V('ga_s') * W)
        S('cl_h0', V('ga_s') * H)
        S('cl_x0', V('ga_cx'))
        S('cl_y0', V('ga_cy'))
        S('cl_p0', 1)
        S('cl_t', 0)
        S('cl_full', 1)
        S('cl_mode', 1)
        S('cl_dir', dir_)
        S('cl_on', 1)
        S('gmode', 0)
        S('launch_keep', 1)
        P.launch(V('_sa'), 0, 0)
        S('launch_keep', 0)
        S('op_x0', V('cl_x0') - dir_ * W)
        S('op_y0', H / 2)
        S('op_w0', W)
        S('op_h0', H)
        S('op_p0', 1)
    with Else():
        S('gmode', 3)                       # nothing there: spring back
        S('gt', 0)


@proc('')
def gesture_update():
    """gesture-bar navigation (navmode 1): drag the bar up to shrink/close the app, edge-swipe for back"""
    with If((V('navmode') == 1) & (V('dlg') == 0) & (V('screen') >= SCR_HOME) & (V('qs_p') < 0.02) & (V('qs_open') == 0)):
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
                with If(((V('mx') < 14) | (V('mx') > W - 14)) & (V('nav_edge') == 1)):
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
            with If((V('g_still') >= 7) & (V('nav_hold') == 1) & (V('my') > H * 0.42) &
                    (V('my') < H * (V('nav_close') + 8) / 100)):
                with If(V('g_rec') == 0):
                    S('sw_focus', V('app'))
                    S('sw_off', 0)
                S('g_rec', 1)                      # held halfway: the app becomes the centre card of the app switcher
            with If(V('g_rec') == 1):
                S('ga_s', V('ga_s') + (SW_W / W - V('ga_s')) * V('lk30'))
                S('ga_cx', V('ga_cx') + (W / 2 - V('ga_cx')) * V('lk30'))
                S('ga_cy', V('ga_cy') + (SW_Y + SW_H / 2 - V('ga_cy')) * V('lk30'))
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
                      with If(V('my') < H * V('nav_close') / 100):
                        P.close_app_anim()
                      with Else():
                        with If((abs_(V('mx') - V('gx0')) > 60) & (V('ga_s') > 0.8) & (V('nav_swipe') == 1)):
                            P.swipe_switch(1 - 2 * (V('mx') < V('gx0')))
                        with Else():
                          with If(V('ga_s') > 0.9):
                            S('gmode', 0)
                          with Else():
                            S('gmode', 3)
                            S('gt', 0)
                with If((V('gmode') == 0) & (abs_(V('mx') - V('gx0')) < 8) & (V('py') - V('my') < 8) & (V('nav_tap') != 0)):
                    P.bar_tap()
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


SW_PITCH, SW_W, SW_H, SW_Y = 250, 230, 129, 104


@proc('hold')
def draw_switcher(hold):
    """App switcher (Android/iOS style carousel of live app windows, current app in the centre, older ones to the left).
    hold = 1: shown while the gesture bar is held halfway - the dragged app window itself is the centre card and the others
    appear around it (no input here).  hold = 0: the Recents screen with the same layout (scroll, tap, swipe up to dismiss)."""
    S('_swn', listlen(L('rec')))
    S('_swk', indexof(L('rec'), V('sw_focus')))
    with If(V('_swk') == 0):
        S('_swk', V('_swn'))
    S('_swmin', 0 - (V('_swk') - 1) * SW_PITCH)         # sw_off < 0 scrolls the carousel right = towards older apps
    S('_swmax', (V('_swn') - V('_swk')) * SW_PITCH)
    with If(hold == 0):
        with If((V('press') == 1) & (V('my') > 60) & (V('my') < H - NB)):
            S('rs_on', 1)
            S('rs_x0', V('mx'))
            S('rs_y0', V('my'))
            S('rs_s0', V('sw_off'))
            S('rs_axis', 0)
            S('rs_app', 0)
            S('_swp', V('_swk') + round_((V('mx') - W / 2 + V('sw_off')) / SW_PITCH))
            with If((V('_swp') >= 1) & (V('_swp') <= V('_swn')) & (V('my') > SW_Y - 40) & (V('my') < SW_Y + SW_H) &
                    (abs_(V('mx') - (W / 2 + (V('_swp') - V('_swk')) * SW_PITCH - V('sw_off'))) < SW_W / 2)):
                S('rs_app', item(L('rec'), V('_swp')))
        with If((V('rs_on') == 1) & (V('md') == 1) & (V('moved') == 1) & (V('rs_axis') == 0)):
            with If((abs_(V('my') - V('rs_y0')) > abs_(V('mx') - V('rs_x0'))) & (V('my') < V('rs_y0')) & (V('rs_app') != 0)):
                S('rs_axis', 2)                              # swipe a card up
            with Else():
                S('rs_axis', 1)                              # scroll the carousel
        with If((V('rs_on') == 1) & (V('rs_axis') == 1) & (V('md') == 1)):
            S('sw_off', V('rs_s0') - (V('mx') - V('rs_x0')))
        with If((V('rs_on') == 1) & (V('rs_axis') == 2) & (V('md') == 1)):
            S('rs_vo', clamp(V('my') - V('rs_y0'), -200, 0))
        with If((V('md') == 0) & (V('rs_on') == 1)):
            S('rs_on', 0)
            with If((V('rs_axis') == 2) & (V('rs_vo') < -60) & (V('rc_dis_app') == 0)):
                S('rc_dis_app', V('rs_app'))
                S('rc_dis_t', 0)
            S('rs_axis', 0)
        with If(V('rs_on') == 0):
            S('_swt', clamp(round_(V('sw_off') / SW_PITCH) * SW_PITCH, V('_swmin'), V('_swmax')))
            S('sw_off', V('sw_off') + (V('_swt') - V('sw_off')) * V('lk35'))            # snap to the nearest card
            S('rs_vo', V('rs_vo') * (1 - V('lk35')))
        with If(V('rs_axis') == 1):
            S('sw_off', clamp(V('sw_off'), V('_swmin') - 120, V('_swmax') + 120))
    S('_swi', 0)
    with repeat(V('_swn')):
        inc('_swi')
        S('cur_layer', 1)                    # drawing a thumbnail resets the input layer
        S('_swA', item(L('rec'), V('_swi')))
        S('_swX', W / 2 + (V('_swi') - V('_swk')) * SW_PITCH - V('sw_off'))
        S('_swcy', SW_Y + SW_H / 2)
        S('_swOff', 0)
        S('_swFa', 1)
        S('_swSc', 1)
        with If(hold == 1):
            P.ease((V('g_still') - 7) / 6)                   # neighbours grow in once the bar is held
            S('_swFa', V('ez_o'))
            S('_swSc', 0.85 + 0.15 * V('ez_o'))
        with If(hold == 2):                                  # leaving the switcher: cards sink back and fade
            P.ease(V('rx_t') / V('anim_n'))
            S('_swFa', 1 - V('ez_o'))
            S('_swSc', 1 - 0.1 * V('ez_o'))
            S('_swOff', V('ez_o') * 24)
        with If(hold == 0):
            P.stag(abs_(V('_swi') - V('_swk')))
            S('_swOff', V('stag_o'))
            with If((V('rs_axis') == 2) & (V('rs_app') == V('_swA'))):
                S('_swOff', V('_swOff') + V('rs_vo'))
                S('_swFa', 1 - (0 - V('rs_vo')) / 260)
        with If((V('rc_dis_app') == V('_swA')) | (V('rc_dis_app') == -1)):
            P.ease((V('rc_dis_t') - (V('_swi') - 1) * 1.5 * (V('rc_dis_app') == -1)) / 8)
            S('_swOff', V('_swOff') - V('ez_o') * 150)
            S('_swFa', 1 - V('ez_o'))
        with If((V('_swX') > -SW_W) & (V('_swX') < W + SW_W)):
            S('_swx0', V('_swX') - SW_W / 2 * V('_swSc'))
            S('_swy0', V('_swcy') - SW_H / 2 * V('_swSc') + V('_swOff'))
            S('_swCl', 0)
            S('_swT', 0)
            with If(hold == 0):
                P.tapr(V('_swX') + SW_W / 2 - 34, V('_swy0') - 40, 34, 32)
                S('_swCl', V('tap_o'))
                P.tapr(V('_swx0'), V('_swy0'), SW_W, SW_H)
                S('_swT', V('tap_o'))
            S('gh', 100 - V('_swFa') * 100)
            P.appicon(item(L('app_icon'), V('_swA')), V('_swx0') + 14, V('_swy0') - 22, 24)
            P.text(V('_swx0') + 34, V('_swy0') - 22, item(L('app_name'), V('_swA')), 13, 1, 0, 150)
            with If(hold == 0):
                P.icon('close', V('_swx0') + SW_W * V('_swSc') - 12, V('_swy0') - 22, 14, 0)
            with If(~((hold == 1) & (V('_swA') == V('sw_focus'))) & ~((hold == 2) & (V('_swA') == V('rx_skip')))):
                P.draw_thumb(V('_swA'), V('_swX'), V('_swy0') + SW_H * V('_swSc') / 2, SW_W * V('_swSc'),
                             SW_H * V('_swSc'), V('_swFa'))
            S('gh', 0)
            with If((V('_swCl') == 1) & (V('rc_dis_app') == 0)):
                S('rc_dis_app', V('_swA'))
                S('rc_dis_t', 0)
                S('_swT', 0)
            with If((V('_swT') == 1) & (V('rc_dis_app') == 0)):
                P.launch(V('_swA'), V('_swX') - 31, V('_swy0') + SW_H / 2 - 31)
                S('op_w0', SW_W)
                S('op_h0', SW_H)
                S('op_p0', 1)
    with If(V('rc_dis_app') != 0):
        change(V('rc_dis_t'), V('fsc'))
        with If(V('rc_dis_t') > 8 + V('_swn') * 1.5):
            with If(V('rc_dis_app') == -1):
                list_clear(L('rec'))
            with Else():
                with If(indexof(L('rec'), V('rc_dis_app')) > 0):
                    list_delete(L('rec'), indexof(L('rec'), V('rc_dis_app')))
            S('rc_dis_app', 0)
            S('sw_focus', 0)


@proc('')
def draw_unlock_overlay():
    """right after unlocking, the lock face slides up and fades out over Home"""
    with If(V('unl_t') < V('anim_n') * 1.4):
        P.ease(V('unl_t') / (V('anim_n') * 0.9))
        S('lock_ex', 1)
        S('fade_b', clamp(V('ez_o') * 140, 0, 100))
        S('_ucl', V('cur_layer'))
        S('cur_layer', -1)
        P.set_base(1, W / 2, H / 2 - V('ez_o') * H * 0.6)
        P.draw_lock()
        P.set_base(1, W / 2, H / 2)
        S('cur_layer', V('_ucl'))
        S('lock_ex', 0)
        S('fade_b', 0)
        S('fade', 0)
    with If(V('unl_t') < 99):
        change(V('unl_t'), V('fsc'))
        with If(V('unl_t') >= V('anim_n') * 1.4):
            with If(V('pin_show') == 1):
                S('pin_show', 0)
                S('pin_in', '')
                S('pin_a', 0)
                S('pin_lp', 0)
        with If(V('unl_t') > 24):
            S('unl_t', 99)


@proc('')
def draw_rec_exit():
    """after leaving the app switcher its dim + cards fade out over whatever comes next"""
    with If(V('rx_t') < V('anim_n')):
        S('_rcl', V('cur_layer'))
        S('cur_layer', -1)
        P.ease(V('rx_t') / V('anim_n'))
        S('gh', 55 + 45 * V('ez_o'))
        P.rect(0, 0, W, H, pal('black'))
        S('gh', 0)
        P.draw_switcher(2)
        S('cur_layer', V('_rcl'))


@proc('')
def draw_recents():
    S('cur_layer', 1)
    with If(V('g_rec') == 1):
        S('pg_t', 99)                                # came from hold-halfway: already fully shown
    P.ease(V('pg_t') / V('anim_n'))
    S('gh', 100 - 45 * V('ez_o'))                     # dim fades in
    P.rect(0, 0, W, H, pal('black'))
    S('gh', 0)
    S('_rcn', listlen(L('rec')))
    with If(V('_rcn') == 0):
        S('fade', 100 - V('ez_o') * 100)
        P.text_c(W / 2, 170, 'No recent apps', 16, 1, 0)
        S('fade', 0)
    P.draw_switcher(0)
    with If((V('_rcn') == 0) & (V('rc_dis_app') == 0) & (V('rc_auto') == 1)):
        S('rc_auto', 0)
        P.nav_home()                                 # "Close all" finished: back to Home
    with If(V('_rcn') > 0):
        S('_rcf', 0)
        with If(V('rc_dis_app') == -1):
            P.ease(V('rc_dis_t') / 5)
            S('_rcf', V('ez_o') * 100)
            S('cur_layer', -1)
        S('fade', V('_rcf'))
        P.btn(W / 2 - 60, 288, 120, 30, 'Close all', 0)
        S('fade', 0)
        S('cur_layer', 1)
        with If(V('tap_o') == 1):
            S('rc_dis_app', -1)
            S('rc_dis_t', 0)
            S('rc_auto', 1)


V('rc_auto', 0)
V('nc_h', 160)


# ------------------------------------------------------------ status/nav ---
@proc('a')
def statusbar(a):
    """a = 0 transparent over the wallpaper .. 1 solid app bar; everything cross-fades with it"""
    S('cur_layer', 1)
    S('_sv', V('tx') * a)
    with If(a > 0.01):
        S('fade', (1 - a) * 100)
        P.rect(0, 0, W, SB, V('c_bg'))
        S('fade', 0)
    P.text(14, SB / 2, V('tstr'), 12, 1, V('_sv'), 0)
    with If(V('h24') == 0):
        P.text(14 + 8 + 5.6 * length(V('tstr')), SB / 2, V('ampm'), 9, 1, V('_sv'), 0)
    S('fade', (1 - V('wifi_a')) * 100)
    P.icon('wifi', W - 64, SB / 2, 14, V('_sv'))
    S('fade', V('wifi_a') * 100)
    P.icon('wifi_off', W - 64, SB / 2, 14, V('_sv'))
    S('fade', a * 100)
    P.rrect(W - 46, SB / 2 - 5.5, 24, 11, 3, pal('gray'))
    P.rrect(W - 44, SB / 2 - 3.5, 20, 7, 1.5, pal('white'))
    S('fade', (1 - a) * 100)
    P.rrect(W - 46, SB / 2 - 5.5, 24, 11, 3, V('c_div'))
    P.rrect(W - 44, SB / 2 - 3.5, 20, 7, 1.5, pal('green'))
    S('fade', 0)
    P.rect(W - 21.5, SB / 2 - 2, 2, 4, pal('gray'))


@proc('mode')
def nav_pcol(mode):
    """colour of the gesture bar -> _pc (palette index); mode 0 = over wallpaper, 1 = over an app"""
    S('_pc', pal('white'))                                   # nav_col 0 = automatic (contrast with the screen)
    with If((mode == 1) & (V('dark') == 0)):
        S('_pc', pal('black'))
    with If(V('nav_col') == 1):
        S('_pc', pal('white'))
    with If(V('nav_col') == 2):
        S('_pc', pal('black'))
    with If(V('nav_col') == 3):
        S('_pc', V('c_acc'))
    with If(V('nav_col') == 4):
        S('_pc', pal('gray'))


@proc('a')
def navbar(a):
    """a = solidity (0 over wallpaper .. 1 app).  bar_a fades the whole bar in/out (e.g. on unlock), nm_a cross-fades
    gesture pill <-> 3 buttons, pc_mix cross-fades the pill colour when it changes."""
    S('cur_layer', 1)
    with If(V('screen') <= SCR_LOCK):
        S('cur_layer', -1)                                    # fading out on the lock screen: not tappable
    S('_nv', V('tx') * a)
    with If(a > 0.01):
        S('fade', 100 - V('bar_a') * a * 100)
        P.rect(0, H - NB, W, NB, V('c_bg'))
    S('_ny', H - NB / 2)
    P.nav_pcol(round_(a))
    with If(V('_pc') != V('pc_cur')):
        S('pc_prev', V('pc_cur'))
        S('pc_cur', V('_pc'))
        S('pc_mix', 0)
    S('pc_mix', V('pc_mix') + (1 - V('pc_mix')) * V('lk35'))
    with If(V('pc_mix') > 0.997):
        S('pc_mix', 1)
    S('_pv', V('bar_a') * V('nm_a'))
    with If(V('_pv') > 0.01):
        S('_pw', V('nav_barw') * (0.6 + 0.4 * V('bar_a')))
        with If(V('gtype') == 1):
            S('_pw', V('_pw') * 1.25)
        with If((V('pc_mix') < 0.99) & (V('pc_prev') > 0)):
            S('fade', 100 - V('_pv') * (1 - V('pc_mix')) * 100)
            P.rrect(W / 2 - V('_pw') / 2, H - 7 - V('nav_barh'), V('_pw'), V('nav_barh'), V('nav_barh') / 2, V('pc_prev'))
        S('fade', 100 - V('_pv') * V('pc_mix') * 100)
        P.rrect(W / 2 - V('_pw') / 2, H - 7 - V('nav_barh'), V('_pw'), V('nav_barh'), V('nav_barh') / 2, V('pc_cur'))
    S('_bv', V('bar_a') * (1 - V('nm_a')))
    with If(V('_bv') > 0.01):
        S('fade', 100 - V('_bv') * 100)
        P.icon('back', W / 2 - 100, V('_ny'), 18, V('_nv'))
        P.icon('home', W / 2, V('_ny'), 18, V('_nv'))
        P.icon('recents', W / 2 + 100, V('_ny'), 18, V('_nv'))
    S('fade', 0)
    with If(V('navmode') == 0):
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
    with If(V('screen') == SCR_APP):
        S('sw_focus', V('app'))                       # the app you came from is the centre card
    with Else():
        S('sw_focus', 0)                              # otherwise the most recent one
    S('sw_off', 0)
    S('kb_open', 0)
    S('qs_open', 0)
    with If(V('screen') == SCR_REC):
        S('screen', SCR_HOME)
    with Else():
        S('screen', SCR_REC)


@proc('')
def nav_back():
    S('pg_back', 1)                                  # the next page change slides in from the left
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
        S('_kin', 0)
        with If((V('hit_o') == 1) & (V('md') == 1)):
            S('_kcol', V('c_div'))
            S('_kin', 2)
        P.rrect(V('_kx') + V('_kin'), y + V('_kin'), 56 - V('_kin') * 2, 26 - V('_kin') * 2, 6, V('_kcol'))
        P.text_c(V('_kx') + 28, y + 13 - V('_kin') * 4, V('_kc'), 15 + V('_kin') * 2, 0, V('tx'))
        with If(V('_kt') == 1):
            P.kb_type(V('_kc'))


@proc('x y w h label ic')
def kb_fn(x, y, w, h, label, ic):
    """function key (shift/backspace/enter/page): draws, sets tap_o"""
    P.tap(x, y, w, h)
    S('_ft', V('tap_o'))
    S('_fcol', V('c_div'))
    S('_fin', 0)
    with If((V('hit_o') == 1) & (V('md') == 1)):
        S('_fcol', V('c_surf'))
        S('_fin', 2)
    P.rrect(x + V('_fin'), y + V('_fin'), w - V('_fin') * 2, h - V('_fin') * 2, 6, V('_fcol'))
    with If(ic != ''):
        P.icon(ic, x + w / 2, y + h / 2, 17, V('tx'))
    with Else():
        P.text_c(x + w / 2, y + h / 2, label, 12, 1, V('tx'))
    S('tap_o', V('_ft'))


@proc('')
def draw_keyboard():
    S('cur_layer', 1)
    with If(V('kb_open') == 0):
        S('cur_layer', -1)                            # sliding away: visible, not tappable
    S('_ky', V('kb_top'))                           # kb_top follows kb_a, so the keyboard slides and apps resize with it
    P.rect(0, V('kb_top'), W, KB_H + 2, V('c_surf2'))
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
    with If(V('kb_open') == 1):
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
CC_H, NC_H = 150, 236          # panel heights (control centre / notification centre)
L('qt_a', [0, 0, 0, 0])        # tile on/off animation


@proc('')
def panel_input():
    """Pull down from the status bar: right half = control centre, left half = notifications.  The panel follows the
    finger; release snaps it open/closed (by position and direction).  A plain tap on the status bar toggles it.
    While open, a vertical drag anywhere on it (or the dim area) pulls it back up."""
    S('_pok', 0)
    with If((V('screen') > SCR_LOCK) & (V('dlg') == 0) & (V('gmode') == 0)):
        S('_pok', 1)
    with If((V('press') == 1) & (V('_pok') == 1)):
        with If(V('my') < SB + 6):
            with If(V('qs_open') == 0):
                S('qs_kind', 1 + (V('mx') < W / 2))
                S('kb_open', 0)
            S('qs_tapc', 1)
            S('qs_cand', 1)
            S('qs_y0', V('my'))
            S('qs_p0', V('qs_p'))
            S('press', 0)
        with Else():
            with If(V('qs_open') == 1):
                S('qs_cand', 1)
                S('qs_tapc', 0)
                S('qs_y0', V('my'))
                S('qs_p0', V('qs_p'))
    with If((V('md') == 1) & (V('qs_cand') == 1) & (V('moved') == 1) & (V('qs_drag') == 0)):
        with If(abs_(V('my') - V('qs_y0')) > abs_(V('mx') - V('px')) * 0.8):
            S('qs_drag', 1)
            S('qs_tapc', 0)
        with Else():
            S('qs_cand', 0)
    S('_ph', CC_H + 20)
    with If(V('qs_kind') == 2):
        S('_ph', NC_H + 20)
    with If((V('md') == 1) & (V('qs_drag') == 1)):
        S('qs_p', clamp(V('qs_p0') + (V('my') - V('qs_y0')) / V('_ph'), 0, 1))
    with If((V('md') == 0) & ((V('qs_drag') == 1) | (V('qs_tapc') == 1))):
        with If(V('qs_drag') == 1):
            S('_qth', 0.75)                             # pushing up: closes once it is a quarter of the way up
            with If(V('my') > V('qs_y0')):
                S('_qth', 0.25)                         # pulling down: opens past a quarter
            S('qs_open', 0)
            with If(V('qs_p') > V('_qth')):
                S('qs_open', 1)
        with Else():
            S('qs_open', 1 - V('qs_open'))
        S('qs_drag', 0)
        S('qs_tapc', 0)
        S('qs_cand', 0)
        S('rel', 0)
    with If(V('md') == 0):
        S('qs_cand', 0)
    with If(V('qs_drag') == 0):
        S('qs_p', V('qs_p') + (V('qs_open') - V('qs_p')) * V('lk35'))
        with If(abs_(V('qs_open') - V('qs_p')) < 0.003):
            S('qs_p', V('qs_open'))
    with If(V('_pok') == 0):
        S('qs_open', 0)


@proc('')
def draw_panels():
    S('cur_layer', 1)
    with If((V('qs_open') == 0) | (V('qs_drag') == 1)):
        S('cur_layer', -1)                                  # moving: no taps
    S('gh', 100 - 50 * V('qs_p'))
    P.rect(0, 0, W, H, pal('black'))
    S('gh', 0)
    with If(V('qs_kind') == 1):
        P.draw_cc()
    with Else():
        P.draw_nc()
    P.set_tf(1, W / 2, H / 2)
    S('fade', 0)


@proc('')
def draw_cc():
    P.tapr(0, SB + CC_H + 10, W, H - SB - CC_H - 10)
    with If(V('tap_o') == 1):
        S('qs_open', 0)
    P.set_tf(1, W / 2, H / 2 - (1 - V('qs_p')) * (CC_H + 30))
    S('fade', (1 - clamp(V('qs_p') * 1.6, 0, 1)) * 100)
    P.rrect(20, SB + 2, W - 40, CC_H, 18, V('c_surf'))
    P.rrect(W / 2 - 18, SB + CC_H - 8, 36, 4, 2, V('c_div'))           # grab handle
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
        S('_qa', item(L('qt_a'), V('_qi')))
        S('_qa', V('_qa') + (V('_qon') - V('_qa')) * V('lk35'))
        with If(abs_(V('_qon') - V('_qa')) < 0.003):
            S('_qa', V('_qon'))
        list_replace(L('qt_a'), V('_qi'), V('_qa'))
        P.tapr(V('_qx'), V('_qy'), 136, 62)
        S('_qt', V('tap_o'))
        S('_qin', 0)
        with If((V('hit_o') == 1) & (V('md') == 1) & (V('moved') == 0)):
            S('_qin', 3)                                       # pressed: tile sinks a little
        S('_qf', V('fade'))
        P.rrect(V('_qx') + V('_qin'), V('_qy') + V('_qin'), 136 - V('_qin') * 2, 62 - V('_qin') * 2, 14, V('c_surf2'))
        S('fade', 100 - (100 - V('_qf')) * V('_qa'))
        P.rrect(V('_qx') + V('_qin'), V('_qy') + V('_qin'), 136 - V('_qin') * 2, 62 - V('_qin') * 2, 14, V('c_acc'))
        S('fade', V('_qf'))
        P.icon(V('_qic'), V('_qx') + 68, V('_qy') + 22, 22, V('tx') * (1 - V('_qa')))
        P.text_c(V('_qx') + 68, V('_qy') + 47, V('_qn'), 12, 1, V('tx') * (1 - V('_qa')))
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


@proc('')
def draw_nc():
    P.tapr(0, SB + V('nc_h') + 10, W, H - SB - V('nc_h') - 10)
    with If(V('tap_o') == 1):
        S('qs_open', 0)
    P.set_tf(1, W / 2, H / 2 - (1 - V('qs_p')) * (V('nc_h') + 30))
    S('fade', (1 - clamp(V('qs_p') * 1.6, 0, 1)) * 100)
    S('_nf', V('fade'))
    S('_nht', 56 + clamp(listlen(L('nt_txt')), 1, 4) * 46 + 20 + (listlen(L('nt_txt')) > 4) * 16)
    S('nc_h', V('nc_h') + (V('_nht') - V('nc_h')) * V('lk35'))
    P.rrect(20, SB + 2, W - 40, V('nc_h'), 18, V('c_surf'))
    P.rrect(W / 2 - 18, SB + V('nc_h') - 8, 36, 4, 2, V('c_div'))
    P.text(38, SB + 24, 'Notifications', 16, 1, V('tx'), 0)
    S('_nn', listlen(L('nt_txt')))
    with If(V('_nn') == 0):
        P.text_c(W / 2, SB + 120, 'No notifications', 13, 0, V('tx2'))
    with Else():
        with If(V('nt_clr') == 99):
            P.btn(W - 130, SB + 10, 92, 26, 'Clear all', 0)
            with If(V('tap_o') == 1):
                S('nt_clr', 0)
    change(V('nt_dt'), V('fsc'))
    S('_ni', 0)
    with repeat(V('_nn')):
        inc('_ni')
        with If(V('_ni') <= 4):
            S('_ny', SB + 44 + (V('_ni') - 1) * 46)
            S('_nx', 0)
            S('fade', V('_nf'))
            with If((V('nt_dt') < V('anim_n')) & (V('_ni') >= V('nt_di'))):
                P.ease(V('nt_dt') / V('anim_n'))
                change(V('_ny'), (1 - V('ez_o')) * 46)          # rows below a removed one slide up
            with If(V('nt_clr') < 99):
                P.ease((V('nt_clr') - (V('_ni') - 1) * 1.5) / V('anim_n'))
                S('_nx', V('ez_o') * 120)                       # "Clear all": rows slide away one by one
                S('fade', 100 - (100 - V('_nf')) * (1 - V('ez_o')))
            P.tapr(W - 66 + V('_nx'), V('_ny') + 4, 34, 34)
            S('_ncl', V('tap_o'))
            P.rrect(34 + V('_nx'), V('_ny'), W - 68, 40, 12, V('c_surf2'))
            P.icon('info', 56 + V('_nx'), V('_ny') + 20, 18, V('tx2'))
            P.text(76 + V('_nx'), V('_ny') + 20, item(L('nt_txt'), V('_ni')), 13, 1, V('tx'), W - 230)
            P.text_r(W - 76 + V('_nx'), V('_ny') + 20, item(L('nt_time'), V('_ni')), 11, 0, V('tx2'))
            P.icon('close', W - 49 + V('_nx'), V('_ny') + 20, 12, V('tx2'))
            with If((V('_ncl') == 1) & (V('nt_clr') == 99)):
                list_delete(L('nt_txt'), V('_ni'))
                list_delete(L('nt_time'), V('_ni'))
                S('nt_di', V('_ni'))
                S('nt_dt', 0)
    S('fade', V('_nf'))
    with If(V('_nn') > 4):
        P.text_c(W / 2, SB + V('nc_h') - 22, join('+ ', V('_nn') - 4, ' more'), 11, 0, V('tx2'))
    with If(V('nt_clr') < 99):
        change(V('nt_clr'), V('fsc'))
        with If(V('nt_clr') > V('anim_n') + 6):
            list_clear(L('nt_txt'))
            list_clear(L('nt_time'))
            S('nt_clr', 99)


# ----------------------------------------------------------------- dialog --
@proc('')
def draw_dialog():
    S('cur_layer', 2)
    with If(V('dlg') == 0):
        S('cur_layer', -1)                            # closing: fades out, not tappable
    S('gh', 100 - 60 * V('dlg_a'))
    P.rect(0, 0, W, H, pal('black'))
    S('gh', 0)
    S('fade', (1 - V('dlg_a')) * 100)
    P.set_tf(0.85 + 0.15 * V('dlg_a'), W / 2, H / 2)
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
    S('fade', 0)


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
        S('_tout', 0)
        with If(V('toast_t') < 14):
            S('gh', 100 - V('toast_t') * 100 / 14)
            S('_tout', (1 - V('toast_t') / 14) * 16)
        P.ease((100 - V('toast_t')) / 8)
        P.set_tf(1, W / 2, H / 2 - (1 - V('ez_o')) * 34 - V('_tout'))
        P.rrect(W / 2 - V('tw_o') / 2 - 16, SB + 8, V('tw_o') + 32, 30, 15, pal('black'))
        P.text_c(W / 2, SB + 23, V('toast'), 13, 1, 0)
        P.set_tf(1, W / 2, H / 2)
        S('gh', 0)


# ------------------------------------------------------------------ frame ---
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
        P.draw_rec_exit()
        with If((V('gmode') == 1) & (V('g_rec') == 1)):
            S('gh', 45)
            P.rect(0, 0, W, H, pal('black'))
            S('gh', 0)
            P.draw_switcher(1)
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
            P.set_base(V('cur_s'), V('cur_cx'), V('cur_cy'))
    with If(V('_opening') == 0):
        S('clip0', SB)
        S('clip1', H - NB)
        P.rrect(0, 0, W, H, (1 - V('gs')) * 60, V('c_bg'))
        with If(V('_tfm') == 0):
            P.ease(V('pg_t') / V('anim_n'))                       # page transition: slide in from the right
            P.set_tf(1, W / 2 + (1 - V('ez_o')) * 36 * V('pg_dir') * V('pg_slide'), H / 2)
        S('no_hit', V('_tfm'))                               # dragged / springing-back window: inert
        P.app_draw()
        S('no_hit', 0)
        with If(V('gs') != 1):
            # shrunken window: bars drawn in window space hide anything that overlaps them (no clipping exists)
            P.rect(0, 0, W, SB, V('c_bg'))
            P.rect(0, H - NB, W, NB, V('c_bg'))
        P.set_base(1, W / 2, H / 2)
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
    P.set_base(1, W / 2, H / 2)
    S('no_hit', 0)
    P.panel_input()
    P.gesture_update()
    P.time_update()
    P.bg_tasks()
    inc('frame_n')
    if MODE == 'sprite':
        for _n in CM_LISTS:                      # new command buffer for this frame
            list_clear(L(_n))
        S('cm_n', 0)
        with If(V('pen_dirty') == 1):          # only Paint draws with the pen; clearing it requests a redraw (ends the VM step)
            pen_clear()
            S('pen_dirty', 0)
    else:
        pen_clear()
    S('gh', 0)
    effect('GHOST', 0)
    # which layer owns input this frame
    S('act_layer', 0)
    with If((V('qs_open') == 1) | (V('screen') == SCR_REC)):        # a panel that is closing never blocks input
        S('act_layer', 1)
    with If(V('dlg') == 1):
        S('act_layer', 2)
    with If(V('gmode') == 1):
        S('act_layer', 3)
    S('cur_layer', 0)
    S('clip0', SB)
    S('clip1', H - NB)
    with If(V('screen') != SCR_APP):
        S('kb_open', 0)
    # ---- everything that appears/disappears eases towards its target (time based)
    with If((V('screen') == SCR_APP) & (V('open_t') >= V('anim_n')) & (V('gmode') == 0)):
        S('_sm', 1)
    with Else():
        S('_sm', 0)
    S('sb_a', V('sb_a') + (V('_sm') - V('sb_a')) * V('lk35'))
    with If(abs_(V('_sm') - V('sb_a')) < 0.003):
        S('sb_a', V('_sm'))
    S('_bt', 0)
    with If(V('screen') > SCR_LOCK):
        S('_bt', 1)
    S('bar_a', V('bar_a') + (V('_bt') - V('bar_a')) * V('lk30'))
    with If(abs_(V('_bt') - V('bar_a')) < 0.003):
        S('bar_a', V('_bt'))
    S('nm_a', V('nm_a') + (V('navmode') - V('nm_a')) * V('lk35'))
    with If(abs_(V('navmode') - V('nm_a')) < 0.003):
        S('nm_a', V('navmode'))
    S('kb_a', V('kb_a') + (V('kb_open') - V('kb_a')) * V('lk50'))
    with If(abs_(V('kb_open') - V('kb_a')) < 0.003):
        S('kb_a', V('kb_open'))
    S('dlg_a', V('dlg_a') + (V('dlg') - V('dlg_a')) * V('lk50'))
    with If(abs_(V('dlg') - V('dlg_a')) < 0.003):
        S('dlg_a', V('dlg'))
    S('wifi_a', V('wifi_a') + (V('wifi') - V('wifi_a')) * V('lk35'))
    with If(abs_(V('wifi') - V('wifi_a')) < 0.003):
        S('wifi_a', V('wifi'))
    with If(V('kb_a') < 0.01):
        S('kb_top', H)
    with Else():
        S('kb_top', H - NB - KB_H * V('kb_a'))
    # ---- screen transitions that need the previous screen drawn on top for a moment
    with If((V('prev_scr') == SCR_REC) & (V('screen') != SCR_REC)):
        S('rx_t', 0)
        S('rx_skip', (V('screen') == SCR_APP) * V('app'))
    S('prev_scr', V('screen'))
    dispatch(V('screen'), [
        (SCR_BOOT, lambda: P.draw_boot()),
        (SCR_LOCK, lambda: P.draw_lock()),
        (SCR_HOME, lambda: (P.draw_home(), P.draw_closing(), P.draw_rec_exit(), P.draw_unlock_overlay())),
        (SCR_APP, lambda: P.draw_app()),
        (SCR_REC, lambda: P.draw_recents()),
    ])
    change(V('rx_t'), V('fsc'))
    with If(V('kb_a') > 0.01):
        P.draw_keyboard()
    with If(V('screen') > SCR_BOOT):
        with If(V('screen') == SCR_LOCK):
            P.statusbar(0)
        with Else():
            P.statusbar(V('sb_a'))
    with If(V('bar_a') > 0.01):
        P.navbar(V('sb_a'))
    with If(V('screen') == SCR_LOCK):
        P.ease(V('pg_t') / (V('anim_n') * 1.4))          # waking up: from black
        with If(V('ez_o') < 1):
            S('gh', V('ez_o') * 100)
            P.rect(0, 0, W, H, pal('black'))
            S('gh', 0)
    with If(V('qs_p') > 0.003):
        P.draw_panels()
        P.statusbar(0)
    with If(V('dlg_a') > 0.01):
        P.draw_dialog()
    P.draw_toast()
    S('_psig', V('screen') * 10000000 + V('app') * 1000000 + V('view') * 100000 + V('clk_tab') * 10000 + V('f_dir'))
    with If(V('_psig') != V('pg_sig')):
        S('pg_sig', V('_psig'))
        S('pg_t', 0)
        S('pg_dir', 1 - 2 * V('pg_back'))
        S('pg_slide', 1)
    S('pg_back', 0)
    S('_lsig', listlen(L('fs_id')) * 1000 + listlen(L('rec')))
    with If(V('_lsig') != V('ls_sig')):            # a list changed (file added/removed): rows re-settle, page stays
        with If(V('pg_t') > V('anim_n')):
            S('pg_t', 0)
            S('pg_slide', 0)
        S('ls_sig', V('_lsig'))
    with If(V('pg_t') < 99):
        change(V('pg_t'), V('fsc'))
    # a press that caused a screen/view change must not activate widgets of the new screen on release
    S('_sig', V('screen') * 100000 + V('app') * 1000 + V('view') * 100 + V('qs_open') * 10 + V('dlg') * 3 +
      V('kb_open'))
    with If(V('_sig') != V('ui_sig')):
        S('ui_sig', V('_sig'))
        S('moved', 1)
    with If(V('fclk') - V('last_save') >= 150):
        S('last_save', V('fclk'))
        P.store_save()
    # dark-mode switch: the old background colour dissolves; wallpaper change: a soft dip
    with If(V('th_t') < V('anim_n') * 1.5):
        P.ease(V('th_t') / (V('anim_n') * 1.5))
        S('gh', 15 + 85 * V('ez_o'))
        P.rect(0, 0, W, H, V('th_prev'))
        S('gh', 0)
        change(V('th_t'), V('fsc'))
    with If(V('wp_t') < V('anim_n') * 1.5):
        P.ease(V('wp_t') / (V('anim_n') * 1.5))
        S('gh', 55 + 45 * V('ez_o'))
        P.rect(0, 0, W, H, pal('black'))
        S('gh', 0)
        change(V('wp_t'), V('fsc'))
    # screen brightness
    with If(V('bright') < 100):
        S('gh', 100 - (100 - V('bright')) * 0.75)
        P.rect(0, 0, W, H, pal('black'))
        S('gh', 0)
    effect('GHOST', 0)
    if MODE == 'sprite':
        broadcast('render')                      # the Element clones draw this frame's buffer right after this script yields


V('_sm', 0)
V('ui_sig', 0)
V('pg_back', 0)
V('pg_dir', 1)
V('pg_slide', 1)
V('ls_sig', 0)
V('_lsig', 0)
V('pen_dirty', 0)
V('pg_sig', 0)
V('_psig', 0)
V('_sig', 0)


def make_main_script():
    """green-flag script (built after every module is imported so all procedures exist)"""
    with Script('flag'):
        hide()
        stage_size(W, H)
        rotation_all()
        if MODE == 'sprite':
            broadcast_wait('init_pool')           # Element creates its clone pool, then z-orders it
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
        S('th_dark', V('dark'))
        S('th_t', 99)
        S('wp_prev', V('wall'))
        S('wp_t', 99)
        S('unl_t', 99)
        S('rx_t', 99)
        S('bar_a', 0)
        S('nm_a', V('navmode'))
        S('kb_a', 0)
        S('dlg_a', 0)
        S('pin_a', 0)
        S('wifi_a', V('wifi'))
        S('prev_scr', SCR_BOOT)
        backdrop(7)
        with forever():
            P.frame()
