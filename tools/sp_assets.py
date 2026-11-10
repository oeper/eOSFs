"""Costumes for the sprite build: the Element clone pool (shapes/icons) - text is rendered by Iris Text."""
import assets
from sb3 import Costume
from sp_prims_data import RR_ASPECT, RR_RATIO


def _svg(w, h, body):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{body}</svg>'


FILL = {1: '#FFFFFF', 2: '#2F6BFF'}     # family 1 = white (grays via brightness), 2 = accent (hue/brightness effects)


def element_costumes():
    cs = []
    for f, col in FILL.items():
        cs.append(Costume(f'sq_{f}', _svg(100, 100, f'<rect width="100" height="100" fill="{col}"/>'), 50, 50))
        cs.append(Costume(f'ci_{f}', _svg(100, 100, f'<circle cx="50" cy="50" r="50" fill="{col}"/>'), 50, 50))
        for ai, a in enumerate(RR_ASPECT, 1):
            w = round(40 * a, 2)
            for ri, r in enumerate(RR_RATIO, 1):
                rx = r * 40
                cs.append(Costume(f'rr_{f}_{ai}_{ri}', _svg(w, 40, f'<rect width="{w}" height="40" rx="{rx}" ry="{rx}" fill="{col}"/>'),
                                  w / 2, 20))
    cs += assets.ui_icons()
    cs += assets.app_icons()
    cs.append(assets.pill_costume())
    names = [c.name for c in cs]
    assert len(names) == len(set(names))
    return cs
