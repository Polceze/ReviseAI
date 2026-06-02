from flask import Blueprint, render_template

pages_bp = Blueprint('pages', __name__)

@pages_bp.route('/')
def index():
    return render_template('index.html')

@pages_bp.route('/analytics')
def analytics():
    return render_template('analytics.html')

@pages_bp.route('/sessions')
def sessions():
    return render_template('sessions.html')

@pages_bp.route('/donate')
def donate():
    return render_template('donate.html')

@pages_bp.route('/upgrade')
def upgrade():
    return render_template('donate.html')  # Alias for donate