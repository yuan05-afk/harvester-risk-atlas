"""Map markers use the true sample average, including means that fall offshore."""
from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd

from harvester_risk_atlas.map_points import (
    PH_FIT_BOUNDS,
    choose_plot_point,
    hotspot_name,
    marker_radius,
    on_ph_land,
    species_plot_points,
)

ROOT = Path(__file__).resolve().parents[1]


class ChoosePlotPointTests(unittest.TestCase):
    def test_offshore_average_stays_at_the_true_mean(self):
        # Mean sits east of Luzon, in the water. A land record must not replace it.
        chosen = choose_plot_point(14.5, 121.8)
        self.assertEqual(chosen, (14.5, 121.8, "centroid"))

    def test_on_land_average_stays(self):
        chosen = choose_plot_point(14.5, 120.5)
        self.assertEqual(chosen, (14.5, 120.5, "centroid"))

    def test_average_west_of_the_philippines_stays(self):
        # Eurycoma-like mean: south of Vietnam, west of the country box.
        chosen = choose_plot_point(3.4183908, 107.68206095)
        self.assertEqual(chosen[2], "centroid")
        self.assertAlmostEqual(chosen[0], 3.4183908)
        self.assertAlmostEqual(chosen[1], 107.68206095)

    def test_visayan_sea_mean_is_kept(self):
        chosen = choose_plot_point(11.5, 123.5)
        self.assertEqual(chosen, (11.5, 123.5, "centroid"))

    def test_missing_coordinates_are_omitted(self):
        self.assertIsNone(choose_plot_point(None, None))
        self.assertIsNone(choose_plot_point(float("nan"), 121.0))
        self.assertIsNone(choose_plot_point(14.5, None))


class OccurrencesDoNotMoveTheMeanTests(unittest.TestCase):
    def test_land_records_are_not_a_placement_source(self):
        hpi = pd.DataFrame(
            {
                "scientific_name": ["Eurycoma longifolia", "Mentha × piperita"],
                "lat_mean": [3.4, None],
                "lon_mean": [107.7, None],
            }
        )
        occurrences = pd.DataFrame(
            {
                "scientific_name": ["Eurycoma longifolia", "Eurycoma longifolia", "Mentha × piperita"],
                "lat": [14.6, 10.3, 14.6],
                "lon": [121.0, 123.9, 121.0],
            }
        )
        plotted = species_plot_points(hpi, occurrences)
        self.assertEqual(list(plotted["scientific_name"]), ["Eurycoma longifolia"])
        self.assertAlmostEqual(float(plotted.iloc[0]["plot_lat"]), 3.4)
        self.assertAlmostEqual(float(plotted.iloc[0]["plot_lon"]), 107.7)
        self.assertEqual(plotted.iloc[0]["plot_source"], "centroid")


class HotspotAndRadiusTests(unittest.TestCase):
    def test_selected_species_wins_when_it_can_be_plotted(self):
        plotted = pd.DataFrame(
            {
                "scientific_name": ["A a", "B b"],
                "plot_lat": [14.5, 10.0],
                "plot_lon": [121.0, 124.0],
                "plot_source": ["centroid", "centroid"],
            }
        )
        scores = pd.DataFrame({"scientific_name": ["A a", "B b"], "hpi": [0.2, 0.9]})
        self.assertEqual(hotspot_name(plotted, scores, "A a"), "A a")

    def test_mentha_never_wins_focus(self):
        plotted = pd.DataFrame(
            {
                "scientific_name": ["Mentha × piperita", "Arcangelisia flava"],
                "plot_lat": [14.5, 10.3],
                "plot_lon": [121.0, 123.9],
                "plot_source": ["centroid", "centroid"],
            }
        )
        scores = pd.DataFrame(
            {
                "scientific_name": ["Mentha × piperita", "Arcangelisia flava"],
                "hpi": [0.99, 0.52],
            }
        )
        self.assertEqual(hotspot_name(plotted, scores, "Mentha × piperita"), "Arcangelisia flava")
        self.assertEqual(hotspot_name(plotted, scores, None), "Arcangelisia flava")

    def test_highest_hpi_when_selection_is_not_plotted(self):
        plotted = pd.DataFrame(
            {
                "scientific_name": ["Arcangelisia flava", "Lagerstroemia speciosa"],
                "plot_lat": [11.047, 14.0],
                "plot_lon": [121.973, 121.0],
                "plot_source": ["centroid", "centroid"],
            }
        )
        scores = pd.DataFrame(
            {
                "scientific_name": ["Mentha × piperita", "Arcangelisia flava", "Lagerstroemia speciosa"],
                "hpi": [0.99, 0.52, 0.40],
            }
        )
        self.assertEqual(hotspot_name(plotted, scores, "Mentha × piperita"), "Arcangelisia flava")

    def test_radius_is_stronger_than_a_speck_and_stays_bounded(self):
        self.assertGreaterEqual(marker_radius(0), 12)
        self.assertLessEqual(marker_radius(1), 18)
        self.assertLess(marker_radius(0.2), marker_radius(0.8))

    def test_country_fit_covers_the_archipelago(self):
        (south, west), (north, east) = PH_FIT_BOUNDS
        self.assertLess(south, 5.5)
        self.assertGreater(north, 18.0)
        self.assertLess(west, 118.0)
        self.assertGreater(east, 126.0)


class ShippedMaskTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hpi = pd.read_csv(ROOT / "data" / "processed" / "hpi_scores.csv")
        cls.occ = pd.read_parquet(ROOT / "data" / "processed" / "occurrences_sample.parquet")
        cls.plotted = species_plot_points(cls.hpi, cls.occ)

    def test_known_land_and_water(self):
        self.assertTrue(on_ph_land(14.60, 120.98))  # Manila
        self.assertTrue(on_ph_land(10.32, 123.89))  # Cebu
        self.assertFalse(on_ph_land(11.60, 123.60))  # Visayan Sea
        self.assertFalse(on_ph_land(11.047, 121.973))  # abutra sample average

    def test_every_marker_is_the_true_sample_average(self):
        located = self.hpi.dropna(subset=["lat_mean", "lon_mean"])
        self.assertGreater(len(self.plotted), 20)
        self.assertEqual(
            set(self.plotted["scientific_name"]),
            set(located["scientific_name"].astype(str)),
        )
        merged = located.merge(self.plotted, on="scientific_name", how="inner")
        for rec in merged.itertuples(index=False):
            self.assertAlmostEqual(rec.plot_lat, rec.lat_mean)
            self.assertAlmostEqual(rec.plot_lon, rec.lon_mean)
            self.assertEqual(rec.plot_source, "centroid")
        self.assertEqual(int((self.plotted["plot_source"] == "land_record").sum()), 0)
        self.assertNotIn("Mentha × piperita", set(self.plotted["scientific_name"]))

    def test_eurycoma_stays_west_of_the_philippines(self):
        row = self.plotted.loc[self.plotted["scientific_name"] == "Eurycoma longifolia"].iloc[0]
        source = self.hpi.loc[self.hpi["scientific_name"] == "Eurycoma longifolia"].iloc[0]
        self.assertAlmostEqual(row.plot_lat, source.lat_mean)
        self.assertAlmostEqual(row.plot_lon, source.lon_mean)
        self.assertLess(float(row.plot_lon), 116.0)
        self.assertFalse(on_ph_land(row.plot_lat, row.plot_lon))
        self.assertEqual(row.plot_source, "centroid")

    def test_channel_means_are_not_moved_onto_a_main_island(self):
        for name in ("Vitex negundo", "Arcangelisia flava"):
            row = self.plotted.loc[self.plotted["scientific_name"] == name].iloc[0]
            source = self.hpi.loc[self.hpi["scientific_name"] == name].iloc[0]
            self.assertAlmostEqual(row.plot_lat, source.lat_mean)
            self.assertAlmostEqual(row.plot_lon, source.lon_mean)
            self.assertEqual(row.plot_source, "centroid")
        abutra = self.plotted.loc[self.plotted["scientific_name"] == "Arcangelisia flava"].iloc[0]
        self.assertFalse(on_ph_land(abutra.plot_lat, abutra.plot_lon))

    def test_app_fits_the_philippines_and_offers_the_hotspot_control(self):
        app = (ROOT / "app" / "streamlit_app.py").read_text(encoding="utf-8")
        self.assertIn("Focus highest-HPI hotspot", app)
        self.assertIn("fit_bounds", app)
        self.assertIn("PH_FIT_BOUNDS", app)
        self.assertIn("NEVER_FOCUS", (ROOT / "src" / "harvester_risk_atlas" / "map_points.py").read_text(encoding="utf-8"))
        self.assertNotIn("MarkerCluster", app)
        self.assertNotIn("zoom_start=6 if not focus else 8", app)
        self.assertNotIn("land_record", app)
        self.assertNotIn("nearest Philippines land record", app)
        self.assertNotIn("Nearest land record", app)
        self.assertIn("This mean is not on Philippines land.", app)


if __name__ == "__main__":
    unittest.main()
