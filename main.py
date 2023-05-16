from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests, json


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)

##CREATE DATABASE
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///movies.db"
#Optional: But it will silence the deprecation warning in the console.
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

API_ENDPOINT = "https://api.themoviedb.org/3/search/movie"
MOVIE_DB_INFO_URL = "https://api.themoviedb.org/3/movie"
API_KEY = "ed7301492928e1eb9cdeddc945ea2aab"


##CREATE DB TABLE
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(250), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return '<Title %r>' % self.title


# EDIT RATING FORM
class EditMovieForm(FlaskForm):
    rating = StringField("Your Rating Out of 10 e.g. 7.5")
    review = StringField("Your Review")
    submit = SubmitField("Done")

# ADD MOVIE FORM
class AddMovieForm(FlaskForm):
    title = StringField("Movie Title")
    submit = SubmitField("Add Movie")

db.create_all()

# Home route - list all favorite movies, if in db
@app.route("/")
def home():
    ##READ ALL RECORDS
    all_movies = Movie.query.order_by(Movie.rating).all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", movies=all_movies)


# route for adding new movies
@app.route("/add", methods=["GET", "POST"])
def add():
    form = AddMovieForm()
    title = form.title.data
    params = {
        "api_key": API_KEY,
        "query": title,
    }

    if form.validate_on_submit():
        response = requests.get(url=API_ENDPOINT,params=params)
        result = response.json()["results"]
        return render_template("select.html", movies=result)
    return render_template("add.html", form=form)

# route for editing existing favorite movie
@app.route("/edit", methods=["GET", "POST"])
def edit():
    form = EditMovieForm()
    movie_id = request.args.get("id")
    movie = Movie.query.get(movie_id)

    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", movie=movie, form=form)


@app.route("/find")
def find():
    form = EditMovieForm()
    movie_id = request.args.get("id")
    movie = Movie.query.get(movie_id)
    print(movie)
    MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500/"
    print(MOVIE_DB_IMAGE_URL)

    if movie_id:
        movie_api_url = f"{MOVIE_DB_INFO_URL}/{movie_id}"
        response = requests.get(movie_api_url, params={"api_key": API_KEY, "language": "en-US"})
        data = response.json()
        new_movie = Movie(
            title=data["title"],
            img_url=f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}",
            year=data["release_date"][0:4],
            description=data["overview"],
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for("edit", id=new_movie.id))


@app.route("/delete")
def delete():
    movie_id = request.args.get('id')

    # DELETE MOVIE FROM DB BY ID
    movie_to_delete = Movie.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
