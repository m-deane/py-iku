"""DSS-fidelity round-trip acceptance harness.

Loads canonical DSS recipe / processor JSON shapes derived from the public-doc
snapshot at ``docs/dataiku-reference/`` and asserts they round-trip cleanly
through py-iku's serialization layer (``DataikuFlow.from_dict`` / ``to_dict``
and ``PrepareStep.from_dict`` / ``to_dict``).

See ``README.md`` in this directory for what failures mean and how to extend
the fixture set.
"""
