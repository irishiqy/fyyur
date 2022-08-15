#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from sqlalchemy import ForeignKey
from forms import *
from flask_migrate import Migrate
from datetime import datetime
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app,db)
migrate.init_app(app)
# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(500))
    seeking_description = db.Column(db.Boolean, default=False)
    shows_art=db.relationship('Show', backref='Venue')

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(500))
    seeking_venue = db.Column(db.Boolean, default=False)
    shows_art=db.relationship('Show', backref='Aritist')

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
class Show(db.Model):
    __tablename__ = 'Show'

    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'),primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'),primary_key=True)
    start_time = db.Column(db.DateTime)

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
#Done. we need to show the shows with their artists,venues and time
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  data=[]
  areas = Venue.query.distinct('city', 'state').all()

  today = datetime.now()
  today = today.strftime('%Y-%m-%d')

  def get_venue(venue):
    venue_id = Venue.id 
    upcoming_shows = db.session.query(Show).join(Artist).filter(Show.venue_id == venue_id).filter(
      Show.start_time>today).all()
    
    upcoming_shows_count = 0
    for show in upcoming_shows:
        upcoming_shows_count = upcoming_shows_count+1
    return {'id': venue_id, 'name': Venue.name, 'num_upcoming_shows': upcoming_shows_count}

  for area in areas:
    venues = Venue.query.filter(Venue.city == area.city, Venue.state == area.state).all()
    record = {
      'city': area.city,
      'state': area.state,
      'venues': [get_venue(venue) for venue in venues],
    }
    data.append(record)
  return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on venues with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_term = request.form.get('search_term')
  search_results = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()
  count_results = len(search_results)
  response = {}
  data = []

  today = datetime.now()
  today = today.strftime('%Y-%m-%d')
  def get_upcoming_number(venue_id):
    total = db.session.query(Show).join(Artist).filter(Show.venue_id == venue_id).filter(
    Show.start_time>today).all()
    return len(total)
  for result in search_results:
    data.append({
      "id": result.id,
      "name": result.name,
      "num_upcoming_shows": get_upcoming_number(result.id)
    })
  response["count"] = count_results
  response["data"] = data

  #example style
  ''' response={
    "count": 1,
    "data": [{
      "id": 2,
      "name": "The Dueling Pianos Bar",
      "num_upcoming_shows": 0,
    }]
  }
  '''
  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  venue = Venue.query.get(venue_id)
  arr = venue.genres[1:-1] 
  arr = ''.join(arr).split(",")
  venue.genres = arr
  today = datetime.now()
  today = today.strftime('%Y-%m-%d')
  if venue.seeking_description:
    venue.seeking_text = "We are on the lookout for a local artist to play every two weeks. Please call us."
  
  #Query upcoming and past shows
  upcoming_shows = db.session.query(Show).join(Artist).filter(Show.venue_id == venue_id).filter(
    Show.start_time>today).all()
  past_shows = db.session.query(Show).join(Artist).filter(Show.venue_id == venue_id).filter(
    Show.start_time<today).all()
  #Function to get filtered shows data for display, past or upcoming
  def shows(shows):
    show_render_data = []
    shows_count = 0
    for show in shows:
      shows_count = shows_count+1
      show_render_data.append(
        {
          "start_time" : Show.start_time,
          "artist_id" : Show.artist_id,
          "artist_image_link" : Show.artist.image_link,
          "artist_name" : Show.artist.name
        }
      )
    return [shows_count, show_render_data]
  past_shows = shows(past_shows)
  upcoming_shows = shows(upcoming_shows)

  venue.past_shows_count = past_shows[0]
  venue.past_shows = past_shows[1]

  venue.upcoming_shows_count = upcoming_shows[0]
  venue.upcoming_shows = upcoming_shows[1]


  '''
  data1={
    "id": 1,
    "name": "The Musical Hop",
    "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
    "address": "1015 Folsom Street",
    "city": "San Francisco",
    "state": "CA",
    "phone": "123-123-1234",
    "website": "https://www.themusicalhop.com",
    "facebook_link": "https://www.facebook.com/TheMusicalHop",
    "seeking_talent": True,
    "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
    "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60",
    "past_shows": [{
      "artist_id": 4,
      "artist_name": "Guns N Petals",
      "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
      "start_time": "2019-05-21T21:30:00.000Z"
    }],
    "upcoming_shows": [],
    "past_shows_count": 1,
    "upcoming_shows_count": 0,
  }
  '''
 
  return render_template('pages/show_venue.html', venue=venue)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  form = VenueForm()
  if form.validate():
    venue = Venue( 
      name=request.form['name'],
      city=request.form['city'],
      state=request.form['state'], 
      phone=request.form['phone'],
      address=request.form['address'],
      genres=form.genres.data,
      image_link=request.form['image_link'],
      facebook_link=request.form['facebook_link'],
      website=request.form['website'],
      seeking_description=form.seeking_talent.data
        )
    db.session.add(venue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  # on successful db insert, flash success
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')
  else:
    flash('An error occured. Venue ' + request.form['name'] + ' could not be listed. Please correct submission.')
    return render_template('forms/new_venue.html', form=form)

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data = Artist.query.all()
  return render_template('pages/artists.html', artists=data)
  '''
  data=[{
    "id": 4,
    "name": "Guns N Petals",
  }, {
    "id": 5,
    "name": "Matt Quevedo",
  }, {
    "id": 6,
    "name": "The Wild Sax Band",
  }]
  return render_template('pages/artists.html', artists=data)
  '''

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_term = request.form.get('search_term')
  search_results = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()
  count_results = len(search_results)
  response = {}
  data = []

  today = datetime.now()
  today = today.strftime('%Y-%m-%d')

  def get_upcoming_number(artist_id):
    total = db.session.query(Show).join(Venue).filter(Show.artist_id == artist_id).filter(
    Show.start_time>today).all()
    return len(total)
  for result in search_results:
    data.append({
      "id": result.id,
      "name": result.name,
      "num_upcoming_shows": get_upcoming_number(result.id)
    })
  response["count"] = count_results
  response["data"] = data



  '''
  response={
    "count": 1,
    "data": [{
      "id": 4,
      "name": "Guns N Petals",
      "num_upcoming_shows": 0,
    }]
  }
  '''
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  artist = Artist.query.get(artist_id)
  arr = artist.genres[1:-1] 
  arr = ''.join(arr).split(",")
  artist.genres = arr
  today = datetime.now()
  today = today.strftime('%Y-%m-%d')
  if artist.seeking_venue:
    artist.seeking_text = "Looking for venue to play in."
  
  #Query upcoming and past shows
  upcoming_shows = db.session.query(Show).join(Venue).filter(Show.artist_id == artist_id).filter(
    Show.start_time>today).all()
  past_shows = db.session.query(Show).join(Venue).filter(Show.artist_id == artist_id).filter(
    Show.start_time<today).all()
  #Function to get filtered shows data for display, past or upcoming
  def shows(shows):
    show_render_data = []
    shows_count = 0
    for show in shows:
      shows_count = shows_count+1
      show_render_data.append(
        {
          "start_time" : show.start_time,
          "venue_id" : show.venue_id,
          "venue_image_link" : show.venue.image_link,
          "venue_name" : show.venue.name
        }
      )
    return [shows_count, show_render_data]

  past_shows = shows(past_shows)
  upcoming_shows = shows(upcoming_shows)

  artist.past_shows_count = past_shows[0]
  artist.past_shows = past_shows[1]

  artist.upcoming_shows_count = upcoming_shows[0]
  artist.upcoming_shows = upcoming_shows[1]
  return render_template('pages/show_artist.html', artist=artist)

'''
  data1={
    "id": 4,
    "name": "Guns N Petals",
    "genres": ["Rock n Roll"],
    "city": "San Francisco",
    "state": "CA",
    "phone": "326-123-5000",
    "website": "https://www.gunsnpetalsband.com",
    "facebook_link": "https://www.facebook.com/GunsNPetals",
    "seeking_venue": True,
    "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
    "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
    "past_shows": [{
      "venue_id": 1,
      "venue_name": "The Musical Hop",
      "venue_image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60",
      "start_time": "2019-05-21T21:30:00.000Z"
    }],
    "upcoming_shows": [],
    "past_shows_count": 1,
    "upcoming_shows_count": 0,
  }
 
'''


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  form = ArtistForm()
  
  if form.validate():
    artist = Artist( 
      name=request.form['name'],
      city=request.form['city'],
      state=request.form['state'], 
      phone=request.form['phone'],
      facebook_link=request.form['facebook_link'],
      genres=form.genres.data,
      image_link=request.form['image_link'],
      website=request.form['website']
      )
    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
    return render_template('pages/home.html')
  else:
    flash('An error occured. Artist ' + request.form['name'] + ' could not be listed')
    return render_template('forms/new_artist.html', form=form)


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue={
    "id": 1,
    "name": "The Musical Hop",
    "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
    "address": "1015 Folsom Street",
    "city": "San Francisco",
    "state": "CA",
    "phone": "123-123-1234",
    "website": "https://www.themusicalhop.com",
    "facebook_link": "https://www.facebook.com/TheMusicalHop",
    "seeking_talent": True,
    "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
    "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
  }
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  form = ArtistForm()
  
  if form.validate():
    artist = Artist( 
      name=request.form['name'],
      city=request.form['city'],
      state=request.form['state'], 
      phone=request.form['phone'],
      facebook_link=request.form['facebook_link'],
      genres=form.genres.data,
      image_link=request.form['image_link'],
      website=request.form['website']
      )
    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
    return render_template('pages/home.html')
  else:
    flash('An error occured. Artist ' + request.form['name'] + ' could not be listed')
    return render_template('forms/new_artist.html', form=form)

  # on successful db insert, flash success
  flash('Artist ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  data = []
  all_shows = db.session.query(Show).join(Artist).join(Venue).all()
  for show in all_shows:
    data.append({
          "venue_id" : show.venue_id,
          "venue_name" : show.venue.name,
          "artist_id" : show.artist_id,
          "artist_image_link" : show.artist.image_link,
          "artist_name" : show.artist.name,
          "start_time" : show.start_time
    })

  return render_template('pages/shows.html', shows=data)
  '''
  data=[{
    "venue_id": 1,
    "venue_name": "The Musical Hop",
    "artist_id": 4,
    "artist_name": "Guns N Petals",
    "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
    "start_time": "2019-05-21T21:30:00.000Z"
  }, ]
  '''
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  try:
    form = ShowForm()
    if form.validate():

      artist_id=request.form['artist_id'],
      venue_id=request.form['venue_id'],
      start_time=request.form['start_time']
      artist = Artist.query.get(artist_id)
      venue = Venue.query.get(venue_id)
      start_time = start_time

      new_show = Show(artist_id=artist_id, venue_id=venue_id, start_time=start_time)
      artist.show =[new_show]
      venue.show =[new_show]
      db.session.add_all([artist,venue, new_show])
      db.session.commit()
      flash('Show was successfully listed!')
      return render_template('pages/home.html')
    else:
      flash('An error occurred. Show could not be listed.')
      return render_template('forms/new_show.html', form=form)
  except:
  # on successful db insert, flash success
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
