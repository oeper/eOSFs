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
    const origLoad = vm.extensionManager.loadExtensionURL.bind(vm.extensionManager);
    vm.extensionManager.loadExtensionURL = (id) => (id.startsWith('jgRuntime') || id.includes('local-storage') || id === 'localstorage') ? Promise.resolve() : origLoad(id);   // PM-only / URL extensions
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
    window.vm = vm; window.renderer = renderer;
    window.errors = [];
    return null;
  }, b64);
  if (err) throw new Error(err);

  const api = {
    page, browser,
    async flag() { await page.evaluate(() => vm.greenFlag()); },
    async frames(n = 1) {
      await page.evaluate((n) => {
        for (let i = 0; i < n; i++) { vm.runtime._step(); }
        renderer.draw();
      }, n);
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
