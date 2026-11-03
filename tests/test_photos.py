"""Every plant in the atlas has an openly licensed picture, and credits stay honest."""
import json

import pytest

from harvester_risk_atlas.config import ROOT
from harvester_risk_atlas.sources.photos import crop_box

SPECIES = ROOT / "web" / "public" / "data" / "species.json"
PUBLIC = ROOT / "web" / "public"
OPEN = {"CC0", "CC BY 4.0", "CC BY-NC 4.0"}


def _species():
    return json.loads(SPECIES.read_text(encoding="utf-8"))


def test_every_plant_has_a_photo_file():
    missing = [s["slug"] for s in _species() if not s["photo"] or not (PUBLIC / s["photo"]["src"]).exists()]
    assert missing == []


def test_every_photo_is_credited_and_openly_licensed():
    for s in _species():
        p = s["photo"]
        assert p["licence"] in OPEN, s["slug"]
        assert p["creator"], s["slug"]
        assert p["page"].startswith("https://"), s["slug"]
        assert p["kind"] in {"photo", "specimen"}, s["slug"]
        assert p["source"], s["slug"]


def test_specimen_scans_are_labelled_as_such():
    kinds = {s["slug"]: s["photo"]["kind"] for s in _species()}
    assert kinds["arcangelisia-flava"] == "specimen"
    assert kinds["hydnocarpus-alcalae"] == "specimen"


def test_crop_box_scales_fractions_to_pixels():
    assert crop_box((1000, 2000), "0.1,0.25,0.9,0.75") == (100, 500, 900, 1500)
    assert crop_box((1000, 2000), "") is None


@pytest.mark.parametrize("bad", ["0,0,1", "0.5,0,0.4,1", "0,0,1.2,1", "-0.1,0,1,1"])
def test_crop_box_rejects_bad_specs(bad):
    with pytest.raises(ValueError):
        crop_box((100, 100), bad)
