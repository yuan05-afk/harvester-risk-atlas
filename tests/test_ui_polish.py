"""Snapshot extras: legends under the axes, compare-card HTML, IUCN line, PDF brief."""
from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd

from harvester_risk_atlas.charts import compare_components, hpi_distribution
from harvester_risk_atlas.hpi import dossier_choices, mapped_species, unmapped_note
from harvester_risk_atlas.pdf_brief import _iucn_line, render_field_brief_pdf

ROOT = Path(__file__).resolve().parents[1]


def _row(**overrides):
    base = {
        "scientific_name": "Arcangelisia flava",
        "vernacular_ph": "abutra",
        "family": "Menispermaceae",
        "hpi": 0.519,
        "hpi_band": "Moderate",
        "hpi_confidence": 0.85,
        "n_occurrences": 60,
        "archetype_label": "Harvest-pressured",
        "component_rarity": 0.165,
        "component_climate": 0.546,
        "component_harvest": 0.844,
        "component_pa_gap": 0.610,
        "lat_mean": 11.05,
        "lon_mean": 121.97,
        "notes": "yellow root; ethnobotany only",
        "iucn_status": "not_queried",
        "iucn_category": None,
        "iucn_category_code": None,
        "iucn_year": None,
        "iucn_note": "Set IUCN_API_TOKEN. Do not invent categories.",
    }
    base.update(overrides)
    return pd.Series(base)


class LegendTests(unittest.TestCase):
    def test_compare_legend_sits_below_the_title(self):
        figure = compare_components(
            _row(),
            _row(scientific_name="Lagerstroemia speciosa", vernacular_ph="banaba"),
        )
        self.assertIn("Component comparison", figure.layout.title.text)
        self.assertLess(figure.layout.legend.y, 0)
        self.assertGreaterEqual(figure.layout.margin.b, 110)
        self.assertGreaterEqual(figure.layout.margin.l, 72)

    def test_distribution_legend_sits_below_the_title(self):
        frame = pd.DataFrame(
            [
                {"hpi": 0.2, "hpi_band": "Lower relative pressure", "scientific_name": "A a"},
                {"hpi": 0.5, "hpi_band": "Moderate", "scientific_name": "B b"},
                {"hpi": 0.8, "hpi_band": "Higher relative pressure", "scientific_name": "C c"},
            ]
        )
        figure = hpi_distribution(frame)
        self.assertLess(figure.layout.legend.y, 0)
        self.assertGreaterEqual(figure.layout.margin.b, 100)


class SnapshotUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = (ROOT / "app" / "streamlit_app.py").read_text(encoding="utf-8")
        cls.css = (ROOT / "app" / "styles.css").read_text(encoding="utf-8")
        cls.deploy = (ROOT / "DEPLOY.md").read_text(encoding="utf-8")
        cls.reqs = (ROOT / "requirements.txt").read_text(encoding="utf-8")

    def test_map_howto_and_talk_track(self):
        self.assertIn("How to read this", self.app)
        self.assertIn("60-sec talk track", self.app)
        self.assertIn("Weights transparency (HPI v1.1)", self.app)
        self.assertIn("0.30", self.app)

    def test_compare_cards_are_unindented_html(self):
        self.assertIn('class="hra-sci-name"', self.app)
        self.assertIn("st.html", self.app)
        self.assertIn("IUCN not linked", self.app)
        self.assertIn("hra-sci-name", self.css)
        # The card builder joins lines so Markdown cannot code-fence them.
        self.assertIn('return "".join(parts)', self.app)

    def test_deploy_entry_and_reportlab(self):
        self.assertIn("app/streamlit_app.py", self.deploy)
        self.assertIn("reportlab==4.2.5", self.reqs)


class UnmappedSpeciesTests(unittest.TestCase):
    def test_mentha_without_coords_is_skipped(self):
        frame = pd.read_csv(ROOT / "data" / "processed" / "hpi_scores.csv")
        mapped, skipped = mapped_species(frame)
        self.assertNotIn("Mentha × piperita", set(mapped["scientific_name"]))
        self.assertIn("Mentha × piperita", set(skipped["scientific_name"]))
        self.assertEqual(len(mapped) + len(skipped), len(frame))
        self.assertTrue(mapped["lat_mean"].notna().all())
        self.assertTrue(mapped["lon_mean"].notna().all())
        self.assertTrue((frame["iucn_status"] == "not_queried").all())
        note = unmapped_note(skipped)
        self.assertIn("Mentha × piperita", note)
        self.assertIn("yerba buena", note)
        self.assertIn("no georeferenced points", note)
        self.assertEqual(unmapped_note(mapped.iloc[0:0]), "")
        self.assertTrue(skipped["lat_mean"].isna().all())
        self.assertTrue(skipped["lon_mean"].isna().all())
        choices = dossier_choices(mapped, skipped)
        self.assertEqual(choices[-1], "Mentha × piperita")
        self.assertNotEqual(choices[0], "Mentha × piperita")
        self.assertGreater(float(skipped["hpi"].max()), float(mapped["hpi"].max()))
        app = (ROOT / "app" / "streamlit_app.py").read_text(encoding="utf-8")
        self.assertIn("No georeferenced points", app)
        self.assertIn("_species_row(selected, hpi, omitted)", app)
        self.assertNotIn("styles.css", app[app.find("def main"):])


class IucnAndPdfTests(unittest.TestCase):
    def test_missing_category_is_not_linked(self):
        line = _iucn_line(_row().to_dict())
        self.assertIn("not linked", line)
        self.assertNotIn("CR", line)

    def test_cited_code_is_shown(self):
        line = _iucn_line(
            _row(iucn_status="ok", iucn_category_code="CR", iucn_category="CR", iucn_year=2022).to_dict()
        )
        self.assertIn("CR", line)
        self.assertIn("2022", line)

    def test_pdf_bytes(self):
        pdf = render_field_brief_pdf(
            _row().to_dict(),
            ["Prefer cultivated material when feasible."],
        )
        self.assertTrue(pdf.startswith(b"%PDF"))
        self.assertGreater(len(pdf), 500)


if __name__ == "__main__":
    unittest.main()
