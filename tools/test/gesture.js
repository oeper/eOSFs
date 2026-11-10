const { open } = require('./harness');
const OUT = (process.env.EOS_OUT || '/tmp/eos-test') + '/'; require('fs').mkdirSync(OUT, { recursive: true });
let fails = 0;
const expect = (n, c, e = '') => { console.log((c ? 'PASS ' : 'FAIL ') + n + (c ? '' : '  -> ' + e)); if (!c) fails++; };
const icon = i => [125 + ((i - 1) % 4) * 130, 177 + Math.floor((i - 1) / 4) * 98];
(async () => {
  const h = await open(process.argv[2], { gesture: true }); const V = n => h.getVar(n);
  await h.flag(); await h.frames(80);
  expect('gesture bar is the default', await V('navmode') === 1);
  await h.click(320, 200); await h.frames(3);
  await h.shot(OUT + 'g_home.png');
  // ---- open animation
  await h.click(...icon(3)); await h.frames(4);
  await h.shot(OUT + 'g_open_mid.png');
  expect('opening: app is scaled down', (await V('gs')) < 1 || (await V('open_t')) < 10 );
  await h.frames(12);
  expect('app open, scale back to 1', await V('screen') === 3 && await V('gs') === 1 && await V('open_t') >= 10);
  await h.shot(OUT + 'g_app.png');
  // ---- drag bar up: app shrinks and follows the finger
  await h.mouse(320, 350, false); await h.frames(1);
  await h.mouse(320, 350, true); await h.frames(1);
  for (let i = 1; i <= 6; i++) { await h.mouse(320 + i * 8, 350 - i * 22, true); await h.frames(1); }
  expect('dragging: gmode 1 and app shrunk', await V('gmode') === 1 && await V('ga_s') < 0.8, `${await V('gmode')} ${await V('ga_s')}`);
  await h.shot(OUT + 'g_drag.png');
  const s1 = await V('ga_s'), cx1 = await V('ga_cx');
  await h.mouse(368, 150, true); await h.frames(1);
  expect('further up = smaller', await V('ga_s') < s1);
  expect('card follows finger horizontally', Math.abs((await V('ga_cx')) - (320 + 48)) < 10, await V('ga_cx'));
  await h.shot(OUT + 'g_drag2.png');
  // release high -> closes into icon
  await h.mouse(368, 150, false); await h.frames(2);
  expect('release high: Home is reached at once, card keeps morphing', await V('screen') === 2 && await V('cl_on') === 1, `${await V('screen')} ${await V('cl_on')}`);
  await h.frames(3); await h.shot(OUT + 'g_close_mid.png');
  await h.frames(2); await h.shot(OUT + 'g_close_mid2.png');
  await h.frames(12);
  expect('closing layer finished', await V('cl_on') === 0 && await V('gmode') === 0 && await V('gs') === 1, `${await V('cl_on')} ${await V('gmode')}`);
  expect('closed app stays in recents', (await V('rec')).includes(3));
  // ---- open another app while one is still closing
  await h.click(...icon(3)); await h.frames(14);
  await h.drag(320, 350, 320, 140, 6); await h.frames(1);
  expect('closing started', await V('cl_on') === 1 && await V('screen') === 2);
  await h.click(...icon(4)); await h.frames(2);
  expect('another app opens while the first is closing', await V('app') === 4 && await V('screen') === 3 && await V('cl_on') === 1, `${await V('app')} ${await V('screen')} ${await V('cl_on')}`);
  await h.shot(OUT + 'g_overlap.png');
  await h.frames(16);
  expect('both animations finish', await V('cl_on') === 0 && await V('open_t') >= 10 && await V('screen') === 3);
  // ---- close an app while it is still opening
  await h.click(320, 10); await h.frames(1); await h.click(320, 300); await h.frames(2);
  await h.mouse(0, 0, false);
  await h.click(...[320, 346]); await h.frames(14);
  await h.drag(320, 350, 320, 140, 6); await h.frames(16);
  expect('back home', await V('screen') === 2);
  await h.click(...icon(2)); await h.frames(3);
  expect('opening in progress', await V('open_t') < 10 && await V('screen') === 3);
  await h.drag(320, 350, 320, 140, 4); await h.frames(1);
  expect('can close while still opening', await V('screen') === 2 && await V('cl_on') === 1, `${await V('screen')} ${await V('cl_on')}`);
  await h.frames(16);
  await h.click(320, 346); await h.frames(1);   // a tap right before a gesture must not block it
  // ---- swipe halfway and hold -> other open apps appear; release -> app switcher
  await h.click(...icon(2)); await h.frames(14);
  await h.mouse(320, 350, false); await h.frames(1); await h.mouse(320, 350, true); await h.frames(1);
  await h.mouse(320, 250, true); await h.frames(2); await h.mouse(320, 220, true); await h.frames(12);
  expect('holding halfway shows the switcher preview', await V('g_rec') === 1 && await V('gmode') === 1, `${await V('g_rec')} ${await V('gmode')}`);
  await h.shot(OUT + 'g_hold.png');
  await h.mouse(320, 220, false); await h.frames(3);
  expect('release after hold opens recents', await V('screen') === 4, await V('screen'));
  await h.click(320, 300); await h.frames(1);
  await h.drag(320, 350, 320, 220, 6); await h.frames(3);
  expect('swipe up in recents -> home', await V('screen') === 2, await V('screen'));
  // ---- re-open an app that is still closing: continues from its current window (no jump to the icon)
  await h.click(...icon(3)); await h.frames(14);
  await h.drag(320, 350, 320, 140, 6); await h.frames(3);
  const cw = await V('cl_cw');
  expect('closing window is mid-size', cw > 62 && cw < 640 && await V('cl_on') === 1, cw);
  await h.click(...icon(3)); await h.frames(1);
  expect('re-open starts from the closing window size', Math.abs((await V('cur_w')) - cw) < 120 && await V('cur_w') > 90, `${await V('cur_w')} vs ${cw}`);
  await h.frames(16);
  expect('re-opened fully', await V('screen') === 3 && await V('open_t') >= 10 && await V('cur_w') === 640);
  // ---- grabbing the bar mid-opening continues from the opening size (no jump)
  await h.drag(320, 350, 320, 140, 6); await h.frames(16);
  await h.click(...icon(3)); await h.frames(3);
  await h.mouse(320, 350, false); await h.frames(1);
  const ow = await V('cur_w');
  await h.mouse(320, 350, true); await h.frames(1);
  const gw = (await V('ga_s')) * 640;
  expect('grab continues from current size (eases, no jump)', gw >= ow - 5 && gw <= (ow + 614) / 2 + 40, `${gw} vs ${ow}`);
  await h.mouse(320, 350, false); await h.frames(20);
  // ---- drag a little and release low -> snaps back
  await h.click(...icon(3)); await h.frames(14);
  await h.mouse(320, 350, false); await h.frames(1);
  await h.mouse(320, 350, true); await h.frames(1);
  await h.mouse(320, 300, true); await h.frames(1); await h.mouse(320, 296, true); await h.frames(1);
  expect('small drag shrinks a bit', await V('gmode') === 1 && await V('ga_s') < 1);
  await h.mouse(320, 296, false); await h.frames(2);
  expect('release low snaps back', await V('gmode') === 3);
  await h.frames(10);
  expect('snap back finished, still in app', await V('screen') === 3 && await V('gmode') === 0 && await V('gs') === 1);
  // plain tap on the bar does nothing
  await h.click(320, 350); await h.frames(3);
  expect('tap on bar is harmless', await V('screen') === 3 && await V('gmode') === 0);
  // calculator still works after the transitions (input not stuck)
  await h.click(182, 149.5); await h.frames(1);        // C
  await h.click(182, 149.5 + 36); await h.frames(2);   // '7'
  expect('app responds after gesture', await V('calc_d') == 7, await V('calc_d'));
  // ---- edge swipe back (Files -> subfolder -> swipe -> parent)
  await h.drag(320, 350, 320, 140, 8); await h.frames(20);
  expect('closed again', await V('screen') === 2);
  await h.click(...icon(1)); await h.frames(14);
  await h.click(300, 82); await h.frames(3);
  expect('entered Documents', await V('f_dir') === 2);
  await h.drag(4, 200, 120, 200, 6); await h.frames(3);
  expect('edge swipe = back (up a folder)', await V('f_dir') === 1 && await V('screen') === 3, `${await V('f_dir')} ${await V('screen')}`);
  await h.drag(636, 200, 520, 200, 6); await h.frames(25);
  expect('edge swipe from the right at root closes app (animated)', await V('screen') === 2, await V('screen'));
  // ---- home: swipe up -> recents, swipe up in recents -> home
  await h.drag(320, 350, 320, 220, 6); await h.frames(3);
  expect('home swipe up opens recents', await V('screen') === 4);
  await h.shot(OUT + 'g_recents.png');
  await h.drag(320, 350, 320, 220, 6); await h.frames(3);
  expect('recents swipe up goes home', await V('screen') === 2);
  // ---- gesture closes keyboard + app (terminal)
  await h.click(...icon(5)); await h.frames(14);
  expect('terminal keyboard open', await V('kb_open') === 1);
  await h.drag(320, 350, 320, 120, 8); await h.frames(20);
  expect('gesture from keyboard screen closes app', await V('screen') === 2 && await V('kb_open') === 0);
  // ---- dark mode + paint (stroke replay must scale too)
  await h.click(...icon(6)); await h.frames(14);
  await h.drag(150, 150, 400, 250, 12);
  await h.mouse(320, 350, false); await h.frames(1); await h.mouse(320, 350, true); await h.frames(1);
  for (let i = 1; i <= 5; i++) { await h.mouse(320, 350 - i * 25, true); await h.frames(1); }
  await h.shot(OUT + 'g_paint_drag.png');
  await h.mouse(320, 225, false); await h.frames(20);
  // ---- settings switch to 3 buttons and back
  await h.click(...icon(8)); await h.frames(14);
  await h.drag(300, 280, 300, 60, 6); await h.frames(2);
  await h.shot(OUT + 'g_settings_nav.png');
  await h.setVar('scroll', 150); await h.frames(2);
  await h.shot(OUT + 'g_settings_nav2.png');
  console.log('threads alive', await h.page.evaluate(() => vm.runtime.threads.length));
  await h.close(); console.log(fails ? fails + ' FAILED' : 'ALL OK');
})().catch(e => { console.error(e); process.exit(1); });
