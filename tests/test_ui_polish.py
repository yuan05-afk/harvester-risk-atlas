"""Legend placement, compare-card HTML, IUCN badge, weights copy, and PDF brief."""
from __future__ import annotations

import unittest

import pandas as pd

from harvester_risk_atlas.charts import compare_components, hpi_distribution
from harvester_risk_atlas.hpi import weights_explainer_markdown
from harvester_risk_atlas.markup import (
    compare_card_html,
    compare_grid_html,
    iucn_badge_html,
    iucn_plain_label,
    map_howto_html,
)
from harvester_risk_atlas.pdf_brief import render_field_brief_pdf


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
        figure = compare_components(_row(), _row(scientific_name="Lagerstroemia speciosa", vernacular_ph="banaba"))
        self.assertEqual(figure.layout.title.text, "Component comparison")
        self.assertLess(figure.layout.legend.y, 0)
        self.assertGreaterEqual(figure.layout.margin.t, 64)
        self.assertGreaterEqual(figure.layout.margin.b, 80)

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
        self.assertGreaterEqual(figure.layout.margin.t, 64)
        self.assertGreaterEqual(figure.layout.margin.b, 80)


class CompareCardTests(unittest.TestCase):
    def test_cards_are_dedented_html_and_keep_the_binomial(self):
        left = _row()
        right = _row(scientific_name="Lagerstroemia speciosa", vernacular_ph="banaba")
        fragment = compare_grid_html(left, right)
        self.assertTrue(fragment.startswith("<div"))
        for line in fragment.splitlines():
            self.assertFalse(line.startswith(" "), line)
        self.assertNotIn("```", fragment)
        card = compare_card_html(left)
        self.assertIn('class="genus">Arcangelisia</span>', card)
        self.assertIn('class="epithet">flava</span>', card)
        self.assertNotIn("ARCANGELISI", card)
        self.assertNotIn("text-transform:uppercase", card.lower())


class IucnBadgeTests(unittest.TestCase):
    def test_missing_category_is_not_recorded(self):
        badge = iucn_badge_html(_row())
        self.assertIn("Not recorded", badge)
        self.assertIn("unknown", badge)
        self.assertNotIn(">CR<", badge)
        self.assertEqual(iucn_plain_label(_row()), "Not recorded")

    def test_cited_code_renders(self):
        row = _row(iucn_status="ok", iucn_category_code="CR", iucn_year=2022)
        badge = iucn_badge_html(row)
        self.assertIn('class="iucn-badge cr"', badge)
        self.assertIn(">CR<", badge)
        self.assertIn("Critically Endangered", badge)
        self.assertIn("2022", badge)
        self.assertEqual(iucn_plain_label(row), "CR — Critically Endangered (2022)")


class MethodsAndMapTests(unittest.TestCase):
    def test_weights_sum_and_are_named(self):
        text = weights_explainer_markdown()
        self.assertIn("0.30", text)
        self.assertIn("0.25", text)
        self.assertIn("0.20", text)
        self.assertIn("Sum 1.00.", text)
        self.assertIn("never an input", text)

    def test_map_howto_strip(self):
        fragment = map_howto_html()
        self.assertTrue(fragment.startswith("<div"))
        self.assertIn("How to read this map", fragment)
        self.assertIn("not harvest sites", fragment)
        for line in fragment.splitlines():
            self.assertFalse(line.startswith(" "))


class PdfBriefTests(unittest.TestCase):
    def test_pdf_bytes_and_missing_iucn(self):
        pdf = render_field_brief_pdf(_row().to_dict(), ["Prefer cultivated material when feasible."])
        self.assertTrue(pdf.startswith(b"%PDF"))
        self.assertGreater(len(pdf), 800)


if __name__ == "__main__":
    unittest.main()
