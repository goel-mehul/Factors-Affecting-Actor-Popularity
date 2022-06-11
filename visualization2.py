import json
import sqlite3
import matplotlib
import matplotlib.pyplot as plt
import numpy as np


############# The db file ##############
db_file = 'Popular_Actors.db'
conn = sqlite3.connect(db_file)
cur = conn.cursor()


def create_data_dict(cur):
    '''
    This method creates a dictionary object that keeps genre id's as keys and their count as values.
    The method takes the cur parameter to access the database.
    The method returns the dictionary object.
    '''
    cur.execute("SELECT genres FROM films")
    data = cur.fetchall()
    dict = {}
    for item in data:
        for genre in item:
            if ',' in genre:
                list1 = genre.split(',')
                for list_item in list1:
                    dict[list_item] = dict.get(list_item, 0) + 1
            else:
                dict[genre] = dict.get(genre, 0) + 1
    return dict


def clean_data_dict(dict):
    '''
    This method cleans the dictionary object to make it easier for creating a pe chart.
    The method takes the dictionary object as a parameter.
    The method returns a new list which contains genre_id's in int and then corresponding occurrences.
    '''
    list1 = []
    for key in dict:
        list1.append([key, dict[key]])
    list2 = sorted(list1)
    list2.pop(0)
    list3 = []
    for item in list2:
        list3.append([int(item[0]), item[1]])
    return sorted(list3)

def add_genre_names(data, cur):
    '''
    This method updates the list and changes the genre id's to the names of genres.
    The method takes two parameters.
    It takes cur to access the database.
    It takes a list that contains information received from the previous method.
    It returns the updated list.
    '''
    cur.execute("SELECT * FROM Genres")
    list1 = cur.fetchall()
    for i in range(len(data)):
        data[i][0] = list1[i][1]
    return data

def dump_results(data):
    '''
    Creates a JSON response containing the different genre id's and the number of occurrences
    for the films of the top 100 actors ranked by popularity.
    The method takes the data as a a parameter.
    '''
    dict = {}
    for item in data:
        dict[item[0]] = item[1]
    body = {}
    body["Most Popular film Genres"] = dict

    with open('piechart_results.txt', 'w') as fp:
        json.dump(body, fp, indent=4)

def create_pie_chart(data):
    '''
    This method plots the pie chart.
    The method takes the final data that is needed to create the pie chart.
    The method doesn't return anything.
    '''
    labels = []
    sizes = []
    for item in data:
        labels.append(item[0])
        sizes.append(item[1])
    fig1, ax1 = plt.subplots()
    plt.title("What Genre Films Most Popular Actors Do\n")
    ax1.pie(sizes, labels = labels, autopct='%1.1f%%', shadow=True, startangle=90)
    ax1.axis('equal')
    plt.show()

def main():
    '''
    The main method where code execution takes place.
    It calls the above mentioned four methods in order.
    '''
    data = create_data_dict(cur)
    data2 = clean_data_dict(data)
    data3 = add_genre_names(data2, cur)
    dump_results(data3)
    create_pie_chart(data3)

if __name__ == "__main__":
    main()
