const { open } = require('./harness');
let fails = 0;
const expect = (n, c, e = '') => { console.log((c ? 'PASS ' : 'FAIL ') + n + (c ? '' : '  -> ' + e)); if (!c) fails++; };
const icon = i => [125 + ((i - 1) % 4) * 130, 177 + Math.floor((i - 1) / 4) * 98];
(async () => {
  // ---- session 1
  let h = await open(process.argv[2]); let V = n => h.getVar(n);
  await h.flag(); await h.frames(80); await h.click(320, 200); await h.frames(3);
  await h.click(...icon(2)); await h.frames(14);
  await h.click(528, 42); await h.frames(4);
  await h.setVar('ti', 'remember this\nline two ¦§ stays'); await h.frames(3);   // note: weird chars cannot be typed anyway
  await h.setVar('ti', 'remember this\nline two'); await h.frames(3);
  await h.click(320, 346); await h.frames(14);   // home -> triggers save
  await h.setVar('dark', 1); await h.setVar('accent', 4); await h.setVar('wall', 3); await h.setVar('pin', '4321'); await h.setVar('sn_best', 17);
  await h.frames(160);
  const store = await h.store();
  console.log('stored keys', Object.keys(store), 'fs length', (store['eos:fs'] || '').length);
  expect('fs saved', (store['eos:fs'] || '').includes('remember this'));
  await h.close();
  // ---- session 2 (fresh VM, same storage)
  h = await open(process.argv[2], { store }); V = n => h.getVar(n);
  await h.flag(); await h.frames(80);
  expect('dark restored', await V('dark') === 1, await V('dark'));
  expect('accent restored', await V('accent') === 4);
  expect('wallpaper restored', await V('wall') === 3);
  expect('pin restored', await V('pin') === 4321 || await V('pin') === '4321', await V('pin'));
  expect('snake best restored', await V('sn_best') === 17);
  const data = await V('fs_data');
  expect('note text restored (with newline)', data.includes('remember this\nline two'), JSON.stringify(data));
  const names = await V('fs_name');
  expect('default files restored', names.includes('welcome.txt') && names.includes('Documents'), JSON.stringify(names));
  expect('fs_next beyond max id', await V('fs_next') > Math.max(...await V('fs_id')), await V('fs_next'));
  expect('list lengths consistent', (await V('fs_id')).length === (await V('fs_parent')).length && (await V('fs_id')).length === (await V('fs_data')).length);
  await h.close();
  // ---- corrupted storage falls back to defaults
  h = await open(process.argv[2], { store: { 'eos:fs': 'garbage', 'eos:settings': 'x' } }); V = n => h.getVar(n);
  await h.flag(); await h.frames(80);
  expect('corrupt storage keeps defaults', (await V('fs_name')).includes('welcome.txt') && await V('dark') === 0);
  await h.close();
  console.log(fails ? fails + ' FAILED' : 'ALL OK');
})().catch(e => { console.error(e); process.exit(1); });
