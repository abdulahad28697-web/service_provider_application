"""ORM model layer.

Importing this package registers every model with ``Base.metadata`` so that
``Base.metadata.create_all`` (run at application startup) and Alembic both see
the full schema. Each concrete model lives in its own module, named after the
entity it represents.
"""
# The noqa comments keep linters quiet: the imports are *intentional* — their
# side effect (model registration) is what matters, not the (unused) names.
import app.models.admin_log  # noqa: F401
import app.models.booking  # noqa: F401
import app.models.category  # noqa: F401
import app.models.provider  # noqa: F401
import app.models.review  # noqa: F401
import app.models.schedule  # noqa: F401
import app.models.service  # noqa: F401
import app.models.user  # noqa: F401
import app.models.user_profile  # noqa: F401
