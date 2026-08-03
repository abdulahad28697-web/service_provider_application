"""Service (business-logic) layer.

Services implement the application's rules and workflows on top of the
repository layer. Controllers (routers) stay thin and delegate here, which lets
the business rules be unit-tested independently of HTTP. Each service is
constructed with a session and composes the repositories it needs.
"""
