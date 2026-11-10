#!/usr/bin/env python3
"""Builds the sprite edition: every app is a sprite, every UI element is a clone of the Element sprite, text by Iris Text.
   python3 tools/build_sprites.py [out.pmp]"""
import os
import sys

os.environ['EOS_MODE'] = 'sprite'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import assets
import sb3
from sb3 import unit, UNITS, Costume

sb3.DEFAULT_WARP[0] = False
with unit('lib', uselib=False, sprite=False):          # shared code, copied (pruned) into every sprite that uses it
    import os_core, os_sys, os_apps, os_store          # noqa
import sp_element
import sp_assets

BLANK = Costume('blank', '<svg xmlns="http://www.w3.org/2000/svg" width="2" height="2" viewBox="0 0 2 2"/>', 1, 1)
APP_SPRITES = ['Files', 'Notes', 'Calculator', 'Clock', 'Terminal', 'Paint', 'Snake', 'Settings']
IRIS_URL = 'https://extensions.penguinmod.com/extensions/Gen1x/iris-text.js'


def main(out):
    sp_element.define()
    with unit('System'):
        os_sys.make_main_script()
    order = ['System'] + APP_SPRITES + ['Measure', 'Element']      # Element last = on top
    for name in order:
        u = UNITS[name]
        u.costumes = sp_assets.element_costumes() if name == 'Element' else [BLANK]
        u.prune = name not in ('Element', 'Measure')
    costumes, backdrops, widths, info = assets.build()
    proj = sb3.build_multi(out, backdrops, extensions=['pen', 'jgRuntime', 'localstorage', 'g1nxIrisText'],
                           order=order, extension_urls={'localstorage': 'https://extensions.turbowarp.org/local-storage.js',
                                           'g1nxIrisText': IRIS_URL})
    n = sum(len(t['blocks']) for t in proj['targets'])
    print(f'wrote {out}: {len(proj["targets"]) - 1} sprites, {n} blocks, {os.path.getsize(out)//1024} KiB')



if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'eOS-sprites.pmp'))
