#!/usr/bin/env python3
"""Structural sanity check of a generated .pmp/.sb3: dangling block ids, undeclared variables/lists/broadcasts,
calls to unknown procedures or with wrong arguments, missing/mismatched assets - for every sprite."""
import hashlib
import json
import sys
import zipfile


def main(path):
    z = zipfile.ZipFile(path)
    d = json.loads(z.read('project.json'))
    errs = []
    names = set(z.namelist())
    stage = d['targets'][0]
    gvars = set(stage['variables'])
    glists = set(stage['lists'])
    bcasts = set(stage.get('broadcasts', {}))
    totals = {'blocks': 0, 'procs': 0, 'sprites': len(d['targets']) - 1}
    for t in d['targets']:
        for c in t['costumes']:
            if c['md5ext'] not in names:
                errs.append(f"{t['name']}: missing asset {c['md5ext']}")
            elif hashlib.md5(z.read(c['md5ext'])).hexdigest() != c['assetId']:
                errs.append(f"{t['name']}: md5 mismatch {c['name']}")
        if t['isStage']:
            continue
        lvars = set(t['variables'])
        B = t['blocks']
        totals['blocks'] += len(B)
        protos = {}
        for b in B.values():
            if b['opcode'] == 'procedures_prototype':
                protos[b['mutation']['proccode']] = json.loads(b['mutation']['argumentids'])
        totals['procs'] += len(protos)
        for bid, b in B.items():
            where = f"{t['name']}:{bid}"
            for ref in ('next', 'parent'):
                if b[ref] is not None and b[ref] not in B:
                    errs.append(f'{where}.{ref} -> missing {b[ref]}')
            for k, inp in b['inputs'].items():
                for part in inp[1:]:
                    if isinstance(part, str) and part not in B:
                        errs.append(f'{where}.{k} -> missing block {part}')
                    if isinstance(part, list) and part[0] == 12 and part[2] not in gvars | lvars:
                        errs.append(f'{where}.{k} -> undeclared variable {part[1]}')
                    if isinstance(part, list) and part[0] == 13 and part[2] not in glists:
                        errs.append(f'{where}.{k} -> undeclared list {part[1]}')
                    if isinstance(part, list) and part[0] == 11 and part[2] not in bcasts:
                        errs.append(f'{where}.{k} -> undeclared broadcast {part[1]}')
            for k, f in b['fields'].items():
                if k == 'VARIABLE' and f[1] not in gvars | lvars:
                    errs.append(f'{where} field var {f[0]} undeclared')
                if k == 'LIST' and f[1] not in glists:
                    errs.append(f'{where} field list {f[0]} undeclared')
                if k == 'BROADCAST_OPTION' and b['opcode'] == 'event_whenbroadcastreceived' and f[1] not in bcasts:
                    errs.append(f'{where} hat broadcast {f[0]} undeclared')
            if b['opcode'] == 'procedures_call':
                pc = b['mutation']['proccode']
                if pc not in protos:
                    errs.append(f'{where} call to unknown procedure {pc!r}')
                elif set(b['inputs']) != set(protos[pc]):
                    errs.append(f'{where} wrong args for {pc!r}')
    print(f"{totals['sprites']} sprites, {totals['blocks']} blocks, {totals['procs']} custom blocks, "
          f"{len(gvars)} global variables, {len(glists)} lists, {len(bcasts)} broadcasts")
    for e in errs[:30]:
        print('ERROR', e)
    print('lint:', 'FAILED' if errs else 'ok')
    return 1 if errs else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))
