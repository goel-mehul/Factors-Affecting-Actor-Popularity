import requests
import json
import sqlite3


############# The db file ##############
db_file = 'Popular_Actors.db'
conn = sqlite3.connect(db_file)
cur = conn.cursor()

#cur.execute('CREATE TABLE IF NOT EXISTS Actors (actor_id INTEGER PRIMARY KEY, name TEXT, gender INTEGER, films TEXT, avg_rating INTEGER, fav_genre INTEGER)')
cur.execute('CREATE TABLE IF NOT EXISTS Films (film_id INTEGER PRIMARY KEY, name TEXT, genres TEXT, rating INTEGER)')

conn.commit()
#########################################
key = 'eff108aecbb73d143e06dc125caf045f'
base = 'https://api.themoviedb.org/3/discover/movie?api_key=eff108aecbb73d143e06dc125caf045f&language=en-US&sort_by=vote_average.desc&include_adult=false&include_video=false&page=1&with_cast='
#########################################

def pull_films(info):
    '''
    Takes in a python object created from the JSON response containing an actor's filmography
    and adds the top 10 of those films to the database. Returns a list of the film's ids to be
    added to the films attribute of the actor's tuple in the database.
    '''
    filmography = []
    film_list = len(info["results"])
    if film_list >= 10:
        film_list = 10

    for film in range(film_list):
        pos = info["results"][film]
        identity = pos["id"]
        name = pos["original_title"]
        
        int_genres = pos["genre_ids"]
        genres = []
        for genre in int_genres:
            genres.append(str(genre))

        votes = pos["vote_average"]
        cur.execute('INSERT or IGNORE INTO Films (film_id, name, genres, rating) VALUES (?, ?, ?, ?)', (identity, name, ",".join(genres), votes))
        filmography.append(str(identity))
    conn.commit()
    return filmography

def select_actors():
    '''
    Selects up tp 25 actors to query with the API based on whether or not they 
    have already been called.
    '''
    cur.execute('SELECT actor_id FROM Actors WHERE actor_films IS NULL OR actor_films=""')
    disk = []
    for actor in cur:
        disk.append(actor)
    return disk[:25]

def call_actors():
    '''
    Selects up to 25 from the database and adds a list of 10 of their best rated films 
    to their films attribute.
    '''
    disk = select_actors()
    for actor in disk:
        actor_id = actor[0]
        full_req = base + str(actor_id)
        response = requests.get(full_req)
        cata = json.loads(response.content)
        cur.execute('UPDATE Actors SET actor_films= ? WHERE actor_id= ?', (",".join(pull_films(cata)), actor_id))
        conn.commit()
        

def main():
    call_actors()

if __name__ == "__main__":
    main()