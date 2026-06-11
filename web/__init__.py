"""Spletna plast (UI + API) nad obstoječim ValidatorEngine.

Ta paket NE vsebuje validacijske logike. Je tanka plast, ki obstoječi
``ValidatorEngine`` izpostavi prek HTTP API-ja (FastAPI) in postreže
brskalniški uporabniški vmesnik (React, brez build koraka).
"""

__all__ = ["backend"]
