"""blocks/ — Blocks computed by code from the store, never by a model.

Imports nothing from `vault`: this is what keeps `vault.store` importing
`blocks` (for the registry) free of a cycle.
"""

BLOCKS = {
    "travel-log": {"title": "Travel Log", "kinds": ("photo", "place"), "file": "travel-log.md"},
}
