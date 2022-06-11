import json
import sqlite3
import math
import matplotlib.pyplot as plt
import numpy as np


############# The db file ##############
db_file = 'Popular_Actors.db'
conn = sqlite3.connect(db_file)
cur = conn.cursor()
#######################################

#cur.execute('ALTER TABLE Actors ADD film_avg INTEGER')
#conn.commit()

def get_all_actors():
    '''
    Selects all actor names from the Actors table in the database and 
    returns a list of the names.
    '''
    cur.execute('SELECT actor_name FROM Actors')
    disk = []
    for actor in cur:
        disk.append(actor[0])
    return disk

def avg_actor_films(films, name):
    '''
    Takes in an actor's name and a list of their film_ids from the Actors table in the 
    database and uses the ids to get the rating for each film in the actor's list. The 
    ratings are used to calculate the average rating of an actor's best films. That value 
    is added to the film_avg attribute in the actor's tupple in the Actor's table.
    '''
    rating_list = []
    for film in films:
        cur.execute('SELECT rating FROM Films WHERE film_id=?', (int(film),))
        rating_list.append(int(cur.fetchone()[0]))
    ########
    total = 0
    for rating in rating_list:
        total += rating
    avg = total/len(rating_list)
    cur.execute('UPDATE Actors SET film_avg=? WHERE actor_name=?',(avg, name))
    conn.commit()


def average_films():
    '''
    Populates the film_avg attribute of all actors in the Actors table.
    '''
    disk = get_all_actors()
    for actor in disk:
        cur.execute('SELECT actor_films, actor_name FROM Actors WHERE actor_name=?', (actor,))
        code_list = cur.fetchone()[0].split(',')
        avg_actor_films(code_list, actor)

###############################################################################

def select_actors():
    '''
    Returns a list of Actor names ordered by rank.
    '''
    cur.execute('SELECT actor_name FROM Actors_Popularity ORDER BY popularity_rank ASC')
    disk = []
    for actor in cur:
        disk.append(actor[0])
    return disk

def split_pop():
    '''
    Returns a number that is half the length of the Actors_Popularity table rounded down.
    '''
    cur.execute('SELECT COUNT (DISTINCT actor_name) FROM Actors_Popularity')
    total = cur.fetchone()[0]
    top_num = math.floor(total/2)
    return top_num

def group_avg_list(group):
    '''
    Takes in a list of actor names and returns a list of their average film ratings.
    '''
    avg_list = []
    for actor in group:
        cur.execute('SELECT actor_id FROM Actors WHERE actor_name=?',(actor,))
        identify = cur.fetchone()[0]
        cur.execute('SELECT film_avg FROM Actors_Popularity INNER JOIN Actors on Actors.actor_name = Actors_Popularity.actor_name WHERE actor_id=?', (identify,))
        value = cur.fetchone()[0]
        avg_list.append(value)
    return avg_list

def group_avg(avg_list):
    '''
    Takes in a list of average film ratings and returns an overall average for the group.
    '''
    overall_total = 0
    for avg in avg_list:
        overall_total += avg
        overall_total = round(overall_total, 4)
    overall_avg = overall_total/len(avg_list)
    return overall_avg

def rank_avg():
    '''
    Returns a tuple of the average film ratings (in a list) for the top and bottom half
    of the actors ranked by popularity.
    '''
    top_num = split_pop()
    disk = select_actors()
    top_group = disk[:top_num]
    bottom_group = disk[top_num:]
    top_avg = group_avg_list(top_group)
    bottom_avg = group_avg_list(bottom_group)
    return (top_avg, bottom_avg)

################################################################################


def plot_results(avgs_tuple):
    '''
    Takes in a tuple of the average film ratings (in a list) for the top and bottom half
    of the actors ranked by popularity and creates a histogram from the results.
    '''
    n_bins = 20
    fig, axs = plt.subplots(1, 2, sharey=True, tight_layout=True)
    axs[0].hist(avgs_tuple[0], bins=n_bins)
    axs[1].hist(avgs_tuple[1], bins=n_bins)
    axs[0].set_title('Average film rating for Actors ranking above 50')
    axs[1].set_title('Average film rating for Actors ranked between 50-100')
    axs[0].set_xlabel('Avg film rating')
    axs[1].set_xlabel('Avg film rating')
    axs[0].set_ylabel('# of actors')
    plt.show()


def dump_results():
    '''
    Creates a JSON response containing rhe group average and individual averages
    for the top 100 actors ranked by popularity
    '''
    film_scores = rank_avg()
    body = {}
    body["Top 100 Actors from 1-50"] = {
        "Average film rating" : group_avg(film_scores[0]),
        "Average rating for each actor's higest rated films" : film_scores[0]
    }
    body["Top 100 Actors from 50-100"] = {
        "Average film rating" : group_avg(film_scores[1]),
        "Average rating for each actor's higest rated films" : film_scores[1]
    }

    with open('calculation_results.txt', 'w') as fp:
        json.dump(body, fp, indent=4)







def main():
    ## Run average_films() to populate the film_avg attribute of all actors in the Actors table
    average_films()
    ## Run plot_results(rank_avg()) to plot the results of the calculation to a matplotlib histogram
    plot_results(rank_avg())
    ##Run dump_results() to dump the results into a txt file named calculation_results.txt
    dump_results()
    


if __name__ == "__main__":
    main()



