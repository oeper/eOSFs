// Transitions must take time (nothing may pop in or out) - checks + mid-transition screenshots.
const { open } = require('./harness');
const OUT = (process.env.EOS_OUT || '/tmp/eos-test') + '/'; require('fs').mkdirSync(OUT, { recursive: true });
let fails = 0;
const expect = (n, c, e = '') => { console.log((c ? 'PASS ' : 'FAIL ') + n + (c ? '' : '  -> ' + e)); if (!c) fails++; };
const icon = i => [125 + ((i - 1) % 4) * 130, 177 + Math.floor((i - 1) / 4) * 98];
const between = (v, a, b) => v > a && v < b;

(async () => {
  const h = await open(process.argv[2], { gesture: true }); const V = n => h.getVar(n);
  await h.flag(); await h.frames(72);
  // ---- boot -> lock wakes from black
  await h.frames(2); await h.shot(OUT + 'a_lock_wake.png');
  expect('lock screen wakes in (pg_t mid)', await V('screen') === 1 && await V('pg_t') < 14, await V('pg_t'));
  await h.frames(20);
  // ---- unlock: lock face slides away over Home, icons rise in, bar fades in
  await h.click(320, 200, 1); await h.frames(3);
  expect('unlock: Home immediately, lock overlay animating', await V('screen') === 2 && between(await V('unl_t'), 0, 14), await V('unl_t'));
  expect('gesture bar fades in (not instantly there)', between(await V('bar_a'), 0.05, 0.95), await V('bar_a'));
  await h.shot(OUT + 'a_unlock_mid.png');
  await h.frames(30);
  expect('unlock finished', await V('unl_t') === 99 && await V('bar_a') > 0.97, `${await V('unl_t')} ${await V('bar_a')}`);
  // ---- PIN pad cross-fade
  await h.setVar('pin', '1234');
  await h.click(320, 10, 1); await h.frames(2);              // (status bar) - then lock via quick settings tile
  await h.setVar('qs_open', 0); await h.setVar('screen', 1); await h.frames(20);
  await h.click(320, 200, 1); await h.frames(3);
  expect('PIN pad fades in', between(await V('pin_a'), 0.05, 0.95), await V('pin_a'));
  await h.shot(OUT + 'a_pin_mid.png');
  await h.frames(12);
  const pad = d => { const k = d === 0 ? 11 : d; return [320 + ((k - 1) % 3 - 1) * 76, 128 + Math.floor((k - 1) / 3) * 46 + 19]; };
  for (const d of [9, 9, 9, 9]) await h.click(...pad(d), 1);
  await h.frames(2);
  expect('wrong PIN shakes the dots', between(await V('pin_sh'), 0, 12), await V('pin_sh'));
  await h.shot(OUT + 'a_pin_shake.png');
  await h.frames(14);
  for (const d of [1, 2, 3]) await h.click(...pad(d), 1);
  await h.click(...pad(4), 1); await h.frames(3);
  expect('PIN unlock -> Home with the pad animating away', await V('screen') === 2 && between(await V('unl_t'), 0, 14));
  await h.shot(OUT + 'a_pin_unlock_mid.png');
  await h.frames(30);
  expect('PIN state cleared after the animation', await V('pin_show') === 0 && (await V('pin_in')) === '');
  await h.setVar('pin', '');
  // ---- app switcher: entry dim fades in, exit fades out
  await h.click(...icon(3)); await h.frames(14);
  await h.drag(320, 350, 320, 140, 6); await h.frames(16);
  await h.click(...icon(4)); await h.frames(14);
  await h.drag(320, 350, 320, 140, 6); await h.frames(16);
  await h.drag(320, 350, 320, 230, 6); await h.frames(1);
  expect('switcher opens from Home', await V('screen') === 4);
  await h.frames(14);
  await h.drag(320, 350, 320, 230, 6); await h.frames(2);
  expect('leaving the switcher: cards fade out over Home', await V('screen') === 2 && between(await V('rx_t'), 0, 10), await V('rx_t'));
  await h.shot(OUT + 'a_switcher_exit.png');
  await h.frames(16);
  // open from switcher: the other cards fade, the tapped one grows
  await h.drag(320, 350, 320, 230, 6); await h.frames(16);
  await h.click(320, 170, 1); await h.frames(3);
  expect('opening from the switcher animates', await V('screen') === 3 && await V('open_t') < 10 && between(await V('rx_t'), 0, 10));
  await h.shot(OUT + 'a_switcher_open.png');
  await h.frames(16);
  // ---- status bar solidity cross-fades instead of popping
  expect('status bar solid in an app', await V('sb_a') > 0.95, await V('sb_a'));
  await h.mouse(320, 350, false); await h.frames(1); await h.mouse(320, 350, true); await h.frames(1);
  await h.mouse(320, 300, true); await h.frames(2);
  expect('status bar fades towards transparent while the app is pulled away', between(await V('sb_a'), 0.05, 0.95), await V('sb_a'));
  await h.mouse(320, 140, true); await h.frames(2); await h.mouse(320, 140, false); await h.frames(20);
  // ---- keyboard slides both ways, apps resize with it
  await h.click(...icon(2)); await h.frames(14);
  await h.click(528, 42, 1); await h.frames(2);
  expect('keyboard slides up', between(await V('kb_a'), 0.05, 0.95), await V('kb_a'));
  await h.frames(10);
  await h.drag(4, 200, 120, 200, 6); await h.frames(1);   // back = hide keyboard
  expect('keyboard slides down (still visible)', await V('kb_open') === 0 && between(await V('kb_a'), 0.05, 0.95), await V('kb_a'));
  await h.shot(OUT + 'a_kb_hide.png');
  await h.frames(10);
  expect('keyboard gone', await V('kb_a') < 0.02);
  // ---- dialog pops in and fades out
  await h.drag(4, 200, 120, 200, 6); await h.frames(10);
  await h.drag(320, 350, 320, 140, 6); await h.frames(16);
  await h.click(...icon(1)); await h.frames(1);
  await h.frames(14);
  await h.click(612, 82, 1); await h.frames(2);
  expect('dialog fades in', between(await V('dlg_a'), 0.05, 0.95), await V('dlg_a'));
  await h.frames(10);
  await h.click(248, 221, 1); await h.frames(1);            // Cancel
  expect('dialog fades out', await V('dlg') === 0 && between(await V('dlg_a'), 0.05, 0.95), await V('dlg_a'));
  await h.shot(OUT + 'a_dialog_out.png');
  await h.frames(12);
  // ---- dark mode dissolves, wallpaper dips
  await h.drag(320, 350, 320, 140, 6); await h.frames(16);
  await h.click(...icon(8)); await h.frames(14);
  await h.click(588, 112, 1); await h.frames(3);
  expect('dark mode change dissolves', between(await V('th_t'), 0, 14), await V('th_t'));
  await h.shot(OUT + 'a_theme_mid.png');
  await h.frames(20);
  // ---- nav mode change cross-fades pill <-> buttons
  await h.setVar('navmode', 0); await h.frames(3);
  expect('pill -> buttons cross-fade', between(await V('nm_a'), 0.05, 0.95), await V('nm_a'));
  await h.shot(OUT + 'a_navmode_mid.png');
  await h.setVar('navmode', 1); await h.frames(20);
  // ---- control centre / notification centre follow the finger
  await h.drag(320, 350, 320, 140, 6); await h.frames(16);
  await h.mouse(500, 8, false); await h.frames(1); await h.mouse(500, 8, true); await h.frames(1);
  await h.mouse(500, 60, true); await h.frames(1); await h.mouse(500, 90, true); await h.frames(1);
  const p1 = await V('qs_p');
  expect('pulling down the right side drags the control centre', await V('qs_kind') === 1 && between(p1, 0.2, 0.7) && await V('qs_drag') === 1, `${await V('qs_kind')} ${p1}`);
  await h.shot(OUT + 'a_cc_drag.png');
  await h.mouse(500, 90, false); await h.frames(2);
  expect('released past a quarter: snaps open', await V('qs_open') === 1 && await V('qs_p') > p1);
  await h.frames(12);
  expect('control centre fully open', await V('qs_p') === 1);
  await h.shot(OUT + 'a_cc_open.png');
  // tap a tile -> it cross-fades
  await h.click(34 + 148 + 68, 24 + 14 + 30, 1); await h.frames(2);
  const qa = (await V('qt_a'))[1];
  expect('dark-mode tile cross-fades', between(qa, 0.05, 0.95), qa);
  await h.frames(16);
  await h.click(34 + 148 + 68, 24 + 14 + 30, 1); await h.frames(16);
  // drag it back up from anywhere
  await h.mouse(320, 140, false); await h.frames(1); await h.mouse(320, 140, true); await h.frames(1);
  await h.mouse(320, 110, true); await h.frames(1); await h.mouse(320, 60, true); await h.frames(1);
  expect('dragging up pulls the panel back', between(await V('qs_p'), 0.1, 0.9) && await V('qs_drag') === 1, await V('qs_p'));
  await h.mouse(320, 60, false); await h.frames(14);
  expect('released: closes', await V('qs_open') === 0 && await V('qs_p') === 0, await V('qs_p'));
  // small pull and let go: springs back closed
  await h.drag(500, 8, 500, 30, 3); await h.frames(14);
  expect('a short pull springs back', await V('qs_open') === 0 && await V('qs_p') === 0);
  // left side -> notifications (with the "Wrong PIN" toast from earlier in the list)
  await h.drag(120, 8, 120, 200, 6); await h.frames(14);
  expect('left side opens the notification centre', await V('qs_kind') === 2 && await V('qs_open') === 1);
  const n0 = (await V('nt_txt')).length;
  await h.shot(OUT + 'a_nc_open.png');
  expect('notifications are recorded', n0 >= 1, n0);
  await h.click(591, 24 + 44 + 20, 1); await h.frames(2);
  expect('dismissing a notification', (await V('nt_txt')).length === n0 - 1);
  await h.frames(12);
  await h.click(320, 330, 1); await h.frames(14);
  expect('tap outside closes', await V('qs_open') === 0 && await V('qs_p') === 0);
  // tap on the status bar toggles (animated)
  await h.click(500, 8, 1); await h.frames(2);
  expect('status bar tap opens with animation', await V('qs_open') === 1 && between(await V('qs_p'), 0.05, 0.95), await V('qs_p'));
  await h.frames(12); await h.click(500, 8, 1); await h.frames(14);
  expect('status bar tap closes again', await V('qs_p') === 0);
  console.log('threads alive', await h.page.evaluate(() => vm.runtime.threads.length));
  await h.close();
  console.log(fails ? fails + ' FAILED' : 'ALL OK');
})().catch(e => { console.error(e); process.exit(1); });
