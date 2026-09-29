"""Catalog integrity, scoring, charts, and a smoke pass over each page."""

from __future__ import annotations

import unittest
from pathlib import Path

from hra.brief import brief_markdown
from hra.charts import cohort_figure, compare_figure, decade_figure, waterfall_figure
from hra.data import by_id, demo_species, load_catalog, species_list
from hra.mapping import ESRI_GRAY, build_map
from hra.scoring import score_record
from hra.theme import FOREST, RISK_COLORS, STONE, risk_color

ROOT = Path(__file__).resolve().parents[1]


class CatalogTests(unittest.TestCase):
    def test_snapshot_exists(self):
        catalog = load_catalog()
        self.assertGreaterEqual(len(catalog["species"]), 8)
        self.assertIn("not an IUCN assessment", catalog["scope"])

    def test_iucn_fields_are_sourced(self):
        for species in load_catalog()["species"]:
            iucn = species.get("iucn")
            if iucn is None:
                continue
            self.assertIn(iucn["code"], {"CR", "EN", "VU", "NT", "LC"})
            self.assertTrue(iucn.get("source_title"))
            self.assertTrue(iucn.get("iucn_taxon_id"))
            self.assertTrue(iucn.get("url", "").startswith("https://www.iucnredlist.org/"))
            self.assertNotIn("assessment_year", iucn)

    def test_missing_category_is_not_filled(self):
        recorded = [row for row in species_list() if row["iucn"] is None]
        self.assertTrue(recorded)
        for row in recorded:
            self.assertIsNone(row["score"]["listing"])
            self.assertIsNone(row["score"]["hpi"])

    def test_demo_species_is_scored(self):
        demo = demo_species()
        self.assertEqual(demo["scientific_name"], "Aquilaria malaccensis")
        self.assertEqual(demo["iucn"]["code"], "CR")
        self.assertIsNotNone(demo["score"]["hpi"])
        self.assertIn(demo["score"]["band"], RISK_COLORS)


class ScoringTests(unittest.TestCase):
    def test_partial_is_not_zero(self):
        score = score_record({"iucn": None, "occurrences": {"georeferenced_count": 10, "top_country_share": 0.9}})
        self.assertIsNone(score["hpi"])
        self.assertNotEqual(score["hpi"], 0)
        self.assertTrue(score["gaps"])

    def test_complete_sum(self):
        score = score_record(
            {
                "iucn": {"code": "NT"},
                "occurrences": {"georeferenced_count": 40, "top_country_share": 0.5},
            }
        )
        self.assertEqual(score["listing"], 18)
        self.assertEqual(score["concentration"], 25)
        self.assertEqual(score["hpi"], 43)
        self.assertEqual(score["band"], "Moderate")

    def test_risk_color_only_for_bands(self):
        self.assertEqual(risk_color(None), "#8e8e93")
        self.assertEqual(risk_color("Severe"), RISK_COLORS["Severe"])


class ChartTests(unittest.TestCase):
    def test_cohort_stays_neutral(self):
        figure = cohort_figure(species_list())
        self.assertEqual(figure.data[0].marker.color, FOREST)

    def test_waterfall_colors_only_the_total(self):
        demo = demo_species()
        figure = waterfall_figure(demo["score"])
        colors = list(figure.data[0].marker.color)
        self.assertEqual(colors[0], FOREST)
        self.assertEqual(colors[1], STONE)
        self.assertEqual(colors[2], RISK_COLORS[demo["score"]["band"]])

    def test_partial_waterfall_has_no_fake_total(self):
        partial = next(row for row in species_list() if row["score"]["hpi"] is None and row["score"]["listing"] is not None)
        figure = waterfall_figure(partial["score"])
        self.assertEqual(len(figure.data[0].x), 1)

    def test_decade_and_compare(self):
        demo = demo_species()
        other = by_id("boswellia-sacra")
        self.assertIsNotNone(decade_figure(demo))
        figure = compare_figure(demo, other)
        self.assertEqual(figure.data[0].marker.color, FOREST)
        self.assertEqual(figure.data[1].marker.color, STONE)
        self.assertEqual(figure.layout.title.text, "Component comparison")
        self.assertLess(figure.layout.legend.y, 0)
        self.assertGreaterEqual(figure.layout.margin.t, 64)
        self.assertGreaterEqual(figure.layout.margin.b, 80)

    def test_empty_decade(self):
        self.assertIsNone(decade_figure({"occurrences": {"years": []}}))


class BriefAndMapTests(unittest.TestCase):
    def test_brief_does_not_invent_a_score(self):
        partial = next(row for row in species_list() if row["score"]["hpi"] is None)
        other = demo_species()
        text = brief_markdown(partial, other)
        self.assertIn("HPI is not scored", text)
        self.assertIn("HPI is not scored", text)
        self.assertIn("population estimate", text.casefold())
        self.assertNotIn("population decline", text.casefold())

    def test_compare_cards_render_as_html(self):
        from hra.ui import compare_card_html

        demo = demo_species()
        other = by_id("boswellia-sacra")
        long_name = {
            "scientific_name": "Arcangelisia flava",
            "common_name": None,
            "vernacular_names": [],
            "iucn": {"code": "LC", "label": "Least Concern"},
            "score": {"complete": True, "hpi": 12, "band": "Lower", "listing": 8, "concentration": 4, "gaps": []},
        }
        for species in (demo, other, long_name):
            fragment = compare_card_html(species)
            self.assertTrue(fragment.startswith("<div"))
            for line in fragment.splitlines():
                self.assertFalse(line.startswith(" "), line)
            self.assertNotIn("```", fragment)
        self.assertIn('class="genus">Arcangelisia</span>', compare_card_html(long_name))
        self.assertIn('class="epithet">flava</span>', compare_card_html(long_name))
        self.assertNotIn("ARCANGELISI", compare_card_html(long_name))

    def test_map_uses_esri_gray(self):
        atlas = build_map(species_list()[:2])
        tiles = " ".join(child.tiles for child in atlas._children.values() if hasattr(child, "tiles"))
        self.assertIn("World_Light_Gray_Base", tiles)
        self.assertIn(ESRI_GRAY, tiles)


class AppSmokeTests(unittest.TestCase):
    def test_each_page_and_empty_filter(self):
        from streamlit.testing.v1 import AppTest

        import hra.ui as ui

        ui.st_folium = lambda *args, **kwargs: {"last_object_clicked": None}
        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=40)
        app.run()
        self.assertEqual(len(app.exception), 0)
        app.sidebar.toggle[0].set_value(True).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.sidebar.selectbox[0].value, "aquilaria-malaccensis")
        self.assertEqual(app.sidebar.selectbox[1].value, "boswellia-sacra")
        labels = [button.label for button in app.sidebar.button]
        self.assertEqual(labels[:3], ["Map", "Dossier", "Brief"])
        app.sidebar.button[1].click().run()
        self.assertEqual(len(app.exception), 0)
        app.sidebar.button[2].click().run()
        self.assertEqual(len(app.exception), 0)
        app.sidebar.button[0].click().run()
        self.assertEqual(len(app.exception), 0)
        app.text_input[0].set_value("zzzz-not-a-species").run()
        self.assertEqual(len(app.exception), 0)
        blob = " ".join(block.value for block in app.markdown)
        self.assertIn("No species match", blob)


if __name__ == "__main__":
    unittest.main()
