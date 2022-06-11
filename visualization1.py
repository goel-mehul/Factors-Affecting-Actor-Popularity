import json
import sqlite3
import matplotlib
import matplotlib.pyplot as plt
import numpy as np


############# The db file ##############
db_file = 'Popular_Actors.db'
conn = sqlite3.connect(db_file)
cur = conn.cursor()

def collect_data_for_scatterplot(cur):
    '''
    The method collects the data through which a scatterplot of popularity rank and average film rating is created.
    The method take cur as a parameter.
    The method joins the Actors_Popularity table with the Actors table to get both the popularity rank and film_avg.
    The method then creates two new lists.
    rank is a list of popularity ranks.
    avg_rating is a list of average films rating
    The method returns a new list containing both of the previous lists.
    '''
    cur.execute("SELECT Actors.actor_name, popularity_rank, film_avg "
                "FROM Actors_Popularity "
                "JOIN Actors "
                "ON Actors_Popularity.actor_name = Actors.actor_name "
                "ORDER BY popularity_rank")
    list1 = cur.fetchall()
    rank = []
    avg_rating = []
    for item in list1:
        rank.append(item[1])
        avg_rating.append(item[2])
    return [rank, avg_rating]

def create_scatterplot(data):
    '''
    This method plots the scatterplot between popularity ranks and average film ratings.
    The method takes a list parameter.
    This contains the data that needs to be plotted for the scatterplot.
    The method after creating the scatterplot also finds the correlation coefficient between the two variables.
    The method returns this correlation coefficient.
    '''
    X = np.array(data[0])
    Y = np.array(data[1])

    plt.plot(X, Y, 'o')
    m, b = np.polyfit(X, Y, 1)
    plt.plot(X, m * X + b)
    plt.xlabel("Popularity Rank")
    plt.ylabel("Average Film Rating");
    correlation_coef = np.corrcoef(X, Y)
    plt.show()
    return correlation_coef[0][1]


def main():
    '''
    This is the main method and it calls both of the above methods to create the scatterplot.
    It also prints out the correlation coefficient rounded to two decimal places.
    '''
    data = collect_data_for_scatterplot(cur)
    coef = create_scatterplot(data)
    print("The correlation between Popularity Rank and Average Film Rating is " + str(round(coef, 2)))


if __name__ == "__main__":
    main()