"""HTTP API layer.

Routers (controllers) live here, grouped by API version under :mod:`app.api.v1`.
Controllers stay thin: they parse/validate input, call the service layer, and
shape the response envelope — no business logic.
"""
