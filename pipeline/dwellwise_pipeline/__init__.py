"""Nightly ingestion of public data for DwellWise.

Each source is fetched, stored raw, validated, transformed and loaded in one
transaction. A failed run leaves the previous data in place.
"""
