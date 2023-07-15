import requests

from bs4 import BeautifulSoup


# Fetch a list of IMDB top 250 movies

headers = {"Accept-Language": "en-US,en;q=0.5"}
r = requests.get("https://www.imdb.com/chart/top/", headers=headers)
soup = BeautifulSoup(r.text, "html.parser")

# with open("movie_list.txt", "w") as f:
# 	lines = [ item.a.text + "\n" for item in soup.select("td.titleColumn") ]
# 	f.writelines(lines)



lines = [ item.a.text for item in soup.select("td.titleColumn") ]
invalid = []
for item in lines:
	title = item.strip("\n").replace(" ", "_")
	r = requests.get(f"https://en.wikipedia.org/api/rest_v1/page/html/{title}")
	soup = BeautifulSoup(r.text, "html.parser")
	
	# Check that the result contains a plot section
	if not soup.select("#Plot"):
		invalid.append(title)