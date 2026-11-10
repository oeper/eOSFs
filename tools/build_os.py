#!/usr/bin/env python3
"""Builds eOS.pmp  (python3 tools/build_os.py [out.pmp])"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import assets
import sb3
import os_core, os_sys, os_apps, os_store   # noqa: registers procedures/scripts

def main(out):
    os_sys.make_main_script()
    costumes, backdrops, widths, info = assets.build()
    sb3.Reg.lists['gw'][1] = widths
    proj = sb3.build_project(out, 'eOS', costumes, backdrops, extensions=['pen', 'jgRuntime', 'localstorage'],
                              extension_urls={'localstorage': 'https://extensions.turbowarp.org/local-storage.js'})
    n = len(proj['targets'][1]['blocks'])
    print(f'wrote {out}: {n} blocks, {len(costumes)} costumes, {os.path.getsize(out)//1024} KiB')

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'eOS.pmp'))
