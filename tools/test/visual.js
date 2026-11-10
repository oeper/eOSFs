const { open } = require('./harness');
const OUT = (process.env.EOS_OUT || '/tmp/eos-test') + '/'; require('fs').mkdirSync(OUT, { recursive: true });
const icon = i => [125 + ((i - 1) % 4) * 130, 177 + Math.floor((i - 1) / 4) * 98];
let fails = 0;
const expect = (n, c, e = '') => { console.log((c ? 'PASS ' : 'FAIL ') + n + (c ? '' : '  -> ' + e)); if (!c) fails++; };
(async () => {
  const h = await open(process.argv[2]); const V = n => h.getVar(n);
  await h.flag(); await h.frames(40); await h.shot(OUT + 'v_boot.png');
  await h.frames(50); await h.shot(OUT + 'v_lock.png');
  await h.setVar('pin', '1234');
  await h.click(320, 200); await h.frames(3); await h.shot(OUT + 'v_pin.png');
  await h.setVar('pin', ''); await h.click(244, 285); // Back key on pad
  await h.frames(3);
  await h.click(320, 200); await h.frames(3);
  expect('unlock without pin', await V('screen') === 2, await V('screen'));
  // launch animation mid-way
  await h.click(...icon(2)); await h.frames(4); await h.shot(OUT + 'v_anim.png'); await h.frames(10);
  // shift + physical typing in a new note
  await h.click(528, 42); await h.frames(4);
  await h.click(60, 202 + 81); await h.frames(1);          // shift
  await h.click(50, 221); await h.frames(1);               // q -> Q
  expect('shift capitalises', (await V('ti')) === 'Q', JSON.stringify(await V('ti')));
  expect('shift resets after one letter', await V('kb_shift') === 0);
  await h.click(60, 202 + 81); await h.frames(1);
  await h.shot(OUT + 'v_shift.png');
  await h.click(60, 202 + 81); await h.frames(1);          // shift off again
  await h.key('a', true); await h.frames(3); await h.key('a', false); await h.frames(2);
  await h.key('b', true); await h.frames(3); await h.key('b', false); await h.frames(2);
  await h.key(' ', true); await h.frames(3); await h.key(' ', false); await h.frames(2);
  await h.key('7', true); await h.frames(3); await h.key('7', false); await h.frames(2);
  expect('physical keyboard types', (await V('ti')) === 'Qab 7', JSON.stringify(await V('ti')));
  await h.key('Enter', true); await h.frames(3); await h.key('Enter', false); await h.frames(2);
  expect('physical enter -> newline in editor', (await V('ti')) === 'Qab 7\n', JSON.stringify(await V('ti')));
  // symbols page
  await h.click(60, 202 + 112); await h.frames(1);   // 123
  expect('symbol page', await V('kb_page') === 1);
  await h.shot(OUT + 'v_sym.png');
  await h.click(60, 202 + 112); await h.frames(1);
  await h.click(320, 346); await h.frames(3);
  // dark mode tour
  await h.setVar('dark', 1); await h.setVar('accent', 3);
  await h.page.evaluate(() => {}); await h.frames(2);
  await h.click(320, 346); await h.frames(3);
  // force theme refresh via QS dark toggle twice
  await h.click(320, 10); await h.frames(3); await h.click(34 + 148 + 68, 68); await h.frames(2); await h.click(34 + 148 + 68, 68); await h.frames(2);
  await h.click(320, 300); await h.frames(3);
  await h.shot(OUT + 'v_home_dark.png');
  const names = ['files', 'notes', 'calc', 'clock', 'term', 'paint', 'snake', 'settings'];
  for (const i of [1, 3, 4, 6, 7, 8]) {
    await h.click(...icon(i)); await h.frames(14); await h.shot(OUT + `v_dark_${names[i - 1]}.png`);
    await h.click(320, 346); await h.frames(3);
  }
  console.log('dark', await V('dark'), 'accent', await V('accent'));
  await h.close(); console.log(fails ? fails + ' FAILED' : 'ALL OK');
})().catch(e => { console.error(e); process.exit(1); });
