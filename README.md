<h1>Weather Effects on Mental Health</h1>

<h2>Goal</h2>

My goal is to calculate the average ratings of the top 10 best films for each actor in IMDB's best male Actors of the 2010's and determine whether the top best 50 best actors were really in better films than the bottom 50 or if the ranks were somewhat determined on other factors like real-life personability or politics. I also wanted to find out the genre distribution of the best films of the top 100 Actors to determine what type of film was most popular. I planned on scraping IMDB for the list of the most popular actors in the world (https://www.imdb.com/list/ls022928819/) and their rank and then using The Movie Database API to find their top 10 highest rated films. I wanted to make a histogram and a scatter plot to show the distribution of ratings and pie chart to show the distribution of genres.

My goal is to calculate the average ratings of the top 10 best films for each actor in IMDB's most popular actors and determine whether there was a correlation between the popularity rank and average film rating. I also wanted to see if the top best 50 best actors were really in better films than the bottom 50. Both these findings are done to see whether the popularity ranks are based on their films or if there are other factors like real-life personability or politics that contribute to popularity. I also wanted to find out the genre distribution of the best films of the top 100 Actors to determine what types of films most popular actors plan to do.

<h2>Data Used</h2>

I planned on scraping IMDB for the list of the most popular actors in the world (https://www.imdb.com/list/ls022928819/) and then using The Movie Database (https://developers.themoviedb.org/3/getting-started/introduction) API to find their top 10 highest rated films. I wanted to make a histogram and a scatter plot to show the distribution of ratings and a pie chart to show the distribution of genres.


<h2>Problems Faced</h2>
I faced a bit of trouble with modeling the database in the best way because I wasn't always sure which attributes I would need to make the calculations efficiently and answer my questions. Sometimes I needed to go into the database and add attributes to a table or remake the table to remove certain attributes. Through trial and error, I figured out exactly which attributes I needed in which tables and was able to successfully complete the project.

<h2>Calculations Done</h2>
--- calculations from the data in the database ---

The name of the file containing the calculations from the data in the database for finding out the correlation between popularity rank and average film rating is: calculation_results.txt

The name of the file containing the calculations from the data in the database for finding out the distribution of genres for best films is: piechart_results.txt

<h2>Visualizations Done</h2>

I created three different visualizations to understand the correlation and existing patterns in the dataset.

The scatterplot that shows the correlation between popularity rank and average film rating. File name: scatterplot.PNG

<br/>![Scatterplot](https://github.com/goel-mehul/Factors-Affecting-Actor-Popularity/blob/main/Visualizations/scatterplot.PNG "Scatterplot")
<h4 align="center">Figure 1: Scatterplot</h4>

The histogram that shows the distribution of the top 50 and bottom 50 of the top 100 actors with relation to their average film rating. File name: histogram.png

<br/>![Histogram](https://github.com/goel-mehul/Factors-Affecting-Actor-Popularity/blob/main/Visualizations/histogram.png "Histogram")
<h4 align="center">Figure 2: Histogram</h4>

The pie chart that shows the distribution of genres for the top 10 films of the most popular actors. File name: piechart.PNG

<br/>![Pie Chart](https://github.com/goel-mehul/Factors-Affecting-Actor-Popularity/blob/main/Visualizations/piechart.PNG "Pie Chart")
<h4 align="center">Figure 3: Pie Chart</h4>


<h2>Instructions for running the code</h2>

<h3>Step 1:</h3>
Step 1 is to run the part1.py python file to set up a database and create two tables Actors and Actor_Popularity. Data about most popular actors are collected from the 'themoviedb' API and the IMDb website. The two tables are filled with these two different data and completed. One point to note, the Actors_Popularity table has an empty string in the films column. This column will be updated later. Also to note, after every run, only 25 new rows will be added to the database. Part1.py needs to be run four times to complete the database and move to the next step.


<h3>Step 2:</h3>
Step two is to use the Popular_Actors.db Actors table to create a new table called Films that list the top 10 highest rated films from all of the actors and put the ids of those films in the actor_name attribute of the actor. Run populate_films.py to create and populate the Films table with the top 10 films for 25 of the actors listed in the Actors table whose films haven't already been recorded.

<h3>Step 3:</h3>

**Visualization 1 (Scatterplot)**
Run visualization1.py to create a scatterplot showing the relation of popularity rank and their average film rating. The method also outputs the calculated correlation coefficient of the scatterplot. The results show that there is a negative weak correlation. This shows that as popularity rank increases, the average film rating decreases. The correlation value is -0.19.

**Visualization 2 (Histogram)**
Run calculate.py to populate the film_avg attribute of the Actor's table, create a histogram of the average film ratings for the top and bottom half of the top 100 list, and output a JSON formatted text file called  calculation_results.txt with the calculation results. The histogram shows that both sides of the rank have similar distribution but the top 10 are more distributed in the < 8.5 range. Overall, the top 50 actors do have, on average, films that are ranked higher, so there is a strong correlation between the two.


**Visualization 3 (Pie chart)**
Run visualization2.py to create a pie chart depicting the different genres of the 731 films present in the Films table. This shows what kinds of films, popular actors mostly do. The top five results are Drama (23.4%), Documentary (14.7%), comedy (7.3%), Action (6.5%), Crime (6.2%).
