"""eOS apps: virtual file system, Files, Notes (+shared text editor), Calculator, Clock, Terminal, Paint, Snake, Settings."""
from sb3 import *
from os_core import *
from modes import MODE, app_unit
import assets
import os_sys  # noqa  (kb_begin, ask, launch ... are procedures resolved lazily)

# =============================================================== data =====
WELCOME = ("Welcome to eOS!\n\nThis is a small operating system running inside PenguinMod. "
           "Everything you see is drawn live with the pen.\n\nTry the Terminal, draw something in Paint, "
           "or edit this file: tap the text to bring up the keyboard.")
DEFAULT_FS = [
    # id, name, parent, type(1=folder), data
    (1, 'root', 0, 1, ''),
    (2, 'Documents', 1, 1, ''),
    (3, 'Notes', 1, 1, ''),
    (4, 'Pictures', 1, 1, ''),
    (5, 'System', 1, 1, ''),
    (6, 'welcome.txt', 2, 0, WELCOME),
    (7, 'Shopping.txt', 3, 0, "Milk\nBread\nPenguin food"),
    (8, 'Ideas.txt', 3, 0, "- Add a music player\n- Make a browser\n- Wi-Fi settings"),
    (9, 'version.txt', 5, 0, "eOS 1.0\nbuilt for PenguinMod"),
]
L('fs_id', [r[0] for r in DEFAULT_FS])
L('fs_name', [r[1] for r in DEFAULT_FS])
L('fs_parent', [r[2] for r in DEFAULT_FS])
L('fs_type', [r[3] for r in DEFAULT_FS])
L('fs_data', [r[4] for r in DEFAULT_FS])
V('fs_next', 10)

PAINT_NAMES = ('black', 'white', 'red', 'a_orange', 'yellow', 'green', 'sky', 'a_blue', 'a_purple', 'brown')
_HEX = dict(assets.PAL)
L('paint_hex', ['#' + _HEX[n] for n in PAINT_NAMES])
L('ps_x')
L('ps_y')
L('ps_c')
L('ps_w')
L('ps_s')
L('term_out')
L('sn_x')
L('sn_y')

for _n, _v in [
    ('f_dir', 1), ('ed_file', 0), ('fs_i', 0), ('fs_f', 0), ('fs_c', 0), ('fs_new', 0), ('fs_nm', ''), ('fs_p', ''),
    ('ren_id', 0), ('pv_o', ''),
    ('calc_d', '0'), ('calc_a', 0), ('calc_op', ''), ('calc_new', 1), ('calc_h', ''),
    ('clk_tab', 1), ('sw_run', 0), ('sw_start', 0), ('sw_acc', 0), ('tm_set', 60), ('tm_run', 0), ('tm_end', 0),
    ('tm_left', 60), ('tm_flash', 0),
    ('t_cwd', 1), ('tcmd', ''), ('targ', ''), ('targ2', ''), ('t_open', 0),
    ('pt_c', 1), ('pt_w', 4), ('pt_last_x', -99), ('pt_last_y', -99), ('pt_on', 0),
    ('sn_dir', 1), ('sn_nd', 1), ('sn_fx', 5), ('sn_fy', 5), ('sn_score', 0), ('sn_best', 0), ('sn_state', 0),
    ('sn_t', 0), ('sn_spd', 8),
    ('fmt_o', ''), ('arg_i', 0), ('tl_n', 0), ('tl_add', 0), ('tl_t', 99), ('tm_bar', 0), ('tm_tot', 60), ('pt_hy', SB + 195), ('ed_clen', -1), ('ed_cfile', 0), ('ed_py', 0), ('ed_px', 24),
]:
    V(_n, _v)




def seg_group(gid, var, opts, y, h=28):
    """row of choices; the selected one gets an accent pill that slides between choices (os_core seg_hl)"""
    for (lbl, val, x, w) in opts:
        P.btn(x, y, w, h, lbl, 0)
        with If(V('tap_o') == 1):
            S(var, val)
    for (lbl, val, x, w) in opts:
        with If(V(var) == val):
            S('_sgtx', x)
            S('_sgtw', w)
            S('_sgtl', lbl)
    P.seg_hl(gid, V('_sgtx'), y, V('_sgtw'), h)
    S('fade', clamp(abs_(item(L('seg_x'), gid) - V('_sgtx')) / 24, 0, 1) * 100)     # label appears as the pill arrives
    P.text_c(V('_sgtx') + V('_sgtw') / 2, y + h / 2, V('_sgtl'), 13, 1, 0)
    S('fade', 0)


# ============================================================= file system ==
@proc('id')
def fs_idx(id_):
    S('fs_i', indexof(L('fs_id'), id_))


@proc('parent name')
def fs_find(parent, name):
    """-> fs_f = list index of child `name` in folder `parent` (0 if none)"""
    S('fs_f', 0)
    S('_fi', 0)
    with repeat(listlen(L('fs_id'))):
        inc('_fi')
        with If((V('fs_f') == 0) & (item(L('fs_parent'), V('_fi')) == parent) &
                (item(L('fs_name'), V('_fi')) == name)):
            S('fs_f', V('_fi'))


@proc('parent')
def fs_count(parent):
    S('fs_c', 0)
    S('_fi', 0)
    with repeat(listlen(L('fs_id'))):
        inc('_fi')
        with If(item(L('fs_parent'), V('_fi')) == parent):
            inc('fs_c')


@proc('parent name type data')
def fs_add(parent, name, type_, data):
    S('fs_new', V('fs_next'))
    inc('fs_next')
    list_add(L('fs_id'), V('fs_new'))
    list_add(L('fs_name'), name)
    list_add(L('fs_parent'), parent)
    list_add(L('fs_type'), type_)
    list_add(L('fs_data'), data)


@proc('parent base ext')
def fs_free_name(parent, base, ext):
    """-> fs_nm : a name not yet used in `parent`"""
    S('fs_nm', join(base, ext))
    S('_fn', 1)
    P.fs_find(parent, V('fs_nm'))
    with until(V('fs_f') == 0):
        inc('_fn')
        S('fs_nm', join(base, ' ', V('_fn'), ext))
        P.fs_find(parent, V('fs_nm'))


@proc('id')
def fs_path(id_):
    """-> fs_p absolute path"""
    S('fs_p', '')
    S('_pc', id_)
    S('_pg', 0)
    with until((V('_pc') == 1) | (V('_pc') == 0) | (V('_pg') > 20)):
        inc('_pg')
        P.fs_idx(V('_pc'))
        with If(V('fs_i') == 0):
            S('_pc', 0)
        with Else():
            S('fs_p', join('/', item(L('fs_name'), V('fs_i')), V('fs_p')))
            S('_pc', item(L('fs_parent'), V('fs_i')))
    with If(V('fs_p') == ''):
        S('fs_p', '/')


@proc('id')
def fs_delete(id_):
    P.fs_idx(id_)
    with If(id_ <= 5):
        P.notify("System folders can't be removed")
    with If((V('fs_i') > 0) & (id_ > 5)):
        S('_dd', 1)
        with If(item(L('fs_type'), V('fs_i')) == 1):
            P.fs_count(id_)
            with If(V('fs_c') > 0):
                S('_dd', 0)
                P.notify('Folder is not empty')
        with If(V('_dd') == 1):
            list_delete(L('fs_id'), V('fs_i'))
            list_delete(L('fs_name'), V('fs_i'))
            list_delete(L('fs_parent'), V('fs_i'))
            list_delete(L('fs_type'), V('fs_i'))
            list_delete(L('fs_data'), V('fs_i'))


@proc('s n')
def preview(s, n):
    """first n chars of s with newlines flattened -> pv_o"""
    S('pv_o', '')
    S('_vi', 1)
    S('_vl', length(s))
    with until((V('_vi') > V('_vl')) | (V('_vi') > n)):
        S('_vc', letter(V('_vi'), s))
        with If(V('_vc') == '\n'):
            S('pv_o', join(V('pv_o'), ' '))
        with Else():
            S('pv_o', join(V('pv_o'), V('_vc')))
        inc('_vi')


@proc('')
def fs_reset():
    for nm in ('fs_id', 'fs_name', 'fs_parent', 'fs_type', 'fs_data'):
        list_clear(L(nm))
    for (i, n, p, t, d) in DEFAULT_FS:
        list_add(L('fs_id'), i)
        list_add(L('fs_name'), n)
        list_add(L('fs_parent'), p)
        list_add(L('fs_type'), t)
        list_add(L('fs_data'), d)
    S('fs_next', 10)


# ============================================================ shared UI =====
@proc('title')
def header(title):
    S('clip0', SB)
    P.rect(0, SB, W, 36, V('c_surf'))
    P.rect(0, SB + 36, W, 1, V('c_div'))
    P.text(16, SB + 18, title, 16, 1, V('tx'), W - 230)


@proc('')
def text_submit():
    """called once when Enter is pressed in the on-screen keyboard (ti_act says which field it belonged to)"""
    with If(V('ti_act') < 30):
        S('kb_open', 0)
    with If((V('ti_act') >= 10) & (V('ti_act') <= 12) & (V('ti') != '')):
        S('_parent', V('f_dir'))
        with If(V('ti_act') == 12):
            P.fs_idx(V('ren_id'))
            S('_parent', item(L('fs_parent'), V('fs_i')))
        P.fs_find(V('_parent'), V('ti'))
        S('_dup', 0)
        with If(V('fs_f') > 0):
            S('_dup', 1)
            with If((V('ti_act') == 12) & (item(L('fs_id'), V('fs_f')) == V('ren_id'))):
                S('_dup', 0)
        with If((V('ti_act') == 12) & (V('ren_id') <= 5)):
            P.notify("System folders can't be renamed")
        with Else():
            with If(V('_dup') == 1):
                P.notify('That name is already used')
            with Else():
                with If(V('ti_act') == 10):
                    P.fs_add(V('f_dir'), V('ti'), 1, '')
                with If(V('ti_act') == 11):
                    S('_nn', V('ti'))
                    with If(~contains(V('ti'), '.')):
                        S('_nn', join(V('ti'), '.txt'))
                    P.fs_add(V('f_dir'), V('_nn'), 0, '')
                    S('ed_file', V('fs_new'))
                    S('view', 1)
                    P.kb_begin('', '', 20, 1, 1500)
                with If(V('ti_act') == 12):
                    P.fs_idx(V('ren_id'))
                    list_replace(L('fs_name'), V('fs_i'), V('ti'))
    with If(V('ti_act') == 30):
        if MODE == 'sprite':
            broadcast_wait('term_run')
        else:
            P.term_run()


@proc('')
def dlg_run():
    with If(V('dlg_act') == 1):
        P.fs_delete(V('dlg_arg'))
    with If(V('dlg_act') == 2):
        P.factory_reset()
    with If(V('dlg_act') == 3):
        P.paint_clear()
    with If(V('dlg_act') == 5):
        with If(indexof(L('home_apps'), V('dlg_arg')) > 0):
            list_delete(L('home_apps'), indexof(L('home_apps'), V('dlg_arg')))
        with If(indexof(L('rec'), V('dlg_arg')) > 0):
            list_delete(L('rec'), indexof(L('rec'), V('dlg_arg')))
        P.notify(join(item(L('app_name'), V('dlg_arg')), ' removed'))
        P.store_save()
    with If(V('dlg_act') == 4):
        S('screen', SCR_BOOT)
        S('boot_t', 0)
        backdrop(7)
        S('qs_open', 0)
        S('kb_open', 0)
        list_clear(L('rec'))


@proc('')
def factory_reset():
    P.fs_reset()
    S('dark', 0)
    S('accent', 0)
    S('wall', 1)
    S('bright', 100)
    S('wifi', 1)
    S('bt', 0)
    S('h24', 0)
    S('pin', '')
    S('navmode', 1)
    S('anim_n', 10)
    for _n, _v in (('nav_col', 0), ('nav_barw', 110), ('nav_barh', 5), ('nav_close', 74), ('nav_swipe', 1), ('nav_edge', 1),
                   ('nav_hold', 1), ('nav_tap', 0)):
        S(_n, _v)
    P.theme()
    P.paint_clear()
    list_clear(L('term_out'))
    S('f_dir', 1)
    S('view', 0)
    S('sn_best', 0)
    S('vol', 70)
    S('mute', 0)
    S('st_app', 0)
    list_clear(L('home_apps'))
    for _a in range(1, NAPPS + 1):
        list_add(L('home_apps'), _a)
    P.home_snap()
    P.store_save()
    P.notify('eOS has been reset')


@proc('a')
def app_init(a):
    S('view', 0)
    S('scroll', 0)
    if MODE == 'sprite':
        broadcast_wait_dyn(join('init_', a))          # every app sprite listens for its own id
    else:
        with If(a == APP_FILES):
            S('f_dir', 1)
        with If(a == APP_CALC):
            P.calc_reset()
        with If(a == APP_CLOCK):
            S('clk_tab', 1)
        with If(a == APP_TERM):
            S('t_open', 0)
            P.kb_begin('', '', 30, 0, 80)
        with If(a == APP_SNAKE):
            P.snake_reset()


@proc('')
def app_back():
    """sets back_o = 1 when the app consumed the Back press"""
    S('back_o', 0)
    with If(V('app') == APP_FILES):
        with If(V('view') == 1):
            S('view', 0)
            S('kb_open', 0)
            S('back_o', 1)
        with Else():
            with If(V('f_dir') != 1):
                P.fs_idx(V('f_dir'))
                S('f_dir', item(L('fs_parent'), V('fs_i')))
                S('scroll', 0)
                S('back_o', 1)
    with If((V('app') == APP_NOTES) & (V('view') == 1)):
        S('view', 0)
        S('kb_open', 0)
        S('back_o', 1)
    with If((V('app') == APP_SET) & (V('view') > 0)):
        S('view', 0)
        S('pin_in', '')
        S('back_o', 1)


@proc('')
def app_draw():
    # text input submitted?
    with If(V('kb_done') == 1):
        S('kb_done', 0)
        P.text_submit()
    if MODE == 'sprite':
        broadcast_wait_dyn(join('draw_', V('app')))
    else:
        dispatch(V('app'), [
            (APP_FILES, lambda: P.app_files()),
            (APP_NOTES, lambda: P.app_notes()),
            (APP_CALC, lambda: P.app_calc()),
            (APP_CLOCK, lambda: P.app_clock()),
            (APP_TERM, lambda: P.app_term()),
            (APP_PAINT, lambda: P.app_paint()),
            (APP_SNAKE, lambda: P.app_snake()),
            (APP_SET, lambda: P.app_settings()),
            (APP_STORE, lambda: P.app_store()),
        ])
    S('cur_layer', 0)


@proc('')
def bg_tasks():
    """things that keep running while an app is in the background"""
    with If(V('tm_run') == 1):
        S('tm_left', V('tm_end') - timer())
        with If(V('tm_left') <= 0):
            S('tm_run', 0)
            S('tm_left', 0)
            S('tm_flash', 90)
            P.notify('Timer finished')
    with If(V('tm_flash') > 0):
        change(V('tm_flash'), 0 - V('fsc'))
    with If(V('st_app') > 0):                       # an app is being installed (keeps going in the background)
        change(V('st_p'), V('fsc') / 55)
        with If(V('st_p') >= 1):
            with If(indexof(L('home_apps'), V('st_app')) == 0):
                list_add(L('home_apps'), V('st_app'))
                P.slot_pos(listlen(L('home_apps')))
                list_replace(L('hp_x'), V('st_app'), V('sp_x'))
                list_replace(L('hp_y'), V('st_app'), V('sp_y'))
                list_replace(L('hp_s'), V('st_app'), 0)        # its Home icon pops in
            P.notify(join(item(L('app_name'), V('st_app')), ' installed'))
            S('st_app', 0)
            S('st_p', 0)
            P.store_save()


@proc('')
def paint_clear():
    list_clear(L('ps_x'))
    list_clear(L('ps_y'))
    list_clear(L('ps_c'))
    list_clear(L('ps_w'))
    list_clear(L('ps_s'))



# ================================================================ editor ====
@proc('')
def editor():
    """shared text editor for the file in ed_file (view 1)"""
    P.fs_idx(V('ed_file'))
    S('_ei', V('fs_i'))
    S('_eb', H - NB - 6)
    with If(V('kb_open') == 1):
        S('_eb', V('kb_top') - 6)
    S('clip0', SB + 37)
    # tap on the text area opens the keyboard
    with If(V('kb_open') == 0):
        P.tapr(0, SB + 37, W, V('_eb') - SB - 37)
        with If(V('tap_o') == 1):
            P.kb_begin('', item(L('fs_data'), V('_ei')), 20, 1, 1500)
    with If((V('kb_open') == 1) & (V('ti_act') == 20)):
        list_replace(L('fs_data'), V('_ei'), V('ti'))
    S('_et', item(L('fs_data'), V('_ei')))
    P.rect(0, SB + 37, W, H - SB - 37, V('c_surf'))
    # measure, then draw bottom-anchored when the text is longer than the page
    with If((length(V('_et')) != V('ed_clen')) | (V('ed_file') != V('ed_cfile'))):
        P.para(24, 0, W - 48, V('_et'), 14, 20, V('tx'), 0)      # measuring is the expensive part: cache it
        S('ed_clen', length(V('_et')))
        with If(V('ed_file') != V('ed_cfile')):
            S('scroll', 0)
        S('ed_cfile', V('ed_file'))
        S('ed_py', V('p_y'))
        S('ed_px', V('p_x'))
    S('_ov', V('ed_py') + 14 - (V('_eb') - (SB + 49)))     # how far the text overflows the page
    with If(V('_ov') < 0):
        S('_ov', 0)
    with If(V('kb_open') == 1):
        S('_eoff', 0 - V('_ov'))                            # typing: follow the caret
    with Else():
        P.scroll_update(V('_ov'))                           # reading: drag to scroll
        S('_eoff', 0 - V('scroll'))
    if MODE == 'sprite':
        # the caret is part of the text (Iris places it right after the last character); hidden = transparent
        with If(V('kb_open') == 1):
            S('caret_u', 2 + 2 * ((V('fclk') % 30) >= 18))
        P.para(24, SB + 56 + V('_eoff'), W - 48, V('_et'), 14, 20, V('tx'), 1)
        S('caret_u', 0)
    else:
        P.para(24, SB + 56 + V('_eoff'), W - 48, V('_et'), 14, 20, V('tx'), 1)
        with If(((V('fclk') % 30) < 18) & (V('kb_open') == 1)):
            P.rect(V('ed_px') + 1, SB + 56 + V('_eoff') + V('ed_py') - 8, 2, 17, V('c_acc'))
    with If(V('_et') == ''):
        P.text(24, SB + 56, 'Empty file - tap here to start typing', 14, 0, V('tx2'), 0)
    P.header(item(L('fs_name'), V('_ei')))
    P.text_r(W - 16, SB + 18, join(length(V('_et')), ' chars'), 12, 0, V('tx2'))


# ================================================================= Files ====
with app_unit('Files'):
    @proc('i y')
    def file_row(i, y):
        S('_rid', item(L('fs_id'), i))
        S('_rty', item(L('fs_type'), i))
        S('_rname', item(L('fs_name'), i))
        # action buttons sit on top of the row -> handled first
        P.tapr(W - 46, y + 4, 36, 36)
        S('_rdel', V('tap_o'))
        P.tapr(W - 88, y + 4, 36, 36)
        S('_rren', V('tap_o'))
        P.tapr(0, y, W, 44)
        S('_rt', V('tap_o'))
        S('_rcol', V('c_surf'))
        with If((V('hit_o') == 1) & (V('md') == 1) & (V('moved') == 0)):
            S('_rcol', V('c_div'))
        P.rrect(12, y + 1, W - 24, 42, 10, V('_rcol'))
        with If(V('_rty') == 1):
            P.icon('folder', 38, y + 22, 24, V('tx2'))
            P.text(60, y + 15, V('_rname'), 14, 1, V('tx'), W - 230)
            P.fs_count(V('_rid'))
            P.text(60, y + 32, join(V('fs_c'), ' items'), 11, 0, V('tx2'), 200)
        with Else():
            P.icon('file', 38, y + 22, 22, V('tx2'))
            P.text(60, y + 15, V('_rname'), 14, 1, V('tx'), W - 230)
            P.text(60, y + 32, join(length(item(L('fs_data'), i)), ' chars'), 11, 0, V('tx2'), 200)
        P.icon('edit', W - 70, y + 22, 16, V('tx2'))
        P.icon('trash', W - 28, y + 22, 16, V('tx2'))
        with If(V('_rdel') == 1):
            P.ask('Delete?', join('"', V('_rname'), '" will be removed.'), 'Delete', 1, V('_rid'))
        with If(V('_rren') == 1):
            S('ren_id', V('_rid'))
            P.kb_begin('Rename', V('_rname'), 12, 0, 30)
        with If(V('_rt') == 1):
            with If(V('_rty') == 1):
                S('f_dir', V('_rid'))
                S('scroll', 0)
            with Else():
                S('ed_file', V('_rid'))
                S('view', 1)
                S('kb_open', 0)


    @proc('')
    def app_files():
        with If(indexof(L('fs_id'), V('f_dir')) == 0):
            S('f_dir', 1)
        with If((V('view') == 1) & (indexof(L('fs_id'), V('ed_file')) == 0)):
            S('view', 0)
        with If(V('view') == 1):
            P.editor()
        with Else():
            S('clip0', SB + 37)
            P.fs_count(V('f_dir'))
            S('_fc', V('fs_c'))
            P.scroll_update(V('_fc') * 46 + 70 - (H - NB - SB))
            with If(V('_fc') == 0):
                P.text_c(W / 2, 170, 'This folder is empty', 14, 0, V('tx2'))
            S('_fp', 0)
            S('_rowi', 0)
            S('_fy', SB + 44 - V('scroll'))
            with repeat(2):
                inc('_fp')
                S('_fk', 0)
                with repeat(listlen(L('fs_id'))):
                    inc('_fk')
                    with If((item(L('fs_parent'), V('_fk')) == V('f_dir')) &
                            (item(L('fs_type'), V('_fk')) == 2 - V('_fp'))):
                        P.stag(V('_rowi'))
                        P.file_row(V('_fk'), V('_fy') + V('stag_o'))
                        inc('_rowi')
                        change(V('_fy'), 46)
            P.fs_path(V('f_dir'))
            P.header(V('fs_p'))
            P.btn(W - 192, SB + 5, 88, 26, 'New folder', 0)
            with If(V('tap_o') == 1):
                P.kb_begin('New folder name', '', 10, 0, 30)
            P.btn(W - 98, SB + 5, 82, 26, 'New file', 1)
            with If(V('tap_o') == 1):
                P.kb_begin('New file name', '', 11, 0, 30)



    if MODE == 'sprite':
        with Script('receive:draw_1'):
            P.app_files()
        with Script('receive:init_1'):
            S('f_dir', 1)


# ================================================================= Notes ====
with app_unit('Notes'):
    @proc('')
    def app_notes():
        with If((V('view') == 1) & (indexof(L('fs_id'), V('ed_file')) == 0)):
            S('view', 0)
        with If(V('view') == 1):
            P.editor()
        with Else():
            S('clip0', SB + 37)
            P.fs_count(3)
            S('_fc', V('fs_c'))
            P.scroll_update(V('_fc') * 62 + 70 - (H - NB - SB))
            with If(V('_fc') == 0):
                P.text_c(W / 2, 170, 'No notes yet - tap New note', 14, 0, V('tx2'))
            S('_fy', SB + 46 - V('scroll'))
            S('_rowi', 0)
            S('_fk', 0)
            with repeat(listlen(L('fs_id'))):
                inc('_fk')
                with If((item(L('fs_parent'), V('_fk')) == 3) & (item(L('fs_type'), V('_fk')) == 0)):
                    S('_nid', item(L('fs_id'), V('_fk')))
                    S('_nk', V('_fk'))
                    P.stag(V('_rowi'))
                    inc('_rowi')
                    S('_fy0', V('_fy'))
                    change(V('_fy'), V('stag_o'))
                    P.tapr(W - 54, V('_fy') + 8, 40, 40)
                    S('_ndel', V('tap_o'))
                    P.tapr(14, V('_fy'), W - 28, 56)
                    S('_nt', V('tap_o'))
                    S('_ncol', V('c_surf'))
                    with If((V('hit_o') == 1) & (V('md') == 1) & (V('moved') == 0)):
                        S('_ncol', V('c_div'))
                    P.rrect(14, V('_fy'), W - 28, 56, 12, V('_ncol'))
                    P.rrect(14, V('_fy'), 6, 56, 3, pal('yellow'))
                    P.text(34, V('_fy') + 17, item(L('fs_name'), V('_nk')), 14, 1, V('tx'), W - 150)
                    P.preview(item(L('fs_data'), V('_nk')), 60)
                    P.text(34, V('_fy') + 38, V('pv_o'), 12, 0, V('tx2'), W - 150)
                    P.icon('trash', W - 34, V('_fy') + 28, 17, V('tx2'))
                    with If(V('_ndel') == 1):
                        P.ask('Delete note?', join('"', item(L('fs_name'), V('_nk')), '" will be removed.'), 'Delete',
                              1, V('_nid'))
                    with If(V('_nt') == 1):
                        S('ed_file', V('_nid'))
                        S('view', 1)
                        S('kb_open', 0)
                    S('_fy', V('_fy0') + 62)
            P.header('Notes')
            P.btn(W - 112, SB + 5, 96, 26, 'New note', 1)
            with If(V('tap_o') == 1):
                P.fs_free_name(3, 'Note', '.txt')
                P.fs_add(3, V('fs_nm'), 0, '')
                S('ed_file', V('fs_new'))
                S('view', 1)
                P.kb_begin('', '', 20, 1, 1500)



    if MODE == 'sprite':
        with Script('receive:draw_2'):
            P.app_notes()
        with Script('receive:init_2'):
            S('view', 0)


# ============================================================== Calculator ==
with app_unit('Calculator'):
    @proc('')
    def calc_reset():
        S('calc_d', '0')
        S('calc_a', 0)
        S('calc_op', '')
        S('calc_new', 1)
        S('calc_h', '')


    @proc('')
    def calc_eval():
        """apply calc_op to calc_a and the displayed number"""
        S('_cb', V('calc_d'))
        with If(V('calc_op') == '+'):
            S('_cr', V('calc_a') + V('_cb'))
        with If(V('calc_op') == '-'):
            S('_cr', V('calc_a') - V('_cb'))
        with If(V('calc_op') == '×'):
            S('_cr', V('calc_a') * V('_cb'))
        with If(V('calc_op') == '÷'):
            with If(V('_cb') == 0):
                S('_cr', 'Error')
            with Else():
                S('_cr', V('calc_a') / V('_cb'))
        with If(V('_cr') == 'Error'):
            S('calc_d', 'Error')
        with Else():
            S('_cr', round_(V('_cr') * 10000000000) / 10000000000)
            S('calc_d', V('_cr'))
        S('calc_a', V('calc_d'))


    @proc('k')
    def calc_key(k):
        S('cb_t', 0)
        with If(V('calc_d') == 'Error'):
            P.calc_reset()
        with If(k == 'C'):
            P.calc_reset()
        with If(contains('0123456789', k) & (length(k) == 1)):
            with If((V('calc_new') == 1) | ((V('calc_d') == '0') & (length(V('calc_d')) == 1))):
                S('calc_d', k)
                S('calc_new', 0)
            with Else():
                with If(length(V('calc_d')) < 13):
                    S('calc_d', join(V('calc_d'), k))
        with If(k == '.'):
            with If(V('calc_new') == 1):
                S('calc_d', '0.')
                S('calc_new', 0)
            with Else():
                with If(~contains(V('calc_d'), '.')):
                    S('calc_d', join(V('calc_d'), '.'))
        with If(k == '±'):
            with If(V('calc_d') != 0):
                S('calc_d', 0 - V('calc_d'))
        with If(k == '%'):
            S('calc_d', round_(V('calc_d') / 100 * 10000000000) / 10000000000)
            S('calc_new', 1)
        with If((k == '+') | (k == '-') | (k == '×') | (k == '÷')):
            with If((V('calc_op') != '') & (V('calc_new') == 0)):
                P.calc_eval()
            with Else():
                S('calc_a', V('calc_d'))
            S('calc_op', k)
            S('calc_new', 1)
            S('calc_h', join(V('calc_a'), ' ', k))
        with If(k == '='):
            with If(V('calc_op') != ''):
                S('calc_h', join(V('calc_a'), ' ', V('calc_op'), ' ', V('calc_d'), ' ='))
                P.calc_eval()
                S('calc_op', '')
                S('calc_new', 1)


    CALC_KEYS = ['C', '±', '%', '÷', '7', '8', '9', '×', '4', '5', '6', '-', '1', '2', '3', '+', '0', '.', '=']


    @proc('')
    def app_calc():
        P.header('Calculator')
        S('_cx0', W / 2 - 180)
        P.rrect(V('_cx0'), SB + 42, 360, 60, 14, V('c_surf'))
        P.text_r(V('_cx0') + 344, SB + 56, V('calc_h'), 12, 0, V('tx2'))
        change(V('cb_t'), V('fsc'))
        P.ease(V('cb_t') / 7)
        S('_cs', 38 * (1 + 0.12 * (1 - V('ez_o'))))
        with If(length(V('calc_d')) > 9):
            S('_cs', 30 * (1 + 0.12 * (1 - V('ez_o'))))
        with If(length(V('calc_d')) > 12):
            S('_cs', 24 * (1 + 0.12 * (1 - V('ez_o'))))
        P.text_r(V('_cx0') + 344, SB + 84, V('calc_d'), V('_cs'), 1, V('tx'))
        S('_ck', 0)
        S('_cy', SB + 122)
        with repeat(19):
            inc('_ck')
            S('_cx', V('_cx0') + ((V('_ck') - 1) % 4) * 92)
            S('_cy', SB + 110 + floor((V('_ck') - 1) / 4) * 36)
            S('_cw', 84)
            with If(V('_ck') == 17):
                S('_cx', V('_cx0'))
                S('_cw', 176)
            with If(V('_ck') == 18):
                S('_cx', V('_cx0') + 184)
            with If(V('_ck') == 19):
                S('_cx', V('_cx0') + 276)
            S('_cl', item(L('calc_keys'), V('_ck')))
            P.tap(V('_cx'), V('_cy'), V('_cw'), 31)
            S('_ct', V('tap_o'))
            S('_cc', V('c_surf'))
            S('_ctx', V('tx'))
            with If((V('_ck') % 4 == 0) | (V('_ck') == 19)):
                S('_cc', V('c_acc'))
                S('_ctx', 0)
            with If((V('_ck') < 4) & (V('_ck') != 4)):
                S('_cc', V('c_surf2'))
            with If(V('_ck') == 4):
                S('_cc', V('c_acc'))
                S('_ctx', 0)
            S('_cin', 0)
            with If((V('hit_o') == 1) & (V('md') == 1)):
                S('_cc', V('c_div'))
                S('_cin', 2)
            P.rrect(V('_cx') + V('_cin'), V('_cy') + V('_cin'), V('_cw') - V('_cin') * 2, 31 - V('_cin') * 2, 9, V('_cc'))
            P.text_c(V('_cx') + V('_cw') / 2, V('_cy') + 15.5, V('_cl'), 16 - V('_cin') * 0.5, 1, V('_ctx'))
            with If(V('_ct') == 1):
                P.calc_key(V('_cl'))


    L('calc_keys', CALC_KEYS)



    if MODE == 'sprite':
        with Script('receive:draw_3'):
            P.app_calc()
        with Script('receive:init_3'):
            P.calc_reset()


# ================================================================== Clock ===
with app_unit('Clock'):
    @proc('n')
    def fmt_ms(secs):
        """secs (float) -> fmt_o  MM:SS.cc"""
        S('_fm', floor(secs / 60))
        S('_fs', floor(secs % 60))
        S('_fc2', floor((secs * 100) % 100))
        P.pad2(V('_fm'))
        S('fmt_o', join(V('pad_o'), ':'))
        P.pad2(V('_fs'))
        S('fmt_o', join(V('fmt_o'), V('pad_o'), '.'))
        P.pad2(V('_fc2'))
        S('fmt_o', join(V('fmt_o'), V('pad_o')))


    @proc('')
    def app_clock():
        P.header('Clock')
        # tabs
        S('_tb', 0)
        with repeat(3):
            inc('_tb')
            S('_tx0', W / 2 - 210 + (V('_tb') - 1) * 140)
            P.tapr(V('_tx0'), SB + 40, 140, 30)
            with If(V('tap_o') == 1):
                S('clk_tab', V('_tb'))
            with If(V('clk_tab') == V('_tb')):
                P.text_c(V('_tx0') + 70, SB + 54, item(L('clk_tabs'), V('_tb')), 14, 1, V('tx'))
                S('_tabt', V('_tx0') + 30)
            with Else():
                P.text_c(V('_tx0') + 70, SB + 54, item(L('clk_tabs'), V('_tb')), 14, 0, V('tx2'))
        S('tab_x', V('tab_x') + (V('_tabt') - V('tab_x')) * V('lk30'))
        P.rrect(V('tab_x'), SB + 68, 80, 3, 1.5, V('c_acc'))
        with If(V('clk_tab') == 1):
            P.clock_face(W / 2 - 150, 214, 102)
            P.text(W / 2 + 10, 150, V('tstr'), 48, 1, V('tx'), 0)
            P.text(W / 2 + 12, 196, V('dstr'), 14, 0, V('tx2'), 0)
            P.text(W / 2 + 12, 218, join('Seconds: ', V('ss')), 12, 0, V('tx2'), 0)
        with If(V('clk_tab') == 2):
            S('_se', V('sw_acc'))
            with If(V('sw_run') == 1):
                S('_se', V('sw_acc') + timer() - V('sw_start'))
            P.fmt_ms(V('_se'))
            P.text_c(W / 2, 170, V('fmt_o'), 56, 1, V('tx'))
            P.btn(W / 2 - 130, 236, 120, 40, 'Reset', 0)
            with If(V('tap_o') == 1):
                S('sw_run', 0)
                S('sw_acc', 0)
            with If(V('sw_run') == 1):
                P.btn(W / 2 + 10, 236, 120, 40, 'Stop', 2)
                with If(V('tap_o') == 1):
                    S('sw_acc', V('sw_acc') + timer() - V('sw_start'))
                    S('sw_run', 0)
            with Else():
                P.btn(W / 2 + 10, 236, 120, 40, 'Start', 1)
                with If(V('tap_o') == 1):
                    S('sw_start', timer())
                    S('sw_run', 1)
        with If(V('clk_tab') == 3):
            with If(V('tm_run') == 0):
                S('tm_left', V('tm_set'))
            S('_tl', V('tm_left'))
            with If(V('tm_run') == 1):
                S('_tl', V('tm_left') + 0.99)
            P.pad2(floor(V('_tl') / 60))
            S('_tm1', V('pad_o'))
            P.pad2(floor(V('_tl') % 60))
            S('_tcol', V('tx'))
            with If(V('tm_flash') > 0):
                with If((V('tm_flash') % 20) < 10):
                    P.rrect(W / 2 - 150, 122, 300, 90, 22, V('c_acc'))
                    S('_tcol', 0)
            P.text_c(W / 2, 168, join(V('_tm1'), ':', V('pad_o')), 62, 1, V('_tcol'))
            S('_tbt', 0)
            with If(V('tm_run') == 1):
                S('_tbt', V('tm_left') / clamp(V('tm_tot'), 1, 99999))
            S('tm_bar', V('tm_bar') + (V('_tbt') - V('tm_bar')) * V('lk35'))
            with If(V('tm_bar') > 0.003):
                P.rrect(W / 2 - 150, 210, 300, 4, 2, V('c_div'))
                P.rrect(W / 2 - 150, 210, 300 * V('tm_bar'), 4, 2, V('c_acc'))
            with If(V('tm_run') == 0):
                P.btn(W / 2 - 190, 226, 90, 34, '-1 min', 0)
                with If(V('tap_o') == 1):
                    S('tm_set', clamp(V('tm_set') - 60, 10, 5940))
                P.btn(W / 2 - 94, 226, 90, 34, '-10 s', 0)
                with If(V('tap_o') == 1):
                    S('tm_set', clamp(V('tm_set') - 10, 10, 5940))
                P.btn(W / 2 + 4, 226, 90, 34, '+10 s', 0)
                with If(V('tap_o') == 1):
                    S('tm_set', clamp(V('tm_set') + 10, 10, 5940))
                P.btn(W / 2 + 100, 226, 90, 34, '+1 min', 0)
                with If(V('tap_o') == 1):
                    S('tm_set', clamp(V('tm_set') + 60, 10, 5940))
                P.btn(W / 2 - 60, 276, 120, 38, 'Start', 1)
                with If(V('tap_o') == 1):
                    S('tm_end', timer() + V('tm_set'))
                    S('tm_tot', V('tm_set'))
                    S('tm_run', 1)
            with Else():
                P.btn(W / 2 - 130, 238, 120, 40, 'Cancel', 0)
                with If(V('tap_o') == 1):
                    S('tm_run', 0)
                P.btn(W / 2 + 10, 238, 120, 40, 'Pause', 2)
                with If(V('tap_o') == 1):
                    S('tm_set', ceil(V('tm_left')))
                    S('tm_run', 0)


    L('clk_tabs', ['Clock', 'Stopwatch', 'Timer'])


    L('acc_hex', ['#' + dict(assets.PAL)[n] for n in ('a_blue', 'a_teal', 'a_green', 'a_orange', 'a_pink', 'a_purple')])


    @proc('cx cy r')
    def clock_face(cx, cy, r):
        P.circle(cx, cy, r * 2 + 8, V('c_div'))
        P.circle(cx, cy, r * 2, V('c_surf'))
        S('_cti', 0)
        with repeat(12):
            S('_ca', V('_cti') * 30)
            P.hand(cx + sin(V('_ca')) * (r - 14), cy - cos(V('_ca')) * (r - 14),
                   cx + sin(V('_ca')) * (r - 6), cy - cos(V('_ca')) * (r - 6), 3, pal('gray'))
            inc('_cti')
        S('_ca', (V('hh') % 12 + V('mm') / 60) * 30)
        P.hand(cx, cy, cx + sin(V('_ca')) * r * 0.5, cy - cos(V('_ca')) * r * 0.5, 6, V('c_acc'))
        S('_ca', (V('mm') + V('ss') / 60) * 6)
        P.hand(cx, cy, cx + sin(V('_ca')) * r * 0.74, cy - cos(V('_ca')) * r * 0.74, 4,
               V('c_acc'))
        S('_ca', V('ssf') * 6)
        P.hand(cx - sin(V('_ca')) * r * 0.12, cy + cos(V('_ca')) * r * 0.12, cx + sin(V('_ca')) * r * 0.86,
               cy - cos(V('_ca')) * r * 0.86, 2, pal('red'))
        P.circle(cx, cy, 10, pal('red'))



    if MODE == 'sprite':
        with Script('receive:draw_4'):
            P.app_clock()
        with Script('receive:init_4'):
            S('clk_tab', 1)


# =============================================================== Terminal ===
with app_unit('Terminal'):
    @proc('s')
    def tout(s):
        list_add(L('term_out'), s)
        with If(listlen(L('term_out')) > 120):
            list_delete(L('term_out'), 1)


    @proc('s')
    def split_cmd(s):
        """s -> tcmd (first word), targ (rest)"""
        S('tcmd', '')
        S('targ', '')
        S('_si', 1)
        S('_sn', length(s))
        with until((V('_si') > V('_sn')) | (letter(V('_si'), s) == ' ')):
            S('tcmd', join(V('tcmd'), letter(V('_si'), s)))
            inc('_si')
        inc('_si')
        with until(V('_si') > V('_sn')):
            S('targ', join(V('targ'), letter(V('_si'), s)))
            inc('_si')


    @proc('s')
    def split_arg(s):
        """s -> targ (first word), targ2 (rest)"""
        S('_a', V('targ'))
        S('targ', '')
        S('targ2', '')
        S('_si', 1)
        S('_sn', length(s))
        with until((V('_si') > V('_sn')) | (letter(V('_si'), s) == ' ')):
            S('targ', join(V('targ'), letter(V('_si'), s)))
            inc('_si')
        inc('_si')
        with until(V('_si') > V('_sn')):
            S('targ2', join(V('targ2'), letter(V('_si'), s)))
            inc('_si')


    @proc('path')
    def resolve(path):
        """path (absolute or relative to t_cwd) -> res_o = fs id, 0 if not found"""
        S('res_o', V('t_cwd'))
        S('_ri2', 1)
        S('_rn2', length(path))
        S('_seg', '')
        with If(letter(1, path) == '/'):
            S('res_o', 1)
            S('_ri2', 2)
        with Else():
            S('_ri2', 1)
        # walk segments (the loop runs one extra time to flush the final segment)
        with until((V('_ri2') > V('_rn2') + 1) | (V('res_o') == 0)):
            S('_c2', letter(V('_ri2'), path))
            with If((V('_c2') == '/') | (V('_ri2') > V('_rn2'))):
                with If(V('_seg') != ''):
                    with If(V('_seg') == '..'):
                        P.fs_idx(V('res_o'))
                        with If(V('res_o') != 1):
                            S('res_o', item(L('fs_parent'), V('fs_i')))
                    with Else():
                        with If(V('_seg') != '.'):
                            P.fs_find(V('res_o'), V('_seg'))
                            with If((V('fs_f') == 0)):
                                S('res_o', 0)
                            with Else():
                                S('res_o', item(L('fs_id'), V('fs_f')))
                S('_seg', '')
            with Else():
                S('_seg', join(V('_seg'), V('_c2')))
            inc('_ri2')


    V('res_o', 1)


    @proc('')
    def term_run():
        with If(indexof(L('fs_id'), V('t_cwd')) == 0):
            S('t_cwd', 1)
        P.fs_path(V('t_cwd'))
        P.tout(join('eos:', V('fs_p'), '$ ', V('ti')))
        P.split_cmd(V('ti'))
        S('_cmd', V('tcmd'))
        S('_arg', V('targ'))
        S('ti', '')
        with If(V('_cmd') == ''):
            stop_this()
        with If(V('_cmd') == 'help'):
            P.tout('help clear echo date whoami uname neofetch')
            P.tout('ls cd pwd mkdir touch cat rm mv')
            P.tout('open <app>   theme dark|light   lock   reboot')
            P.tout('echo text > file  writes text into a file')
        with If(V('_cmd') == 'clear'):
            list_clear(L('term_out'))
        with If(V('_cmd') == 'echo'):
            P.term_echo(V('_arg'))
        with If(V('_cmd') == 'date'):
            P.tout(join(V('dstr'), ' ', V('tsec'), ' ', V('ampm')))
        with If(V('_cmd') == 'whoami'):
            P.tout('user')
        with If(V('_cmd') == 'uname'):
            P.tout('eOS 1.0 (PenguinMod, pen renderer)')
        with If(V('_cmd') == 'neofetch'):
            P.tout('  eOS 1.0')
            P.tout('  Kernel: Scratch VM')
            P.tout(join('  Uptime: ', floor(timer() / 60), ' min'))
            with If(V('dark') == 1):
                P.tout('  Theme: dark')
            with Else():
                P.tout('  Theme: light')
            P.tout(join('  Files: ', listlen(L('fs_id')), ' items'))
            P.tout('  Apps: 8')
        with If(V('_cmd') == 'pwd'):
            P.fs_path(V('t_cwd'))
            P.tout(V('fs_p'))
        with If(V('_cmd') == 'ls'):
            S('_lt', V('t_cwd'))
            with If(V('_arg') != ''):
                P.resolve(V('_arg'))
                S('_lt', V('res_o'))
            with If(V('_lt') == 0):
                P.tout('ls: no such directory')
            with Else():
                P.fs_count(V('_lt'))
                with If(V('fs_c') == 0):
                    P.tout('(empty)')
                S('_lk', 0)
                S('_lo', '')
                with repeat(listlen(L('fs_id'))):
                    inc('_lk')
                    with If(item(L('fs_parent'), V('_lk')) == V('_lt')):
                        with If(item(L('fs_type'), V('_lk')) == 1):
                            S('_lo', join(V('_lo'), item(L('fs_name'), V('_lk')), '/   '))
                        with Else():
                            S('_lo', join(V('_lo'), item(L('fs_name'), V('_lk')), '   '))
                with If(V('_lo') != ''):
                    P.tout(V('_lo'))
        with If(V('_cmd') == 'cd'):
            with If(V('_arg') == ''):
                S('t_cwd', 1)
            with Else():
                P.resolve(V('_arg'))
                with If(V('res_o') == 0):
                    P.tout('cd: no such directory')
                with Else():
                    P.fs_idx(V('res_o'))
                    with If(item(L('fs_type'), V('fs_i')) == 1):
                        S('t_cwd', V('res_o'))
                    with Else():
                        P.tout('cd: not a directory')
        with If((V('_cmd') == 'mkdir') | (V('_cmd') == 'touch')):
            with If(V('_arg') == ''):
                P.tout(join(V('_cmd'), ': missing name'))
            with Else():
                P.fs_find(V('t_cwd'), V('_arg'))
                with If(V('fs_f') > 0):
                    P.tout(join(V('_cmd'), ': already exists'))
                with Else():
                    with If(V('_cmd') == 'mkdir'):
                        P.fs_add(V('t_cwd'), V('_arg'), 1, '')
                    with Else():
                        P.fs_add(V('t_cwd'), V('_arg'), 0, '')
        with If(V('_cmd') == 'cat'):
            P.resolve(V('_arg'))
            with If(V('res_o') == 0):
                P.tout('cat: no such file')
            with Else():
                P.fs_idx(V('res_o'))
                with If(item(L('fs_type'), V('fs_i')) == 1):
                    P.tout('cat: is a directory')
                with Else():
                    P.term_lines(item(L('fs_data'), V('fs_i')))
        with If(V('_cmd') == 'rm'):
            P.resolve(V('_arg'))
            with If(V('res_o') == 0):
                P.tout('rm: no such file or folder')
            with Else():
                P.fs_delete(V('res_o'))
        with If(V('_cmd') == 'mv'):
            P.split_arg(V('_arg'))
            P.resolve(V('targ'))
            with If((V('res_o') <= 5) | (V('targ2') == '')):
                P.tout('usage: mv <old> <new-name>')
            with Else():
                P.fs_idx(V('res_o'))
                list_replace(L('fs_name'), V('fs_i'), V('targ2'))
        with If(V('_cmd') == 'theme'):
            with If(V('_arg') == 'dark'):
                S('dark', 1)
                P.theme()
            with If(V('_arg') == 'light'):
                S('dark', 0)
                P.theme()
            with If((V('_arg') != 'dark') & (V('_arg') != 'light')):
                P.tout('usage: theme dark|light')
        with If(V('_cmd') == 'lock'):
            P.go_lock()
        with If(V('_cmd') == 'reboot'):
            P.dlg_run_reboot()
        with If(V('_cmd') == 'open'):
            S('_oi', indexof(L('app_name'), V('_arg')))
            with If(V('_oi') == 0):
                P.tout('open: unknown app')
            with Else():
                P.launch(V('_oi'), 0, 0)
                S('open_t', 99)
        with If(~((V('_cmd') == 'help') | (V('_cmd') == 'clear') | (V('_cmd') == 'echo') | (V('_cmd') == 'date') |
                  (V('_cmd') == 'whoami') | (V('_cmd') == 'uname') | (V('_cmd') == 'neofetch') | (V('_cmd') == 'pwd') |
                  (V('_cmd') == 'ls') | (V('_cmd') == 'cd') | (V('_cmd') == 'mkdir') | (V('_cmd') == 'touch') |
                  (V('_cmd') == 'cat') | (V('_cmd') == 'rm') | (V('_cmd') == 'mv') | (V('_cmd') == 'theme') |
                  (V('_cmd') == 'lock') | (V('_cmd') == 'reboot') | (V('_cmd') == 'open'))):
            P.tout(join(V('_cmd'), ': command not found (try help)'))


    @proc('')
    def dlg_run_reboot():
        S('dlg_act', 4)
        P.dlg_run()


    @proc('s')
    def term_lines(s):
        """add multi-line text to the terminal output"""
        S('_ln', '')
        S('_li', 1)
        with repeat(length(s)):
            with If(letter(V('_li'), s) == '\n'):
                P.tout(V('_ln'))
                S('_ln', '')
            with Else():
                S('_ln', join(V('_ln'), letter(V('_li'), s)))
            inc('_li')
        P.tout(V('_ln'))


    @proc('s')
    def term_echo(s):
        """echo text  |  echo text > file"""
        S('_gt', 0)
        S('_ei2', 1)
        with repeat(length(s)):
            with If((letter(V('_ei2'), s) == '>') & (V('_gt') == 0)):
                S('_gt', V('_ei2'))
            inc('_ei2')
        with If(V('_gt') == 0):
            P.tout(s)
        with Else():
            S('_txt', '')
            S('_fn2', '')
            S('_ei2', 1)
            with repeat(length(s)):
                with If(V('_ei2') < V('_gt') - 1):
                    S('_txt', join(V('_txt'), letter(V('_ei2'), s)))
                with If(V('_ei2') > V('_gt') + 1):
                    S('_fn2', join(V('_fn2'), letter(V('_ei2'), s)))
                inc('_ei2')
            with If(V('_fn2') == ''):
                P.tout('echo: missing file name')
            with Else():
                P.fs_find(V('t_cwd'), V('_fn2'))
                with If(V('fs_f') == 0):
                    P.fs_add(V('t_cwd'), V('_fn2'), 0, V('_txt'))
                with Else():
                    list_replace(L('fs_data'), V('fs_f'), V('_txt'))


    @proc('')
    def app_term():
        P.rect(0, SB, W, H - SB, pal('black'))
        S('_tb', H - NB - 4)
        with If(V('kb_open') == 1):
            S('_tb', V('kb_top') - 4)
        with If(V('kb_open') == 0):
            P.tapr(0, SB, W, V('_tb') - SB)
            with If(V('tap_o') == 1):
                P.kb_begin('', V('ti'), 30, 0, 80)
        P.fs_path(V('t_cwd'))
        S('_nl', floor((V('_tb') - SB - 20) / 15))
        S('_tn', listlen(L('term_out')))
        S('_t0', V('_tn') - V('_nl') + 1)
        with If(V('_t0') < 1):
            S('_t0', 1)
        with If(V('_tn') != V('tl_n')):
            S('tl_add', clamp(V('_tn') - V('tl_n'), 0, 8))
            S('tl_n', V('_tn'))
            S('tl_t', 0)
        change(V('tl_t'), V('fsc'))
        P.ease(V('tl_t') / 5)
        S('_tle', V('ez_o'))
        S('_ty', SB + 12 + (1 - V('_tle')) * 15 * V('tl_add'))
        S('_tk', V('_t0') - 1)
        with repeat(V('_tn') - V('_t0') + 1):
            inc('_tk')
            with If(V('_tk') > V('_tn') - V('tl_add')):
                S('fade', (1 - V('_tle')) * 100)             # the new lines fade in while the text scrolls up
            P.text(10, V('_ty'), item(L('term_out'), V('_tk')), 12, 0, 0, W - 20)
            S('fade', 0)
            change(V('_ty'), 15)
        S('_pr', join('eos:', V('fs_p'), '$ '))
        P.tw(V('_pr'), 12, 1)
        P.text(10, V('_ty'), V('_pr'), 12, 1, -25, 0)
        S('_cxx', 10 + V('tw_o'))
        P.text(V('_cxx'), V('_ty'), V('ti'), 12, 0, 0, W - 40 - V('tw_o'))
        P.tw(V('ti'), 12, 0)
        with If((V('fclk') % 30) < 18):
            P.rect(V('_cxx') + V('tw_o') + 1, V('_ty') - 7, 7, 14, pal('white'))





    if MODE == 'sprite':
        with Script('receive:draw_5'):
            P.app_term()
        with Script('receive:init_5'):
            S('t_open', 0)
            P.kb_begin('', '', 30, 0, 80)
        with Script('receive:term_run'):
            P.term_run()


# ================================================================== Paint ===
with app_unit('Paint'):
    PX0, PY0, PW, PH = 78, SB + 38, 552, H - NB - SB - 44


    @proc('', warp=True)
    def paint_draw():
        """canvas background (sprite build: pen layer) + stroke replay; warp so a pen loop doesn't cost one VM step per iteration"""
        if MODE == 'sprite':
            # the canvas lives on the pen layer (below all sprites): white background drawn with fat pen lines
            S('pen_dirty', 1)
            pen_up()
            pen_color(item(L('paint_hex'), 2))
            pen_size(8 * V('gs'))
            S('_pyy', PY0 + 4)
            with repeat(ceil(PH / 8)):
                goto(gx(PX0 + 4), gy(V('_pyy')))
                pen_down()
                goto(gx(PX0 + PW - 4), gy(V('_pyy')))
                pen_up()
                change(V('_pyy'), 8)
        else:
            P.rrect(PX0 - 2, PY0 - 2, PW + 4, PH + 4, 6, V('c_div'))
            P.rect(PX0, PY0, PW, PH, pal('white'))
        # replay strokes
        S('_pn', listlen(L('ps_x')))
        S('_pi', 0)
        pen_up()
        with repeat(V('_pn')):
            inc('_pi')
            with If(item(L('ps_s'), V('_pi')) == 1):
                pen_up()
                pen_color(item(L('paint_hex'), item(L('ps_c'), V('_pi'))))
                pen_size(item(L('ps_w'), V('_pi')) * V('gs'))
                goto(V('gox') + item(L('ps_x'), V('_pi')) * V('gs') - 320, 180 - V('goy') - item(L('ps_y'), V('_pi')) * V('gs'))
                pen_down()
            with Else():
                goto(V('gox') + item(L('ps_x'), V('_pi')) * V('gs') - 320, 180 - V('goy') - item(L('ps_y'), V('_pi')) * V('gs'))
        pen_up()

    @proc('')
    def app_paint():
        P.header('Paint')
        P.paint_draw()
        # canvas input: a press that starts in the canvas draws
        P.hit(PX0, PY0, PW, PH)
        with If((V('press') == 1) & (V('hit_o') == 1)):
            S('pt_on', 1)
            S('press', 0)
            S('pt_new', 1)
        with If(V('md') == 0):
            S('pt_on', 0)
        with If((V('pt_on') == 1) & (V('md') == 1)):
            S('_hw', V('pt_w') / 2 + 1)
            S('_ppx', clamp(V('mx'), PX0 + V('_hw'), PX0 + PW - V('_hw')))
            S('_ppy', clamp(V('my'), PY0 + V('_hw'), PY0 + PH - V('_hw')))
            with If((V('pt_new') == 1) | (abs_(V('_ppx') - V('pt_last_x')) + abs_(V('_ppy') - V('pt_last_y')) > 2)):
                with If(listlen(L('ps_x')) < 3000):
                    list_add(L('ps_x'), V('_ppx'))
                    list_add(L('ps_y'), V('_ppy'))
                    list_add(L('ps_c'), V('pt_c'))
                    list_add(L('ps_w'), V('pt_w'))
                    list_add(L('ps_s'), V('pt_new'))
                S('pt_new', 0)
                S('pt_last_x', V('_ppx'))
                S('pt_last_y', V('_ppy'))
        # toolbar
        P.rect(0, SB + 37, 72, H - SB - 37, V('c_surf'))
        P.rect(72, SB + 37, 1, H, V('c_div'))
        change(V('pt_pop'), V('fsc'))
        P.ease(V('pt_pop') / 8)
        S('_pk', 0)
        with repeat(10):
            inc('_pk')
            S('_px2', 20 + ((V('_pk') - 1) % 2) * 30)
            S('_py2', SB + 56 + floor((V('_pk') - 1) / 2) * 28)
            P.tapr(V('_px2') - 13, V('_py2') - 13, 26, 26)
            with If(V('tap_o') == 1):
                S('pt_c', V('_pk'))
                S('pt_pop', 0)
            with If(V('pt_c') == V('_pk')):
                P.circle(V('_px2'), V('_py2'), 26 + 8 * (1 - V('ez_o')), V('c_acc'))
            P.circle(V('_px2'), V('_py2'), 20, V('c_div'))
            P.circle(V('_px2'), V('_py2'), 18, item(L('paint_pal'), V('_pk')))
        # brush sizes
        S('_pk', 0)
        with repeat(3):
            inc('_pk')
            S('_pw2', 2 + (V('_pk') - 1) * 4 + (V('_pk') - 1) * (V('_pk') - 1) * 2)
            S('_py3', SB + 206 + (V('_pk') - 1) * 24)
            P.tapr(8, V('_py3') - 11, 56, 22)
            with If(V('tap_o') == 1):
                S('pt_w', V('_pw2'))
            with If(V('pt_w') == V('_pw2')):
                S('_pht', V('_py3') - 11)
        S('pt_hy', V('pt_hy') + (V('_pht') - V('pt_hy')) * V('lk35'))     # selection glides between sizes
        P.rrect(8, V('pt_hy'), 56, 22, 8, V('c_surf2'))
        S('_pk', 0)
        with repeat(3):
            inc('_pk')
            S('_pw2', 2 + (V('_pk') - 1) * 4 + (V('_pk') - 1) * (V('_pk') - 1) * 2)
            S('_py3', SB + 206 + (V('_pk') - 1) * 24)
            P.circle(36, V('_py3'), V('_pw2') + 2, pal('dgray'))
        P.btn(8, SB + 278, 56, 24, 'Clear', 2)
        with If(V('tap_o') == 1):
            P.ask('Clear canvas?', 'The drawing will be erased.', 'Clear', 3, 0)
        P.text_r(W - 16, SB + 18, join(listlen(L('ps_x')), ' / 3000'), 11, 0, V('tx2'))


    L('paint_pal', [pal(n) for n in PAINT_NAMES])



    if MODE == 'sprite':
        with Script('receive:draw_6'):
            P.app_paint()
        with Script('receive:init_6'):
            S('view', 0)


# ================================================================== Snake ===
with app_unit('Snake'):
    SN_X0, SN_Y0, SN_C, SN_COLS, SN_ROWS = 12, SB + 40, 18, 24, 14


    @proc('')
    def snake_food():
        S('_ok', 0)
        S('_try', 0)
        with until((V('_ok') == 1) | (V('_try') > 300)):
            inc('_try')
            S('sn_fx', rand(0, SN_COLS - 1))
            S('sn_fy', rand(0, SN_ROWS - 1))
            S('_ok', 1)
            S('_k', 0)
            with repeat(listlen(L('sn_x'))):
                inc('_k')
                with If((item(L('sn_x'), V('_k')) == V('sn_fx')) & (item(L('sn_y'), V('_k')) == V('sn_fy'))):
                    S('_ok', 0)


    @proc('')
    def snake_reset():
        list_clear(L('sn_x'))
        list_clear(L('sn_y'))
        for i in range(3):
            list_add(L('sn_x'), 8 - i)
            list_add(L('sn_y'), 7)
        S('sn_dir', 1)
        S('sn_nd', 1)
        S('sn_score', 0)
        S('sn_state', 0)
        S('sn_t', 0)
        S('sn_spd', 8)
        P.snake_food()


    @proc('d')
    def snake_turn(d):
        with If((d != (V('sn_dir') + 2) % 4)):
            S('sn_nd', d)
            with If(V('sn_state') == 0):
                S('sn_state', 1)


    @proc('')
    def snake_step():
        S('sn_dir', V('sn_nd'))
        S('_nx', item(L('sn_x'), 1))
        S('_ny', item(L('sn_y'), 1))
        with If(V('sn_dir') == 0):
            inc('_ny', -1)
        with If(V('sn_dir') == 1):
            inc('_nx')
        with If(V('sn_dir') == 2):
            inc('_ny')
        with If(V('sn_dir') == 3):
            inc('_nx', -1)
        S('_dead', 0)
        with If((V('_nx') < 0) | (V('_nx') >= SN_COLS) | (V('_ny') < 0) | (V('_ny') >= SN_ROWS)):
            S('_dead', 1)
        S('_k', 0)
        with repeat(listlen(L('sn_x')) - 1):
            inc('_k')
            with If((item(L('sn_x'), V('_k')) == V('_nx')) & (item(L('sn_y'), V('_k')) == V('_ny'))):
                S('_dead', 1)
        with If(V('_dead') == 1):
            S('sn_state', 2)
            S('sn_pop', 0)
            with If(V('sn_score') > V('sn_best')):
                S('sn_best', V('sn_score'))
        with Else():
            list_insert(L('sn_x'), 1, V('_nx'))
            list_insert(L('sn_y'), 1, V('_ny'))
            with If((V('_nx') == V('sn_fx')) & (V('_ny') == V('sn_fy'))):
                inc('sn_score')
                S('sn_spd', clamp(8 - floor(V('sn_score') / 4), 3, 8))
                P.snake_food()
            with Else():
                list_delete(L('sn_x'), listlen(L('sn_x')))
                list_delete(L('sn_y'), listlen(L('sn_y')))


    @proc('')
    def app_snake():
        P.header('Snake')
        # keyboard
        with If(key_pressed('up arrow')):
            P.snake_turn(0)
        with If(key_pressed('right arrow')):
            P.snake_turn(1)
        with If(key_pressed('down arrow')):
            P.snake_turn(2)
        with If(key_pressed('left arrow')):
            P.snake_turn(3)
        # swipe on the board
        P.hit(SN_X0, SN_Y0, SN_COLS * SN_C, SN_ROWS * SN_C)
        with If((V('md') == 1) & (V('moved') == 1) & (V('hit_o') == 1)):
            with If((abs_(V('mx') - V('px')) > 16) | (abs_(V('my') - V('py')) > 16)):
                with If(abs_(V('mx') - V('px')) > abs_(V('my') - V('py'))):
                    with If(V('mx') > V('px')):
                        P.snake_turn(1)
                    with Else():
                        P.snake_turn(3)
                with Else():
                    with If(V('my') > V('py')):
                        P.snake_turn(2)
                    with Else():
                        P.snake_turn(0)
                S('px', V('mx'))
                S('py', V('my'))
        with If(V('sn_state') == 1):
            change(V('sn_t'), V('fsc'))
            with If(V('sn_t') >= V('sn_spd')):
                S('sn_t', 0)
                P.snake_step()
        # board
        P.rrect(SN_X0 - 3, SN_Y0 - 3, SN_COLS * SN_C + 6, SN_ROWS * SN_C + 6, 10, V('c_div'))
        P.rrect(SN_X0, SN_Y0, SN_COLS * SN_C, SN_ROWS * SN_C, 7, V('c_surf'))
        P.circle(SN_X0 + V('sn_fx') * SN_C + SN_C / 2, SN_Y0 + V('sn_fy') * SN_C + SN_C / 2, SN_C - 5 + 3 * sin(V('fclk') * 14), pal('red'))
        S('_sf', 0)                                           # fraction of the way to the next cell
        with If(V('sn_state') == 1):
            S('_sf', clamp(V('sn_t') / V('sn_spd'), 0, 1))
        S('_k', 0)
        with repeat(listlen(L('sn_x'))):
            inc('_k')
            S('_sc', V('c_acc'))
            S('_gx', item(L('sn_x'), V('_k')))
            S('_gy', item(L('sn_y'), V('_k')))
            with If(V('_k') == 1):
                S('_sc', pal('a_green'))
                S('_gx', V('_gx') + ((V('sn_nd') == 1) - (V('sn_nd') == 3)) * V('_sf'))
                S('_gy', V('_gy') + ((V('sn_nd') == 2) - (V('sn_nd') == 0)) * V('_sf'))
            with Else():
                S('_gx', V('_gx') + (item(L('sn_x'), V('_k') - 1) - V('_gx')) * V('_sf'))
                S('_gy', V('_gy') + (item(L('sn_y'), V('_k') - 1) - V('_gy')) * V('_sf'))
            P.rrect(SN_X0 + V('_gx') * SN_C + 1, SN_Y0 + V('_gy') * SN_C + 1, SN_C - 2, SN_C - 2, 5, V('_sc'))
        # side panel
        S('_sx', SN_X0 + SN_COLS * SN_C + 22)
        P.text(V('_sx'), SB + 58, 'Score', 12, 0, V('tx2'), 0)
        P.text(V('_sx'), SB + 82, V('sn_score'), 28, 1, V('tx'), 0)
        P.text(V('_sx'), SB + 112, join('Best ', V('sn_best')), 12, 0, V('tx2'), 0)
        S('_dx', V('_sx') + 56)
        S('_dy', SB + 182)
        for (nm, dx, dy, d) in (('up', 0, -42, 0), ('left', -42, 0, 3), ('right', 42, 0, 1), ('down', 0, 42, 2)):
            P.tap(V('_dx') + dx - 18, V('_dy') + dy - 18, 36, 36)
            S('_dt', V('tap_o'))
            S('_din', 0)
            with If((V('hit_o') == 1) & (V('md') == 1)):
                S('_din', 3)                                  # d-pad key sinks while held
            P.rrect(V('_dx') + dx - 18 + V('_din'), V('_dy') + dy - 18 + V('_din'), 36 - V('_din') * 2,
                    36 - V('_din') * 2, 10, V('c_surf2'))
            P.icon(nm, V('_dx') + dx, V('_dy') + dy, 18, V('tx'))
            with If(V('_dt') == 1):
                P.snake_turn(d)
        with If(V('sn_state') == 0):
            P.rrect(SN_X0 + 76, SN_Y0 + 208, 280, 32, 16, pal('black'))
            P.text_c(SN_X0 + 216, SN_Y0 + 224, 'Swipe or press an arrow to start', 12, 1, 0)
        with If(V('sn_state') == 2):
            change(V('sn_pop'), V('fsc'))
            P.ease(V('sn_pop') / 8)
            P.zoom_at(0.6 + 0.4 * V('ez_o'), SN_X0 + 216, SN_Y0 + 126)
            P.rrect(SN_X0 + 76, SN_Y0 + 78, 280, 96, 16, pal('black'))
            P.text_c(SN_X0 + 216, SN_Y0 + 104, join('Game over - score ', V('sn_score')), 15, 1, 0)
            P.btn(SN_X0 + 156, SN_Y0 + 126, 120, 32, 'Play again', 1)
            P.set_tf(1, W / 2, H / 2)
            with If(V('tap_o') == 1):
                P.snake_reset()



    if MODE == 'sprite':
        with Script('receive:draw_7'):
            P.app_snake()
        with Script('receive:init_7'):
            P.snake_reset()


# ================================================================ Settings ==
with app_unit('Settings'):
    @proc('label y')
    def set_row(label, y):
        P.rrect(14, y, W - 28, 44, 12, V('c_surf'))
        P.text(30, y + 22, label, 14, 0, V('tx'), 300)


    @proc('label y')
    def set_sec(label, y):
        P.text(24, y + 10, label, 11, 1, V('tx2'), 0)


    @proc('')
    def app_settings():
        with If(V('view') == 2):
            P.settings_nav()
        with If(V('view') == 1):
            P.settings_pin()
        with If(V('view') == 0):
            S('clip0', SB + 37)
            P.scroll_update(732)
            S('_y', SB + 44 - V('scroll'))
            # --- Display
            P.set_sec('DISPLAY', V('_y'))
            P.set_row('Dark mode', V('_y') + 22)
            P.switch(1, W - 74, V('_y') + 32, V('dark'))
            with If(V('tap_o') == 1):
                S('dark', 1 - V('dark'))
                P.theme()
            P.set_row('Brightness', V('_y') + 70)
            P.slider(80, 200, V('_y') + 92, 220, V('bright'))
            S('bright', clamp(V('sl_o'), 15, 100))
            # wallpaper
            P.rrect(14, V('_y') + 118, W - 28, 60, 12, V('c_surf'))
            P.text(30, V('_y') + 138, 'Wallpaper', 14, 0, V('tx'), 200)
            S('_wk', 0)
            with repeat(6):
                inc('_wk')
                S('_wx', 214 + (V('_wk') - 1) * 66)
                P.tapr(V('_wx'), V('_y') + 128, 56, 40)
                with If(V('tap_o') == 1):
                    S('wall', V('_wk'))
                    P.theme()
                with If(V('wall') == V('_wk')):
                    P.rrect(V('_wx') - 3, V('_y') + 125, 62, 46, 10, V('c_acc'))
                P.rrect(V('_wx'), V('_y') + 128, 56, 40, 8, pal('w1') + V('_wk') - 1)
            # accent
            P.rrect(14, V('_y') + 186, W - 28, 52, 12, V('c_surf'))
            P.text(30, V('_y') + 212, 'Accent colour', 14, 0, V('tx'), 200)
            S('_wk', 0)
            with repeat(6):
                inc('_wk')
                S('_wx', 240 + (V('_wk') - 1) * 52)
                P.tapr(V('_wx') - 4, V('_y') + 196, 40, 32)
                with If(V('tap_o') == 1):
                    S('accent', V('_wk') - 1)
                    P.theme()
                with If(V('accent') == V('_wk') - 1):
                    P.circle(V('_wx') + 16, V('_y') + 212, 38, pal('dgray'))
                    P.circle(V('_wx') + 16, V('_y') + 212, 34, V('c_surf'))
                P.circle(V('_wx') + 16, V('_y') + 212, 26, pal('a_blue') + V('_wk') - 1)
            # --- General
            P.set_sec('GENERAL', V('_y') + 246)
            P.set_row('24-hour clock', V('_y') + 268)
            P.switch(2, W - 74, V('_y') + 278, V('h24'))
            with If(V('tap_o') == 1):
                S('h24', 1 - V('h24'))
            P.set_row('Wi-Fi', V('_y') + 318)
            P.switch(3, W - 74, V('_y') + 328, V('wifi'))
            with If(V('tap_o') == 1):
                S('wifi', 1 - V('wifi'))
            P.set_row('Bluetooth', V('_y') + 368)
            P.switch(4, W - 74, V('_y') + 378, V('bt'))
            with If(V('tap_o') == 1):
                S('bt', 1 - V('bt'))
            # --- Navigation
            P.set_sec('NAVIGATION', V('_y') + 428)
            P.set_row('Navigation style', V('_y') + 450)
            seg_group(1, 'navmode', [('Gesture bar', 1, W - 250, 112), ('3 buttons', 0, W - 132, 112)], V('_y') + 458)
            P.set_row('Animation speed', V('_y') + 500)
            seg_group(2, 'anim_n', [('Fast', 6, W - 250, 72), ('Normal', 10, W - 170, 72), ('Slow', 16, W - 90, 72)],
                      V('_y') + 508)
            P.btn(W - 190, V('_y') + 546, 176, 28, 'Customise navigation', 0)
            with If(V('tap_o') == 1):
                S('view', 2)
                S('scroll', 0)
            # --- Security
            P.set_sec('SECURITY', V('_y') + 612)
            P.set_row('Screen lock PIN', V('_y') + 634)
            with If(V('pin') == ''):
                P.text_r(W - 140, V('_y') + 656, 'Off', 13, 0, V('tx2'))
                P.btn(W - 124, V('_y') + 640, 100, 32, 'Set PIN', 1)
                with If(V('tap_o') == 1):
                    S('view', 1)
                    S('pin_in', '')
            with Else():
                P.text_r(W - 140, V('_y') + 656, 'On', 13, 0, V('tx2'))
                P.btn(W - 124, V('_y') + 640, 100, 32, 'Remove', 2)
                with If(V('tap_o') == 1):
                    S('pin', '')
                    P.notify('PIN removed')
            # --- Storage / about
            P.set_sec('SYSTEM', V('_y') + 690)
            P.set_row('Storage', V('_y') + 712)
            P.text_r(W - 30, V('_y') + 734, join(listlen(L('fs_id')), ' items'), 13, 0, V('tx2'))
            P.set_row('About', V('_y') + 762)
            P.text_r(W - 30, V('_y') + 784, 'eOS 1.0 for PenguinMod', 13, 0, V('tx2'))
            P.text(30, V('_y') + 806, join('640 x 360  ·  ', listlen(L('home_apps')), ' apps  ·  ', listlen(L('fs_id')) - 1,
                                           ' files and folders'), 12, 0, V('tx2'), 400)
            P.set_sec('SOUND', V('_y') + 826)
            P.set_row('Volume', V('_y') + 848)
            P.slider(82, 200, V('_y') + 870, 220, V('vol'))
            S('vol', round_(clamp(V('sl_o'), 0, 100)))
            P.text_r(W - 30, V('_y') + 870, V('vol'), 13, 0, V('tx2'))
            P.set_row('Mute', V('_y') + 896)
            P.switch(8, W - 74, V('_y') + 906, V('mute'))
            with If(V('tap_o') == 1):
                S('mute', 1 - V('mute'))
                snd(1)
            P.btn(W / 2 - 80, V('_y') + 954, 160, 36, 'Factory reset', 2)
            with If(V('tap_o') == 1):
                P.ask('Reset eOS?', 'All files, settings and drawings will be erased.', 'Reset', 2, 0)
            P.header('Settings')


    @proc('')
    def settings_nav():
        """Settings -> Customise navigation"""
        S('clip0', SB + 37)
        P.scroll_update(250)
        S('_y', SB + 44 - V('scroll'))
        # live preview of the bar
        P.rrect(14, V('_y'), W - 28, 56, 12, V('c_surf2'))
        P.rrect(W / 2 - 110, V('_y') + 8, 220, 40, 8, V('c_bg'))
        P.nav_pcol(1)
        P.rrect(W / 2 - V('nav_barw') / 2, V('_y') + 38 - V('nav_barh') / 2, V('nav_barw'), V('nav_barh'),
                V('nav_barh') / 2, V('_pc'))
        # colour
        P.set_row('Bar colour', V('_y') + 64)
        seg_group(3, 'nav_col', [('Auto', 0, W - 306, 56), ('White', 1, W - 246, 56), ('Black', 2, W - 186, 56),
                                 ('Accent', 3, W - 126, 56), ('Gray', 4, W - 66, 56)], V('_y') + 72)
        # sizes
        P.set_row('Bar width', V('_y') + 114)
        P.slider(81, 300, V('_y') + 136, 230, (V('nav_barw') - 60) / 1.6)
        S('nav_barw', round_(60 + V('sl_o') * 1.6))
        P.set_row('Bar thickness', V('_y') + 164)
        P.slider(82, 300, V('_y') + 186, 230, (V('nav_barh') - 3) / 0.06)
        S('nav_barh', round_(3 + V('sl_o') * 0.06))
        P.set_row('Swipe up distance to close', V('_y') + 214)
        P.slider(83, 300, V('_y') + 236, 230, (V('nav_close') - 40) / 0.45)
        S('nav_close', round_(40 + V('sl_o') * 0.45))
        # gestures
        P.set_row('Swipe the bar sideways to switch apps', V('_y') + 264)
        P.switch(5, W - 74, V('_y') + 274, V('nav_swipe'))
        with If(V('tap_o') == 1):
            S('nav_swipe', 1 - V('nav_swipe'))
        P.set_row('Swipe in from the edge to go back', V('_y') + 314)
        P.switch(6, W - 74, V('_y') + 324, V('nav_edge'))
        with If(V('tap_o') == 1):
            S('nav_edge', 1 - V('nav_edge'))
        P.set_row('Hold halfway to show open apps', V('_y') + 364)
        P.switch(7, W - 74, V('_y') + 374, V('nav_hold'))
        with If(V('tap_o') == 1):
            S('nav_hold', 1 - V('nav_hold'))
        P.set_row('Tap on the bar', V('_y') + 414)
        seg_group(4, 'nav_tap', [('Nothing', 0, W - 328, 76), ('Lock', 1, W - 246, 70), ('Recents', 2, W - 176, 70),
                                 ('Home', 3, W - 96, 70)], V('_y') + 422)
        P.header('Navigation')

    @proc('')
    def settings_pin():
        P.header('Set PIN')
        P.text_c(W / 2, SB + 56, 'Choose a 4-digit PIN', 14, 1, V('tx'))
        S('_pd', 0)
        with repeat(4):
            inc('_pd')
            with If(length(V('pin_in')) >= V('_pd')):
                P.circle(W / 2 - 54 + V('_pd') * 27 - 13.5, SB + 82, 13, V('c_acc'))
            with Else():
                P.circle(W / 2 - 54 + V('_pd') * 27 - 13.5, SB + 82, 13, V('c_div'))
        P.pinpad_dark(SB + 106)
        with If(V('pin_back') == 1):
            S('pin_back', 0)
            S('view', 0)
            S('pin_in', '')
        with If(V('pin_ok') == 1):
            S('pin_ok', 0)
            S('pin', V('pin_in'))
            S('pin_in', '')
            S('view', 0)
            P.notify('PIN set')


    @proc('top')
    def pinpad_dark(top):
        """same keypad as the lock screen but themed for app pages"""
        S('_pk', 0)
        with repeat(12):
            inc('_pk')
            S('_pcx', W / 2 + ((V('_pk') - 1) % 3 - 1) * 76)
            S('_pcy', top + floor((V('_pk') - 1) / 3) * 44)
            S('_pl', V('_pk'))
            with If(V('_pk') == 10):
                S('_pl', 'Back')
            with If(V('_pk') == 11):
                S('_pl', 0)
            with If(V('_pk') == 12):
                S('_pl', 'Del')
            P.tap(V('_pcx') - 32, V('_pcy'), 64, 36)
            S('_pt', V('tap_o'))
            S('_pcol', V('c_surf'))
            with If((V('hit_o') == 1) & (V('md') == 1)):
                S('_pcol', V('c_div'))
            P.rrect(V('_pcx') - 32, V('_pcy'), 64, 36, 18, V('_pcol'))
            P.text_c(V('_pcx'), V('_pcy') + 18, V('_pl'), 15, 1, V('tx'))
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

    if MODE == 'sprite':
        with Script('receive:draw_8'):
            P.app_settings()
        with Script('receive:init_8'):
            S('view', 0)




# =================================================================== Store ==
with app_unit('Store'):
    @proc('')
    def app_store():
        """every app in the catalogue: Open / Remove when installed, Get (with a progress bar) when not"""
        S('clip0', SB + 37)
        P.scroll_update(NAPPS * 50 + 16 - (H - NB - SB - 37))
        S('_si', 0)
        with repeat(NAPPS):
            inc('_si')
            P.stag(V('_si'))
            S('_y', SB + 44 + (V('_si') - 1) * 50 - V('scroll') + V('stag_o'))
            with If((V('_y') > SB - 20) & (V('_y') < H)):
                S('_sin', 0)
                with If(indexof(L('home_apps'), V('_si')) > 0):
                    S('_sin', 1)
                S('_score', 0)
                with If((V('_si') == APP_FILES) | (V('_si') == APP_SET) | (V('_si') == APP_STORE)):
                    S('_score', 1)
                P.rrect(12, V('_y'), W - 24, 46, 12, V('c_surf'))
                P.appicon(item(L('app_icon'), V('_si')), 40, V('_y') + 23, 34)
                P.text(66, V('_y') + 15, item(L('app_name'), V('_si')), 14, 1, V('tx'), 240)
                P.text(66, V('_y') + 32, item(L('app_desc'), V('_si')), 11, 0, V('tx2'), 300)
                with If(V('st_app') == V('_si')):
                    # installing: the bar fills, the percentage counts up
                    P.rrect(W - 190, V('_y') + 20, 120, 6, 3, V('c_surf2'))
                    P.rrect(W - 190, V('_y') + 20, 6 + 114 * clamp(V('st_p'), 0, 1), 6, 3, V('c_acc'))
                    P.text_r(W - 26, V('_y') + 23, join(round_(clamp(V('st_p'), 0, 1) * 100), '%'), 12, 1, V('tx2'))
                with Else():
                    with If(V('_sin') == 1):
                        with If(V('_score') == 1):
                            P.text_r(W - 28, V('_y') + 23, 'Built in', 12, 0, V('tx2'))
                        with Else():
                            P.btn(W - 172, V('_y') + 8, 70, 30, 'Open', 0)
                            with If(V('tap_o') == 1):
                                P.icon_at(V('_si'))
                                P.launch(V('_si'), V('ip_x') - 31, V('ip_y') - 31)
                            P.btn(W - 96, V('_y') + 8, 72, 30, 'Remove', 2)
                            with If(V('tap_o') == 1):
                                P.ask(join('Remove ', item(L('app_name'), V('_si')), '?'),
                                      'You can install it again from the Store at any time.', 'Remove', 5, V('_si'))
                    with Else():
                        P.btn(W - 96, V('_y') + 8, 72, 30, 'Get', 1)
                        with If(V('tap_o') == 1):
                            with If(V('st_app') == 0):
                                S('st_app', V('_si'))
                                S('st_p', 0)
                            with Else():
                                P.notify('Another app is still installing')
        P.header('Store')
        P.text_r(W - 16, SB + 18, join(listlen(L('home_apps')), ' of ', NAPPS, ' installed'), 12, 0, V('tx2'))

    if MODE == 'sprite':
        with Script('receive:draw_9'):
            P.app_store()
        with Script('receive:init_9'):
            S('view', 0)
