from bs4 import BeautifulSoup as bs
import pandas as pd
from requests import get
from json import load, loads, dump
from re import findall
import pprint
import requests
from datetime import date
import os

pp = pprint.PrettyPrinter()
imdb_source = get('http://www.imdb.com/movies-in-theaters/?ref_=nv_mv_inth_1').text
imdb_soup = bs(imdb_source, 'lxml')
imdb_movies = imdb_soup.find_all('table', { 'class': 'nm-title-overview-widget-layout' })

all_movies = {}
all_movies_two = {}
all_movies3 = {}

rt_source = get('''https://www.rottentomatoes.com/browse/in-theaters?minTomato=0&
				maxTomato=100&minPopcorn=0&maxPopcorn=100&
				genres=1;2;4;5;6;8;9;10;11;13;18;14&sortBy=release''').text

rt_soup = bs(rt_source, 'lxml')
js_source = rt_soup.find_all("script")[38].prettify()

final_js = findall('\[{.*}\]', js_source)

"""
Given a page source, return a DataFrame with the parsed data
"""
today = date.today()
datestring = str(today.year)+'-'+str(today.month)+'-'+str(today.day)
r = requests.get('http://www.boxofficemojo.com/daily/chart/?sortdate='+datestring+'&p=.htm')
page_source = r.content
page_soup = bs(page_source, "lxml")
table = page_soup.find_all('table', attrs={'cellpadding': "2"})[2]
output_columns = ['rank', 'title', 'day1', 'day2', 'day3', 'day4']
output = dict((x, []) for x in output_columns)
all_rows = table.find_all('tr')[1:]

for row in all_rows:
    row_cols = row.find_all('td')
    for dict_key, col in zip(output_columns, row_cols):
        output[dict_key].append(col.text)

output_pd = pd.DataFrame(output)
output_pd = output_pd[output_columns]
# for t in output_pd['title']:
#     t = t.split('\n')[0]
#     print(t)
#
# print(output_pd['title'])
# output_pd['title'] = output_pd['title'].split('\n')[0]

json = output_pd.to_json(orient='records')
# print(json)
# obj = open('bomfile.json', 'w')
# obj.write(json)
# obj.close


with open('bomfile.json', 'w') as file:
    parsed_js = loads(json)
    dump(parsed_js, file, indent=4, sort_keys=True)

with open('object.json', 'w') as file:
    parsed_js = loads(final_js[0])
    dump(parsed_js, file, indent=4, sort_keys=True)

with open('object.json', 'r+') as file:
    data = load(file)

    for i in data:

        title = i["title"]
        title = title.title()
        rating = i["mpaaRating"]
        popcorn_score = i["popcornScore"]
        tomato_score = i["tomatoScore"]
        all_movies_two[title] = {
            'rating': rating,
            'popcornscore': popcorn_score,
            'tomatoscore': tomato_score
        }
for i in all_movies_two:
    try:
        all_movies.update(all_movies_two) or all_movies
    except RuntimeError:
        continue

with open('bomfile.json', 'r+') as file:
    data = load(file)

    for item in data:

        title = item['title']

        while not str.isupper(title):
            # title = title.split('\n')
            title = title[:-1]
        # print(title[-3:])
        if title[-3:] == 'X E':
            title = title[:-5]
        else:
            title = title[:-1]
        title = title.title()
        day1 = item['day1']
        day1 = day1.split('\n')[0]
        day2 = item['day2']
        day2 = day2.split('\n')[0]
        day3 = item['day3']
        day3 = day3.split('\n')[0]
        day4 = item['day4']
        day4 = day4.split('\n')[0]

        if day1 is not 'N/A':
            gross = day1
        elif day2 is not 'N/A':
            gross = day2
        elif day3 is not 'N/A':
            gross = day3
        else:
            gross = day4
        all_movies3[title] = {
            # 'metascore': metascore,
            # 'genre': genre,
            'Gross': gross
        }
print(all_movies3)
for movie in imdb_movies:
    # print(movie.find("span", { "class" : "metascore" }))
    if movie.find("span", { "class" : "metascore" }) is not None:
        metascore = movie.find("span", { "class" : "metascore" }).text.rstrip()

        genre = movie.find("p", { "class" : "cert-runtime-genre" }).span.text
        title = movie.find('td', { "class" : "overview-top" }).h4.a.text[:-7].lstrip()
        title = title.title()
        if title in all_movies3:
            d = all_movies3[title]
            gross = d['Gross']

        else:
            gross = 'unknown'
        if title in all_movies_two:
            d = all_movies_two[title]
            rating = d["rating"]
            popcorn_score = d["popcornscore"]
            tomato_score = d["tomatoscore"]
        else:
            popcorn_score = 'unknown'
            tomato_score = 'unkown'
            rating = 'unrated'
        all_movies[title] = {'Genre': genre, 'Rating':rating, 'IMDB Metascore': metascore, 'Popcorn Score': popcorn_score, "Tomato Score": tomato_score,'Gross': gross}
# for i in all_movies3:
#     try:
#         all_movies.update(all_movies3) or all_movies
#     except RuntimeError:
#         continue
# for i in all_movies:
#     try:
#         if i is in all_movies3:
#
#         p = all_movies[i]
#         pp = all_movies3[i]
#         p['Gross'] = pp['Gross']
#     except RuntimeError:
#         continue


with open(datestring+'.json', 'w') as file:
    x = ([all_movies])
    dump(x, file, indent=4, sort_keys=True)
os.remove("bomfile.json")
os.remove("object.json")