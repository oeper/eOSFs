"""eOS persistence through the TurboWarp "Local Storage" extension (browser localStorage).

Format: records are joined with the section sign, fields with the broken bar.  Neither can be typed with the
on-screen or physical keyboard, so file data can never contain them.
"""
from sb3 import *
from os_core import *

FS, SEP = '§', '¦'
STORE_ID = 'eos'

L('ld_tmp')
for _n, _v in [('_ld', ''), ('_lf', ''), ('_li', 0), ('_lmax', 0)]:
    V(_n, _v)


@proc('')
def store_save():
    ls_project(STORE_ID)
    S('_sv', '')
    S('_k', 0)
    with repeat(listlen(L('fs_id'))):
        inc('_k')
        S('_sv', join(V('_sv'), item(L('fs_id'), V('_k')), SEP, item(L('fs_name'), V('_k')), SEP,
                      item(L('fs_parent'), V('_k')), SEP, item(L('fs_type'), V('_k')), SEP,
                      item(L('fs_data'), V('_k')), FS))
    ls_set('fs', V('_sv'))
    ls_set('settings', join(V('dark'), SEP, V('accent'), SEP, V('wall'), SEP, V('bright'), SEP, V('wifi'), SEP,
                            V('bt'), SEP, V('h24'), SEP, V('pin'), SEP, V('sn_best'), SEP, V('navmode'), SEP,
                            V('anim_n'), SEP))


@proc('s')
def split_to_tmp(s):
    """split on SEP / FS into the ld_tmp list (every separator ends one field)"""
    list_clear(L('ld_tmp'))
    S('_lf', '')
    S('_li', 1)
    with repeat(length(s)):
        S('_lc', letter(V('_li'), s))
        with If((V('_lc') == SEP) | (V('_lc') == FS)):
            list_add(L('ld_tmp'), V('_lf'))
            S('_lf', '')
        with Else():
            S('_lf', join(V('_lf'), V('_lc')))
        inc('_li')


@proc('')
def store_load():
    ls_project(STORE_ID)
    # ---- settings
    S('_ld', ls_get('settings'))
    with If(length(V('_ld')) > 8):
        P.split_to_tmp(V('_ld'))
        with If(listlen(L('ld_tmp')) == 11):
            S('navmode', item(L('ld_tmp'), 10))
            S('anim_n', item(L('ld_tmp'), 11))
        with If(listlen(L('ld_tmp')) >= 9):
            S('dark', item(L('ld_tmp'), 1))
            S('accent', item(L('ld_tmp'), 2))
            S('wall', item(L('ld_tmp'), 3))
            S('bright', item(L('ld_tmp'), 4))
            S('wifi', item(L('ld_tmp'), 5))
            S('bt', item(L('ld_tmp'), 6))
            S('h24', item(L('ld_tmp'), 7))
            S('pin', item(L('ld_tmp'), 8))
            S('sn_best', item(L('ld_tmp'), 9))
    # ---- files: parse records, keep the defaults if anything looks wrong
    S('_ld', ls_get('fs'))
    with If(length(V('_ld')) > 10):
        for nm in ('fs_id', 'fs_name', 'fs_parent', 'fs_type', 'fs_data'):
            list_clear(L(nm))
        list_clear(L('ld_tmp'))
        S('_lf', '')
        S('_li', 1)
        S('_ln', length(V('_ld')))
        with until(V('_li') > V('_ln')):
            S('_lc', letter(V('_li'), V('_ld')))
            with If(V('_lc') == SEP):
                list_add(L('ld_tmp'), V('_lf'))
                S('_lf', '')
            with Else():
                with If(V('_lc') == FS):
                    list_add(L('ld_tmp'), V('_lf'))
                    S('_lf', '')
                    with If(listlen(L('ld_tmp')) == 5):
                        list_add(L('fs_id'), item(L('ld_tmp'), 1))
                        list_add(L('fs_name'), item(L('ld_tmp'), 2))
                        list_add(L('fs_parent'), item(L('ld_tmp'), 3))
                        list_add(L('fs_type'), item(L('ld_tmp'), 4))
                        list_add(L('fs_data'), item(L('ld_tmp'), 5))
                    list_clear(L('ld_tmp'))
                with Else():
                    S('_lf', join(V('_lf'), V('_lc')))
            inc('_li')
        with If(indexof(L('fs_id'), 1) == 0):
            P.fs_reset()
        S('_lmax', 0)
        S('_k', 0)
        with repeat(listlen(L('fs_id'))):
            inc('_k')
            with If(item(L('fs_id'), V('_k')) > V('_lmax')):
                S('_lmax', item(L('fs_id'), V('_k')))
        S('fs_next', V('_lmax') + 1)
