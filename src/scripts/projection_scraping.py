from bs4 import BeautifulSoup
import requests
from requests_html import HTMLSession

from curl_extractor import extract_curl_data

def main():
    url, headers = extract_curl_data()
    #response = requests.get(url, headers=headers)
    session = HTMLSession()

    response = session.get(url) # , headers=headers)
    response = response.html.render()

    with open("sleeper.html", "w") as f:
        f.write(response.html.html)

    if response.status_code == 200 and False:
        soup = BeautifulSoup(response.text, "html.parser")
        owner_matchups = soup.find_all("div", class_="score")
        print(owner_matchups)
        for owner_matchup in owner_matchups:
            print(owner_matchup)
    else:
        pass
        #raise ValueError("Bad response, likely out of date cURL.")
if __name__ == "__main__":
    main()
