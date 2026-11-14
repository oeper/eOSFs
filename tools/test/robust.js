const { open } = require('./harness');
let fails = 0;
const expect = (n, c, e = '') => { console.log((c ? 'PASS ' : 'FAIL ') + n + (c ? '' : '  -> ' + e)); if (!c) fails++; };
const icon = i => [96 + ((i - 1) % 5) * 112, 177 + Math.floor((i - 1) / 5) * 98];
(async () => {
  const h = await open(process.argv[2]); const V = n => h.getVar(n);
  const timeFrames = async (label, n = 30) => { const t = await h.page.evaluate(n => { const t0 = performance.now(); for (let i = 0; i < n; i++) vm.runtime._step(); return (performance.now() - t0) / n; }, n); console.log(`  ${label}: ${t.toFixed(1)} ms/frame`); return t; };
  await h.flag(); await h.frames(80); await h.click(320, 200); await h.frames(3);
  await timeFrames('home');
  // terminal: system folder protection + removing cwd
  await h.click(...icon(5)); await h.frames(14);
  const run = async cmd => { await h.setVar('ti', cmd); await h.page.evaluate(() => {}); await h.click(566, 314); await h.frames(2); };
  await run('rm Pictures'); await run('mv Pictures Pics');
  let names = await V('fs_name');
  expect('system folder survives rm/mv', names.includes('Pictures') && !names.includes('Pics'), JSON.stringify(names));
  await run('mkdir tmp'); await run('cd tmp'); await run('mkdir deep'); await run('cd deep'); await run('cd ..'); await run('cd ..'); await run('rm tmp');
  expect('non-empty dir refuses removal', (await V('fs_name')).includes('tmp'));
  await run('cd tmp'); await run('rm deep'); await run('cd ..'); await run('rm tmp');
  expect('empty dirs can be removed', !(await V('fs_name')).includes('tmp') && !(await V('fs_name')).includes('deep'));
  await run('cd /Documents'); await run('pwd'); await run('cd /nonexistent'); await run('cat welcome.txt'); await run('ls /');
  const out = await V('term_out');
  expect('absolute cd + pwd', out.includes('/Documents'), JSON.stringify(out.slice(-12)));
  expect('cat shows welcome text', out.some(l => l.startsWith('Welcome to eOS')));
  await timeFrames('terminal');
  // many lines of output
  for (let i = 0; i < 5; i++) await run('help');
  await timeFrames('terminal full');
  await h.click(320, 346); await h.frames(14);
  // editor with long text
  await h.click(...icon(2)); await h.frames(14); await h.click(528, 42); await h.frames(4);
  await h.setVar('ti', 'The quick brown fox jumps over the lazy dog. '.repeat(32)); await h.frames(3);
  expect('editor handles ~1400 chars', (await V('ti')).length > 1300);
  await timeFrames('editor 1400 chars');
  await h.shot((process.env.EOS_OUT || '/tmp/eos-test') + '/r_editor_long.png');
  await h.click(320, 346); await h.frames(14);
  // paint with many strokes
  await h.click(...icon(6)); await h.frames(14);
  const pts = 2500; const xs = [], ys = [], cs = [], ws = [], ss = [];
  for (let i = 0; i < pts; i++) { xs.push(100 + (i * 7) % 500); ys.push(80 + Math.round(60 * Math.sin(i / 20)) + 60 + Math.floor(i / 500) * 30); cs.push(3); ws.push(4); ss.push(i % 250 === 0 ? 1 : 0); }
  await h.setVar('ps_x', xs); await h.setVar('ps_y', ys); await h.setVar('ps_c', cs); await h.setVar('ps_w', ws); await h.setVar('ps_s', ss);
  await timeFrames('paint 2500 pts');
  await h.shot((process.env.EOS_OUT || '/tmp/eos-test') + '/r_paint.png');
  await h.click(320, 346); await h.frames(14);
  // files with many entries
  await h.click(...icon(1)); await h.frames(14);
  await h.page.evaluate(() => {
    const st = vm.runtime.getTargetForStage(); const g = n => Object.values(st.variables).find(v => v.name === n);
    for (let i = 0; i < 40; i++) { g('fs_id').value.push(100 + i); g('fs_name').value.push('file' + i + '.txt'); g('fs_parent').value.push(1); g('fs_type').value.push(0); g('fs_data').value.push('x'.repeat(i)); }
  });
  await timeFrames('files 44 rows');
  await h.drag(300, 280, 300, 60); await h.frames(2);
  await h.shot((process.env.EOS_OUT || '/tmp/eos-test') + '/r_files_scrolled.png');
  console.log('threads alive', await h.page.evaluate(() => vm.runtime.threads.length));
  await h.close(); console.log(fails ? fails + ' FAILED' : 'ALL OK');
})().catch(e => { console.error(e); process.exit(1); });
