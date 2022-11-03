import os 
import json
import random
import sqlite3
from datetime import datetime, timedelta, time

number_of_artists = 200
number_of_venues = 20

another_show_chance = 4 # A number 2 or larger. Larger numbers mean any artist is more likely to get to play another show. 

show_start_date_iso = '2021-01-01T00:00:00-06:00' #  Midnight Jan 1 2021, central time zone, 6 hours behind UTC
earliest_show_date = datetime.fromisoformat(show_start_date_iso)

days_past_now = 50
latest_show_date = datetime.now() + timedelta(days=days_past_now)

# Code is
#     _ a random word
#     * a name 

artist_name_formats = [  
    '_',                    # For example, Nirvana
    '*',                    # Beyonce
    '*, * and *',           # Crosby, Stills and Nash
    '* _',                  # Billie Eilish
    '_ _',                  # Public Enemy
    'The _',                # The Fall
    'The _ _',              # The Beastie Boys
    '* _ and the _ _',      # Sharon Jones and the Dap Kings
    '* _ and the _ _ _',    # Ziggy Stardust and the Spiders from Mars 
]

# Code is
#     _ a random word
#     * a name 
#     ^ a city name 
venue_name_formats = [
    'the _ club',        
    'the _ theater',    
    '* _ lounge',       
    '_ center',          
    'the _ _ center',    
    'the * music house',    
    'the ^ _ center',   
]

database = 'concerts.sqlite3'

def main():
    clear_database()  # optional 
    create_database()
    artists = generate_artist_names()
    venues = generate_venue_names()
    shows = generate_shows(artists, venues)
    write_database(artists, venues, shows)


def clear_database():
    with sqlite3.connect(database) as conn:
        cursor = conn.cursor()
        cursor.execute('DROP TABLE IF EXISTS artists')
        cursor.execute('DROP TABLE IF EXISTS venues')
        cursor.execute('DROP TABLE IF EXISTS shows')


def create_database():
    with sqlite3.connect(database) as conn:
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS artists (id INTEGER PRIMARY KEY, name TEXT)')
        cursor.execute('CREATE TABLE IF NOT EXISTS venues (id INTEGER PRIMARY KEY, name TEXT, city TEXT, state TEXT)')
        cursor.execute('''CREATE TABLE IF NOT EXISTS shows (
            id INTEGER PRIMARY KEY, artist INTEGER, venue INTEGER, date INTEGER,
            FOREIGN KEY(artist) REFERENCES artists(id), 
            FOREIGN KEY(venue) REFERENCES venues(id) ) ''')
    
        
def generate_artist_names():
    # Read in names, and words 

    names = load_list_from_file(os.path.join('data', 'names.txt'))
    words = load_list_from_file(os.path.join('data', 'words.txt'))

    artist_names = []

    for count in range(number_of_artists):
        artist_name = random.choice(artist_name_formats)

        artist_name = replacer(artist_name, '_', words)
        artist_name = replacer(artist_name, '*', names)

        artist_name = artist_name.title()
        artist = {'id': count+1, 'name': artist_name}
        artist_names.append(artist)

    return artist_names


def generate_venue_names():

    names = load_list_from_file(os.path.join('data', 'names.txt'))
    words = load_list_from_file(os.path.join('data', 'words.txt'))
    cities = load_json_from_file(os.path.join('data', 'cities.json'))

    # Weight the possibility of choosing a city by the city's population
    # so a large city will probably have more venues than a smaller one 
    cities_weights = [ city['population'] for city in cities ]
    cities_names = [ city['city'] for city in cities ]

    venue_names = []

    for count in range(number_of_venues):

        city = random.choices(cities_names, weights=cities_weights, k=1)[0]
        venue_name = random.choice(venue_name_formats)

        venue_name = replacer(venue_name, '_', words)
        venue_name = replacer(venue_name, '*', names)
        venue_name = venue_name.replace('^', city)

        venue_name = venue_name.title()
        venue_dictionary = {'id': count+1, 'name': venue_name, 'city': city, 'state': 'MN'}
        venue_names.append(venue_dictionary)

    return venue_names


def replacer(name, character, word_list):
    blanks = name.count(character)
    for _ in range(blanks): 
        random_word = random.choice(word_list)
        name = name.replace(character, random_word, 1) # replace one character with random word
    return name 


def generate_shows(artists, venues):
    shows = []
    count = 1

    for artist in artists:

        show_date = random_date(earliest_show_date, latest_show_date)
        
        while touring():  # randomly decided if the artist gets to play anothe show
            
            print(show_date)
            venue = random.choice(venues)
            print(venue, artist)
            show = {'id': count, 'artist': artist['id'], 'venue': venue['id'], 'date': int(show_date.timestamp()) }
            shows.append(show)
            count +=1
            show_date = random_date_in_future(show_date, 10)


    return shows


def touring():
    return random.randint(0, another_show_chance) == 0


def write_database(artists, venues, shows):
    with sqlite3.connect(database) as conn:
        cursor = conn.cursor()
        for artist in artists:
            cursor.execute('INSERT INTO artists (id, name) VALUES (?, ?)', (artist['id'], artist['name'] ))
        for venue in venues:
            cursor.execute('INSERT INTO venues (id, name, city, state) VALUES (?, ?, ?, ?)', (venue['id'], venue['name'], venue['city'], venue['state']))    
        for show in shows:
            cursor.execute('INSERT INTO shows (id, artist, venue, date) VALUES (?, ?, ?, ?)', (show['id'], show['artist'], show['venue'], show['date'] ))


def random_date(start, end):
    start_timestamp = int(start.timestamp())
    end_timestamp = int(end.timestamp())
    random_date_timestamp = random.randrange(start_timestamp, end_timestamp)
    random_date = datetime.fromtimestamp(random_date_timestamp)
    # Adjust time part of the datetime to be between 1pm-11pm
    random_date = set_hour_to_concert_hours(random_date)
    return random_date


def random_date_in_future(start, max_days_in_future):
    start_timestamp = int(start.timestamp())
    end_date = start + timedelta(days = max_days_in_future)
    end_timestamp = int(end_date.timestamp())
    random_date_timestamp = random.randrange(start_timestamp, end_timestamp)
    random_date = datetime.fromtimestamp(random_date_timestamp) 
    random_date = set_hour_to_concert_hours(random_date)
    return random_date


def set_hour_to_concert_hours(random_datetime):
    random_date = random_datetime.date() # just the calendar day e.g. 2022-02-01
    concert_hour = random.randint(13, 23) # hours between 1pm-11pm
    concert_minute = random.choice([0, 15, 30, 45])
    concert_time = time(hour=concert_hour, minute=concert_minute, second=0) 
    random_date = datetime.combine(random_date, concert_time)
    return random_date
     
    
def load_list_from_file(filename):
    with open(filename) as f:
        text = f.read()
        lines = text.splitlines()
    return lines


def load_json_from_file(filename):
    with open(filename) as f:
        data = json.load(f)
    return data


if __name__ == '__main__':
    main()