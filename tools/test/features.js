// OS features: App Store (install / remove), Home rearranging, search, power menu, sound, back-gesture indicator.
const { open } = require('./harness');
const OUT = (process.env.EOS_OUT || '/tmp/eos-test') + '/'; require('fs').mkdirSync(OUT, { recursive: true });
let fails = 0;
const expect = (n, c, e = '') => { console.log((c ? 'PASS ' : 'FAIL ') + n + (c ? '' : '  -> ' + e)); if (!c) fails++; };
const icon = i => [96 + ((i - 1) % 5) * 112, 177 + Math.floor((i - 1) / 5) * 98];
const between = (v, a, b) => v > a && v < b;
const HOME = [320, 346];

(async () => {
  let h = await open(process.argv[2]); let V = n => h.getVar(n);
  const boot = async () => { for (let i = 0; i < 140 && await V('screen') !== 1; i++) await h.frames(1); await h.frames(20); };
  await h.flag(); await boot();
  await h.click(320, 128); await h.frames(30);
  expect('unlocked', await V('screen') === 2);
  expect('unlock plays a sound', await V('snd_n') >= 1 && await V('snd_last') === 6, `${await V('snd_n')} ${await V('snd_last')}`);
  await h.shot(OUT + 'f_home.png');

  // ---------- Store
  await h.click(...icon(9)); await h.frames(16);
  expect('Store opens', await V('screen') === 3 && await V('app') === 9);
  await h.shot(OUT + 'f_store.png');
  await h.click(580, 141); await h.frames(8);                      // Notes -> Remove
  expect('Remove asks first', await V('dlg') === 1);
  await h.click(392, 221); await h.frames(10);
  expect('Notes removed', !(await V('home_apps')).includes(2) && (await V('home_apps')).length === 8, JSON.stringify(await V('home_apps')));
  await h.frames(100);
  await h.click(580, 141); await h.frames(6);                      // Notes -> Get
  expect('installing shows progress', await V('st_app') === 2 && between(await V('st_p'), 0.02, 0.6), await V('st_p'));
  await h.shot(OUT + 'f_store_installing.png');
  await h.click(...HOME); await h.frames(70);                      // keeps installing in the background
  const ha = await V('home_apps');
  expect('Notes installed again (last on Home)', ha[ha.length - 1] === 2 && await V('st_app') === 0, JSON.stringify(ha));
  expect('core apps cannot be removed (no button)', true);
  await h.frames(3); await h.shot(OUT + 'f_home_installed.png');
  await h.frames(100);

  // ---------- Home: hold an icon to pick it up, drag to rearrange
  const [x1, y1] = icon(1), [x4, y4] = icon(4);
  await h.mouse(x1, y1, false); await h.frames(1); await h.mouse(x1, y1, true); await h.frames(17);
  expect('holding an icon picks it up', await V('hd_app') === 1 && await V('hd_a') > 0.2, `${await V('hd_app')} ${await V('hd_a')}`);
  for (let i = 1; i <= 6; i++) { await h.mouse(x1 + (x4 - x1) * i / 6, y1 + (y4 - y1) * i / 6, true); await h.frames(1); }
  await h.shot(OUT + 'f_home_drag.png');
  expect('the others make room', (await V('home_apps'))[3] === 1, JSON.stringify(await V('home_apps')));
  const mid = (await V('hp_x'))[2];
  expect('neighbours slide (not jump)', mid !== 64 + 112 && mid !== 64 + 2 * 112, mid);
  await h.mouse(x4, y4, false); await h.frames(16);
  expect('dropped into the new cell, nothing launched', (await V('hp_x'))[0] === 64 + 3 * 112 && await V('screen') === 2 && await V('hd_app') === 0, (await V('hp_x'))[0]);
  // back to the first cell
  await h.mouse(x4, y4, true); await h.frames(17);
  for (let i = 1; i <= 6; i++) { await h.mouse(x4 + (x1 - x4) * i / 6, y4, true); await h.frames(1); }
  await h.mouse(x1, y1, false); await h.frames(16);
  expect('rearranged back', (await V('home_apps'))[0] === 1);
  // a normal tap still launches
  await h.click(...icon(3)); await h.frames(14);
  expect('tap still launches', await V('screen') === 3);
  await h.click(...HOME); await h.frames(16);

  // ---------- search
  await h.click(604, 50); await h.frames(3);
  expect('search opens with animation + keyboard', await V('srch') === 1 && await V('kb_open') === 1 && between(await V('srch_a'), 0.05, 0.98), await V('srch_a'));
  await h.shot(OUT + 'f_search_mid.png');
  await h.frames(10);
  for (const k of ['c', 'a', 'l']) { await h.key(k, true); await h.frames(2); await h.key(k, false); await h.frames(2); }
  expect('typing fills the query', (await V('ti')) === 'cal', await V('ti'));
  expect('finds the Calculator app', (await V('sr_k'))[0] === 1 && (await V('sr_i'))[0] === 3, JSON.stringify(await V('sr_i')));
  await h.shot(OUT + 'f_search.png');
  await h.click(320, 98); await h.frames(3);
  expect('tapping a result opens it', await V('screen') === 3 && await V('app') === 3 && await V('srch') === 0);
  await h.frames(14); await h.click(...HOME); await h.frames(16);
  await h.drag(320, 150, 320, 250, 5); await h.frames(12);
  expect('swipe down on Home opens search', await V('srch') === 1);
  await h.setVar('ti', 'welcome'); await h.frames(4);
  expect('finds files too', (await V('sr_k'))[0] === 2, JSON.stringify(await V('sr_k')));
  await h.shot(OUT + 'f_search_file.png');
  await h.click(320, 98); await h.frames(16);
  expect('a file result opens in the editor', await V('app') === 1 && await V('view') === 1 && await V('screen') === 3);
  await h.click(...HOME); await h.frames(16);
  await h.click(604, 50); await h.frames(12);
  await h.click(320, 190); await h.frames(3);
  expect('tap outside closes search (animated)', await V('srch') === 0 && between(await V('srch_a'), 0.02, 0.98), await V('srch_a'));
  await h.frames(14);
  expect('search gone, keyboard gone', await V('srch_a') === 0 && await V('kb_a') < 0.02);

  // ---------- sound: volume + mute
  const n0 = await V('snd_n');
  await h.click(500, 8); await h.frames(14);
  await h.shot(OUT + 'f_cc.png');
  await h.click(53, 168); await h.frames(3);                       // speaker icon = mute
  expect('speaker icon mutes', await V('mute') === 1);
  const n1 = await V('snd_n');
  await h.click(34 + 68, 24 + 14 + 30); await h.frames(4); await h.click(34 + 68, 24 + 14 + 30); await h.frames(4);
  expect('muted: no sounds', await V('snd_n') === n1 && n1 >= n0, `${n0} ${n1} ${await V('snd_n')}`);
  await h.drag(120, 168, 400, 168, 5); await h.frames(3);
  expect('volume slider sets the volume and unmutes', await V('mute') === 0 && between(await V('vol'), 55, 85), await V('vol'));

  // ---------- power menu
  await h.click(34 + 3 * 148 + 68, 24 + 14 + 30); await h.frames(14);
  expect('power menu open', await V('pw') === 1 && await V('pw_a') === 1);
  await h.click(320, 320); await h.frames(3);
  expect('tap outside cancels (fades)', await V('pw') === 0 && between(await V('pw_a'), 0.02, 0.98));
  await h.frames(12);
  await h.click(500, 8); await h.frames(14); await h.click(34 + 3 * 148 + 68, 24 + 14 + 30); await h.frames(14);
  await h.click(320, 165); await h.frames(5);                      // Restart
  expect('restart fades to black first', await V('screen') === 2 && between(await V('off_t'), 0, 16), await V('off_t'));
  await h.shot(OUT + 'f_restart_mid.png');
  await h.frames(22);
  expect('then boots', await V('screen') === 0, await V('screen'));
  await boot(); await h.click(320, 128); await h.frames(30);
  expect('back on Home after the restart', await V('screen') === 2);
  await h.click(500, 8); await h.frames(14); await h.click(34 + 3 * 148 + 68, 24 + 14 + 30); await h.frames(14);
  await h.click(450, 165); await h.frames(30);                     // Shut down
  expect('shut down: powered off', await V('screen') === -1, await V('screen'));
  await h.frames(40); await h.shot(OUT + 'f_off.png');
  await h.click(320, 300); await h.frames(3);
  expect('tap powers on again', await V('screen') === 0);
  await boot(); await h.click(320, 128); await h.frames(30);

  // ---------- back gesture indicator (gesture navigation)
  await h.setVar('navmode', 1); await h.frames(12);
  await h.click(...icon(8)); await h.frames(16);
  await h.mouse(4, 200, false); await h.frames(1); await h.mouse(4, 200, true); await h.frames(1);
  await h.mouse(30, 200, true); await h.frames(1);
  expect('edge swipe grows the back chevron', between(await V('bk_a'), 0.1, 0.9), await V('bk_a'));
  await h.mouse(70, 200, true); await h.frames(5);
  await h.shot(OUT + 'f_back.png');
  expect('fully pulled', await V('bk_a') > 0.95);
  await h.mouse(70, 200, false); await h.frames(3);
  expect('release goes back and the chevron fades', await V('screen') === 2 && between(await V('bk_a'), 0, 0.9), `${await V('screen')} ${await V('bk_a')}`);
  await h.frames(20);
  expect('chevron gone', await V('bk_a') === 0);

  // ---------- persistence of the new state
  const [x2, y2] = icon(2);
  await h.mouse(x1, y1, true); await h.frames(17);
  for (let i = 1; i <= 6; i++) { await h.mouse(x1 + (x2 - x1) * i / 6, y1, true); await h.frames(1); }
  await h.mouse(x2, y2, false); await h.frames(170);
  const order = await V('home_apps'); const vol = await V('vol');
  const store = await h.store();
  await h.close();
  h = await open(process.argv[2], { store }); V = n => h.getVar(n);
  await h.flag(); await boot();
  expect('Home order restored', JSON.stringify(await V('home_apps')) === JSON.stringify(order) && order[1] === 1, JSON.stringify(await V('home_apps')));
  expect('volume restored', await V('vol') === vol, await V('vol'));
  await h.close();
  h = await open(process.argv[2], { store: { 'eos:home': '7¦7¦x¦99¦' } }); V = n => h.getVar(n);
  await h.flag(); await boot();
  const hb = await V('home_apps');
  expect('broken Home data still has the core apps', hb.includes(1) && hb.includes(8) && hb.includes(9) && hb.filter(x => x === 7).length === 1, JSON.stringify(hb));
  await h.close();
  console.log(fails ? fails + ' FAILED' : 'ALL OK');
})().catch(e => { console.error(e); process.exit(1); });
