"""
Application-wide HTTP error handlers for RepRequest.

Feature modules should raise appropriate HTTP errors rather than
implementing their own duplicate error pages.
"""

from flask import render_template


def register_error_handlers(app):
    """
    Register application-wide HTTP error handlers.
    """

    @app.errorhandler(403)
    def forbidden(error):
        """
        Display a friendly response when an authenticated
        user lacks permission to access a resource.
        """

        return render_template(
            "errors/403.html"
        ), 403