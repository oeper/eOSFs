// Animations must take the same wall time at 30, 60 and 120 fps.
const { open } = require('./harness');
const icon = i => [96 + ((i - 1) % 5) * 112, 177 + Math.floor((i - 1) / 5) * 98];
let fails = 0;
const expect = (n, c, e = '') => { console.log((c ? 'PASS ' : 'FAIL ') + n + (c ? '' : '  -> ' + e)); if (!c) fails++; };
(async () => {
  const durations = {};
  for (const fps of [30, 60, 120]) {
    const h = await open(process.argv[2], { gesture: true, fps }); const V = n => h.getVar(n);
    await h.flag(); await h.frames(Math.round(fps * 3)); await h.click(320, 200); await h.frames(fps / 2);
    await h.click(...icon(3), 2);
    let n = 0; while ((await V('open_t')) < 10 && n < 400) { await h.frames(1); n++; }
    durations[fps] = n / fps;
    // closing
    await h.drag(320, 350, 320, 140, 6);
    let m = 0; while ((await V('cl_on')) === 1 && m < 400) { await h.frames(1); m++; }
    durations['c' + fps] = m / fps;
    // snake speed: cells moved per second must not depend on fps
    await h.click(320, 346); await h.frames(fps / 2);
    await h.close();
  }
  console.log(JSON.stringify(durations));
  const base = durations[30];
  for (const fps of [60, 120]) expect(`open anim duration at ${fps}fps ~ 30fps`, Math.abs(durations[fps] - base) < 0.12, `${durations[fps]} vs ${base}`);
  for (const fps of [60, 120]) expect(`close anim duration at ${fps}fps ~ 30fps`, Math.abs(durations['c' + fps] - durations.c30) < 0.12, `${durations['c' + fps]} vs ${durations.c30}`);
  expect('open takes ~1/3 s', base > 0.25 && base < 0.45, base);
  console.log(fails ? fails + ' FAILED' : 'ALL OK');
})().catch(e => { console.error(e); process.exit(1); });
