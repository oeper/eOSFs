// Headless test harness: real Scratch VM + WebGL renderer in Chromium.
// PenguinMod-only blocks used by eOS are shimmed (setStretch, stage size, fps).
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const NM = path.join(__dirname, 'node_modules');
const W = 640, H = 360;

async function open(pmp, opts = {}) {
  const browser = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage({ viewport: { width: W, height: H } });
  page.on('pageerror', e => console.log('[pageerror]', e.message));
  page.on('console', m => { if (m.type() === 'error' || opts.verbose) console.log('[console]', m.text()); });
  await page.setContent(`<html><body style="margin:0"><canvas id="c" width="${W}" height="${H}"></canvas></body></html>`);
  for (const f of ['scratch-svg-renderer/dist/web/scratch-svg-renderer.js', 'scratch-render/dist/web/scratch-render.js',
                   'scratch-storage/dist/web/scratch-storage.js', 'scratch-vm/dist/web/scratch-vm.js'])
    await page.addScriptTag({ path: path.join(NM, f) });
  if (opts.store) await page.evaluate((s) => { window.__initStore = s; }, opts.store);
  const b64 = fs.readFileSync(pmp).toString('base64');
  const err = await page.evaluate(async (b64) => {
    const canvas = document.getElementById('c');
    const vm = new VirtualMachine();
    const storage = new ScratchStorage.ScratchStorage();
    vm.attachStorage(storage);
    const renderer = new ScratchRender(canvas, -320, 320, -180, 180);
    vm.attachRenderer(renderer);
    vm.attachV2SVGAdapter(new ScratchSVGRenderer.SVGRenderer());
    vm.attachV2BitmapAdapter(new ScratchSVGRenderer.BitmapAdapter());
    const RC = vm.runtime.constructor;
    Object.defineProperty(RC, 'STAGE_WIDTH', { get: () => 640 });
    Object.defineProperty(RC, 'STAGE_HEIGHT', { get: () => 360 });
    Object.defineProperty(RC, 'MAX_CLONES', { get: () => 2000 });
    const origLoad = vm.extensionManager.loadExtensionURL.bind(vm.extensionManager);
    vm.extensionManager.loadExtensionURL = (id) => (id.startsWith('jgRuntime') || id === 'g1nxIrisText' || id.includes('iris-text') || id.includes('local-storage') || id === 'localstorage') ? Promise.resolve() : origLoad(id);   // PM-only / URL extensions
    // shim for the TurboWarp Local Storage extension
    const store = window.__store = Object.assign({}, window.__initStore || {});
    let pid = '';
    vm.runtime._primitives.localstorage_setProjectId = (a) => { pid = String(a.ID); };
    vm.runtime._primitives.localstorage_set = (a) => { store[pid + ':' + a.KEY] = String(a.VALUE); };
    vm.runtime._primitives.localstorage_get = (a) => (store[pid + ':' + a.KEY] !== undefined ? store[pid + ':' + a.KEY] : '');
    const bin = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
    await vm.loadProject(bin.buffer);
    const RT = vm.runtime.targets.find(t => !t.isStage).constructor;
    const orig = RT.prototype._getRenderedDirectionAndScale;
    RT.prototype._getRenderedDirectionAndScale = function () {
      const r = orig.call(this);
      const s = this._stretch || [1, 1];
      r.scale = [r.scale[0] * s[0], r.scale[1] * s[1]];
      return r;
    };
    const prim = vm.runtime._primitives;
    prim.looks_setStretch = (args, util) => {
      const t = util.target;
      t._stretch = [Number(args.X) / 100, Number(args.Y) / 100];
      if (t.renderer) {
        const { direction, scale } = t._getRenderedDirectionAndScale();
        t.renderer.updateDrawableDirectionScale(t.drawableID, direction, scale);
      }
    };
    prim.jgRuntime_setStageSize = () => {};
    prim.jgRuntime_setMaxFrameRate = () => {};
    vm.runtime.currentStepTime = 1000 / 30;
    window.__t = 0;                                  // deterministic project timer (ms)
    const pt = vm.runtime.ioDevices.clock._projectTimer;
    pt.nowObj = { now: () => window.__t };
    pt.start();

    // ---- stand-in for the Iris Text extension (renders the string onto the sprite's own skin with a 2D canvas)
    const IR = 'g1nxIrisText_';
    const st = (t) => (t.__iris = t.__iris || { size: 32, color: '#9966ff', maxw: null, lh: 1.2, text: '', w: 0, h: 0, skin: null, dirty: true, on: false });
    const P = vm.runtime._primitives;
    const unesc = (s) => s.replace(/\\\\([\[\]])/g, '$1');
    P[IR + 'setText'] = (a, u) => { const s = st(u.target); const t = String(a.TEXT); if (s.text !== t) { s.text = t; s.dirty = true; } s.on = true; };
    P[IR + 'setBaseColor'] = (a, u) => { const s = st(u.target); const c = String(a.COLOR); if (s.color !== c) { s.color = c; s.dirty = true; } };
    P[IR + 'setBaseSize'] = (a, u) => { const s = st(u.target); const z = Math.max(1, Number(a.SIZE)); if (s.size !== z) { s.size = z; s.dirty = true; } };
    P[IR + 'setAlign'] = () => {};
    P[IR + 'setMaxWidth'] = (a, u) => { const s = st(u.target); const w = Number(a.WIDTH); if (s.maxw !== w) { s.maxw = w; s.dirty = true; } };
    P[IR + 'clearMaxDimensions'] = (a, u) => { const s = st(u.target); if (s.maxw !== null) { s.maxw = null; s.dirty = true; } };
    P[IR + 'setLineHeight'] = (a, u) => { const s = st(u.target); const l = Number(a.HEIGHT); if (s.lh !== l) { s.lh = l; s.dirty = true; } };
    P[IR + 'clearText'] = (a, u) => {
      const t = u.target, s = st(t); s.on = false; s.text = ''; s.dirty = true;
      const c = t.getCostumes()[t.currentCostume]; if (c && t.renderer) t.renderer.updateDrawableSkinId(t.drawableID, c.skinId);
    };
    P[IR + 'getExactTextWidth'] = (a, u) => st(u.target).w;
    P[IR + 'getExactTextHeight'] = (a, u) => st(u.target).h;
    P[IR + 'renderNow'] = (a, u) => {
      const t = u.target, s = st(t);
      if (!s.on || !s.dirty) return;
      s.dirty = false;
      let raw = s.text, bold = false;
      if (raw.startsWith('[b]') && raw.endsWith('[/b]')) { bold = true; raw = raw.slice(3, -4); }
      const text = unesc(raw);
      const cv = document.createElement('canvas'); const ctx = cv.getContext('2d');
      const font = `${bold ? '600 ' : '500 '}${s.size}px Inter, "Helvetica Neue", Arial, sans-serif`;
      ctx.font = font;
      const lines = [];
      for (const para of text.split('\n')) {
        if (!s.maxw) { lines.push(para); continue; }
        let cur = '';
        for (const word of para.split(/(?<=[ ])/)) {
          if (ctx.measureText(cur + word).width > s.maxw && cur) { lines.push(cur); cur = word; } else cur += word;
        }
        lines.push(cur);
      }
      const lh = s.size * s.lh;
      s.w = Math.max(1, Math.ceil(Math.max(...lines.map(l => ctx.measureText(l).width))));
      s.h = Math.max(1, Math.ceil(lh * lines.length));
      const RES = 2;
      cv.width = s.w * RES; cv.height = s.h * RES;
      const c2 = cv.getContext('2d'); c2.scale(RES, RES); c2.font = font; c2.fillStyle = s.color; c2.textBaseline = 'middle';
      lines.forEach((l, i) => c2.fillText(l, 0, lh * (i + 0.5)));
      if (t.renderer) {
        const old = s.skin;
        s.skin = t.renderer.createBitmapSkin(cv, RES, [s.w / 2, s.h / 2]);
        t.renderer.updateDrawableSkinId(t.drawableID, s.skin);
        if (old !== null) t.renderer.destroySkin(old);
      }
    };

    window.vm = vm; window.renderer = renderer;
    window.errors = [];
    return null;
  }, b64);
  if (err) throw new Error(err);

  const api = {
    page, browser,
    async flag() {
      await page.evaluate(() => vm.greenFlag());
      if (!opts.gesture) { await api.frames(3); await api.setVar('navmode', 0); }   // older suites use the 3 buttons
    },
    async frames(n = 1) {
      await page.evaluate(([n, fps]) => {
        for (let i = 0; i < n; i++) { window.__t += 1000 / fps; vm.runtime._step(); }
        renderer.draw();
      }, [n, opts.fps || 30]);
    },
    // UI coords (0..640, 0..360, y down) -> scratch io state
    async mouse(x, y, down) {
      await page.evaluate(([x, y, down]) => {
        const m = vm.runtime.ioDevices.mouse;
        m._scratchX = Math.round(x - 320); m._scratchY = Math.round(180 - y);
        m._clientX = x; m._clientY = y; m._isDown = !!down;
      }, [x, y, down]);
    },
    async click(x, y, hold = 2) {
      await api.mouse(x, y, false); await api.frames(1);
      await api.mouse(x, y, true); await api.frames(hold);
      await api.mouse(x, y, false); await api.frames(2);
    },
    async drag(x0, y0, x1, y1, steps = 8) {
      await api.mouse(x0, y0, false); await api.frames(1);
      await api.mouse(x0, y0, true); await api.frames(1);
      for (let i = 1; i <= steps; i++) {
        await api.mouse(x0 + (x1 - x0) * i / steps, y0 + (y1 - y0) * i / steps, true); await api.frames(1);
      }
      await api.mouse(x1, y1, false); await api.frames(2);
    },
    async key(k, down) { await page.evaluate(([k, d]) => vm.postIOData('keyboard', { key: k, isDown: d }), [k, down]); },
    async getVar(name) {
      return page.evaluate((name) => {
        const st = vm.runtime.getTargetForStage();
        const v = Object.values(st.variables).find(v => v.name === name);
        const num = x => (typeof x === 'string' && x.trim() !== '' && !isNaN(Number(x))) ? Number(x) : x;
        return v ? (v.type === 'list' ? v.value.map(num) : num(v.value)) : undefined;
      }, name);
    },
    async setVar(name, val) {
      await page.evaluate(([name, val]) => {
        const st = vm.runtime.getTargetForStage();
        Object.values(st.variables).find(v => v.name === name).value = val;
      }, [name, val]);
    },
    async shot(file) {
      const url = await page.evaluate(() => new Promise(res => {
        renderer.requestSnapshot(res); renderer.draw();
      }));
      fs.writeFileSync(file, Buffer.from(url.split(',')[1], 'base64'));
    },
    async store() { return page.evaluate(() => window.__store); },
    async close() { await browser.close(); }
  };
  return api;
}

module.exports = { open };
