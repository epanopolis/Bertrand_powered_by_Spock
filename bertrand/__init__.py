"""
The place where it all starts. This app uses the flask framework's middleware. 
See https://flask.palletsprojects.com/en/stable/ for more info.

"""

import os
import sys
from flask import Flask, Blueprint
from bertrand import utility, spock

def create_app():
    """ Configures the framework and sets up routes to endpoints """
    app = Flask(__name__, instance_relative_config=True)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    def _configure_stdio_utf8():
        '''
        Without this configuration function, users are apt to run into a network
        error when using the production server
        '''
        # Only reconfigure if these are real text streams
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

    _configure_stdio_utf8()

    # Register blueprints
    app.register_blueprint(utility.bp)
    app.register_blueprint(spock.bp)

    app.add_url_rule('/', endpoint='index')

    return app
