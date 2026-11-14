"""Tiny Scratch/PenguinMod project compiler.

Write programs as Python (expressions, `with If(...)`, procedures); get a valid
sb3 / .pmp archive.  Everything is lazily built so procedures may be called
before they are defined (use ``P.name(...)``).

Public surface (import * from this module):
  V('x'), L('list')            variable / list references (global, on the Stage)
  Lit, join, length, letter, rand, floor, ... expression helpers
  set_, change, If, Else, repeat, forever, while_, until, wait, ...
  proc('label', 'argnames')    decorator to define a custom block
  P.name(args)                 call a custom block
  Script('flag') / hat scripts
  Project().build(path)
"""
import hashlib
import json
import zipfile

# --------------------------------------------------------------------------
# id generation
_ctr = [0]


def uid():
    _ctr[0] += 1
    n = _ctr[0]
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    s = ""
    while n:
        s += chars[n % len(chars)]
        n //= len(chars)
    return "id" + s


# --------------------------------------------------------------------------
# Expressions
def lit(v):
    return v if isinstance(v, E) else Lit(v)


class E:
    """Base class of expression nodes (reporters/booleans/literals)."""

    __hash__ = object.__hash__

    def _op(self, opcode, a, b, ka, kb):
        return Op(opcode, {ka: self, kb: lit(b)}) if a is None else Op(opcode, {ka: lit(a), kb: self})

    def __add__(s, o): return Op('operator_add', {'NUM1': s, 'NUM2': lit(o)})
    def __radd__(s, o): return Op('operator_add', {'NUM1': lit(o), 'NUM2': s})
    def __sub__(s, o): return Op('operator_subtract', {'NUM1': s, 'NUM2': lit(o)})
    def __rsub__(s, o): return Op('operator_subtract', {'NUM1': lit(o), 'NUM2': s})
    def __mul__(s, o): return Op('operator_multiply', {'NUM1': s, 'NUM2': lit(o)})
    def __rmul__(s, o): return Op('operator_multiply', {'NUM1': lit(o), 'NUM2': s})
    def __truediv__(s, o): return Op('operator_divide', {'NUM1': s, 'NUM2': lit(o)})
    def __rtruediv__(s, o): return Op('operator_divide', {'NUM1': lit(o), 'NUM2': s})
    def __mod__(s, o): return Op('operator_mod', {'NUM1': s, 'NUM2': lit(o)})
    def __neg__(s): return Op('operator_subtract', {'NUM1': Lit(0), 'NUM2': s})
    def __lt__(s, o): return Op('operator_lt', {'OPERAND1': s, 'OPERAND2': lit(o)})
    def __gt__(s, o): return Op('operator_gt', {'OPERAND1': s, 'OPERAND2': lit(o)})
    def __eq__(s, o): return Op('operator_equals', {'OPERAND1': s, 'OPERAND2': lit(o)})
    def __ne__(s, o): return Not(s == o)
    def __le__(s, o): return Not(s > o)
    def __ge__(s, o): return Not(s < o)
    def __and__(s, o): return Op('operator_and', {'OPERAND1': s, 'OPERAND2': lit(o)})
    def __or__(s, o): return Op('operator_or', {'OPERAND1': s, 'OPERAND2': lit(o)})
    def __invert__(s): return Not(s)
    def __bool__(s):
        raise TypeError('Expr used in Python boolean context - use & | ~ and parentheses')


class Lit(E):
    def __init__(self, v):
        self.v = v


class Op(E):
    def __init__(self, opcode, inputs=None, fields=None, mutation=None):
        self.opcode = opcode
        self.inputs = inputs or {}
        self.fields = fields or {}
        self.mutation = mutation


def Not(x):
    return Op('operator_not', {'OPERAND': lit(x)})


class Menu(E):
    """A shadow-menu input (e.g. costume name).  value may be Lit/Expr."""

    def __init__(self, opcode, field, value):
        self.opcode, self.field, self.value = opcode, field, lit(value)


class Ref(E):
    def __init__(self, kind, name, scope=None):
        self.kind, self.name, self.scope = kind, name, scope  # kind: 'var' | 'list' | 'arg'; scope = sprite for locals


class Reg:
    """Variable / list registry (all global on the Stage)."""
    vars = {}   # name -> (id, initial)
    lists = {}  # name -> (id, initial list)


class Unit:
    """One target (sprite) being built: own procedures, scripts, local variables and costumes.
    The special unit 'lib' holds procedures that are copied into every unit with uselib=True."""

    def __init__(self, name, uselib=True, sprite=True):
        self.name, self.uselib, self.sprite = name, uselib, sprite
        self.procs, self.scripts, self.locals = {}, [], {}
        self.costumes = []
        self.visible, self.x, self.y, self.size = False, 0, 0, 100
        self.prune = False          # drop procedures that are never called (lib copies)


UNITS = {}
_DEF = []          # stack of units being defined
_COMPILING = [None]


def unit(name, uselib=True, sprite=True):
    """with unit('Calculator'): ... everything defined inside belongs to that sprite"""
    if name not in UNITS:
        UNITS[name] = Unit(name, uselib, sprite)

    class _Ctx:
        def __enter__(self):
            _DEF.append(UNITS[name])
            return UNITS[name]

        def __exit__(self, *a):
            _DEF.pop()
    return _Ctx()


def cur_unit():
    if _DEF:
        return _DEF[-1]
    if 'main' not in UNITS:
        UNITS['main'] = Unit('main')
    return UNITS['main']


def VL(name, init=0):
    """sprite-local variable ("for this sprite only" - clones get their own copy)"""
    u = _COMPILING[0] or cur_unit()       # procedure bodies are built lazily while their sprite is being compiled
    if name not in u.locals:
        u.locals[name] = [uid(), init]
    return Ref('var', name, scope=u.name)


def _var_id(ref):
    if ref.scope:
        return UNITS[ref.scope].locals[ref.name][0]
    return Reg.vars[ref.name][0]


def V(name, init=0):
    if name not in Reg.vars:
        Reg.vars[name] = [uid(), init]
    return Ref('var', name)


def L(name, init=None):
    if name not in Reg.lists:
        Reg.lists[name] = [uid(), list(init) if init else []]
    elif init is not None:
        Reg.lists[name][1] = list(init)
    return Ref('list', name)


def Arg(name):
    return Ref('arg', name)


# expression helpers --------------------------------------------------------
def join(*parts):
    parts = [lit(p) for p in parts]
    e = parts[-1]
    for p in reversed(parts[:-1]):
        e = Op('operator_join', {'STRING1': p, 'STRING2': e})
    return e


def length(s): return Op('operator_length', {'STRING': lit(s)})
def letter(i, s): return Op('operator_letter_of', {'LETTER': lit(i), 'STRING': lit(s)})
def contains(s, t): return Op('operator_contains', {'STRING1': lit(s), 'STRING2': lit(t)})
def rand(a, b): return Op('operator_random', {'FROM': lit(a), 'TO': lit(b)})
def round_(x): return Op('operator_round', {'NUM': lit(x)})


def mathop(name, x):
    return Op('operator_mathop', {'NUM': lit(x)}, {'OPERATOR': [name, None]})


def floor(x): return mathop('floor', x)
def ceil(x): return mathop('ceiling', x)
def abs_(x): return mathop('abs', x)
def sqrt(x): return mathop('sqrt', x)
def sin(x): return mathop('sin', x)
def cos(x): return mathop('cos', x)


def clamp(x, lo, hi):
    """max(lo, min(hi, x)) from abs() identities (core blocks only)."""
    return _clamp(x, lo, hi)


def _clamp(x, lo, hi):
    # max(lo, min(hi, x)) using (a+b+|a-b|)/2 identities so x is evaluated cheaply
    mn = (lit(hi) + x - abs_(lit(hi) - x)) / 2
    return (lit(lo) + mn + abs_(lit(lo) - mn)) / 2


def item(lst, i): return Op('data_itemoflist', {'INDEX': lit(i)}, {'LIST': [lst.name, Reg.lists[lst.name][0]]})
def listlen(lst): return Op('data_lengthoflist', {}, {'LIST': [lst.name, Reg.lists[lst.name][0]]})
def indexof(lst, v): return Op('data_itemnumoflist', {'ITEM': lit(v)}, {'LIST': [lst.name, Reg.lists[lst.name][0]]})
def listhas(lst, v): return Op('data_listcontainsitem', {'ITEM': lit(v)}, {'LIST': [lst.name, Reg.lists[lst.name][0]]})


def mouse_x(): return Op('sensing_mousex')
def mouse_y(): return Op('sensing_mousey')
def mouse_down(): return Op('sensing_mousedown')
def timer(): return Op('sensing_timer')
def days_since_2000(): return Op('sensing_dayssince2000')
def costume_number(): return Op('looks_costumenumbername', {}, {'NUMBER_NAME': ['number', None]})


def current(what):
    """what: YEAR MONTH DATE DAYOFWEEK HOUR MINUTE SECOND"""
    return Op('sensing_current', {}, {'CURRENTMENU': [what, None]})


def key_pressed(key):
    return Op('sensing_keypressed', {'KEY_OPTION': Menu('sensing_keyoptions', 'KEY_OPTION', lit(key))})


def costume_menu(v): return Menu('looks_costume', 'COSTUME', lit(v))


def backdrop_menu(v): return Menu('looks_backdrops', 'BACKDROP', lit(v))


# --------------------------------------------------------------------------
# Statements
class St:
    def __init__(self, opcode, inputs=None, fields=None, subs=None, mutation=None):
        self.opcode = opcode
        self.inputs = inputs or {}
        self.fields = fields or {}
        self.subs = subs or {}
        self.mutation = mutation


_stack = []  # stack of lists being built


def emit(st):
    if not _stack:
        raise RuntimeError('statement outside of a script/procedure body')
    _stack[-1].append(st)
    return st


class _Block:
    def __init__(self, st, key):
        self.st, self.key = st, key

    def __enter__(self):
        lst = []
        self.st.subs[self.key] = lst
        _stack.append(lst)
        return self

    def __exit__(self, *a):
        _stack.pop()


def If(cond):
    return _Block(emit(St('control_if', {'CONDITION': lit(cond)})), 'SUBSTACK')


class _Else:
    def __enter__(self):
        last = _stack[-1][-1]
        assert last.opcode in ('control_if', 'control_if_else'), 'Else() must follow If()'
        last.opcode = 'control_if_else'
        lst = []
        last.subs['SUBSTACK2'] = lst
        _stack.append(lst)

    def __exit__(self, *a):
        _stack.pop()


def Else():
    return _Else()


def repeat(n): return _Block(emit(St('control_repeat', {'TIMES': lit(n)})), 'SUBSTACK')
def forever(): return _Block(emit(St('control_forever')), 'SUBSTACK')
def while_(c): return _Block(emit(St('control_while', {'CONDITION': lit(c)})), 'SUBSTACK')
def until(c): return _Block(emit(St('control_repeat_until', {'CONDITION': lit(c)})), 'SUBSTACK')


def wait(s): return emit(St('control_wait', {'DURATION': lit(s)}))
def wait_until(c): return emit(St('control_wait_until', {'CONDITION': lit(c)}))


def stop_this():
    return emit(St('control_stop', {}, {'STOP_OPTION': ['this script', None]}, mutation={'hasnext': 'false'}))


def _target(ref):
    if ref.kind == 'var':
        return {'VARIABLE': [ref.name, _var_id(ref)]}
    return {'LIST': [ref.name, Reg.lists[ref.name][0]]}


def set_(var, val): return emit(St('data_setvariableto', {'VALUE': lit(val)}, _target(var)))
def change(var, val): return emit(St('data_changevariableby', {'VALUE': lit(val)}, _target(var)))
def list_add(lst, v): return emit(St('data_addtolist', {'ITEM': lit(v)}, _target(lst)))
def list_delete(lst, i): return emit(St('data_deleteoflist', {'INDEX': lit(i)}, _target(lst)))
def list_clear(lst): return emit(St('data_deletealloflist', {}, _target(lst)))
def list_insert(lst, i, v): return emit(St('data_insertatlist', {'INDEX': lit(i), 'ITEM': lit(v)}, _target(lst)))
def list_replace(lst, i, v): return emit(St('data_replaceitemoflist', {'INDEX': lit(i), 'ITEM': lit(v)}, _target(lst)))


# looks / motion / pen -----------------------------------------------------
def goto(x, y): return emit(St('motion_gotoxy', {'X': lit(x), 'Y': lit(y)}))
def point(d): return emit(St('motion_pointindirection', {'DIRECTION': lit(d)}))
def show(): return emit(St('looks_show'))
def hide(): return emit(St('looks_hide'))
def set_size(s): return emit(St('looks_setsizeto', {'SIZE': lit(s)}))
def set_stretch(x, y): return emit(St('looks_setStretch', {'X': lit(x), 'Y': lit(y)}))
def costume(v): return emit(St('looks_switchcostumeto', {'COSTUME': costume_menu(v)}))
def sound_play(name): return emit(St('sound_play', {'SOUND_MENU': lit(name)}))
def sound_volume(v): return emit(St('sound_setvolumeto', {'VOLUME': lit(v)}))
def backdrop(v): return emit(St('looks_switchbackdropto', {'BACKDROP': backdrop_menu(v)}))
def effect(name, v): return emit(St('looks_seteffectto', {'VALUE': lit(v)}, {'EFFECT': [name, None]}))
def rotation_all(): return emit(St('motion_setrotationstyle', {}, {'STYLE': ['all around', None]}))
def stamp(): return emit(St('pen_stamp'))
def pen_clear(): return emit(St('pen_clear'))
def pen_down(): return emit(St('pen_penDown'))
def pen_up(): return emit(St('pen_penUp'))
def pen_size(s): return emit(St('pen_setPenSizeTo', {'SIZE': lit(s)}))
def pen_color(c): return emit(St('pen_setPenColorToColor', {'COLOR': lit(c)}))
def ls_project(pid): return emit(St('localstorage_setProjectId', {'ID': lit(pid)}))
def ls_set(key, val): return emit(St('localstorage_set', {'KEY': lit(key), 'VALUE': lit(val)}))
def ls_get(key): return Op('localstorage_get', {'KEY': lit(key)})


BCASTS = {}


def bcast_id(name):
    if name not in BCASTS:
        BCASTS[name] = uid()
    return BCASTS[name]


class ColorIn(E):
    """input of a COLOR-type extension argument (colour picker shadow)"""
    def __init__(self, value):
        self.value = lit(value)


class BcastLit(E):
    def __init__(self, name):
        self.name = name


def broadcast(name): return emit(St('event_broadcast', {'BROADCAST_INPUT': BcastLit(name)}))
def broadcast_wait(name): return emit(St('event_broadcastandwait', {'BROADCAST_INPUT': BcastLit(name)}))
def broadcast_wait_dyn(expr): return emit(St('event_broadcastandwait', {'BROADCAST_INPUT': Menu('event_broadcast_menu', 'BROADCAST_OPTION', lit(expr))}))
def create_clone(of='_myself_'): return emit(St('control_create_clone_of', {'CLONE_OPTION': Menu('control_create_clone_of_menu', 'CLONE_OPTION', lit(of))}))
def delete_clone(): return emit(St('control_delete_this_clone'))
def go_front(): return emit(St('looks_gotofrontback', {}, {'FRONT_BACK': ['front', None]}))
def go_back(): return emit(St('looks_gotofrontback', {}, {'FRONT_BACK': ['back', None]}))
def set_x(x): return emit(St('motion_setx', {'X': lit(x)}))
def set_y(y): return emit(St('motion_sety', {'Y': lit(y)}))
def call_ext(opcode, **inputs): return emit(St(opcode, {k: lit(v) for k, v in inputs.items()}))
def ext_reporter(opcode, **inputs): return Op(opcode, {k: lit(v) for k, v in inputs.items()})


def stage_size(w, h): return emit(St('jgRuntime_setStageSize', {'WIDTH': lit(w), 'HEIGHT': lit(h)}))
def set_fps(f): return emit(St('jgRuntime_setMaxFrameRate', {'FRAMERATE': lit(f)}))


# --------------------------------------------------------------------------
# Custom blocks
class ProcDef:
    def __init__(self, name, argnames, fn, warp=True):
        self.name = name
        self.argnames = argnames
        self.fn = fn
        self.warp = warp
        self.argids = [uid() for _ in argnames]
        self.proccode = name + ''.join(f' {a} %s' for a in argnames)
        self.body = None

    def call(self, *args):
        if len(args) != len(self.argnames):
            raise TypeError(f'{self.name}: expected {len(self.argnames)} args, got {len(args)}')
        inputs = {self.argids[i]: lit(a) for i, a in enumerate(args)}
        return emit(St('procedures_call', inputs, {}, mutation={
            'proccode': self.proccode, 'argumentids': json.dumps(self.argids),
            'warp': 'true' if self.warp else 'false'}))


class _ProcNS:
    def __getattr__(self, name):
        u = _COMPILING[0] or cur_unit()
        if name in u.procs:
            return u.procs[name].call
        if u.uselib and 'lib' in UNITS and name in UNITS['lib'].procs:
            return UNITS['lib'].procs[name].call
        raise AttributeError(f'procedure {name!r} is not defined in sprite {u.name!r}')


P = _ProcNS()


DEFAULT_WARP = [True]      # sprite build: False (a broadcast-and-wait inside a warp procedure busy-waits)


def proc(argnames='', warp=None, name=None):
    argnames = argnames.split() if isinstance(argnames, str) else list(argnames)

    def deco(fn):
        nm = name or fn.__name__
        pd = ProcDef(nm, argnames, fn, DEFAULT_WARP[0] if warp is None else warp)
        cur_unit().procs[nm] = pd
        return pd.call
    return deco


# --------------------------------------------------------------------------
# Scripts (top-level stacks)
class Script:
    """with Script('flag'): ...   hats: flag | always(PM) | key:<name>"""
    def __init__(self, hat='flag', x=0, y=0):
        self.hat = hat
        self.body = []
        self.x, self.y = x, y

    def __enter__(self):
        _stack.append(self.body)
        cur_unit().scripts.append(self)
        return self

    def __exit__(self, *a):
        _stack.pop()


# --------------------------------------------------------------------------
# Serialisation
class Emitter:
    def __init__(self, blocks):
        self.blocks = blocks

    # inputs ----------------------------------------------------------------
    def literal(self, v):
        if isinstance(v, bool):
            return [10, '1' if v else '0']
        if isinstance(v, (int, float)):
            if isinstance(v, float) and v == int(v) and abs(v) < 1e15:
                v = int(v)
            return [4, str(v)]
        return [10, str(v)]

    def input(self, node, parent):
        """-> sb3 input array [shadowKind, ...]"""
        node = lit(node)
        if isinstance(node, Lit):
            return [1, self.literal(node.v)]
        if isinstance(node, ColorIn):
            if isinstance(node.value, Lit):
                return [1, [9, str(node.value.v)]]
            if isinstance(node.value, Ref) and node.value.kind == 'var':
                return [3, [12, node.value.name, _var_id(node.value)], [9, '#000000']]
            return [3, self.reporter(node.value, parent), [9, '#000000']]
        if isinstance(node, BcastLit):
            return [1, [11, node.name, bcast_id(node.name)]]
        if isinstance(node, Menu):
            sid = uid()
            self.blocks[sid] = {
                'opcode': node.opcode, 'next': None, 'parent': parent, 'inputs': {},
                'fields': {node.field: [self.menu_value(node.value), None]}, 'shadow': True, 'topLevel': False}
            if isinstance(node.value, Lit):
                return [1, sid]
            bid = self.reporter(node.value, parent)
            return [3, bid, sid]
        if isinstance(node, Ref):
            if node.kind == 'var':
                return [3, [12, node.name, _var_id(node)], [10, '']]
            if node.kind == 'list':
                return [3, [13, node.name, Reg.lists[node.name][0]], [10, '']]
            bid = self.reporter(node, parent)
            return [3, bid, [10, '']]
        bid = self.reporter(node, parent)
        return [3, bid, [10, '']]

    def menu_value(self, v):
        v = lit(v)
        return str(v.v) if isinstance(v, Lit) else ''

    def reporter(self, node, parent):
        if isinstance(node, Ref) and node.kind in ('var', 'list'):
            bid = uid()
            if node.kind == 'var':
                f = {'VARIABLE': [node.name, _var_id(node)]}
                op = 'data_variable'
            else:
                f = {'LIST': [node.name, Reg.lists[node.name][0]]}
                op = 'data_listcontents'
            self.blocks[bid] = {'opcode': op, 'next': None, 'parent': parent, 'inputs': {}, 'fields': f,
                                'shadow': False, 'topLevel': False}
            return bid
        if isinstance(node, Ref):
            assert node.kind == 'arg'
            bid = uid()
            self.blocks[bid] = {'opcode': 'argument_reporter_string_number', 'next': None, 'parent': parent,
                                'inputs': {}, 'fields': {'VALUE': [node.name, None]}, 'shadow': False,
                                'topLevel': False}
            return bid
        bid = uid()
        b = {'opcode': node.opcode, 'next': None, 'parent': parent, 'inputs': {}, 'fields': {},
             'shadow': False, 'topLevel': False}
        self.blocks[bid] = b
        for k, v in node.inputs.items():
            b['inputs'][k] = self.input(v, bid)
        for k, v in node.fields.items():
            b['fields'][k] = v
        if node.mutation:
            b['mutation'] = self.mut(node.mutation)
        return bid

    def mut(self, m):
        d = {'tagName': 'mutation', 'children': []}
        d.update(m)
        return d

    # statements --------------------------------------------------------------
    def stack(self, stmts, parent):
        first = prev = None
        for st in stmts:
            bid = uid()
            b = {'opcode': st.opcode, 'next': None, 'parent': prev if prev else parent, 'inputs': {},
                 'fields': {}, 'shadow': False, 'topLevel': False}
            self.blocks[bid] = b
            if prev:
                self.blocks[prev]['next'] = bid
            else:
                first = bid
            for k, v in st.inputs.items():
                b['inputs'][k] = self.input(v, bid)
            for k, v in st.fields.items():
                b['fields'][k] = v
            for k, sub in st.subs.items():
                sid = self.stack(sub, bid)
                if sid:
                    b['inputs'][k] = [2, sid]
            if st.mutation:
                b['mutation'] = self.mut(st.mutation)
            prev = bid
        return first


def _collect_calls(node, acc):
    if isinstance(node, list):
        for n in node:
            _collect_calls(n, acc)
    elif isinstance(node, St):
        if node.opcode == 'procedures_call':
            acc.add(node.mutation['proccode'])
        for v in node.inputs.values():
            _collect_calls(v, acc)
        for v in node.subs.values():
            _collect_calls(v, acc)
    elif isinstance(node, Op):
        for v in node.inputs.values():
            _collect_calls(v, acc)
    elif isinstance(node, (Menu, ColorIn)):
        _collect_calls(node.value, acc)


def compile_target_blocks(unit_=None):
    u = unit_ or cur_unit()
    _COMPILING[0] = u
    blocks = {}
    em = Emitter(blocks)
    layout = []   # (top-level block id, number of blocks in the stack) -> editor positions
    # procedures
    procs = list(u.procs.values())
    if u.uselib and 'lib' in UNITS and u.name != 'lib':
        procs = list(UNITS['lib'].procs.values()) + procs
    bodies = {}
    for pd in procs:
        body = []
        _stack.append(body)
        pd.fn(*[Arg(a) for a in pd.argnames])
        _stack.pop()
        bodies[pd.name] = body
    if u.prune:
        by_code = {pd.proccode: pd for pd in procs}
        roots = []
        for sc in u.scripts:
            roots.append(sc.body)
        for pd in u.procs.values():
            roots.append(bodies[pd.name])
        seen = set()
        todo = list(roots)
        while todo:
            lst = todo.pop()
            codes = set()
            _collect_calls(lst, codes)
            for c in codes:
                pd = by_code.get(c)
                if pd and pd.name not in seen:
                    seen.add(pd.name)
                    todo.append(bodies[pd.name])
        procs = [pd for pd in procs if pd.name in seen or pd.name in u.procs]
    for pd in procs:
        body = bodies[pd.name]
        defid, protoid = uid(), uid()
        blocks[defid] = {'opcode': 'procedures_definition', 'next': None, 'parent': None,
                         'inputs': {'custom_block': [1, protoid]}, 'fields': {}, 'shadow': False,
                         'topLevel': True, 'x': 0, 'y': 0}
        pin = {}
        for i, a in enumerate(pd.argnames):
            rid = uid()
            blocks[rid] = {'opcode': 'argument_reporter_string_number', 'next': None, 'parent': protoid,
                           'inputs': {}, 'fields': {'VALUE': [a, None]}, 'shadow': True, 'topLevel': False}
            pin[pd.argids[i]] = [1, rid]
        blocks[protoid] = {'opcode': 'procedures_prototype', 'next': None, 'parent': defid, 'inputs': pin,
                           'fields': {}, 'shadow': True, 'topLevel': False,
                           'mutation': {'tagName': 'mutation', 'children': [], 'proccode': pd.proccode,
                                        'argumentids': json.dumps(pd.argids),
                                        'argumentnames': json.dumps(pd.argnames),
                                        'argumentdefaults': json.dumps(['' for _ in pd.argnames]),
                                        'warp': 'true' if pd.warp else 'false'}}
        n0 = len(blocks)
        first = em.stack(body, defid)
        blocks[defid]['next'] = first
        if first:
            blocks[first]['parent'] = defid
        layout.append((defid, len(blocks) - n0 + 3))
    # scripts
    for sc in u.scripts:
        hat_id = uid()
        if sc.hat == 'flag':
            hb = {'opcode': 'event_whenflagclicked', 'fields': {}}
        elif sc.hat == 'always':
            hb = {'opcode': 'event_always', 'fields': {}}
        elif sc.hat.startswith('receive:'):
            hb = {'opcode': 'event_whenbroadcastreceived', 'fields': {'BROADCAST_OPTION': [sc.hat[8:], bcast_id(sc.hat[8:])]}}
        elif sc.hat == 'clone':
            hb = {'opcode': 'control_start_as_clone', 'fields': {}}
        elif sc.hat.startswith('key:'):
            hb = {'opcode': 'event_whenkeypressed', 'fields': {'KEY_OPTION': [sc.hat[4:], None]}}
        else:
            raise ValueError(sc.hat)
        blocks[hat_id] = {'opcode': hb['opcode'], 'next': None, 'parent': None, 'inputs': {},
                          'fields': hb['fields'], 'shadow': False, 'topLevel': True, 'x': sc.x, 'y': sc.y}
        n0 = len(blocks)
        first = em.stack(sc.body, hat_id)
        blocks[hat_id]['next'] = first
        layout.insert(0, (hat_id, len(blocks) - n0 + 1))
    # editor layout: stack scripts in columns so nothing overlaps
    x = y = 0
    for bid, n in layout:
        h = 70 + 21 * n
        if y > 0 and y + h > 7000:
            x += 1100
            y = 0
        blocks[bid]['x'], blocks[bid]['y'] = x, y
        y += h + 40
    _COMPILING[0] = None
    return blocks


# --------------------------------------------------------------------------
# Assets + project assembly
class Costume:
    def __init__(self, name, svg, cx, cy):
        self.name, self.svg, self.cx, self.cy = name, svg, cx, cy
        self.md5 = hashlib.md5(svg.encode('utf-8')).hexdigest()

    def meta(self):
        return {'name': self.name, 'bitmapResolution': 1, 'dataFormat': 'svg', 'assetId': self.md5,
                'md5ext': self.md5 + '.svg', 'rotationCenterX': self.cx, 'rotationCenterY': self.cy}


class Sound:
    """16-bit mono WAV"""
    def __init__(self, name, data, rate, samples):
        self.name, self.data, self.rate, self.samples = name, data, rate, samples
        self.md5 = hashlib.md5(data).hexdigest()

    def meta(self):
        return {'name': self.name, 'assetId': self.md5, 'dataFormat': 'wav', 'format': '', 'rate': self.rate,
                'sampleCount': self.samples, 'md5ext': self.md5 + '.wav'}


def build_project(path, sprite_name, sprite_costumes, backdrops, extensions=(), extension_urls=None):
    blocks = compile_target_blocks()
    variables = {vid: [name, init] for name, (vid, init) in Reg.vars.items()}
    lists = {lid: [name, init] for name, (lid, init) in Reg.lists.items()}

    def costs(cs): return [c.meta() for c in cs]

    stage = {'isStage': True, 'name': 'Stage', 'variables': variables, 'lists': lists, 'broadcasts': {},
             'blocks': {}, 'comments': {}, 'currentCostume': 0, 'costumes': costs(backdrops), 'sounds': [],
             'volume': 100, 'layerOrder': 0, 'tempo': 60, 'videoTransparency': 50, 'videoState': 'on',
             'textToSpeechLanguage': None}
    sprite = {'isStage': False, 'name': sprite_name, 'variables': {}, 'lists': {}, 'broadcasts': {},
              'blocks': blocks, 'comments': {}, 'currentCostume': 0, 'costumes': costs(sprite_costumes),
              'sounds': [], 'volume': 100, 'layerOrder': 1, 'visible': False, 'x': 0, 'y': 0, 'size': 100,
              'direction': 90, 'draggable': False, 'rotationStyle': 'all around'}
    project = {'targets': [stage, sprite], 'monitors': [], 'extensions': list(extensions),
               'extensionURLs': dict(extension_urls or {}), 'extensionData': {}, 'customFonts': [],
               'meta': {'semver': '3.0.0', 'vm': '0.2.0', 'origin': 'PenguinMod',
                        'agent': '', 'platform': {'name': 'PenguinMod', 'url': 'https://penguinmod.com/',
                                                  'version': 'stable'}}}
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('project.json', json.dumps(project, separators=(',', ':')))
        seen = set()
        for c in list(backdrops) + list(sprite_costumes):
            if c.md5 not in seen:
                seen.add(c.md5)
                z.writestr(c.md5 + '.svg', c.svg)
    return project


def build_multi(path, backdrops, extensions=(), extension_urls=None, order=None):
    """Compile every sprite unit (UNITS) into one project: Stage + one target per sprite."""
    sprites = [UNITS[n] for n in order] if order else [u for u in UNITS.values() if u.sprite and u.name != 'lib']
    targets = []
    for i, u in enumerate(sprites):
        blocks = compile_target_blocks(u)
        targets.append({'isStage': False, 'name': u.name,
                        'variables': {vid: [n, init] for n, (vid, init) in u.locals.items()},
                        'lists': {}, 'broadcasts': {}, 'blocks': blocks, 'comments': {}, 'currentCostume': 0,
                        'costumes': [c.meta() for c in u.costumes],
                        'sounds': [x.meta() for x in getattr(u, 'sounds', [])], 'volume': 100,
                        'layerOrder': i + 1, 'visible': u.visible, 'x': u.x, 'y': u.y, 'size': u.size,
                        'direction': 90, 'draggable': False, 'rotationStyle': 'all around'})
    stage = {'isStage': True, 'name': 'Stage',
             'variables': {vid: [n, init] for n, (vid, init) in Reg.vars.items()},
             'lists': {lid: [n, init] for n, (lid, init) in Reg.lists.items()},
             'broadcasts': {bid: n for n, bid in BCASTS.items()}, 'blocks': {}, 'comments': {},
             'currentCostume': 0, 'costumes': [c.meta() for c in backdrops], 'sounds': [], 'volume': 100,
             'layerOrder': 0, 'tempo': 60, 'videoTransparency': 50, 'videoState': 'on', 'textToSpeechLanguage': None}
    project = {'targets': [stage] + targets, 'monitors': [], 'extensions': list(extensions),
               'extensionURLs': dict(extension_urls or {}), 'extensionData': {}, 'customFonts': [],
               'meta': {'semver': '3.0.0', 'vm': '0.2.0', 'origin': 'PenguinMod', 'agent': '',
                        'platform': {'name': 'PenguinMod', 'url': 'https://penguinmod.com/', 'version': 'stable'}}}
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('project.json', json.dumps(project, separators=(',', ':')))
        seen = set()
        for c in list(backdrops) + [c for u in sprites for c in u.costumes]:
            if c.md5 not in seen:
                seen.add(c.md5)
                z.writestr(c.md5 + '.svg', c.svg)
        for u in sprites:
            for x in getattr(u, 'sounds', []):
                if x.md5 not in seen:
                    seen.add(x.md5)
                    z.writestr(x.md5 + '.wav', x.data)
    return project
