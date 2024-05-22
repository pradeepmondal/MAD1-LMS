import os
from flask import Flask
from application.config import DevelopmentConfig, ProductionConfig
from application.database import db
from flask_restful import Resource, Api
from application.api import SectionApi, BookApi, IssueApi

app = None


def create_app():
    app = Flask(__name__, template_folder='templates')
    if (os.getenv("ENV") == "development"):
        app.config.from_object(DevelopmentConfig)
    elif (os.getenv("ENV") == "production"):
        app.config.from_object(ProductionConfig)
    db.init_app(app)
    api = Api(app)
    app.app_context().push()
    return app, api


app, api = create_app()


api.add_resource(SectionApi, "/api/section/<int:section_id>", "/api/section/")
api.add_resource(BookApi, "/api/book/<int:book_id>", "/api/book/")
api.add_resource(IssueApi, "/api/issue/<int:book_id>/<username>")

from application.controllers import *

if __name__ == '__main__':
    app.run(port=5551)
