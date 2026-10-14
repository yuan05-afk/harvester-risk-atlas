"""Occurrence cleaning rules and IUCN-style range metrics."""
from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from harvester_risk_atlas.clean import clean_occurrences, flag_records  # noqa: E402
from harvester_risk_atlas.grid import aoo_km2, eoo_km2, h3_cells, species_range_table  # noqa: E402
from harvester_risk_atlas.sources.wcvp import classify  # noqa: E402

# Points on Philippine land (Mt Makiling area, Luzon; Cebu City; Davao City).
LUZON = (14.135, 121.200)
CEBU = (10.315, 123.885)
DAVAO = (7.070, 125.610)


def rec(lat, lon, **kw):
    base = {
        "scientific_name": "Testus plantus",
        "lat": lat,
        "lon": lon,
        "coordinate_uncertainty_m": None,
        "year": 2020,
        "basis_of_record": "HUMAN_OBSERVATION",
        "establishment_means": None,
        "issues": "",
    }
    base.update(kw)
    return base


class CleaningRules(unittest.TestCase):
    def reasons(self, rows):
        return flag_records(pd.DataFrame(rows)).tolist()

    def test_good_land_record_is_kept(self):
        self.assertEqual(self.reasons([rec(*LUZON)]), [""])

    def test_each_rule_has_its_own_reason(self):
        rows = [
            rec(None, None),
            rec(0.0, 121.0),
            rec(*LUZON, issues="COUNTRY_COORDINATE_MISMATCH;RECORDED_DATE_INVALID"),
            rec(*LUZON, basis_of_record="LIVING_SPECIMEN"),
            rec(*LUZON, establishment_means="MANAGED"),
            rec(*LUZON, coordinate_uncertainty_m=25_000),
            rec(14.0, 121.0),
            rec(12.88, 121.77),
            rec(12.0, 119.5 + 0.123),  # open sea west of Panay
        ]
        self.assertEqual(
            self.reasons(rows),
            [
                "missing_coordinates",
                "zero_coordinates",
                "severe_issue",
                "not_wild_basis",
                "cultivated",
                "imprecise",
                "imprecise",
                "country_centroid",
                "off_land",
            ],
        )

    def test_benign_issue_is_not_dropped(self):
        self.assertEqual(self.reasons([rec(*LUZON, issues="COORDINATE_ROUNDED")]), [""])

    def test_duplicates_collapse_to_one(self):
        rows = [rec(*LUZON), rec(*LUZON), rec(*LUZON, year=1990)]
        self.assertEqual(self.reasons(rows), ["", "duplicate", ""])

    def test_report_accounts_for_every_record(self):
        rows = [rec(*LUZON), rec(*LUZON), rec(None, None), rec(*CEBU)]
        kept, report = clean_occurrences(pd.DataFrame(rows))
        self.assertEqual(len(kept), 2)
        row = report.iloc[0]
        self.assertEqual(row["n_fetched"], 4)
        self.assertEqual(row["n_kept"], 2)
        self.assertEqual(row["duplicate"] + row["missing_coordinates"], 2)


class RangeMetrics(unittest.TestCase):
    def test_aoo_counts_2km_cells(self):
        # Same point twice → one cell. 0.0001° apart → still one cell.
        self.assertEqual(aoo_km2([LUZON[0], LUZON[0] + 0.0001], [LUZON[1], LUZON[1]]), 4.0)
        # Three far-apart points → three cells.
        lats, lons = zip(LUZON, CEBU, DAVAO)
        self.assertEqual(aoo_km2(lats, lons), 12.0)

    def test_aoo_is_zero_without_records(self):
        self.assertEqual(aoo_km2([], []), 0.0)

    def test_eoo_never_below_aoo(self):
        self.assertEqual(eoo_km2([LUZON[0]], [LUZON[1]], aoo=4.0), 4.0)

    def test_eoo_triangle_matches_hand_calculation(self):
        lats, lons = zip(LUZON, CEBU, DAVAO)
        eoo = eoo_km2(lats, lons)
        # Spherical-excess area of the same triangle, as an independent check.
        def xyz(lat, lon):
            la, lo = math.radians(lat), math.radians(lon)
            return (math.cos(la) * math.cos(lo), math.cos(la) * math.sin(lo), math.sin(la))

        a, b, c = (xyz(*p) for p in (LUZON, CEBU, DAVAO))
        triple = abs(
            a[0] * (b[1] * c[2] - b[2] * c[1])
            - a[1] * (b[0] * c[2] - b[2] * c[0])
            + a[2] * (b[0] * c[1] - b[1] * c[0])
        )
        dot = 1 + sum(x * y for x, y in zip(a, b)) + sum(x * y for x, y in zip(b, c)) + sum(
            x * y for x, y in zip(c, a)
        )
        excess = 2 * math.atan2(triple, dot)
        expected = excess * 6371.0**2
        # Sphere vs WGS84 ellipsoid differ by well under 1% here.
        self.assertAlmostEqual(eoo / expected, 1.0, delta=0.01)

    def test_range_table_lists_unique_hexes(self):
        occ = pd.DataFrame(
            [rec(*LUZON), rec(LUZON[0] + 0.001, LUZON[1]), rec(*DAVAO)]
        )
        table = species_range_table(occ)
        self.assertEqual(table.loc[0, "n_clean"], 3)
        self.assertEqual(table.loc[0, "n_hex"], len(set(h3_cells(occ["lat"], occ["lon"]))))
        self.assertEqual(table.loc[0, "n_hex"], 2)


class Nativity(unittest.TestCase):
    def test_native_endemic_introduced_and_absent(self):
        native = [{"locationId": "TDWG:PHI", "establishmentMeans": None}]
        self.assertEqual(classify(native), {"ph_status": "native", "ph_endemic": True, "n_native_regions": 1})
        wider = native + [{"locationId": "TDWG:BOR", "establishmentMeans": None}]
        self.assertFalse(classify(wider)["ph_endemic"])
        intro = [{"locationId": "TDWG:PHI", "establishmentMeans": "INTRODUCED"}]
        self.assertEqual(classify(intro)["ph_status"], "introduced")
        self.assertEqual(classify([{"locationId": "TDWG:BOR", "establishmentMeans": None}])["ph_status"], "not_listed")


if __name__ == "__main__":
    unittest.main()
