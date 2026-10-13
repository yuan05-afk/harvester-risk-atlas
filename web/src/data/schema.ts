import { z } from "zod";

const num = z.number().nullable();
const pair = z.tuple([num, num]);

export const TIERS = ["High attention", "Watch", "Lower", "Not scored"] as const;
export type Tier = (typeof TIERS)[number];
export const COMPONENTS = ["R", "H", "E", "C"] as const;
export type Component = (typeof COMPONENTS)[number];

export const SpeciesSummary = z.object({
  slug: z.string(),
  name: z.string(),
  vernacular: z.string(),
  family: z.string(),
  ph_status: z.string(),
  endemic: z.boolean(),
  gate: z.string(),
  tier: z.enum(TIERS),
  partial: z.boolean(),
  dao: z.string(),
  iucn: z.object({ status: z.string(), category: z.string().nullable() }),
  habitat: z.string(),
  n_records: z.number(),
  n_clean: z.number(),
  n_cells: z.number(),
  components: z.object({ R: num, H: num, E: num, C: num }),
  sub: z.object({
    r_local: num,
    r_global: num,
    h_part: num,
    h_life_form: num,
    h_sourcing: num,
    e_pa_gap: num,
    e_forest_loss: num,
  }),
  score: num,
  score_ci: pair,
  rank: num,
  rank_ci: pair,
  p_top: num,
  driver: z.string(),
  climate: z.object({ dT: num, dT_range: pair, exceed: num, exceed_range: pair }),
  review: z.object({ needed: z.boolean(), note: z.string() }),
});
export type SpeciesSummary = z.infer<typeof SpeciesSummary>;

export const SpeciesDetail = SpeciesSummary.extend({
  use_context: z.string(),
  cells: z.array(z.string()),
  bounds: z.tuple([z.number(), z.number(), z.number(), z.number()]).nullable(),
  aoo_km2: num,
  eoo_km2: num,
  reporting_rate: num,
  n_cells_surveyed: z.number(),
  n_surveyed_ph: z.number(),
  native_regions: z.number(),
  pa_share: num,
  forest_loss_rate: num,
  provinces: z.array(z.object({ name: z.string(), records: z.number() })),
  history: z.array(
    z.object({
      decade: z.number(),
      observation: z.number(),
      specimen: z.number(),
      literature: z.number(),
      other: z.number(),
    }),
  ),
  basis: z.record(z.string(), z.number()),
  cleaning: z.record(z.string(), z.number()),
  traits: z
    .object({
      parts_used: z.string(),
      part_classes: z.array(z.string()),
      life_form: z.string(),
      sourcing: z.string(),
      habitat_note: z.string(),
      source: z.string(),
      source_url: z.string(),
      accessed: z.string(),
      verified: z.boolean(),
    })
    .nullable(),
  gbif: z.object({ taxon_key: num, match_type: z.string(), fetched_at: z.string(), n_world: z.number() }),
  wcvp: z.object({ key: num, fetched_at: z.string() }),
});
export type SpeciesDetail = z.infer<typeof SpeciesDetail>;

export const Source = z.object({
  id: z.string(),
  name: z.string(),
  use: z.string(),
  licence: z.string(),
  url: z.string(),
  accessed: z.string().optional(),
});
export type Source = z.infer<typeof Source>;

export const Manifest = z.object({
  index: z.string(),
  version: z.string(),
  built_at: z.string(),
  git_sha: z.string(),
  weights: z.object({ R: z.number(), H: z.number(), E: z.number(), C: z.number() }),
  rules: z.object({
    tier_high: z.number(),
    tier_watch: z.number(),
    min_cells: z.number(),
    h3_resolution: z.number(),
    well_surveyed_records: z.number(),
    mc_draws: z.number(),
  }),
  counts: z.object({ species: z.number(), tiers: z.record(z.string(), z.number()) }),
  sources: z.array(Source),
});
export type Manifest = z.infer<typeof Manifest>;

export const Validation = z.object({
  n_scored: z.number(),
  aggregation: z.record(z.string(), num),
  drop_component: z.record(z.string(), num),
  effort_threshold: z.record(z.string(), num),
  dao: z.object({
    n_listed: z.number(),
    n_scored: z.number().optional(),
    listed: z
      .array(z.object({ scientific_name: z.string(), dao_category: z.string(), rank_median: num, tier: z.string() }))
      .optional(),
    mean_rank_listed: num.optional(),
    mean_rank_all: num.optional(),
    p_value: num.optional(),
  }),
  v1_vs_v2: z.object({ n_shared: z.number(), spearman: num }),
  interval_width_median: num,
});
export type Validation = z.infer<typeof Validation>;

export const CellProps = z.object({
  h3: z.string(),
  effort: z.number(),
  pa: num,
  n_high: z.number(),
  n_watch: z.number(),
  n_lower: z.number(),
  n_cohort: z.number(),
  species: z.array(z.string()),
});
export type CellProps = z.infer<typeof CellProps>;
