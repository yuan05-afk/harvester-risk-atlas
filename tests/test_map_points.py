"""Land placement for map markers. Averages that fall offshore must not be drawn."""
from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd

from harvester_risk_atlas.map_points import (
    PH_FIT_BOUNDS,
    choose_plot_point,
    hotspot_name,
    marker_radius,
    on_major_ph_land,
    on_ph_land,
    species_plot_points,
)

ROOT = Path(__file__).resolve().parents[1]


def _square_land(lat: float, lon: float) -> bool:
    return 14.0 <= lat <= 15.0 and 120.0 <= lon <= 121.0


def _square_near(lat: float, lon: float) -> bool:
    return 13.98 <= lat <= 15.02 and 119.98 <= lon <= 121.02


class ChoosePlotPointTests(unittest.TestCase):
    def test_offshore_average_snaps_to_nearest_land_record(self):
        # Mean sits east of the square, in the water. Two records: one on land, one farther offshore.
        chosen = choose_plot_point(
            14.5,
            121.8,
            [(14.6, 120.4), (14.5, 122.4), (10.0, 100.0)],
            on_land=_square_land,
            near_land=_square_near,
        )
        self.assertEqual(chosen, (14.6, 120.4, "land_record"))

    def test_on_land_average_stays(self):
        chosen = choose_plot_point(
            14.5,
            120.5,
            [(14.9, 120.9)],
            on_land=_square_land,
            near_land=_square_near,
        )
        self.assertEqual(chosen, (14.5, 120.5, "centroid"))

    def test_average_outside_the_philippines_uses_a_land_record(self):
        chosen = choose_plot_point(
            3.4,
            107.7,
            [(6.0, 116.5), (14.6, 121.0)],
            on_land=_square_land,
            near_land=_square_near,
        )
        self.assertEqual(chosen[2], "land_record")
        self.assertEqual((chosen[0], chosen[1]), (14.6, 121.0))

    def test_nothing_on_land_is_omitted(self):
        chosen = choose_plot_point(
            11.5,
            123.5,
            [(11.6, 123.6)],
            on_land=_square_land,
            near_land=_square_near,
        )
        self.assertIsNone(chosen)

    def test_missing_coordinates_are_omitted(self):
        self.assertIsNone(
            choose_plot_point(None, None, [], on_land=_square_land, near_land=_square_near)
        )


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
                "plot_source": ["centroid", "land_record"],
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

    def test_highest_hpi_when_selection_has_no_land_point(self):
        plotted = pd.DataFrame(
            {
                "scientific_name": ["Arcangelisia flava", "Lagerstroemia speciosa"],
                "plot_lat": [10.0, 14.0],
                "plot_lon": [122.0, 121.0],
                "plot_source": ["land_record", "centroid"],
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

    def test_every_marker_is_on_philippines_land(self):
        self.assertGreater(len(self.plotted), 20)
        for rec in self.plotted.itertuples(index=False):
            self.assertTrue(
                on_major_ph_land(rec.plot_lat, rec.plot_lon) or on_ph_land(rec.plot_lat, rec.plot_lon),
                f"{rec.scientific_name} plotted at {rec.plot_lat:.3f},{rec.plot_lon:.3f}",
            )

    def test_small_islet_averages_move_onto_a_main_island(self):
        # Sibuyan-sized means look like dots in the Visayan Sea at country zoom.
        vitex = self.plotted.loc[self.plotted["scientific_name"] == "Vitex negundo"].iloc[0]
        self.assertEqual(vitex.plot_source, "land_record")
        self.assertTrue(on_major_ph_land(vitex.plot_lat, vitex.plot_lon))
        abutra = self.plotted.loc[self.plotted["scientific_name"] == "Arcangelisia flava"].iloc[0]
        self.assertTrue(on_major_ph_land(abutra.plot_lat, abutra.plot_lon))

    def test_offshore_averages_move_and_unlocated_species_drop(self):
        abutra = self.plotted.loc[self.plotted["scientific_name"] == "Arcangelisia flava"].iloc[0]
        self.assertEqual(abutra.plot_source, "land_record")
        self.assertNotIn("Mentha × piperita", set(self.plotted["scientific_name"]))
        self.assertGreater(int((self.plotted["plot_source"] == "land_record").sum()), 10)

    def test_app_fits_the_philippines_and_offers_the_hotspot_control(self):
        app = (ROOT / "app" / "streamlit_app.py").read_text(encoding="utf-8")
        self.assertIn("Focus highest-HPI hotspot", app)
        self.assertIn("fit_bounds", app)
        self.assertNotIn("MarkerCluster", app)
        self.assertNotIn("zoom_start=6 if not focus else 8", app)


if __name__ == "__main__":
    unittest.main()
