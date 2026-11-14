const { open } = require('./harness');
const OUT = (process.env.EOS_OUT || '/tmp/eos-test') + '/'; require('fs').mkdirSync(OUT, { recursive: true });
let fails = 0;
const expect = (n, c, e = '') => { console.log((c ? 'PASS ' : 'FAIL ') + n + (c ? '' : '  -> ' + e)); if (!c) fails++; };
const icon = i => [96 + ((i - 1) % 5) * 112, 177 + Math.floor((i - 1) / 5) * 98];
(async () => {
  const h = await open(process.argv[2], { gesture: true }); const V = n => h.getVar(n);
  await h.flag(); await h.frames(80); await h.click(320, 200); await h.frames(3);
  for (const i of [1, 3, 4]) { await h.click(...icon(i)); await h.frames(14); await h.drag(320, 350, 320, 140, 6); await h.frames(16); }
  await h.click(...icon(3)); await h.frames(14);
  const rec0 = await V('rec');
  console.log('rec', JSON.stringify(rec0), 'app', await V('app'));
  // ---- sideways swipe on the bar = previous / next app
  await h.drag(320, 352, 470, 350, 8); await h.frames(2);
  expect('swipe right on the bar -> previous app', await V('app') === rec0[rec0.indexOf(3) - 1] && await V('screen') === 3, `${await V('app')}`);
  expect('old app slides out on the closing layer', await V('cl_on') === 1 && await V('cl_mode') === 1);
  await h.shot(OUT + 'n_switch_mid.png');
  await h.frames(16);
  expect('recents order is not shuffled by switching', JSON.stringify(await V('rec')) === JSON.stringify(rec0), JSON.stringify(await V('rec')));
  expect('switched app fully open', await V('open_t') >= 10 && await V('cl_on') === 0);
  await h.drag(320, 352, 170, 350, 8); await h.frames(18);
  expect('swipe left -> back to the newer app', await V('app') === 3, await V('app'));
  await h.drag(320, 352, 170, 350, 8); await h.frames(18);
  expect('swipe left at the newest app: springs back, stays', await V('app') === 3 && await V('screen') === 3 && await V('gmode') === 0, `${await V('app')} ${await V('gmode')}`);
  // ---- customisation is applied
  await h.setVar('nav_swipe', 0);
  const before = await V('app');
  await h.drag(320, 352, 470, 350, 8); await h.frames(18);
  expect('sideways switch can be disabled', await V('app') === before);
  await h.setVar('nav_swipe', 1);
  await h.setVar('nav_edge', 0); await h.drag(4, 200, 120, 200, 6); await h.frames(4);
  expect('edge-swipe back can be disabled', await V('screen') === 3 && await V('gtype') === 0);
  await h.setVar('nav_edge', 1);
  await h.setVar('nav_close', 50);
  await h.drag(320, 350, 320, 230, 6); await h.frames(3);
  expect('close distance is configurable (50% -> y 230 does not close)', await V('screen') === 3, await V('screen'));
  await h.frames(12);
  await h.setVar('nav_close', 74);
  await h.setVar('nav_col', 3); await h.setVar('nav_barw', 180); await h.setVar('nav_barh', 8); await h.frames(2);
  await h.shot(OUT + 'n_bar_custom.png');
  await h.setVar('nav_tap', 1);
  await h.click(320, 350); await h.frames(3);
  expect('tap on bar -> lock (configurable action)', await V('screen') === 1, await V('screen'));
  await h.setVar('nav_tap', 0); await h.click(320, 200); await h.frames(3);
  // ---- settings page
  await h.click(...icon(8)); await h.frames(14);
  await h.setVar('view', 2); await h.setVar('scroll', 0); await h.frames(3);
  await h.shot(OUT + 'n_settings_nav.png');
  await h.click(300, 160);
  await h.frames(2);
  console.log('nav_col after click', await V('nav_col'));
  // ---- app switcher: hold -> centre card + neighbours, release -> same layout, scroll, tap, swipe-up dismiss
  await h.drag(320, 350, 320, 140, 6); await h.frames(16);
  await h.click(...icon(4)); await h.frames(14);
  await h.mouse(320, 350, false); await h.frames(1); await h.mouse(320, 350, true); await h.frames(1);
  await h.mouse(320, 250, true); await h.frames(2); await h.mouse(320, 220, true); await h.frames(26);
  expect('hold -> the app becomes the centre card', await V('g_rec') === 1 && Math.abs((await V('ga_cx')) - 320) < 6 && Math.abs((await V('ga_s')) - 230 / 640) < 0.03, `${await V('ga_s')} ${await V('ga_cx')}`);
  await h.shot(OUT + 'n_hold.png');
  await h.mouse(320, 220, false); await h.frames(14);
  expect('release -> Recents with the same app focused', await V('screen') === 4 && await V('sw_focus') === 4, `${await V('screen')} ${await V('sw_focus')}`);
  await h.shot(OUT + 'n_released.png');
  const n0 = (await V('rec')).length;
  await h.drag(320, 170, 520, 170, 8); await h.frames(18);
  expect('drag scrolls to older apps and snaps', Math.abs((await V('sw_off')) + 250) < 3, await V('sw_off'));
  await h.drag(320, 190, 320, 80, 8); await h.frames(24);
  expect('swipe a card up dismisses it', (await V('rec')).length === n0 - 1, JSON.stringify(await V('rec')));
  await h.click(320, 346 - 0); await h.frames(1);
  await h.drag(320, 350, 320, 140, 6); await h.frames(16);
  await h.click(...icon(3)); await h.frames(14);
  await h.close();
  // ---- persistence of the new fields
  const h2 = await open(process.argv[2], { gesture: true });
  await h2.flag(); await h2.frames(80);
  await h2.setVar('nav_col', 4); await h2.setVar('nav_barw', 150); await h2.setVar('nav_tap', 2); await h2.setVar('nav_close', 60); await h2.setVar('nav_swipe', 0);
  await h2.click(320, 200); await h2.frames(3); await h2.click(320, 350); await h2.frames(160);
  const store = await h2.store(); await h2.close();
  const h3 = await open(process.argv[2], { gesture: true, store });
  await h3.flag(); await h3.frames(80);
  expect('navigation settings persist', await h3.getVar('nav_col') === 4 && await h3.getVar('nav_barw') === 150 && await h3.getVar('nav_tap') === 2 && await h3.getVar('nav_close') === 60 && await h3.getVar('nav_swipe') === 0,
    JSON.stringify([await h3.getVar('nav_col'), await h3.getVar('nav_barw'), await h3.getVar('nav_tap')]));
  await h3.close();
  console.log(fails ? fails + ' FAILED' : 'ALL OK');
})().catch(e => { console.error(e); process.exit(1); });
