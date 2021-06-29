#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
#Anhar Bawajiyyah
import sys
import json
import dateutil.parser 
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from gevent.pywsgi import WSGIServer
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate



#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate =Migrate(app ,db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#
from models import *
####

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
    
    return render_template('pages/home.html',venues = currentVenues, artists = currentArtists)

#  ----------------------------------------------------------------
#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  
  venues = Venue.query.all()

  venue_session =db.session.query(Venue.city,Venue.state).group_by(Venue.state, Venue.city).all()

  data =[]

##for loop to read the data
  for area in venue_session:
      area_venues = Venue.query.filter_by(state=area.state).filter_by(city=area.city).all()
      venue_data = []
  for venue in area_venues:
      venue_data.append({
        "id": venue.id,
        "name": venue.name, 
        "num_upcoming_shows": len(db.session.query(Show).filter(Show.venue_id==1).filter(Show.start_time>datetime.now()).all())
      })
  data.append({
      "city": area.city,
      "state": area.state, 
      "venues": venue_data
    })
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_term = request.form.get('search_term', '')
  results =Venue.query.filter(Venue.name.ilike('%{}%'.format(request.form['search_term']))).all()



  response={
    "count": len(results),
    "data": []
    }
  for venue in results:
    response["data"].append({
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": len(db.session.query(Show).filter(Show.venue_id == venue.id).filter(Show.start_time > datetime.now()).all()),
      })

  

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id

  venue =Venue.query.get(venue_id)
  venue_shows =venue.shows
  past_showList =[]
  upcoming_showList =[]

  #for loop to read the Venue shows


  upcoming_shows = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time>datetime.now()).all()

  past_shows = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time<datetime.now()).all()

  for shows in upcoming_shows:
    upcoming_showList.append({
        "artist_id":shows.artist_id,
        "artist_name": shows.artist.name,
        "artist_image_link":shows.artist.image_link,
        "start_time":str(shows.start_time)
  # i used str to return the string version of the object 
    })

  for shows in past_shows:
    past_showList.append({
        "artist_id":shows.artist_id,
        "artist_name": shows.artist.name,
        "artist_image_link":shows.artist.image_link,
        "start_time":str(shows.start_time)
  # i used str to return the string version of the object 
    })

  # if statment to check the artist shows
    if(shows.past):
      past_showList.append(past_showList)
    elif(shows.upcoming):
      upcoming_showList.append(upcoming_showList)


  if not venue:
        return redirect(url_for('index'))    
  # if the user is not a venue so he/she will directly returned to home page 


  data={
    "id":venue.id,
    "name":venue.name,
    "genres":venue.genres.spli(','),
    "address":venue.address,
    "city":venue.city,
    "state":venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_showList,
    "upcoming_shows": upcoming_showList,
    "past_shows_count": len(past_showList),
    "upcoming_shows_count": len(upcoming_showList)
  }

  return render_template('pages/show_venue.html', venue=data)

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
  insert_venue = Venue()
  insert_venue.name =request.form['name']
  insert_venue.phone =request.form['phone']

  insert_venue.city =request.form['city']
  insert_venue.state =request.form['state']
  insert_venue.address =request.form['address']
  
  insert_venue.genres =request.form['genres']
  insert_venue.facebook_link =request.form['facebook_link']
  insert_venue.website =request.full_path['website']
  insert_venue.image_link =request.form['image_link']
  try:
    db.session.add(insert_venue)
    db.session.commit()
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    # TODO: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')

  finally:
    db.session.close()
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  venue = Venue.query.get(venue_id)
  if not venue:
    return redirect(url_for('index'))

  else:
    try:
      db.session.delete(venue)
      db.session.commit()
      # on successful db insert, flash success
      flash('Venue ' + venue_id + ' was successfully deleted!')
    except:
      db.session.rollback()
      print(sys.exc_info())
      # TODO: on unsuccessful db insert, flash an error instead.
      flash('An error occurred. Venue ' + venue_id+ ' could not be deleted. please try again')

    finally:
      db.session.close()
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return render_template('pages/home.html')





#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():

  # TODO: replace with real data returned from querying the database
  data =db.session.query(Artist).all()
  return render_template('pages/artist.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".

  results =Artist.query.filter(Artist.name.ilike('%{}%'.format(request.form['search_term']))).all()
  respones={
    "count": len(results),
    "data": []

  }
  #for loop to read the data
  for artist in results:
    respones['data'].append({
      "id": artist.id,
      "name": artist.name,
      "num_upcoming_shows": len(db.session.query(Show).filter(Show.artist_id == results.id).filter(Show.start_time > datetime.now()).all()),

    })
 
  return render_template('pages/search_artists.html', results=respones, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id

  artist =db.session.qurey(Artist).get(artist_id)
  artist_shows =artist.shows
  past_shows = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time>datetime.now()).all()
  past_showsList = []

  upcoming_shows = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time>datetime.now()).all()
  upcoming_showsList = []

##for loop to read the shows data 

  for shows in past_shows:
    past_showsList.append({
    "venue_id":shows.venue_id,
    "venue_name":shows.venue.name,
    "venue_image_link":shows.venue.image_link,
    "start_time":str(shows.start_time)
 # i used str to return the string version of the object 
    })


  for shows in upcoming_shows:
    upcoming_showsList.append({
    "venue_id":shows.venue_id,
    "venue_name":shows.venue.name,
    "venue_image_link":shows.venue.image_link,
    "start_time":str(shows.start_time)
 # i used str to return the string version of the object 
    })

  # if statment to check the artist shows
    if(shows.past):
      past_shows.append(past_showsList)
    elif(shows.upcoming):
      upcoming_shows.append(upcoming_showsList)

# reading the real artist data
  data ={
    "id":artist.id,
    "name":artist.name,
    "genres":artist.genres.split(','),
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link":artist.facebook_link,
    "seeking_venue":artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "upcoming_shows":artist.upcoming_shows,
    "past_shows":artist.past_shows,
    "upcoming_shows_count":len(upcoming_showsList),
    "past_shows_count":len(past_showsList)
  }


  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):


  form = ArtistForm()
  artist =Artist.query.get(artist_id)
  if not artist:
    return redirect(url_for('index'))

  else: 

    artist_information={
     "id":artist.id,
      "name":artist.name,
      "genres":artist.genres.split(','),
      "city": artist.city,
      "state": artist.state,
      "phone": artist.phone,
      "website": artist.website,
      "facebook_link":artist.facebook_link,
      "seeking_venue":artist.seeking_venue,
      "seeking_description": artist.seeking_description,
      "image_link": artist.image_link,
  
  }
  
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist_information)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  artist =Artist.query.get(artist_id)
  artist.name =request.form['name']
  artist.city =request.form['city']
  artist.state =request.form['state']

  artist.phone =request.form['phone']
  artist.facebook_link = request.form['facebook_link']
  artist.genres = request.form['genres']
  artist.image_link = request.form['image_link']
  artist.website = request.form['website']


  try:
    db.session.commit()
    flash("The Artist {} is updated successfully".format(artist.name))
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash("The Artist {} isn't updated successfully, Please try again".format(artist.name))
  finally:
    db.session.close()

  
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)
  venue_information={
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres.split(','),
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link
  }

  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  venue = Venue.query.get(venue_id)
  venue.name = request.form['name']
  venue.city = request.form['city']
  venue.state = request.form['state']

  venue.address = request.form['address']
  venue.phone = request.form['phone']
  venue.facebook_link = request.form['facebook_link']
  venue.genres = request.form['genres']
  venue.image_link = request.form['image_link']
  venue.website = request.form['website']
  try:
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully updated!')
  except:
    db.session.rollback()
    flash('An error occurred. The Venue information could not be updated, Please try again.')
  finally:
    db.session.close()
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

  insert_artist =Artist()
  insert_artist.name =request.form['name']
  insert_artist.city =request.form['city']
  insert_artist.state =request.form['state']
  insert_artist.genres =request.form['genres']
  insert_artist.phone =request.form['phone']
  insert_artist.facebook_link =request.form['facebook_link']
  insert_artist.image_link =request.form['image_link']
  try:
    db.session.add(insert_artist)
    db.session.commit()
    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    # TODO: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Artist ' + insert_artist.name + ' could not be listed, please try again ')
  finally:
    db.session.close()

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  shows_session = db.session.query(Show).join(Artist).join(Venue).all()
  data =[]

  #for loop to read the data
  for show in shows_session:
      data.append({
        "venue_id":show.venue_id,
        "venue_name":show.venue.name,
        "artist_id":show.artist_id,
        "artist_name":show.artist.name,
        "artist_image_link":show.artist.image_link,
        "start_time":str(show.start_time)
         # i used str to return the string version of the object 

      })
  
  
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
  insert_show =Show()
  insert_show.artist_id =request.form['artist_id']
  insert_show.Venue_id =request.form['venue_id']
  date =request.form['start_time'].split(' ')
 
  try:
    db.session.add(insert_show)

    db.session.commit()
    flash('Show has been successfully listed!')
  except:
    db.session.rollback()
    # TODO: on unsuccessful db insert, flash an error instead.
    flash('Show could not be listed. please try again')
  finally:
    db.session.close()
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
    app.run(debug=True, host='0.0.0.0', port=port)
'''
