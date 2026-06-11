"""FastAPI backend za MES Excel Validator.

Izpostavlja obstoječi ``ValidatorEngine`` prek REST API-ja. Vsa validacijska
logika ostaja v ``core/`` in ``rules/`` — ta modul samo orkestrira nalaganje
datotek, zaganjanje validacije v ozadju in dostavo poročil.
"""

from .app import create_app

__all__ = ["create_app"]
