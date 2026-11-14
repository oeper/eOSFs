const { open } = require('./harness');
const OUT = (process.env.EOS_OUT || '/tmp/eos-test') + '/'; require('fs').mkdirSync(OUT, { recursive: true });
let fails = 0;
const expect = (name, cond, extra = '') => { console.log((cond ? 'PASS ' : 'FAIL ') + name + (cond ? '' : '   -> ' + extra)); if (!cond) fails++; };
const icon = i => [96 + ((i - 1) % 5) * 112, 177 + Math.floor((i - 1) / 5) * 98];
const HOME = [320, 346], BACK = [220, 346], RECENTS = [420, 346];
const KT = 202; // keyboard top
function key(ch) {
  const rows = ['qwertyuiop', 'asdfghjkl', 'zxcvbnm'];
  for (let r = 0; r < 3; r++) { const i = rows[r].indexOf(ch); if (i >= 0) { const x0 = r === 0 ? 22 : r === 1 ? 52 : 102; return [x0 + i * 60 + 28, KT + 6 + r * 31 + 13]; } }
  if (ch === ' ') return [306, KT + 112]; if (ch === 'enter') return [566, KT + 112]; if (ch === 'back') return [570, KT + 81];
  throw new Error('no key ' + ch);
}
const CALC = { C: [0, 0], '±': [1, 0], '%': [2, 0], '÷': [3, 0], 7: [0, 1], 8: [1, 1], 9: [2, 1], '×': [3, 1], 4: [0, 2], 5: [1, 2], 6: [2, 2], '-': [3, 2], 1: [0, 3], 2: [1, 3], 3: [2, 3], '+': [3, 3] };
const calcKey = k => k === '0' ? [228, 293.5] : k === '.' ? [366, 293.5] : k === '=' ? [458, 293.5] : [182 + 92 * CALC[k][0], 149.5 + 36 * CALC[k][1]];

(async () => {
  const h = await open(process.argv[2]);
  const type = async s => { for (const c of s) await h.click(...key(c), 2); };
  const calc = async s => { for (const c of s) await h.click(...calcKey(c), 2); };
  const V = n => h.getVar(n);
  await h.flag(); await h.frames(80);
  expect('boots to lock screen', await V('screen') === 1);
  await h.click(320, 200); await h.frames(3);
  expect('tap unlocks to home', await V('screen') === 2);

  // ---------- Calculator
  await h.click(...icon(3)); await h.frames(14);
  expect('calculator opens', await V('app') === 3 && await V('screen') === 3);
  await calc('76×'); await calc('5='); expect('76 x 5 = 380', await V('calc_d') == 380, await V('calc_d'));
  await calc('C'); await calc('0.5+0.25='); expect('0.5 + 0.25 = 0.75', await V('calc_d') == 0.75, await V('calc_d'));
  await calc('C'); await calc('1÷0='); expect('divide by zero -> Error', await V('calc_d') === 'Error', await V('calc_d'));
  await calc('C'); await calc('9-4-3='); expect('chained 9-4-3 = 2', await V('calc_d') == 2, await V('calc_d'));
  await calc('C'); await calc('5±'); expect('+/- gives -5', await V('calc_d') == -5, await V('calc_d'));
  await calc('C'); await calc('50%'); expect('50% = 0.5', await V('calc_d') == 0.5, await V('calc_d'));
  await calc('C'); await calc('1÷3='); 
  await h.shot(OUT + 'i_calc.png');
  expect('1/3 rounded', String(await V('calc_d')) === '0.3333333333', await V('calc_d'));
  await h.click(...HOME); await h.frames(14);
  expect('home button -> home', await V('screen') === 2);

  // ---------- Notes + keyboard
  await h.click(...icon(2)); await h.frames(14);
  await h.shot(OUT + 'i_notes_list.png');
  await h.click(528, 42); await h.frames(4);
  expect('new note opens editor + keyboard', await V('view') === 1 && await V('kb_open') === 1);
  await type('hi there'); await h.frames(2);
  const ed = await V('ti');
  expect('typed text reaches buffer', ed === 'hi there', JSON.stringify(ed));
  await h.shot(OUT + 'i_notes_edit.png');
  await h.click(...key('back')); await h.click(...key('back')); await h.frames(2);
  expect('backspace removes chars', await V('ti') === 'hi the', JSON.stringify(await V('ti')));
  const data = await V('fs_data');
  expect('note saved into fs_data', data.includes('hi the'), JSON.stringify(data));
  await h.click(...BACK); await h.frames(14);   // hides keyboard
  expect('back hides keyboard first', await V('kb_open') === 0 && await V('view') === 1);
  await h.click(...BACK); await h.frames(14);
  expect('back leaves editor', await V('view') === 0 && await V('screen') === 3);
  await h.click(...BACK); await h.frames(14);
  expect('back from list -> home', await V('screen') === 2);

  // ---------- Files: new folder / delete
  await h.click(...icon(1)); await h.frames(14);
  await h.click(452, 42); await h.frames(3);
  expect('new folder prompts keyboard', await V('kb_open') === 1 && await V('ti_act') === 10);
  await type('abc'); await h.click(...key('enter')); await h.frames(3);
  const names = await V('fs_name');
  expect('folder abc created', names.includes('abc'), JSON.stringify(names));
  await h.shot(OUT + 'i_files.png');
  // open Documents (first row) then up
  await h.click(300, 82); await h.frames(3);
  expect('tap folder enters it', await V('f_dir') === 2, await V('f_dir'));
  await h.shot(OUT + 'i_files_docs.png');
  await h.click(...BACK); await h.frames(14);
  expect('back goes to parent dir', await V('f_dir') === 1 && await V('screen') === 3);
  // delete 'abc' (5th row now: Documents, Notes, Pictures, System, abc)  -> trash at x=612
  await h.click(612, 82 + 4 * 46); await h.frames(3);
  expect('delete asks for confirmation', await V('dlg') === 1);
  await h.shot(OUT + 'i_dialog.png');
  await h.click(392, 221); await h.frames(3);
  expect('confirming deletes', !(await V('fs_name')).includes('abc'), JSON.stringify(await V('fs_name')));
  await h.click(...HOME); await h.frames(14);

  // ---------- Terminal
  await h.click(...icon(5)); await h.frames(14);
  expect('terminal opens with keyboard', await V('kb_open') === 1 && await V('ti_act') === 30);
  const run = async cmd => { await h.setVar('ti', cmd); await h.click(...key('enter')); await h.frames(2); };
  await run('help'); await run('mkdir proj'); await run('cd proj'); await run('echo hello world > a.txt'); await run('ls'); await run('cat a.txt'); await run('pwd'); await run('cd ..'); await run('nope');
  const out = await V('term_out');
  expect('echo > writes file', (await V('fs_name')).includes('a.txt') && (await V('fs_data')).includes('hello world'));
  expect('ls lists a.txt', out.some(l => l.includes('a.txt')), JSON.stringify(out.slice(-8)));
  expect('cat prints content', out.filter(l => l === 'hello world').length >= 1, JSON.stringify(out.slice(-8)));
  expect('pwd prints /proj', out.includes('/proj'), JSON.stringify(out.slice(-8)));
  expect('unknown command message', out.some(l => l.startsWith('nope: command not found')));
  await h.shot(OUT + 'i_term.png');
  await h.click(...HOME); await h.frames(14);

  // ---------- Settings: dark mode + wallpaper + PIN
  await h.click(...icon(8)); await h.frames(14);
  await h.click(588, 112); await h.frames(3);
  expect('dark mode switch', await V('dark') === 1);
  await h.shot(OUT + 'i_settings_dark.png');
  await h.click(588, 112); await h.frames(3);
  expect('dark mode off again', await V('dark') === 0);
  await h.click(214 + 66 * 2 + 28, 68 + 148); await h.frames(3);
  expect('wallpaper 3 selected', await V('wall') === 3, await V('wall'));
  await h.click(214 + 28, 68 + 148); await h.frames(3);
  await h.drag(300, 280, 300, 80); await h.frames(3);
  expect('settings scrolls', await V('scroll') > 100, await V('scroll'));
  await h.shot(OUT + 'i_settings_scrolled.png');
  await h.setVar('scroll', 412); await h.frames(3);
  await h.shot(OUT + 'i_settings_bottom.png');
  await h.setVar('scroll', 0); await h.frames(2);
  await h.click(...HOME); await h.frames(14);

  // ---------- PIN lock
  await h.setVar('pin', '1234');
  await h.click(320, 10); await h.frames(3);
  expect('status bar opens quick settings', await V('qs_open') === 1);
  await h.shot(OUT + 'i_qs.png');
  await h.click(34 + 3 * 148 + 68, 24 + 14 + 30); await h.frames(4);   // power tile
  expect('power tile opens the power menu (animated)', await V('pw') === 1 && await V('qs_open') === 0 && await V('pw_a') > 0.05 && await V('pw_a') < 0.95, await V('pw_a'));
  await h.shot(OUT + 'i_power_mid.png');
  await h.frames(12); await h.shot(OUT + 'i_power.png');
  await h.click(190, 165); await h.frames(3);                          // Lock
  expect('power menu: Lock locks', await V('screen') === 1 && await V('pw') === 0);
  await h.click(320, 200); await h.frames(3);
  expect('PIN pad shown', await V('pin_show') === 1);
  await h.shot(OUT + 'i_pin.png');
  const pad = d => { const k = d === 0 ? 11 : d; return [320 + ((k - 1) % 3 - 1) * 76, 128 + Math.floor((k - 1) / 3) * 46 + 19]; };
  for (const d of [1, 1, 1, 1]) await h.click(...pad(d), 2);
  expect('wrong PIN rejected', await V('screen') === 1);
  for (const d of [1, 2, 3, 4]) await h.click(...pad(d), 2);
  expect('correct PIN unlocks', await V('screen') === 2, await V('screen'));
  await h.setVar('pin', '');

  // ---------- Recents
  await h.click(...icon(4)); await h.frames(14);
  await h.click(...RECENTS); await h.frames(3);
  expect('recents screen', await V('screen') === 4);
  await h.shot(OUT + 'i_recents.png');
  const rec = await V('rec');
  console.log('rec list', JSON.stringify(rec));
  await h.click(320, 170); await h.frames(14);   // centre (most recent) card
  expect('tapping card reopens app', await V('screen') === 3 && await V('app') === rec[rec.length - 1], await V('app'));

  // ---------- Clock: stopwatch & timer
  await h.click(320, 79); await h.frames(3);
  expect('stopwatch tab', await V('clk_tab') === 2);
  await h.click(250, 256); await h.frames(1);
  await h.click(390, 256); await h.frames(1);
  expect('stopwatch running', await V('sw_run') === 1);
  await h.shot(OUT + 'i_clock_sw.png');
  await h.click(460, 79); await h.frames(3);
  expect('timer tab', await V('clk_tab') === 3);
  await h.click(320, 295); await h.frames(3);
  expect('timer started', await V('tm_run') === 1);
  await h.shot(OUT + 'i_clock_timer.png');

  // ---------- Paint
  await h.click(...HOME); await h.frames(14);
  await h.click(...icon(6)); await h.frames(14);
  await h.drag(150, 150, 400, 250, 12);
  expect('painting records strokes', (await V('ps_x')).length > 5, (await V('ps_x')).length);
  await h.click(...[42, 80 + 56 * 0]); await h.frames(1);
  await h.shot(OUT + 'i_paint.png');

  // ---------- Snake
  await h.click(...HOME); await h.frames(14);
  await h.click(...icon(7)); await h.frames(14);
  await h.click(564, 206); await h.frames(1);  // right
  await h.frames(60);
  expect('snake running', await V('sn_state') === 1, await V('sn_state'));
  await h.shot(OUT + 'i_snake.png');
  await h.frames(200);
  console.log('snake state after 260 frames:', await V('sn_state'), 'score', await V('sn_score'));
  await h.shot(OUT + 'i_snake_end.png');

  console.log('threads alive', await h.page.evaluate(() => vm.runtime.threads.length));
  await h.close();
  console.log(fails ? `${fails} FAILED` : 'ALL OK');
})().catch(e => { console.error(e); process.exit(1); });
