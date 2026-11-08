// The film's clock. Every time is in film seconds. The narration master (public/audio/vo-master-rt.wav) runs the whole
// film; its word times come from transcribing the master itself (audio/vo-master.words.json, copied to words.json),
// so each picture cue lands on the spoken word. A cue that cannot be found throws, so a broken cue fails the render.
import words from './words.json';
import master from './timeline.generated.json';

export const FPS = 60;
/** The film is as long as the narration master: lead + voice + designed pauses + end hold (tools/master.py). */
export const DURATION = (master as { film: number }).film;
export const frames = (s: number) => Math.round(s * FPS);

type W = { word: string; start: number; end: number };
const WORDS = words as W[];
const norm = (s: string) => s.toLowerCase().replace(/[^a-z0-9]/g, '');

/** Start time of the nth occurrence of a spoken word. */
export function cue(word: string, n = 1): number {
  let k = 0;
  for (const w of WORDS) if (norm(w.word) === norm(word) && ++k === n) return w.start;
  throw new Error(`no cue "${word}" #${n}`);
}
/** End time of the nth occurrence of a spoken word. */
export function cueEnd(word: string, n = 1): number {
  let k = 0;
  for (const w of WORDS) if (norm(w.word) === norm(word) && ++k === n) return w.end;
  throw new Error(`no cue "${word}" #${n}`);
}

/**
 * On-screen words timed to the voice. Tokens are matched in order against the spoken words from `after` on; a token
 * that is not spoken (or is written differently, "1,186") takes the previous word's time + 0.12 s.
 * Markers: *word = italic serif accent; ^word = sappan accent colour.
 */
export function line(text: string, after = 0): Array<{ w: string; at: number; serif?: boolean; blue?: boolean }> {
  let j = WORDS.findIndex((w) => w.start >= after - 0.05);
  if (j < 0) throw new Error(`line "${text}" starts after the voice ends`);
  let last = WORDS[j].start;
  return text.split(' ').map((raw) => {
    const serif = raw.includes('*');
    const blue = raw.includes('^');
    const w = raw.replace(/[*^]/g, '');
    const k = WORDS.slice(j, j + 4).findIndex((x) => norm(x.word) === norm(w));
    if (k >= 0) {
      last = WORDS[j + k].start;
      j += k + 1;
    } else last += 0.12;
    return { w, at: last, serif, blue };
  });
}
