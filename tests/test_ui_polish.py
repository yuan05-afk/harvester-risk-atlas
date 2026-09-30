"""Snapshot extras: legends under the axes, compare-card HTML, IUCN line, PDF brief."""
from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd

from harvester_risk_atlas.charts import compare_components, hpi_distribution
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

    def test_primary_descendants_forced_white(self):
        css = self.css
        self.assertIn('.stButton > button[kind="primary"]', css)
        self.assertIn('button[data-testid="stBaseButton-primary"]', css)
        self.assertIn('.stDownloadButton > button[kind="primary"]', css)
        self.assertIn('button[data-testid="stBaseButton-primary"] *', css)
        self.assertIn("color: #ffffff !important", css)
        self.assertIn("fill: #ffffff !important", css)
        self.assertIn("-webkit-text-fill-color: #ffffff !important", css)
        self.assertIn("#245a42", css)
        self.assertNotIn("linear-gradient", css)
        # Hover/focus/active descendants stay white (label is a nested p/span).
        self.assertIn('button[data-testid="stBaseButton-primary"]:hover *', css)
        self.assertIn('button[data-testid="stBaseButton-primary"]:active *', css)

    def test_demo_caption_has_no_accent_rail(self):
        import re

        match = re.search(r"\.hra-demo-caption\s*\{([^}]*)\}", self.css)
        self.assertIsNotNone(match)
        block = match.group(1)
        self.assertNotIn("border-left", block)
        self.assertNotIn("accent-soft", block)
        self.assertNotIn("0 var(--radius)", block)
        self.assertIn("var(--surface)", block)
        self.assertIn("1px solid var(--hairline)", block)
        self.assertIn("border-radius: var(--radius)", block)
        self.assertNotIn("border-left", self.css)

    def test_howto_and_talktrack_are_hairline_only(self):
        import re

        for cls in (".hra-howto", ".hra-talktrack"):
            match = re.search(rf"{re.escape(cls)}\s*\{{([^}}]*)\}}", self.css)
            self.assertIsNotNone(match, cls)
            block = match.group(1)
            self.assertNotIn("box-shadow", block)
            self.assertIn("1px solid var(--hairline)", block)

    def test_field_brief_pdf_is_secondary_html_stays_primary(self):
        pdf_at = self.app.find("Download field brief (PDF)")
        html_at = self.app.find("Download field brief (HTML)")
        self.assertGreater(html_at, 0)
        self.assertGreater(pdf_at, html_at)
        html_call = self.app[html_at:pdf_at]
        pdf_call = self.app[pdf_at:pdf_at + 450]
        self.assertIn('type="primary"', html_call)
        self.assertIn('type="secondary"', pdf_call)

    def test_leaflet_attribution_muted_inside_map(self):
        self.assertIn(".leaflet-control-attribution", self.app)
        self.assertIn(".leaflet-control-attribution a{color:#86868b !important}", self.app)


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
