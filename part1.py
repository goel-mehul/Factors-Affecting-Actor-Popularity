import requests
from bs4 import BeautifulSoup
import requests
import json
import os
import sqlite3

#####################################
# API key for the themoviedb data.
#####################################
API_KEY = "58a16777781e3378851826f5f021d7d7"

def get_actors():
    '''
    Scrapes an IMDB website that contains the names and the ranks of the most popular actors till 2018.
    The method scrapes the names and the ranks and puts each of them in a seperate list.
    The method returns a final list, contaning the two previously mentioned lists.
    '''

    url = "https://www.imdb.com/list/ls022928819/"
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    actors_name_list = []
    actors = soup.find_all("h3", class_="lister-item-header")
    for i in range(100):
        name = actors[i].find("a")
        actor_name = name.text.strip()
        actors_name_list.append(actor_name)
    actors_popularity = []
    populars = soup.find_all("span", class_="lister-item-index")
    for popular in populars:
        actors_popularity.append(popular.text)
    imdb_actors = []
    for i in range(len(actors_name_list)):
        imdb_actors.append([actors_popularity[i], actors_name_list[i]])
    return imdb_actors


def setUp_imdb_Database(db_name):
    '''
    This method sets up the database for the project. It takes a string parameter db_name.
    This is the name of the database. The method initializes cur and conn.
    It returns cur and conn variables.
    '''
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path+'/'+db_name)
    cur = conn.cursor()
    return cur, conn


def create_imdb_actors_table(cur, conn):
    '''
    This method creates the Actors_Popularity table based on the data collected from scraping the IMDB website.
    The table has two columns, popularity rank, which is the primary key and actor_name.
    Popularity rank contains integer values while actor_name has string values.
    The method takes cur and conn.
    The method doesn't return anything but makes changes to the database.
    '''
    cur.execute("CREATE TABLE IF NOT EXISTS Actors_Popularity (popularity_rank INTEGER PRIMARY KEY, actor_name STRING)")
    conn.commit()


def add_imdb_actors_data(cur, conn, count):
    '''
    This method inserts data rows to the Actors_Popularity table.
    The method takes three parameters. It takes cur, conn from the ssetup database method.
    It takes a count parameter which keeps track of which data row needs to be added to the table.
    It calls the get_actors method to get the list of actor names and their popularity rank.
    The method doesn't return anything but makes changes to the database.
    '''
    list1 = get_actors()
    cur.execute("INSERT INTO Actors_Popularity (popularity_rank, actor_name) VALUES (?, ?)", (list1[count][0], list1[count][1]))
    conn.commit()


def build_imdb_table(cur, conn):
    '''
    This method calls all of the previous methods to make changes in the database with respect to the Actor_Popularity table.
    The method takes two parameters, cur and conn.
    The method first calls the create_imdb_actors_table method to see if the the table exists or not.
    The method then counts the number of rows currently existing in the table and then loops to add 25 more data rows.
    If the table contains equal or more than 100 rows, then nothing more is added to the table.
    The method doesn't return anything.
    '''
    create_imdb_actors_table(cur, conn)
    cur.execute("SELECT COUNT(*) FROM Actors_Popularity")
    data_present = cur.fetchone()
    count = data_present[0]
    if count < 100:
        for i in range(25):
            add_imdb_actors_data(cur, conn, count)
            count+=1


def get_total_actors_list():
    '''
    This method calls the get_actors method to get the list containing the names of the most popular actors.
    The method then creates a new list that contains the names of the actors.
    The names are slightly changed, where any space between the words is replaced by '%20'.
    This is done so that the new list can be run through an API query.
    The method return thee new list with the changed actor's names.
    '''
    list1 = get_actors()
    actors_name_list = []
    for list_item in list1:
        if ' ' in list_item[1]:
            name = list_item[1].replace(' ', '%20')
        else:
            name = list_item[1]
        actors_name_list.append(name)
    return actors_name_list


def get_actors_data(actor_name):
    '''
    This method takes a string name of an actor.
    The method requests the 'themoviedb' api to get data about the actor.
    The requested data is recieved in the form of a json file and is then stored in the form of a dictionary object.
    The method returns a list containing the actor's id, his name and an empty string for films.
    The empty string is filled in a later method.
    '''
    base_url = "https://api.themoviedb.org/3/search/person?api_key="
    url = base_url + API_KEY + "&query=" + actor_name
    r = requests.get(url)
    dict = json.loads(r.text)
    actor_data = dict["results"][0]
    actor_id = actor_data["id"]
    actor_name = actor_data["name"]
    actor_films = ""
    actor_details = [actor_id, actor_name, actor_films]
    return actor_details


def create_actors_table(cur, conn):
    '''
    This method creates the Actors table based on the data collected from requesting to the 'themoviedb' API.
    The table has three columns, actor_id which is the primary key, actor_name and actor_films.
    Actor_id contains integer values while actor_name and actor_films have string values.
    The method takes cur and conn.
    The method doesn't return anything but makes changes to the database.
    '''
    cur.execute("CREATE TABLE IF NOT EXISTS Actors (actor_id INTEGER PRIMARY KEY, actor_name STRING, actor_films STRING)")
    conn.commit()


def add_actor_data(cur, conn, count):
    '''
    This method inserts data rows to the Actors table.
    The method takes three parameters. It takes cur, conn from the setup database method.
    It takes a count parameter which keeps track of which data row needs to be added to the table.
    It calls the get_total_actors_list method to get the list of actor names.
    Using this list the method calls the get_actors_data method to get the actor's id, name and films.
    The method doesn't return anything but makes changes to the database.
    '''
    list1 = get_total_actors_list()
    actor_details = get_actors_data(list1[count])
    cur.execute("INSERT INTO Actors (actor_id , actor_name, actor_films) VALUES (?, ?, ?)", (actor_details[0], actor_details[1], actor_details[2]))
    conn.commit()


def build_actors_table(cur, conn):
    '''
    This method calls all of the previous methods to make changes in the database with respect to the Actors table.
    The method takes two parameters, cur and conn.
    The method first calls the create_actors_table method to see if the the table exists or not.
    The method then counts the number of rows currently existing in the table and then loops to add 25 more data rows.
    If the table contains equal or more than 100 rows, then nothing more is added to the table.
    The method doesn't return anything.
    '''
    create_actors_table(cur, conn)
    cur.execute("SELECT COUNT(*) FROM Actors")
    data_present = cur.fetchone()
    count = data_present[0]
    if count < 100:
        for i in range(25):
            add_actor_data(cur, conn, count)
            count+= 1


def main():
    '''
    This is the main method. It calls three functions.
    It first calls the setUp_imdb_Database method to create a database file.
    It then calls the build_imdb_table to complete the Actors_Popularity Table.
    It then calls the build_actors_table to complete the Actors Table.
    '''
    cur, conn = setUp_imdb_Database("Popular_Actors.db")
    build_imdb_table(cur, conn)
    build_actors_table(cur, conn)

if __name__ == "__main__":
    main()
