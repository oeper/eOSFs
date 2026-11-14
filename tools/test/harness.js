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

    // ---- stand-in for the Iris Text extension, mirroring the real extension's behaviour (read from its source):
    //  * default font is "Handwriting"; text box = max(text width, max width) with the text aligned inside it;
    //    the sprite sits on the box centre (x) and, with "grow downward only", on the centre of the first line (y)
    //  * setters only mark the text dirty; painting happens before the next draw - or, while the glyph worker is on
    //    (default), a few draws later (asynchronous) -> a changed text flickers unless the worker is switched off
    //  * `refresh text` returns a promise (a script using it resumes later!)
    const IR = 'g1nxIrisText_';
    const iris = window.__iris = { worker: true, paints: 0, promiseCalls: 0 };
    const FONTS = { 'Sans Serif': 'Inter, "Helvetica Neue", Arial, sans-serif', 'Handwriting': '"Comic Sans MS", "Segoe Script", cursive', 'Serif': 'serif' };
    const st = (t) => (t.__iris = t.__iris || { size: 32, color: '#9966ff', font: 'Handwriting', align: 'center', maxw: null, lh: 1.2, grow: false,
      text: '', w: 0, h: 0, skin: null, dirty: true, on: false, layoutOk: false, delay: 0, lines: [], bold: false });
    const P = vm.runtime._primitives;
    const dirtyAll = new Set();
    const mark = (t, s) => { s.dirty = true; s.layoutOk = false; s.delay = iris.worker ? 3 : 0; dirtyAll.add(t); };
    const setter = (field, conv) => (a, u) => { const s = st(u.target); const v = conv(a); if (s[field] !== v) { s[field] = v; mark(u.target, s); } };
    P[IR + 'setText'] = (a, u) => { const s = st(u.target); const t = String(a.TEXT); if (s.text !== t || !s.on) { s.text = t; s.on = true; mark(u.target, s); } };
    P[IR + 'setBaseColor'] = setter('color', a => String(a.COLOR));
    P[IR + 'setBaseSize'] = setter('size', a => Math.max(1, Number(a.SIZE)));
    P[IR + 'setFont'] = setter('font', a => String(a.FONT));
    P[IR + 'setAlign'] = setter('align', a => String(a.ALIGN).toLowerCase());
    P[IR + 'setMaxWidth'] = setter('maxw', a => Number(a.WIDTH));
    P[IR + 'clearMaxDimensions'] = setter('maxw', () => null);
    P[IR + 'setLineHeight'] = setter('lh', a => Number(a.HEIGHT));
    P[IR + 'setGrowDownwardOnly'] = setter('grow', a => String(a.ENABLED).toLowerCase() === 'on');
    P[IR + 'setGlyphWorkerEnabledBlock'] = (a) => { iris.worker = String(a.ENABLED) === 'on'; };
    P[IR + 'clearText'] = (a, u) => {
      const t = u.target, s = st(t); s.on = false; s.text = ''; dirtyAll.delete(t);
      const c = t.getCostumes()[t.currentCostume]; if (c && t.renderer) t.renderer.updateDrawableSkinId(t.drawableID, c.skinId);
    };
    const mctx = document.createElement('canvas').getContext('2d');
    const layout = (s) => {
      if (s.layoutOk) return;
      let raw = s.text; s.bold = false; s.caret = null;
      const cm = raw.match(/\[color=([^\]]*)\]\|\[\/color\]$/);
      if (cm) { s.caret = cm[1]; raw = raw.slice(0, cm.index); }
      if (raw.startsWith('[b]')) { s.bold = true; raw = raw.replace('[b]', '').replace('[/b]', ''); }
      const text = raw.replace(/\\([\[\]])/g, '$1');
      s.fontCss = `${s.bold ? '600 ' : '500 '}${s.size}px ${FONTS[s.font] || s.font}`;
      mctx.font = s.fontCss;
      const lines = [];
      for (const para of text.split('\n')) {
        if (!s.maxw) { lines.push(para); continue; }
        let cur = '';
        for (const word of para.split(/(?<=[ ])/)) {
          if (mctx.measureText(cur + word).width > s.maxw && cur) { lines.push(cur); cur = word; } else cur += word;
        }
        lines.push(cur);
      }
      s.lines = lines;
      s.tw = Math.max(0, ...lines.map(l => mctx.measureText(l).width));
      s.lineH = s.size * s.lh;
      s.th = s.lineH * lines.length;
      s.layoutOk = true;
    };
    const paint = (t) => {
      const s = st(t); if (!s.on) return;
      layout(s); iris.paints++;
      const boxW = Math.max(1, Math.ceil(Math.max(s.maxw || 0, s.tw))), boxH = Math.max(1, Math.ceil(s.th));
      const RES = 2, cv = document.createElement('canvas'); cv.width = boxW * RES; cv.height = boxH * RES;
      const c = cv.getContext('2d'); c.scale(RES, RES); c.font = s.fontCss; c.textBaseline = 'middle';
      s.lines.forEach((l, i) => {
        const lw = c.measureText(l).width;
        const x = s.align === 'center' ? (boxW - lw) / 2 : s.align === 'right' ? boxW - lw : 0;
        c.fillStyle = s.color; c.fillText(l, x, s.lineH * (i + 0.5));
        if (s.caret && i === s.lines.length - 1 && !s.caret.startsWith('rgba')) { c.fillStyle = s.caret; c.fillRect(x + lw + 1, s.lineH * i + s.lineH * 0.15, 1.5, s.lineH * 0.7); }
      });
      const rc = [boxW / 2, s.grow ? s.lineH / 2 : boxH / 2];
      if (t.renderer) {
        const old = s.skin;
        s.skin = t.renderer.createBitmapSkin(cv, RES, rc);
        t.renderer.updateDrawableSkinId(t.drawableID, s.skin);
        if (old !== null) t.renderer.destroySkin(old);
      }
      s.dirty = false;
    };
    // paint pending texts right before each draw (the real extension hooks renderer.draw the same way)
    const origDraw = renderer.draw.bind(renderer);
    renderer.draw = function () {
      for (const t of Array.from(dirtyAll)) { const s = st(t); if (s.delay > 0) { s.delay--; continue; } dirtyAll.delete(t); if (s.on) paint(t); }
      return origDraw();
    };
    P[IR + 'getExactTextWidth'] = (a, u) => { const s = st(u.target); layout(s); return s.maxw ? Math.min(s.tw, s.maxw) : s.tw; };
    P[IR + 'getExactTextHeight'] = (a, u) => { const s = st(u.target); layout(s); return s.th; };
    P[IR + 'renderNow'] = () => { iris.promiseCalls++; return new Promise(res => setTimeout(res, 50)); };
    // ---- PenguinMod core blocks used by the sprite build
    P.operator_indexOfTextInText = (a) => { const f = String(a.TEXT1), s = String(a.TEXT2); return s.includes(f) ? s.indexOf(f) + 1 : 0; };
    P.operator_replaceAll = (a) => String(a.text).replaceAll(String(a.term), String(a.res));
    P.operator_getLettersFromIndexToIndexInTextFixed = (a) => String(a.TEXT).substring((Number(a.INDEX1) || 1) - 1, Number(a.INDEX2) || 1);
    P.jgRuntime_setMaxClones = () => {};

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
