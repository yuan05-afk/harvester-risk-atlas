import { motion } from "motion/react";
import type { Component } from "../data/schema";
import { COMPONENT_META, level, LEVELS } from "../lib/vocab";
import { ComponentGlyph } from "./Figures";

/** Four blocks, filled up to the level, in the component's colour, with the word. */
export function LevelMeter({ value, color, label }: { value: number | null; color: string; label: string }) {
  const lv = level(value);
  return (
    <div className="meter" role="img" aria-label={`${label}: ${lv ? lv.word : "not measured"}`}>
      <span className="meter__blocks" aria-hidden="true">
        {LEVELS.map((_, i) => (
          <motion.i
            key={i}
            initial={{ scaleY: 0.2, opacity: 0.4 }}
            whileInView={{ scaleY: 1, opacity: 1 }}
            viewport={{ once: true }}
            transition={{ delay: 0.08 * i, duration: 0.3 }}
            style={{ background: lv && i <= lv.index ? color : undefined }}
          />
        ))}
      </span>
      <span className="meter__word">{lv ? lv.word : "Not measured"}</span>
    </div>
  );
}

/** One tile per scored part: its drawn glyph, plain name, level meter, and the evidence in a sentence. */
export function ReasonTiles({
  values,
  sentences,
  highlight,
}: {
  values: Record<Component, number | null>;
  sentences: Record<"R" | "H" | "E", string>;
  highlight?: string;
}) {
  return (
    <div className="reasons-grid">
      {(["R", "H", "E"] as const).map((k, i) => {
        const meta = COMPONENT_META[k];
        return (
          <motion.section
            key={k}
            className={`reason${highlight === k ? " is-main" : ""}`}
            initial={{ opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-60px" }}
            transition={{ delay: 0.08 * i, duration: 0.35 }}
            style={{ ["--accent" as string]: meta.color }}
          >
            <header className="reason__head">
              <ComponentGlyph k={k} color={meta.color} size={34} />
              <h3>{meta.label}</h3>
              {highlight === k ? <span className="reason__main">Biggest reason</span> : null}
            </header>
            <LevelMeter value={values[k]} color={meta.color} label={meta.label} />
            <p>{sentences[k]}</p>
          </motion.section>
        );
      })}
    </div>
  );
}
