from flask import render_template, abort, request, redirect, url_for
from .models.api import get_collection, get_random
from .models.data_model import *
from whatsNext import app


@app.route('/index', methods=["GET", "POST"])
def index():
    # Homepage, evaluate if the request's method is POST.
    # If yes, retrieve values from login form and call api.get_collection()
    # If that returns True, scrape succesful and can redirect to releases page
    # If returns False, Discogs API call returned an error and we should alert the user
    if request.method == "POST":
        cache.set("username", request.form['username'])
        reset_df()
        if not get_collection(request.form['username'], request.form['sort']):
            return render_template("api_err.html", username=request.form['username'])
        else:
            return redirect(url_for('releases'))
    else:
        return render_template("main.html")


@app.route('/', methods=["GET", "POST"])
@app.route('/releases/', methods=["GET", "POST"])
def releases():
    # Displays table respresenting user's Discogs record collection
    try:
        if 'search' in request.form:
            # If the search button was pressed, pass the form input into the search function
            # That returns a smaller dataframe of those whose artist or album name matches the search term
            # We re-render this same page, now only filling the table with that new df
            results = search(request.form['string'])
            return render_template(
                'releases.html',
                releases=results,
                search=request.form['string'],
                username=cache.get("username")
            )
        elif 'random' in request.form:
            # If the 'Random Album' button was pressed,
            # get a random release_id and pass that to the release() page
            return redirect(url_for('release', release_id=get_random()))
        else:
            # Otherwise a standard GET request, or the 'reset' button was pressed
            # return the releases page with the full collection df
            return render_template(
                'releases.html',
                releases=get_df(),
                search='',
                username=cache.get("username")
            )
    except (KeyError, TypeError) as e:
        return redirect(url_for('index'))


@app.route('/releases/<int:release_id>')
def release(release_id):
    #
    try:
        return render_template(
            'release.html',
            choice=get_dict(release_id),
            color=get_df()[get_df()['release_id'] == release_id].iloc[0]['cover_color'],
            release_id=release_id,
            similar=get_similar(release_id)
        )
    except IndexError:
        abort(404)
    except KeyError:
        abort(404)


@app.route('/releases/<int:release_id>/color')
def color(release_id):
    #
    try:
        return render_template(
            'color.html',
            choice=get_dict(release_id),
            color=get_df()[get_df()['release_id'] == release_id].iloc[0]['cover_color'],
            release_id=release_id,
            similar=get_closest_color(release_id)
        )
    except IndexError:
        abort(404)
    except KeyError:
        abort(404)


@app.route('/data/stats')
def stats():
    return render_template(
        'stats.html',
        bar=get_bar(),
        pie=get_pie(),
        ten=get_top_ten()
    )


@app.route('/data/similarity')
def similarity():
    return render_template(
        'similarity.html',
        hm=get_hm()
    )
