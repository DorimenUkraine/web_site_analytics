from flask import Blueprint

main = Blueprint('main', __name__, template_folder='templates/main', static_folder='static/main')

from . import views
