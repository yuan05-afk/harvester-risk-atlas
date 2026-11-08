// Builds an ffmpeg concat list per capture folder: each frame is held until the next frame's timestamp, so the clip
// plays back in real time. Filenames are "<index>_<ms since clip start>.jpg".
import { existsSync, readFileSync, readdirSync, writeFileSync, statSync } from 'node:fs';
import { join } from 'node:path';

const capture = new URL('../capture/', import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1');
const clips = readdirSync(capture).filter((d) => statSync(join(capture, d)).isDirectory() && !d.startsWith('_'));
const summary = [];
for (const clip of clips) {
  const frames = readdirSync(join(capture, clip))
    .filter((f) => f.endsWith('.jpg'))
    .map((f) => ({ f, t: Number(f.split('_')[1].replace('.jpg', '')) }))
    .sort((a, b) => a.t - b.t);
  if (!frames.length) continue;
  const endFile = join(capture, clip, '_end.txt');
  const end = existsSync(endFile) ? Number(readFileSync(endFile, 'utf8')) : 0;
  const lines = [];
  frames.forEach((fr, k) => {
    const next = frames[k + 1];
    const dur = next ? Math.max(1, next.t - fr.t) / 1000 : Math.max(0.6, (end - fr.t) / 1000);
    lines.push(`file '${join(capture, clip, fr.f).replace(/\\/g, '/')}'`, `duration ${dur.toFixed(4)}`);
  });
  // The concat demuxer ignores the last duration unless the last file is repeated.
  lines.push(`file '${join(capture, clip, frames.at(-1).f).replace(/\\/g, '/')}'`);
  writeFileSync(join(capture, `_${clip}.txt`), lines.join('\n'));
  summary.push(`${clip} ${frames.length} frames ${(frames.at(-1).t / 1000 + 0.6).toFixed(1)}s`);
}
console.log(summary.join('\n'));
