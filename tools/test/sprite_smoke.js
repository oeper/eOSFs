const { open } = require('./harness');
const OUT = (process.env.EOS_OUT || '/tmp/eos-test') + '/'; require('fs').mkdirSync(OUT, { recursive: true });
(async () => {
  const h = await open(process.argv[2], { gesture: true }); const V = n => h.getVar(n);
  await h.flag(); await h.frames(60);
  console.log('cm_n', await V('cm_n'), 'screen', await V('screen'));
  await h.shot(OUT + 'sp_boot.png');
  await h.frames(40); console.log('cm_n', await V('cm_n'), 'screen', await V('screen'));
  await h.shot(OUT + 'sp_lock.png');
  await h.click(320, 200); await h.frames(10);
  console.log('cm_n', await V('cm_n'), 'screen', await V('screen'));
  await h.shot(OUT + 'sp_home.png');
  console.log('clones', await h.page.evaluate(() => vm.runtime._cloneCounter), 'threads', await h.page.evaluate(() => vm.runtime.threads.length));
  await h.close();
})().catch(e => { console.error(e); process.exit(1); });
