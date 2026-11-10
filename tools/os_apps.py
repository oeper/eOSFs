"""eOS apps: virtual file system, Files, Notes (+shared text editor), Calculator, Clock, Terminal, Paint, Snake, Settings."""
from sb3 import *
from os_core import *
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
    ('fmt_o', ''), ('arg_i', 0), ('ed_clen', -1), ('ed_cfile', 0), ('ed_py', 0), ('ed_px', 24),
]:
    V(_n, _v)


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
        P.term_run()


@proc('')
def dlg_run():
    with If(V('dlg_act') == 1):
        P.fs_delete(V('dlg_arg'))
    with If(V('dlg_act') == 2):
        P.factory_reset()
    with If(V('dlg_act') == 3):
        P.paint_clear()
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
    P.theme()
    P.paint_clear()
    list_clear(L('term_out'))
    S('f_dir', 1)
    S('view', 0)
    S('sn_best', 0)
    P.store_save()
    P.notify('eOS has been reset')


@proc('a')
def app_init(a):
    S('view', 0)
    S('scroll', 0)
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
    dispatch(V('app'), [
        (APP_FILES, lambda: P.app_files()),
        (APP_NOTES, lambda: P.app_notes()),
        (APP_CALC, lambda: P.app_calc()),
        (APP_CLOCK, lambda: P.app_clock()),
        (APP_TERM, lambda: P.app_term()),
        (APP_PAINT, lambda: P.app_paint()),
        (APP_SNAKE, lambda: P.app_snake()),
        (APP_SET, lambda: P.app_settings()),
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
        inc('tm_flash', -1)


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
    P.rect(0, SB + 37, W, H, V('c_surf'))
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
    P.para(24, SB + 56 + V('_eoff'), W - 48, V('_et'), 14, 20, V('tx'), 1)
    with If(((V('frame_n') % 30) < 18) & (V('kb_open') == 1)):
        P.rect(V('ed_px') + 1, SB + 56 + V('_eoff') + V('ed_py') - 8, 2, 17, V('c_acc'))
    with If(V('_et') == ''):
        P.text(24, SB + 56, 'Empty file - tap here to start typing', 14, 0, V('tx2'), 0)
    P.header(item(L('fs_name'), V('_ei')))
    P.text_r(W - 16, SB + 18, join(length(V('_et')), ' chars'), 12, 0, V('tx2'))


# ================================================================= Files ====
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
        S('_fy', SB + 44 - V('scroll'))
        with repeat(2):
            inc('_fp')
            S('_fk', 0)
            with repeat(listlen(L('fs_id'))):
                inc('_fk')
                with If((item(L('fs_parent'), V('_fk')) == V('f_dir')) &
                        (item(L('fs_type'), V('_fk')) == 2 - V('_fp'))):
                    P.file_row(V('_fk'), V('_fy'))
                    change(V('_fy'), 46)
        P.fs_path(V('f_dir'))
        P.header(V('fs_p'))
        P.btn(W - 192, SB + 5, 88, 26, 'New folder', 0)
        with If(V('tap_o') == 1):
            P.kb_begin('New folder name', '', 10, 0, 30)
        P.btn(W - 98, SB + 5, 82, 26, 'New file', 1)
        with If(V('tap_o') == 1):
            P.kb_begin('New file name', '', 11, 0, 30)


# ================================================================= Notes ====
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
        S('_fk', 0)
        with repeat(listlen(L('fs_id'))):
            inc('_fk')
            with If((item(L('fs_parent'), V('_fk')) == 3) & (item(L('fs_type'), V('_fk')) == 0)):
                S('_nid', item(L('fs_id'), V('_fk')))
                S('_nk', V('_fk'))
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
                change(V('_fy'), 62)
        P.header('Notes')
        P.btn(W - 112, SB + 5, 96, 26, 'New note', 1)
        with If(V('tap_o') == 1):
            P.fs_free_name(3, 'Note', '.txt')
            P.fs_add(3, V('fs_nm'), 0, '')
            S('ed_file', V('fs_new'))
            S('view', 1)
            P.kb_begin('', '', 20, 1, 1500)


# ============================================================== Calculator ==
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
    S('_cs', 38)
    with If(length(V('calc_d')) > 9):
        S('_cs', 30)
    with If(length(V('calc_d')) > 12):
        S('_cs', 24)
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
        with If((V('hit_o') == 1) & (V('md') == 1)):
            S('_cc', V('c_div'))
        P.rrect(V('_cx'), V('_cy'), V('_cw'), 31, 9, V('_cc'))
        P.text_c(V('_cx') + V('_cw') / 2, V('_cy') + 15.5, V('_cl'), 16, 1, V('_ctx'))
        with If(V('_ct') == 1):
            P.calc_key(V('_cl'))


L('calc_keys', CALC_KEYS)


# ================================================================== Clock ===
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
            P.rrect(V('_tx0') + 30, SB + 68, 80, 3, 1.5, V('c_acc'))
        with Else():
            P.text_c(V('_tx0') + 70, SB + 54, item(L('clk_tabs'), V('_tb')), 14, 0, V('tx2'))
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


@proc('x1 y1 x2 y2 w color')
def hand(x1, y1, x2, y2, w, color):
    """round-capped pen line in UI coordinates (clock hands/ticks)"""
    pen_up()
    pen_color(color)
    pen_size(w)
    goto(x1 - 320, 180 - y1)
    pen_down()
    goto(x2 - 320, 180 - y2)
    pen_up()


L('acc_hex', ['#' + dict(assets.PAL)[n] for n in ('a_blue', 'a_teal', 'a_green', 'a_orange', 'a_pink', 'a_purple')])


@proc('cx cy r')
def clock_face(cx, cy, r):
    P.circle(cx, cy, r * 2 + 8, V('c_div'))
    P.circle(cx, cy, r * 2, V('c_surf'))
    S('_cti', 0)
    with repeat(12):
        S('_ca', V('_cti') * 30)
        P.hand(cx + sin(V('_ca')) * (r - 14), cy - cos(V('_ca')) * (r - 14),
               cx + sin(V('_ca')) * (r - 6), cy - cos(V('_ca')) * (r - 6), 3, '#8B94A5')
        inc('_cti')
    S('_ca', (V('hh') % 12 + V('mm') / 60) * 30)
    P.hand(cx, cy, cx + sin(V('_ca')) * r * 0.5, cy - cos(V('_ca')) * r * 0.5, 6, item(L('acc_hex'), V('accent') + 1))
    S('_ca', (V('mm') + V('ss') / 60) * 6)
    P.hand(cx, cy, cx + sin(V('_ca')) * r * 0.74, cy - cos(V('_ca')) * r * 0.74, 4,
           item(L('acc_hex'), V('accent') + 1))
    S('_ca', V('ss') * 6)
    P.hand(cx - sin(V('_ca')) * r * 0.12, cy + cos(V('_ca')) * r * 0.12, cx + sin(V('_ca')) * r * 0.86,
           cy - cos(V('_ca')) * r * 0.86, 2, '#EF4444')
    P.circle(cx, cy, 10, pal('red'))


# =============================================================== Terminal ===
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
        S('screen', SCR_LOCK)
        S('pin_show', 0)
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
    P.rect(0, SB, W, H, pal('black'))
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
    S('_ty', SB + 12)
    S('_tk', V('_t0') - 1)
    with repeat(V('_tn') - V('_t0') + 1):
        inc('_tk')
        P.text(10, V('_ty'), item(L('term_out'), V('_tk')), 12, 0, 0, W - 20)
        change(V('_ty'), 15)
    S('_pr', join('eos:', V('fs_p'), '$ '))
    P.tw(V('_pr'), 12, 1)
    P.text(10, V('_ty'), V('_pr'), 12, 1, -25, 0)
    S('_cxx', 10 + V('tw_o'))
    P.text(V('_cxx'), V('_ty'), V('ti'), 12, 0, 0, W - 40 - V('tw_o'))
    P.tw(V('ti'), 12, 0)
    with If((V('frame_n') % 30) < 18):
        P.rect(V('_cxx') + V('tw_o') + 1, V('_ty') - 7, 7, 14, pal('white'))




# ================================================================== Paint ===
@proc('')
def paint_clear():
    list_clear(L('ps_x'))
    list_clear(L('ps_y'))
    list_clear(L('ps_c'))
    list_clear(L('ps_w'))
    list_clear(L('ps_s'))


PX0, PY0, PW, PH = 78, SB + 38, 552, H - NB - SB - 44


@proc('')
def app_paint():
    P.header('Paint')
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
            pen_size(item(L('ps_w'), V('_pi')))
            goto(item(L('ps_x'), V('_pi')) - 320, 180 - item(L('ps_y'), V('_pi')))
            pen_down()
        with Else():
            goto(item(L('ps_x'), V('_pi')) - 320, 180 - item(L('ps_y'), V('_pi')))
    pen_up()
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
    P.rect(0, SB + 37, 72, H, V('c_surf'))
    P.rect(72, SB + 37, 1, H, V('c_div'))
    S('_pk', 0)
    with repeat(10):
        inc('_pk')
        S('_px2', 20 + ((V('_pk') - 1) % 2) * 30)
        S('_py2', SB + 56 + floor((V('_pk') - 1) / 2) * 28)
        P.tapr(V('_px2') - 13, V('_py2') - 13, 26, 26)
        with If(V('tap_o') == 1):
            S('pt_c', V('_pk'))
        with If(V('pt_c') == V('_pk')):
            P.circle(V('_px2'), V('_py2'), 26, V('c_acc'))
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
            P.rrect(8, V('_py3') - 11, 56, 22, 8, V('c_surf2'))
        P.circle(36, V('_py3'), V('_pw2') + 2, pal('dgray'))
    P.btn(8, SB + 278, 56, 24, 'Clear', 2)
    with If(V('tap_o') == 1):
        P.ask('Clear canvas?', 'The drawing will be erased.', 'Clear', 3, 0)
    P.text_r(W - 16, SB + 18, join(listlen(L('ps_x')), ' / 3000'), 11, 0, V('tx2'))


L('paint_pal', [pal(n) for n in PAINT_NAMES])


# ================================================================== Snake ===
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
        inc('sn_t')
        with If(V('sn_t') >= V('sn_spd')):
            S('sn_t', 0)
            P.snake_step()
    # board
    P.rrect(SN_X0 - 3, SN_Y0 - 3, SN_COLS * SN_C + 6, SN_ROWS * SN_C + 6, 10, V('c_div'))
    P.rrect(SN_X0, SN_Y0, SN_COLS * SN_C, SN_ROWS * SN_C, 7, V('c_surf'))
    P.circle(SN_X0 + V('sn_fx') * SN_C + SN_C / 2, SN_Y0 + V('sn_fy') * SN_C + SN_C / 2, SN_C - 4, pal('red'))
    S('_k', 0)
    with repeat(listlen(L('sn_x'))):
        inc('_k')
        S('_sc', V('c_acc'))
        with If(V('_k') == 1):
            S('_sc', pal('a_green'))
        P.rrect(SN_X0 + item(L('sn_x'), V('_k')) * SN_C + 1, SN_Y0 + item(L('sn_y'), V('_k')) * SN_C + 1,
                SN_C - 2, SN_C - 2, 5, V('_sc'))
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
        P.rrect(V('_dx') + dx - 18, V('_dy') + dy - 18, 36, 36, 10, V('c_surf2'))
        P.icon(nm, V('_dx') + dx, V('_dy') + dy, 18, V('tx'))
        with If(V('_dt') == 1):
            P.snake_turn(d)
    with If(V('sn_state') == 0):
        P.rrect(SN_X0 + 76, SN_Y0 + 208, 280, 32, 16, pal('black'))
        P.text_c(SN_X0 + 216, SN_Y0 + 224, 'Swipe or press an arrow to start', 12, 1, 0)
    with If(V('sn_state') == 2):
        P.rrect(SN_X0 + 76, SN_Y0 + 78, 280, 96, 16, pal('black'))
        P.text_c(SN_X0 + 216, SN_Y0 + 104, join('Game over - score ', V('sn_score')), 15, 1, 0)
        P.btn(SN_X0 + 156, SN_Y0 + 126, 120, 32, 'Play again', 1)
        with If(V('tap_o') == 1):
            P.snake_reset()


# ================================================================ Settings ==
@proc('label y')
def set_row(label, y):
    P.rrect(14, y, W - 28, 44, 12, V('c_surf'))
    P.text(30, y + 22, label, 14, 0, V('tx'), 300)


@proc('label y')
def set_sec(label, y):
    P.text(24, y + 10, label, 11, 1, V('tx2'), 0)


@proc('')
def app_settings():
    with If(V('view') == 1):
        P.settings_pin()
    with Else():
        S('clip0', SB + 37)
        P.scroll_update(412)
        S('_y', SB + 44 - V('scroll'))
        # --- Display
        P.set_sec('DISPLAY', V('_y'))
        P.set_row('Dark mode', V('_y') + 22)
        P.switch(W - 74, V('_y') + 32, V('dark'))
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
        P.switch(W - 74, V('_y') + 278, V('h24'))
        with If(V('tap_o') == 1):
            S('h24', 1 - V('h24'))
        P.set_row('Wi-Fi', V('_y') + 318)
        P.switch(W - 74, V('_y') + 328, V('wifi'))
        with If(V('tap_o') == 1):
            S('wifi', 1 - V('wifi'))
        P.set_row('Bluetooth', V('_y') + 368)
        P.switch(W - 74, V('_y') + 378, V('bt'))
        with If(V('tap_o') == 1):
            S('bt', 1 - V('bt'))
        # --- Security
        P.set_sec('SECURITY', V('_y') + 428)
        P.set_row('Screen lock PIN', V('_y') + 450)
        with If(V('pin') == ''):
            P.text_r(W - 140, V('_y') + 472, 'Off', 13, 0, V('tx2'))
            P.btn(W - 124, V('_y') + 456, 100, 32, 'Set PIN', 1)
            with If(V('tap_o') == 1):
                S('view', 1)
                S('pin_in', '')
        with Else():
            P.text_r(W - 140, V('_y') + 472, 'On', 13, 0, V('tx2'))
            P.btn(W - 124, V('_y') + 456, 100, 32, 'Remove', 2)
            with If(V('tap_o') == 1):
                S('pin', '')
                P.notify('PIN removed')
        # --- Storage / about
        P.set_sec('SYSTEM', V('_y') + 506)
        P.set_row('Storage', V('_y') + 528)
        P.text_r(W - 30, V('_y') + 550, join(listlen(L('fs_id')), ' items'), 13, 0, V('tx2'))
        P.set_row('About', V('_y') + 578)
        P.text_r(W - 30, V('_y') + 600, 'eOS 1.0 for PenguinMod', 13, 0, V('tx2'))
        P.btn(W / 2 - 80, V('_y') + 634, 160, 36, 'Factory reset', 2)
        with If(V('tap_o') == 1):
            P.ask('Reset eOS?', 'All files, settings and drawings will be erased.', 'Reset', 2, 0)
        P.header('Settings')


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
