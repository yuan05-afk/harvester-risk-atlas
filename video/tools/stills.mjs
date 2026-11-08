// Renders stills of a composition at given film seconds with one bundle, then tiles them into one sheet.
//   node tools/stills.mjs FilmV2 look/v2-sheet.png 2 9 18.5 ...
import { bundle } from '@remotion/bundler';
import { renderStill, selectComposition } from '@remotion/renderer';
import { execFileSync } from 'node:child_process';
import { mkdirSync } from 'node:fs';
import { join } from 'node:path';

const [id, out, ...secs] = process.argv.slice(2);
const root = new URL('..', import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1');
const serveUrl = await bundle({ entryPoint: join(root, 'src/index.ts') });
const composition = await selectComposition({ serveUrl, id });
const dir = join(root, 'look', 'stills-tmp');
mkdirSync(dir, { recursive: true });
const files = [];
for (const [i, s] of secs.entries()) {
  const file = join(dir, `s${String(i).padStart(2, '0')}.png`);
  await renderStill({ serveUrl, composition, frame: Math.round(Number(s) * composition.fps), output: file, scale: 0.5 });
  files.push(file);
  process.stdout.write(`${s} `);
}
const cols = 4;
const rows = Math.ceil(files.length / cols);
const inputs = files.flatMap((f) => ['-i', f]);
const layout = files.map((_, k) => `${(k % cols) * 960}_${Math.floor(k / cols) * 540}`).join('|');
execFileSync('ffmpeg', ['-loglevel', 'error', '-y', ...inputs, '-filter_complex', `xstack=inputs=${files.length}:layout=${layout}:fill=white`, join(root, out)]);
console.log(`\n${out} (${files.length} stills, ${rows} rows)`);
