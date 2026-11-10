#!/usr/bin/env python3
"""Structural sanity check of a generated .pmp/.sb3 (dangling ids, undeclared vars/lists/costumes, arg counts)."""
import json, sys, zipfile, hashlib

def main(path):
    z = zipfile.ZipFile(path)
    d = json.loads(z.read('project.json'))
    errs = []
    names = set(z.namelist())
    stage, spr = d['targets'][0], d['targets'][1]
    vars_ = {k: v[0] for k, v in stage['variables'].items()}
    lists = {k: v[0] for k, v in stage['lists'].items()}
    B = spr['blocks']
    for t in d['targets']:
        for c in t['costumes']:
            if c['md5ext'] not in names:
                errs.append(f"missing asset {c['md5ext']}")
            elif hashlib.md5(z.read(c['md5ext'])).hexdigest() != c['assetId']:
                errs.append(f"md5 mismatch {c['name']}")
    protos = {}
    for bid, b in B.items():
        if b['opcode'] == 'procedures_prototype':
            protos[b['mutation']['proccode']] = json.loads(b['mutation']['argumentids'])
    for bid, b in B.items():
        for ref in ('next', 'parent'):
            if b[ref] is not None and b[ref] not in B:
                errs.append(f'{bid}.{ref} -> missing {b[ref]}')
        for k, inp in b['inputs'].items():
            for part in inp[1:]:
                if isinstance(part, str) and part not in B:
                    errs.append(f'{bid}.{k} -> missing block {part}')
                if isinstance(part, list) and part[0] == 12 and part[2] not in vars_:
                    errs.append(f'{bid}.{k} -> undeclared variable {part[1]}')
                if isinstance(part, list) and part[0] == 13 and part[2] not in lists:
                    errs.append(f'{bid}.{k} -> undeclared list {part[1]}')
        for k, f in b['fields'].items():
            if k == 'VARIABLE' and f[1] not in vars_:
                errs.append(f'{bid} field var {f[0]} undeclared')
            if k == 'LIST' and f[1] not in lists:
                errs.append(f'{bid} field list {f[0]} undeclared')
        if b['opcode'] == 'procedures_call':
            pc = b['mutation']['proccode']
            if pc not in protos:
                errs.append(f'{bid} call to unknown procedure {pc}')
            elif set(b['inputs']) != set(protos[pc]):
                errs.append(f'{bid} wrong args for {pc}')
    cs = {c['name'] for c in spr['costumes']}
    print(f"{len(B)} blocks, {len(vars_)} variables, {len(lists)} lists, {len(protos)} custom blocks, {len(cs)} costumes")
    for e in errs[:30]:
        print('ERROR', e)
    print('lint:', 'FAILED' if errs else 'ok')
    return 1 if errs else 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))
