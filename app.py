# updated Flask app with fixed session keys, GET guards, and plot endpoints
from flask import Flask, session, render_template, request, flash, url_for, redirect, send_file
from io import BytesIO, StringIO
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from flask_bootstrap import Bootstrap
import app_functions  # your helper functions
from app_functions import __version__
import pandas as pd

plt.style.use('ggplot')
plt.switch_backend('Agg')

# Global list to hold generated figures for the current session
figures = []

app = Flask(__name__)
app.config.from_object(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = app_functions.random_id(50)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
Bootstrap(app)

@app.route('/', methods=['GET', 'POST'])
def home():
    # Clear any old figures or session data if starting fresh
    if request.method == 'GET':
        figures.clear()
        session.pop('filtered_num', None)

    if request.method == 'POST' and request.form.get('submit_button') == 'submit_data':
        # Read input files into DataFrames
        meta_stream = request.files['metadata'].stream.read().decode('utf-8')
        df = pd.read_csv(StringIO(meta_stream))

        ann_stream = request.files['annotation'].stream.read().decode('utf-8')
        annotation = pd.read_csv(StringIO(ann_stream))

        # Perform all visualizations and get return values
        fig1, fig2, filtered_count = app_functions.make_all_visualisations(df, annotation)

        # Store numeric result in session, and figures in global list
        session['filtered_num'] = filtered_count
        figures.clear()
        figures.extend([fig1, fig2])

        return redirect(url_for('results'))

    return render_template('home.html', version=__version__)

@app.route('/results', methods=['GET', 'POST'])
def results():
    # Prevent direct GET without data
    if 'filtered_num' not in session:
        return redirect(url_for('home'))

    if request.method == 'POST' and request.form.get('submit_button') == 'go_back':
        return redirect(url_for('home'))

    return render_template(
        'results.html',
        filtered_num=session.get('filtered_num'),
        version=__version__,
        plot1_url=url_for('plot1'),
        plot2_url=url_for('plot2')
    )

@app.route('/data', methods=['GET', 'POST'])
def data():
    if request.method == 'POST' and request.form.get('submit_button') == 'go_back':
        return redirect(url_for('home'))
    return render_template('data.html')

# Endpoint to serve first plot
@app.route('/plot1.png')
def plot1():
    if not figures:
        return "No plot available", 404
    buf = BytesIO()
    figures[0].savefig(buf, format='png')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

# Endpoint to serve second plot
@app.route('/plot2.png')
def plot2():
    if len(figures) < 2:
        return "No plot available", 404
    buf = BytesIO()
    figures[1].savefig(buf, format='png')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

@app.after_request
def add_header(response):
    """
    Add headers to force no caching.
    """
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.errorhandler(404)
def page_not_found(e):
    flash('The URL you entered does not exist; you have been redirected to the home page.')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
