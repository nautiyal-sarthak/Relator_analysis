from __future__ import print_function
from realtor_analytics import getMergedDataframe
import numpy
import pandas as pd
import requests
import json



#sale_folderid = "14-vUH394CZ9BbjdbjKEHHcXbFxcHV--l"
#rent_folderid = "1xXUgEae8hpe1IQt8mye5lkaAIL4_ZKyO"

#saleDf = getMergedDataframe(sale_folderid)
#rentDf = getMergedDataframe(rent_folderid)

#sale_post = saleDf['PostalCode'].str[0:3].unique()
#rent_post = rentDf['PostalCode'].str[0:3].unique()



def sendreq(fsa):
    url = "https://vanitysoft-canada-postal-boundaries-v1.p.rapidapi.com/rest/v1/public/boundary/ca/fsa"

    querystring = {"postal-fsa": fsa}

    headers = {
        "X-RapidAPI-Key": "8dad1163famsh719ed34c5b72a5cp17fa4djsn73aefcc92c9a",
        "X-RapidAPI-Host": "vanitysoft-canada-postal-boundaries-v1.p.rapidapi.com"
    }

    response = requests.request("GET", url, headers=headers, params=querystring)
    j = json.loads(response.text)
    if len(j["features"]) > 0:
       feature = j["features"][0]
       feature["properties"]["name"] = fsa
       out = json.dumps(feature)

       with open('data.json', 'a') as f:
              json.dump(out + ",", f)


FSAA = {
       #"H7W":"Laval",
       #"J2X":"SAINT-JEAN-SUR-RICHELIEU",
       #"H4X":"CÔTE SAINT LUC",
       #"J3Y":"SAINT-HUBERT",
       #"J3N":"SAINT BASILE LE GRAND",
       #"H3P":"MONT-ROYAL",
       #"J6T":"SALABERRY-DE-VALLEYFIELD",
       #"H8R":"LACHINE",
       #"H7V":"LAVAL",
       # "H2R":"MONTRÉAL",
       # "H2G":"MONTRÉAL",
       # "J4R":"SAINT-LAMBERT",
       # "H4K":"MONTRÉAL",
       # "J4V":"GREENFIELD PARK",
       # "J3V":"SAINT-BRUNO",
       # "H4C":"MONTRÉAL",
       # "H9X":"SAINTE-ANNE-DE-BELLEVUE",
       # "J5W":"L'ASSOMPTION",
       # "H2L":"MONTRÉAL",
       # "J4G":"LONGUEUIL",
       # "H9G":"DOLLARD-DES-ORMEAUX",
       # "H7Y":"LAVAL",
       # "H3T":"MONTRÉAL",
       # "J0M":"SALLUIT",
       #"H3K":"MONTREAL",
       # "H3S":"MONTRÉAL",
       # "H4V":"COTE SAINT-LUC",
       # "H3G":"MONTRÉAL",
       # "H9C":"L'ÎLE-BIZARD",
       # "J4Z":"BROSSARD",
       # "H2E":"MONTRÉAL",
       # "H4S":"SAINT-LAURENT",
       # "H4P":"MONT-ROYAL",
       # "H3L":"MONTRÉAL",
       # "H8T":"LACHINE",
       # "J3L":"CHAMBLY",
       # "H7E":"LAVAL",
       # "H9E":"L'ÎLE-BIZARD",
       # "J3Z":"SAINT-HUBERT",
       # "H7P":"LAVAL",
       # "J7N":"MIRABEL",
       # "J7P":"SAINT-EUSTACHE",
       # "H1V":"MONTRÉAL",
       # "H2A":"MONTRÉAL",
       # "H2J":"MONTRÉAL",
       # "J4X":"BROSSARD",
       # "J3M":"MARIEVILLE",
       # "H1H":"",
       # "H1X":"",
       # "H1Y":"",
       # "H1W":"",
       # "H2M":"",
       # "H3N":"",
       # "H4W":"",
       # "H9B":"",
       # "J4L":"",
       # "H2K":"",
       # # "H4R":"",
       #
       #
       # "H9S":"",
       # "H7R":"",
       # "J4P":"",
       # "H2H":"",
       # "H4A":"",
       # "H3V":"",
       # "H4E":"",
       # "H3M":"",
       # "H2S":"",
       # "H2C":"",
       # "J7M":"",
       # "H9W":"",
       # "J0N":"",
       # "H9R":"",

       # "J0L":"",
       # "H3H":"",
       # "H3R":"",
       # "H2Y":"",
       # "H8Z":"",
       # "J4K":"",
       # "H8P":"",
       # "H1G":"",
       # "H4B":"",
       # "H9P":"",
       # "H9K":"",
       # "H1S":"",
       # "H9A":"",
       # "H1Z":"",
       # "H1B":"",


       # "H2N":"",
       # "J0P":"",
       # "J6N":"",
       # "J0Z":"",
       # "J7R":"",
       # "H1M":"",
       # "H7M":"",
       # "H4M":"",
       # "J4N":"",
       # "H3Y":"",
       # "J6J":"",
       # "J7W":"",
       # "J4Y":"",
       # "J7G":"",
       # "J2Y":"",
       # "J3K":"",
       # "J4T":"",
       # "H7Z":"",
       # "H2V":"",
       # "H2W":"",
       # "H3X":"",
       # "H3C":"",
       # "J4W":"",
       # "H7X":"",
       # "H2P":"",
       # "H4G":"",
       # "H7S":"",
       # "J7C":"",
       # "H3W":"",
       # "J7V":"",
       # "H3J":"",
       # "J3G":"",
       # "H8N":"",
       #"J5A":"saint-constant",
       #"H1L":"",
       #"H3E":"",
       # "H4H":"",
       # "H2X":"",
       # "H7G":"",
       # "J7T":"",
       # "J0R":"",
       # "H9H":"",
       # "J5B":"",
       # "H2Z":"",
       # "H8Y":"",
       # "H2B":"",
       # "J3E":"",
       # "J5R":"",
       # "H7T":"",
       # "J4M":"",
       #"H4L":"saint-laurent",
       # "H1R":"",
       # "J4S":"",
       # "J4H":"",
       # "H1T":"",
       # "H1N":"",
       # "H8S":"",
       # "J3H":"",
       # "H4J":"",
       # "H8H":"",
       # "J5C":"",
       # "H3B":"",
       "H3A":"",
       "H7L":"",
       "J3B":"",
       "H4N":"",
       "H7N":"",
       "H1K":"",
       "J4B":"",
       "J4J":"",
       "H2T":"",
       "J2W":"",
       "J5H":"",
       "H1P":"",
       "H3Z":"",
       "H9J":""
}


struc = {
    "H3A": "",
    "H7L": "",
    "J3B": "",
    "H4N": "",
    "H7N": "",
    "H1K": "",
    "J4B": "",
    "J4J": "",
    "H2T": "",
    "J2W": "",
    "J5H": "",
    "H1P": "",
    "H3Z": "",
    "H9J": ""
}

for k, v in struc.items():
    print(k)
    sendreq(k)

print("done")





