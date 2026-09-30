"""Cloud bootstrap: import harvester_risk_atlas without wiping sys.modules.

Community Cloud (Python 3.11.4–3.11.11) raised a redacted KeyError at
``from harvester_risk_atlas.config import`` in app/streamlit_app.py.
The frames are importlib._bootstrap:

    _find_and_load line 1176
    _find_and_load_unlocked line 1147
    _load_unlocked line 701  →  module = sys.modules.pop(spec.name)

That pop raises when another session thread deletes the package during
exec_module. The app used to do that delete on every run, including a
hard refresh. A reboot still picks up new exports; ``-e .`` installs them.
"""
from __future__ import annotations

import importlib
import importlib.machinery
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CloudImportTests(unittest.TestCase):
    def test_entry_does_not_drop_sys_modules(self):
        app = (ROOT / "app" / "streamlit_app.py").read_text(encoding="utf-8")
        code = "\n".join(
            line for line in app.splitlines() if not line.lstrip().startswith("#")
        )
        self.assertNotIn("del sys.modules", code)
        self.assertNotIn("sys.modules.pop", code)
        self.assertNotIn("list(sys.modules)", code)
        self.assertIn("sys.path.insert", code)
        reqs = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        self.assertIn("-e .", reqs)

    def test_config_and_entry_symbols_import(self):
        """Same package imports the Streamlit entry performs, without Streamlit."""
        from harvester_risk_atlas.config import (
            DATA_PROCESSED,
            HPI_CSV,
            HPI_WEIGHTS,
            OCCURRENCES_PARQUET,
        )
        from harvester_risk_atlas.hpi import (  # noqa: F401
            dossier_actions,
            dossier_choices,
            hpi_formula_markdown,
            mapped_species,
            normalize_weights,
            top_rank_movers,
            unmapped_note,
            weight_sensitivity,
        )
        from harvester_risk_atlas.names import resolve_query  # noqa: F401
        from harvester_risk_atlas.pdf_brief import (  # noqa: F401
            render_field_brief_html,
            render_field_brief_pdf,
        )
        from harvester_risk_atlas.archetypes import (  # noqa: F401
            archetype_summary,
            assign_archetypes,
            pick_demo_species,
        )
        from harvester_risk_atlas.charts import (  # noqa: F401
            compare_components,
            component_bar,
            component_waterfall,
            decade_histogram,
            fig_to_html_bytes,
            fig_to_png_bytes,
            hpi_distribution,
            hpi_spark_svg,
            rank_shift_bars,
        )
        from harvester_risk_atlas.suitability import suitability_sketch  # noqa: F401
        from harvester_risk_atlas.map_points import (  # noqa: F401
            HOTSPOT_PAD_DEG,
            PH_FIT_BOUNDS,
            hotspot_name,
            hpi_marker_color,
            marker_radius,
            on_ph_land,
            species_at_click,
            species_plot_points,
        )

        self.assertEqual(
            HPI_WEIGHTS,
            {
                "rarity": 0.30,
                "climate_stress": 0.25,
                "harvest_proxy": 0.25,
                "pa_gap": 0.20,
            },
        )
        self.assertTrue(str(HPI_CSV).endswith("hpi_scores.csv"))
        self.assertTrue(str(OCCURRENCES_PARQUET).endswith("occurrences_sample.parquet"))
        self.assertEqual(DATA_PROCESSED.name, "processed")

        # A rerun must keep the already-imported module. Re-importing after a
        # wipe is what raced the other session.
        again = importlib.import_module("harvester_risk_atlas.config")
        self.assertIs(again.HPI_WEIGHTS, HPI_WEIGHTS)

    def test_pop_during_exec_module_is_the_cloud_keyerror(self):
        """Deleting the module inside exec_module is the KeyError at _load_unlocked."""

        class DropDuringExec:
            def create_module(self, spec):
                return None

            def exec_module(self, module):
                sys.modules.pop(module.__name__, None)

        name = "_hra_cloud_import_probe"
        sys.modules.pop(name, None)
        spec = importlib.machinery.ModuleSpec(name, DropDuringExec(), origin="built-in")
        with self.assertRaises(KeyError) as caught:
            importlib._bootstrap._load_unlocked(spec)
        self.assertEqual(caught.exception.args, (name,))
        self.assertNotIn(name, sys.modules)


if __name__ == "__main__":
    unittest.main()
