# tests/timeline/test_timeline_hashchain.py

import pytest
from arvis.timeline.timeline_hashchain import hash_entry, TimelineHashChain
from tests.timeline.helpers import make_entry
from tests.timeline.helpers import make_entries

def test_hash_entry_deterministic():

    e = make_entry(1)

    h1 = hash_entry(e)
    h2 = hash_entry(e)

    assert h1 == h2

def test_hash_entry_changes_on_mutation():

    e1 = make_entry(1)
    e2 = make_entry(1)

    # mutate field
    e2 = e2.__class__(**{**e2.__dict__, "title": "different"})

    assert hash_entry(e1) != hash_entry(e2)


def test_hashchain_deterministic():

    entries = make_entries(5)

    c1 = TimelineHashChain.build(entries)
    c2 = TimelineHashChain.build(entries)

    assert c1.hashes == c2.hashes


def test_hashchain_order_sensitive():

    entries = make_entries(3)

    c1 = TimelineHashChain.build(entries)
    c2 = TimelineHashChain.build(reversed(entries))

    assert c1.hashes != c2.hashes


def test_append_equivalent_to_build():

    entries = make_entries(4)

    chain = TimelineHashChain.build(entries[:3])
    chain2 = chain.append(entries[3])

    full = TimelineHashChain.build(entries)

    assert chain2.hashes == full.hashes


def test_hashchain_verify_success():

    entries = make_entries(5)

    chain = TimelineHashChain.build(entries)

    chain.verify(entries)


def test_hashchain_verify_detects_corruption():

    entries = make_entries(4)

    chain = TimelineHashChain.build(entries)

    corrupted = list(entries)
    corrupted[2] = corrupted[2].__class__(**{**corrupted[2].__dict__, "title": "evil"})

    with pytest.raises(ValueError):
        chain.verify(corrupted)