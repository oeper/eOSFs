"""Generates every costume/backdrop the OS needs (all vector, all self-contained)."""
import math
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

from sb3 import Costume

FONT_DIR = '/usr/share/fonts/opentype/inter/'
W, H = 640, 360

# --- palette ---------------------------------------------------------------
PAL = [
    ('white', 'FFFFFF'), ('black', '000000'),
    ('l_bg', 'F1F3F7'), ('l_surf', 'FFFFFF'), ('l_surf2', 'E7EAF0'), ('l_div', 'D3D8E1'),
    ('d_bg', '0F1115'), ('d_surf', '1B1E25'), ('d_surf2', '272B34'), ('d_div', '363B47'),
    ('a_blue', '2F6BFF'), ('a_teal', '10B2A0'), ('a_green', '22A559'),
    ('a_orange', 'F97316'), ('a_pink', 'E8458F'), ('a_purple', '8B5CF6'),
    ('red', 'EF4444'), ('amber', 'F5A524'), ('green', '2BC16B'), ('gray', '8B94A5'),
    ('yellow', 'FACC15'), ('brown', '8B5A2B'), ('lgray', 'C5CAD4'),
    ('dgray', '4B5262'), ('sky', '38BDF8'),
    ('w1', '6D28D9'), ('w2', '0E7490'), ('w3', '15803D'), ('w4', 'BE185D'), ('w5', '3B4660'), ('w6', '9A2A1A'),
]
PIDX = {n: i + 1 for i, (n, _) in enumerate(PAL)}   # costume numbers (1-based)
NPAL = len(PAL)


def rect_costume(name, hexcol):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100">'
           f'<rect width="100" height="100" fill="#{hexcol}"/></svg>')
    return Costume(name, svg, 50, 50)


def circle_costume(name, hexcol):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100">'
           f'<circle cx="50" cy="50" r="50" fill="#{hexcol}"/></svg>')
    return Costume(name, svg, 50, 50)


# --- glyphs ------------------------------------------------------------------
CHARS = [chr(c) for c in range(33, 127)] + list('×÷−±•°…')


def glyph_costumes(path, prefix):
    font = TTFont(path)
    gs = font.getGlyphSet()
    cmap = font.getBestCmap()
    upem = font['head'].unitsPerEm
    s = 100.0 / upem
    out, widths = [], []
    for ch in CHARS:
        gname = cmap[ord(ch)]
        g = gs[gname]
        pen = SVGPathPen(gs, ntos=lambda v: ('%.2f' % v).rstrip('0').rstrip('.'))
        g.draw(TransformPen(pen, (s, 0, 0, -s, 10, 100)))
        d = pen.getCommands()
        adv = g.width * s
        pad = 10
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{adv + 2 * pad:.2f}" height="140" '
               f'viewBox="0 0 {adv + 2 * pad:.2f} 140"><path d="{d}" fill="#FFFFFF"/></svg>')
        out.append((Costume(prefix + ch, svg, pad, 100), round(adv, 2)))
    return out


# --- UI icons (white, stroke based, 24x24 grid) -----------------------------
def _icon(name, body, stroke=True):
    st = ('fill="none" stroke="#FFFFFF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"'
          if stroke else 'fill="#FFFFFF"')
    # NOTE: no transform attributes anywhere - Scratch's SVG loader rewrites paths under transforms and
    # mangles h/H/V commands.  Icons live in a 24-unit viewBox and are scaled by the stamp stretch.
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">'
           f'<g {st}>{body}</g></svg>')
    return Costume('i_' + name, svg, 12, 12)


def _rot_rect(cx, cy, x, y, w, h, deg):
    """rotated rectangle as a plain polygon (avoids transform attributes)"""
    a = math.radians(deg)
    pts = []
    for px, py in ((x, y), (x + w, y), (x + w, y + h), (x, y + h)):
        dx, dy = px - cx, py - cy
        pts.append((cx + dx * math.cos(a) - dy * math.sin(a), cy + dx * math.sin(a) + dy * math.cos(a)))
    return '<polygon points="' + ' '.join(f'{px:.2f},{py:.2f}' for px, py in pts) + '"/>'


def gear_body():
    teeth = ''.join(_rot_rect(12, 12, 10.2, 1.6, 3.6, 5, a) for a in range(0, 360, 45))
    return (f'<g fill="#FFFFFF" stroke="none">{teeth}<circle cx="12" cy="12" r="7.6"/>'
            f'<circle cx="12" cy="12" r="3" fill="#000000" fill-opacity="0"/></g>')


def ui_icons():
    ic = []
    ic.append(_icon('wifi', '<path d="M2.5 9a14 14 0 0 1 19 0"/><path d="M5.8 12.6a9 9 0 0 1 12.4 0"/>'
                            '<path d="M9.1 16a4.3 4.3 0 0 1 5.8 0"/><circle cx="12" cy="19.3" r="1.1" fill="#FFF"/>'))
    ic.append(_icon('wifi_off', '<path d="M2.5 9a14 14 0 0 1 19 0" opacity=".35"/><path d="M5.8 12.6a9 9 0 0 1 12.4 0" '
                                'opacity=".35"/><path d="M9.1 16a4.3 4.3 0 0 1 5.8 0" opacity=".35"/>'
                                '<path d="M3 3l18 18"/>'))
    ic.append(_icon('back', '<path d="M15 5l-7 7 7 7"/>'))
    ic.append(_icon('home', '<circle cx="12" cy="12" r="7.5"/>'))
    ic.append(_icon('recents', '<rect x="5" y="5" width="14" height="14" rx="3"/>'))
    ic.append(_icon('backspace', '<path d="M9 5h10a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H9L3 12z"/><path d="M12.5 9.5l5 5M17.5 9.5l-5 5"/>'))
    ic.append(_icon('shift', '<path d="M12 4l8 9h-5v6H9v-6H4z"/>'))
    ic.append(_icon('shift_on', '<path d="M12 4l8 9h-5v6H9v-6H4z" fill="#FFFFFF"/>'))
    ic.append(_icon('enter', '<path d="M19 6v6a2 2 0 0 1-2 2H5"/><path d="M9 10l-4 4 4 4"/>'))
    ic.append(_icon('lock', '<rect x="5" y="11" width="14" height="9" rx="2.5"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>'))
    ic.append(_icon('sun', '<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2.2M12 19.3v2.2M2.5 12h2.2M19.3 12h2.2'
                           'M5.2 5.2l1.6 1.6M17.2 17.2l1.6 1.6M18.8 5.2l-1.6 1.6M6.8 17.2l-1.6 1.6"/>'))
    ic.append(_icon('moon', '<path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5z"/>'))
    ic.append(_icon('plus', '<path d="M12 5v14M5 12h14"/>'))
    ic.append(_icon('minus', '<path d="M5 12h14"/>'))
    ic.append(_icon('folder', '<path d="M3 7a2 2 0 0 1 2-2h4l2 2.5h8a2 2 0 0 1 2 2V17a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>'))
    ic.append(_icon('file', '<path d="M6 3h8l5 5v11a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z"/><path d="M14 3v5h5"/>'))
    ic.append(_icon('trash', '<path d="M4 7h16M9 7V4.5h6V7M6.5 7l1 13h9l1-13M10 11v6M14 11v6"/>'))
    ic.append(_icon('edit', '<path d="M4 20l1-4L16.5 4.5a2 2 0 0 1 3 3L8 19z"/>'))
    ic.append(_icon('check', '<path d="M5 12.5l4.5 4.5L19 7.5"/>'))
    ic.append(_icon('chev_r', '<path d="M9 5l7 7-7 7"/>'))
    ic.append(_icon('chev_l', '<path d="M15 5l-7 7 7 7"/>'))
    ic.append(_icon('chev_d', '<path d="M5 9l7 7 7-7"/>'))
    ic.append(_icon('close', '<path d="M6 6l12 12M18 6L6 18"/>'))
    ic.append(_icon('play', '<path d="M8 5l11 7-11 7z" fill="#FFFFFF"/>'))
    ic.append(_icon('pause', '<rect x="6.5" y="5" width="3.8" height="14" rx="1" fill="#FFFFFF"/>'
                             '<rect x="13.7" y="5" width="3.8" height="14" rx="1" fill="#FFFFFF"/>'))
    ic.append(_icon('reset', '<path d="M4 12a8 8 0 1 0 2.4-5.7L4 8.5"/><path d="M4 4v4.5h4.5"/>'))
    ic.append(_icon('up', '<path d="M12 19V5M6 11l6-6 6 6"/>'))
    ic.append(_icon('down', '<path d="M12 5v14M6 13l6 6 6-6"/>'))
    ic.append(_icon('left', '<path d="M19 12H5M11 6l-6 6 6 6"/>'))
    ic.append(_icon('right', '<path d="M5 12h14M13 6l6 6-6 6"/>'))
    ic.append(_icon('bolt', '<path d="M13 3L5 14h6l-1 7 8-11h-6z" fill="#FFFFFF"/>'))
    ic.append(_icon('gear', gear_body(), stroke=False))
    ic.append(_icon('bt', '<path d="M7 7l10 10-5 4V3l5 4L7 17"/>'))
    ic.append(_icon('eraser', '<path d="M7 20h12M5.5 15.5l9-9a2 2 0 0 1 3 0l2 2a2 2 0 0 1 0 3L11 20H8z"/>'))
    ic.append(_icon('info', '<circle cx="12" cy="12" r="9"/><path d="M12 11v6"/><circle cx="12" cy="7.6" r="1" fill="#FFF"/>'))
    ic.append(_icon('palette', '<path d="M12 3a9 9 0 1 0 0 18c1.5 0 2-1 1.4-2.2-.7-1.4.2-2.8 1.8-2.8H18a3 3 0 0 0 3-3A9 9 0 0 0 12 3z"/>'
                               '<circle cx="7.5" cy="11" r="1" fill="#FFF"/><circle cx="10" cy="7" r="1" fill="#FFF"/>'
                               '<circle cx="15" cy="7.5" r="1" fill="#FFF"/>'))
    ic.append(_icon('shield', '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/>'))
    ic.append(_icon('storage', '<ellipse cx="12" cy="6" rx="7.5" ry="3"/><path d="M4.5 6v6c0 1.7 3.4 3 7.5 3s7.5-1.3 7.5-3V6"/>'
                               '<path d="M4.5 12v6c0 1.7 3.4 3 7.5 3s7.5-1.3 7.5-3v-6"/>'))
    ic.append(_icon('clock', '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.5 2"/>'))
    ic.append(_icon('power', '<path d="M12 3v8"/><path d="M6.6 6.6a8 8 0 1 0 10.8 0"/>'))
    ic.append(_icon('search', '<circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5L21 21"/>'))
    ic.append(_icon('vol', '<path d="M4 9.5h3.5L12 5.5v13l-4.5-4H4z"/><path d="M15.5 9a4.5 4.5 0 0 1 0 6"/>'
                           '<path d="M18 6.5a8 8 0 0 1 0 11"/>'))
    ic.append(_icon('vol_off', '<path d="M4 9.5h3.5L12 5.5v13l-4.5-4H4z"/><path d="M16 9.5l5 5M21 9.5l-5 5"/>'))
    ic.append(_icon('download', '<path d="M12 4v11M7 10.5l5 5 5-5M5 20h14"/>'))
    return ic


def ui_sounds():
    """short synthesised UI sounds (16-bit mono WAV): name -> list of (freq0, freq1, seconds, gain) segments"""
    import math, struct
    from sb3 import Sound
    rate = 22050
    spec = {
        'tap': [(880, 660, 0.035, 0.5)],
        'open': [(520, 880, 0.09, 0.45)],
        'close': [(820, 480, 0.09, 0.45)],
        'notify': [(880, 880, 0.08, 0.5), (1175, 1175, 0.14, 0.5)],
        'lock': [(660, 660, 0.05, 0.45), (440, 440, 0.08, 0.45)],
        'unlock': [(520, 520, 0.05, 0.45), (784, 784, 0.1, 0.45)],
        'error': [(220, 200, 0.09, 0.55), (0, 0, 0.03, 0), (220, 190, 0.12, 0.55)],
        'key': [(1300, 1000, 0.02, 0.35)],
    }
    out = []
    for name, segs in spec.items():
        pcm, ph = [], 0.0
        for f0, f1, dur, gain in segs:
            n = int(rate * dur)
            for i in range(n):
                t = i / n
                ph += 2 * math.pi * (f0 + (f1 - f0) * t) / rate
                env = min(1, i / (rate * 0.004)) * (1 - t) ** 1.6           # 4 ms attack, smooth decay: no clicks
                pcm.append(int(32767 * gain * env * (math.sin(ph) + 0.25 * math.sin(2 * ph)) / 1.25))
        data = b''.join(struct.pack('<h', v) for v in pcm)
        wav = (b'RIFF' + struct.pack('<I', 36 + len(data)) + b'WAVEfmt ' + struct.pack('<IHHIIHH', 16, 1, 1, rate, rate * 2, 2, 16)
               + b'data' + struct.pack('<I', len(data)) + data)
        out.append(Sound(name, wav, rate, len(pcm)))
    return out


# --- app icons: gradient rounded squares ------------------------------------
def _app(name, c1, c2, body):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100">'
           f'<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#{c1}"/>'
           f'<stop offset="1" stop-color="#{c2}"/></linearGradient></defs>'
           f'<rect width="100" height="100" rx="24" fill="url(#g)"/>{body}</svg>')
    return Costume('a_' + name, svg, 50, 50)


def app_icons():
    ap = []
    ap.append(_app('files', 'FFC53D', 'F5A000',
                   '<path d="M20 34a6 6 0 0 1 6-6h14l7 8h27a6 6 0 0 1 6 6v28a6 6 0 0 1-6 6H26a6 6 0 0 1-6-6z" fill="#FFF"/>'))
    ap.append(_app('notes', 'FFE066', 'FFC800',
                   '<rect x="24" y="20" width="52" height="60" rx="7" fill="#FFF"/>'
                   '<g stroke="#E0A800" stroke-width="5" stroke-linecap="round"><path d="M34 38h32M34 52h32M34 66h20"/></g>'))
    ap.append(_app('calc', '4B5262', '1F2430',
                   '<rect x="24" y="18" width="52" height="20" rx="5" fill="#9AE6B4"/>'
                   + ''.join(f'<rect x="{26 + 17 * c}" y="{46 + 15 * r}" width="14" height="11" rx="3" '
                             f'fill="{"#FF9F0A" if c == 2 else "#FFFFFF"}"/>' for r in range(3) for c in range(3))))
    ap.append(_app('clock', '3B82F6', '1D4ED8',
                   '<circle cx="50" cy="50" r="30" fill="#FFF"/><g stroke="#1D4ED8" stroke-width="5" '
                   'stroke-linecap="round"><path d="M50 50V30M50 50l14 8"/></g><circle cx="50" cy="50" r="3.5" fill="#1D4ED8"/>'))
    ap.append(_app('term', '2B2F3A', '0B0D12',
                   '<path d="M26 34l18 14-18 14" fill="none" stroke="#4ADE80" stroke-width="7" stroke-linecap="round" '
                   'stroke-linejoin="round"/><path d="M50 68h24" stroke="#4ADE80" stroke-width="7" stroke-linecap="round"/>'))
    ap.append(_app('paint', 'F472B6', '8B5CF6',
                   '<path d="M50 20a30 30 0 1 0 0 60c5 0 6-4 4-7-2-4 0-9 6-9h8a8 8 0 0 0 8-8c0-20-10-36-26-36z" fill="#FFF"/>'
                   '<circle cx="36" cy="46" r="5" fill="#EF4444"/><circle cx="46" cy="32" r="5" fill="#FACC15"/>'
                   '<circle cx="62" cy="34" r="5" fill="#22C55E"/><circle cx="68" cy="50" r="5" fill="#3B82F6"/>'))
    ap.append(_app('snake', '4ADE80', '15803D',
                   '<path d="M28 68h30a10 10 0 0 0 0-20H42a10 10 0 0 1 0-20h30" fill="none" stroke="#FFF" '
                   'stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>'
                   '<circle cx="72" cy="28" r="3.2" fill="#15803D"/>'))
    ap.append(_app('settings', '9AA3B2', '5B6475', gear_icon_body()))
    ap.append(_app('store', '38BDF8', '2563EB',
                   '<path d="M28 40h44l-4 34a6 6 0 0 1-6 5H38a6 6 0 0 1-6-5z" fill="#FFF"/>'
                   '<path d="M40 40v-6a10 10 0 0 1 20 0v6" fill="none" stroke="#FFF" stroke-width="6" stroke-linecap="round"/>'
                   '<path d="M50 50v14M43 58l7 7 7-7" fill="none" stroke="#2563EB" stroke-width="5" stroke-linecap="round" '
                   'stroke-linejoin="round"/>'))
    return ap


def gear_icon_body():
    teeth = '<g fill="#FFF">' + ''.join(_rot_rect(50, 50, 43, 14, 14, 18, a) for a in range(0, 360, 45)) + '</g>'
    return teeth + '<circle cx="50" cy="50" r="25" fill="#FFF"/><circle cx="50" cy="50" r="11" fill="#6B7487"/>'


# --- wallpapers --------------------------------------------------------------
WALLS = [
    ('Aurora', '1B2A6B', '6D28D9', 'EC4899'),
    ('Ocean', '053B66', '0E7490', '22D3EE'),
    ('Forest', '0B3D2E', '15803D', '84CC16'),
    ('Sunset', '4C1D95', 'BE185D', 'F97316'),
    ('Slate', '1E2433', '3B4660', '64748B'),
    ('Ember', '3B0A0A', '9A2A1A', 'F59E0B'),
]


def wallpapers():
    out = []
    for i, (n, a, b, c) in enumerate(WALLS):
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
               f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#{a}"/>'
               f'<stop offset=".55" stop-color="#{b}"/><stop offset="1" stop-color="#{c}"/></linearGradient></defs>'
               f'<rect width="{W}" height="{H}" fill="url(#g)"/>'
               f'<circle cx="{110 + 90 * i}" cy="{70 + 25 * (i % 3)}" r="150" fill="#FFFFFF" opacity=".06"/>'
               f'<circle cx="{560 - 70 * (i % 4)}" cy="{300 - 20 * (i % 3)}" r="190" fill="#FFFFFF" opacity=".07"/>'
               f'<circle cx="{330 + 40 * i}" cy="360" r="130" fill="#000000" opacity=".10"/></svg>')
        out.append(Costume('wp' + str(i + 1), svg, W // 2, H // 2))
    return out


def pill_costume():
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="64" height="38" viewBox="0 0 64 38">'
           '<rect width="64" height="38" rx="19" fill="#FFFFFF"/></svg>')
    return Costume('k_pill', svg, 32, 19)


def black_backdrop():
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"><rect width="{W}" height="{H}" fill="#000"/></svg>'
    return Costume('black', svg, W // 2, H // 2)


def build():
    """Returns (sprite_costumes, backdrops, glyph_width_list, info)."""
    costumes = []
    for n, h in PAL:
        costumes.append(rect_costume('r_' + n, h))
    for n, h in PAL:
        costumes.append(circle_costume('c_' + n, h))
    costumes += ui_icons()
    costumes += app_icons()
    costumes.append(pill_costume())
    gw_pairs = []
    gw_pairs += glyph_costumes(FONT_DIR + 'Inter-Medium.otf', 'g')
    gw_pairs += glyph_costumes(FONT_DIR + 'Inter-Bold.otf', 'b')
    widths = [0] * len(costumes)
    for c, w in gw_pairs:
        costumes.append(c)
        widths.append(w)
    # unique names
    names = [c.name for c in costumes]
    assert len(names) == len(set(names)), 'duplicate costume names'
    backdrops = wallpapers() + [black_backdrop()]
    return costumes, backdrops, widths, {'npal': NPAL, 'walls': [w[0] for w in WALLS]}


if __name__ == '__main__':
    c, b, w, info = build()
    print(len(c), 'costumes', len(b), 'backdrops')
