"""
Development entry point for RepRequest.

Application configuration and feature logic belong inside the
app package rather than this file.
"""

from app import create_app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)