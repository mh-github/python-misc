#!/usr/bin/env python

import requests
from bs4 import BeautifulSoup
from openpyxl import Workbook

# 1. Fetch Results
print ("\nFetching results.....")
r = requests.post(
    url='http://www.indiavotes.com/ac/info?stateac=29&eid=257',
    headers={
        'X-Requested-With': 'XMLHttpRequest'
    }
)
page = BeautifulSoup(r.text, 'lxml')

place_urls = []
table      = page.find(id='m1')
cells      = table.find_all('td', attrs={'class':'tal'})
for cell in cells:
    link = cell.find('a')
    if link:
        url = link.get('href')
        if url.find('details') != -1:
            place = link.next_element
            place_urls.append((place, url))

results = {}
for (place, url) in place_urls:
    results[place] = []

    r = requests.post(
        url=url,
        headers={
            'X-Requested-With': 'XMLHttpRequest'
        }
    )
    page      = BeautifulSoup(r.text, 'lxml')
    table     = page.find(id='m1')
    cells     = table.find_all('td')
    counter   = 0
    # candidate = [place]
    candidate = []

    for cell in cells:
        counter += 1

        if counter % 5 == 0: #end of row
            candidate.append(cell.find('a').next_element)
            # got candidate's full details, add to results dictionary
            results[place].append(candidate)
            candidate = []
        else:
            candidate.append(cell.next_element)

counter  = inc = bjp = 0
bjp_wins = []

# Processing results
print "\nProcessing results....."
# constituencies in which margin was < #3's votes
for place in results:
    candidates = results[place]
    first      = candidates[0]
    second     = candidates[1]
    if len(candidates) > 2: # process only when there is a third candidate
        third  = candidates[2]
        margin = int(first[2].replace(',', '')) - int(second[2].replace(',', ''))
        if  margin < int(third[2].replace(',', '')):
            counter += 1
            print "\n------------------------"
            print ("%d. %s" % (counter, place))
            print ("Winner: %s, %s - %s" % (first[1], first[4], first[2]))
            print ("Second: %s, %s - %s" % (second[1], second[4], second[2]))
            print "Margin = " + str(margin)
            print ("Third: %s, %s - %s" % (third[1], third[4], third[2]))

            if first[4] == "Indian National Congress":
                inc += 1
            elif first[4] == "Bharatiya Janta Party":
                bjp += 1
                bjp_wins.append(place)

print ("\n\nTotal close-contest consituencies = %d" % (inc + bjp))
print ("Number of constituencies won by BJP = %d" % bjp)
print ("Number of constituencies won by INC = %d" % inc)

print "\n\nSecond runner-up's party in constituencies won by BJP"
print "-----------------------------------------------------"
for place1 in bjp_wins:
    for place2 in results:
        if place1 == place2 and results[place2][1][4] == "Indian National Congress":
            print ("%s : %s" % (place1, results[place2][2][4]))

# 3. Writing to Excel book
print "\nWriting full state results to Excel book....."
wb            = Workbook()
dest_filename = 'Gujarat_election_results_2017.xlsx'
ws1           = wb.active
ws1.title     = "All Constituencies"
header        = ["Constituency", "Position", "Candidate", "Votes", "Percentage", "Party"]
row           = []

ws1.append(header)
for place in results:
    candidates = results[place]
    for candidate in candidates:
        row = [place]
        for item in candidate:
            row.append(item)
        ws1.append(row)

wb.save(filename = dest_filename)