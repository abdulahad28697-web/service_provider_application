"""Pydantic schema layer.

Request/response models for the HTTP API, grouped by domain. Schemas are the
boundary contract between the API and the rest of the application; they are
independent of the ORM models (validation and serialisation only).
"""
