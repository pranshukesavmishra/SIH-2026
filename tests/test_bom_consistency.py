"""
The parts list exists in three places. They must not disagree.

A hand-maintained copy of this table once summed to Rs 5,944 while
claiming Rs 6,124, and the row it was missing was the diametric magnets --
the single part whose absence stops the build before it starts. Nobody
noticed because nothing compared the table to itself.

So: docs/data/bom_tier_a.json is the source, the markdown table and the
printed PDF are generated from it, and this file fails if any of the
three drift.
"""
from __future__ import annotations

import json
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
BOM = ROOT / "docs" / "data" / "bom_tier_a.json"
DOC = ROOT / "docs" / "TERMINAL_MK3.md"
PDF = ROOT / "docs" / "submission" / "ZeroDrift_Mk3_Build_Guide.pdf"

VALID_BASIS = {"verified", "estimate", "reuse Mk1"}


@pytest.fixture(scope="module")
def bom():
    return json.loads(BOM.read_text())


def rupees(text):
    return {int(m.replace(",", "")) for m in re.findall(r"₹([\d,]+)", text)}


# -- the data is internally sound ---------------------------------------

def test_stated_total_equals_the_sum_of_the_items(bom):
    computed = sum(i["qty"] * i["unit_inr"]
                   for s in bom["sections"] for i in s["items"])
    assert computed == bom["total_inr"], (
        f"BOM sections sum to Rs {computed:,} but total_inr says "
        f"Rs {bom['total_inr']:,}")


def test_every_item_declares_whether_its_price_was_verified(bom):
    for s in bom["sections"]:
        for i in s["items"]:
            assert i["price_basis"] in VALID_BASIS, (
                f"{i['item']!r} has price_basis {i['price_basis']!r}; a price "
                "whose provenance is unstated cannot be defended to a judge")


def test_no_item_is_silently_free(bom):
    """A zero price must be an explicit reuse, not an omission."""
    for s in bom["sections"]:
        for i in s["items"]:
            if i["unit_inr"] == 0:
                assert i["price_basis"] == "reuse Mk1", (
                    f"{i['item']!r} costs nothing but is not marked as reused")


# -- the parts that stop the build dead are present ---------------------

@pytest.mark.parametrize("needle, why", [
    ("Diametric magnet",
     "an AS5600 with no magnet rotating in front of it reads a constant; "
     "this was missing once already"),
    ("100 µF",
     "required across VMOT by the A4988 datasheet; omitting it destroys "
     "both drivers on first power-up"),
    ("TCA9548A",
     "both AS5600s are fixed at address 0x36 and cannot share a bus"),
])
def test_build_stopping_parts_are_on_the_list(bom, needle, why):
    names = [i["item"] for s in bom["sections"] for i in s["items"]]
    assert any(needle in n for n in names), f"{needle} missing -- {why}"


def test_the_deleted_servos_have_not_crept_back(bom):
    """
    Mk1 stripped two MG90S servos. The fine-servo stage is deleted by
    design; a servo reappearing here means someone rebuilt the old BOM.
    """
    names = " ".join(i["item"] for s in bom["sections"] for i in s["items"]).lower()
    assert "mg90s" not in names and "servo" not in names


# -- the rendered copies agree with the data ----------------------------

def test_markdown_table_carries_every_item_and_the_right_total(bom):
    doc = DOC.read_text()
    for s in bom["sections"]:
        for i in s["items"]:
            assert i["item"] in doc, f"{i['item']!r} is in the BOM but not in {DOC.name}"
    assert f"₹{bom['total_inr']:,}" in doc


@pytest.mark.skipif(not PDF.exists(), reason="printed guide not present")
def test_printed_guide_states_the_same_total(bom):
    import shutil
    import subprocess
    if not shutil.which("pdftotext"):
        pytest.skip("pdftotext unavailable")
    text = subprocess.run(["pdftotext", "-layout", str(PDF), "-"],
                          capture_output=True, text=True, timeout=60).stdout
    assert bom["total_inr"] in rupees(text), (
        f"the printed guide does not state Rs {bom['total_inr']:,}; it is the "
        "document someone actually carries to the shop, so it is the one that "
        "must not be stale")


# -- the stage demo runs from a laptop, with no wall socket -------------

def test_no_mains_adapter_is_on_the_list(bom):
    """
    The demo is given on a stage from a laptop, so the build must not
    depend on a wall socket being available and working. A mains adapter
    reappearing here means someone reverted the power design without
    reading why it changed.
    """
    names = " ".join(i["item"] for s in bom["sections"] for i in s["items"]).lower()
    assert "dc power adapter" not in names and "psu" not in names


def test_the_motor_rail_has_a_supply_that_is_not_the_laptop(bom):
    """
    USB gives 5 V and the A4988 needs 8-35 V on VMOT, so the steppers
    cannot run off the laptop however the rest is wired. Something has to
    lift a portable supply to at least 8 V, or the gimbal does not move
    and the entire demo is a still photograph.
    """
    names = [i["item"].lower() for s in bom["sections"] for i in s["items"]]
    assert any("battery pack" in n or "trigger" in n for n in names), (
        "nothing on the list can supply the A4988's VMOT away from mains")


def test_both_nanos_have_a_usb_cable(bom):
    """
    Clone Nanos ship without one often enough that this is a real
    build-stopper, and it is the kind of omission nobody notices until
    the shops are shut.
    """
    for s in bom["sections"]:
        for i in s["items"]:
            if "usb-b" in i["item"].lower() or "mini-usb" in i["item"].lower():
                assert i["qty"] >= 2, "one cable, two Nanos"
                return
    raise AssertionError("no USB cable for the Nanos is on the list")


def test_every_item_says_where_to_buy_it(bom):
    """
    Routing used to live only in the rendered HTML, so adding an item
    meant hand-editing a row and hand-adjusting three column subtotals.
    It belongs with the price.
    """
    allowed = {"amar", "blinkit", "online", "have"}
    for s in bom["sections"]:
        for i in s["items"]:
            assert i.get("source") in allowed, (
                f"{i['item']!r} does not say where to buy it")


def test_the_buy_list_column_subtotals_add_up_to_the_grand_total(bom):
    """
    Three source columns and a grand total is four numbers that can
    disagree. They are generated together now; this checks they still do.
    """
    import re
    html = (DOC.parent / "submission" / "buylist_checklist_source.html").read_text()
    row = re.search(r'<tr class="totrow">(.*?)</tr>', html, re.S).group(1)
    figures = [int(x.replace(",", "")) for x in re.findall(r"₹([\d,]+)", row)]
    grand, columns = figures[0], figures[1:]
    assert grand == bom["total_inr"]
    assert sum(columns) == grand, f"columns sum to {sum(columns):,}, total says {grand:,}"
