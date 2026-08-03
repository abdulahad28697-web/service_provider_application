"""Data-access (repository) layer.

Repositories isolate all database interaction behind small, focused classes.
Each repository is bound to one aggregate and is constructed with an
:class:`~sqlalchemy.ext.asyncio.AsyncSession`. Repositories return ORM objects
(or ``None``); business rules and validation live in the service layer, so
repositories stay free of HTTP and domain-policy concerns.
"""
