import requests
import json
import ast
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException        

#initialise
mystr = ''

# user input
userin = input('Enter activity name (and location if known): ')

# split input into word list
words = userin.split()

for word in words:
    mystr += word + '+'
mystr = mystr.rstrip(mystr[-1])

url = "https://nominatim.openstreetmap.org/search.php?q=" + mystr + "&format=jsonv2"
response = requests.get(url)

# gets text of json file
jtext = response.text
# as string, for distinguishing between name and location based on commas
jtext = jtext.replace('"',' ')

# if no results, jtext = "[]" meaning length is 2
if len(jtext) > 2:
    # Activity name, street number, street address, city, state and zip and lat and long.
    start = jtext.find("display_name")
    end = jtext.find("place_rank")
    # 15 indexes after display_name : is name
    substr = jtext[start + 15:end - 1]
    # split string then get activity name
    sublst = substr.split(", ")
    act = sublst[0]
    stnum = 0
    stadd = ""
    city = ""
    county = ""
    state = ""
    zip = 0
    lat = ""
    lon = ""

    numoradd = ""
    numoradd = sublst[1]
    # get street number or address, then assign element to variables accordingly
    if numoradd[0].isdigit():
        stnum = sublst[1]
        stadd = sublst[2]
        city = sublst[3]
        if ("County" or "county" in sublst[4]):
            county = sublst[4]
            state = sublst[5]
            zip = sublst[6]
        else:
            county = ""
            state = sublst[4]
            zip = sublst[5]
    elif numoradd[0].isalpha():
        stnum = ""
        stadd = sublst[1]
        city = sublst[2]
        if ("County" or "county" in sublst[3]):
            county = sublst[3]
            state = sublst[4]
            zip = sublst[5]
        else:
            county = ""
            state = sublst[3]
            zip = sublst[4]
    # find lat
    start = jtext.find("lat : ")
    end = jtext.find(" , lon : ")
    lat = jtext[start + 5 : end]
    # find lon
    start = jtext.find("lon : ")
    end = jtext.find(" , display_name : ")
    lon = jtext[start + 5 : end]

    # find osm type
    start = jtext.find("osm_type : ")
    end = jtext.find(" , osm_id :")
    osmtype = jtext[start + 11 : end]
    # node or way
    if osmtype == "node":
        osmtype = "N"
    if osmtype == "way":
        osmtype = "W"
    # find osm id
    start = jtext.find("osm_id :")
    end = jtext.find(" boundingbox ")
    osmid = jtext[start + 8 : end - 1]
    # find category
    start = jtext.find("category : ")
    end = jtext.find(" , type : ")
    category = jtext[start + 11 : end]
    gurl = "https://nominatim.openstreetmap.org/ui/details.html?osmtype=" + osmtype + "&osmid=" + osmid + "&class=" + category

    driver = webdriver.Chrome('/home/beeswax/Downloads/chromedriver')
    def check_exists_by_xpath(xpath):
        try:
            driver.find_element_by_xpath(xpath)
        except NoSuchElementException:
            return False
        return True


    driver.get(gurl)

    findwkdta = []
    if check_exists_by_xpath('//div[@class="line"]'):
        # wikidata
        findwkdta = driver.find_elements_by_xpath('//div[@class="line"]')

    wikidatalist = []
    for p in range(len(findwkdta)):
        wikidatalist.append(findwkdta[p].text)

    wikidata = ""
    for p in range(len(wikidatalist)):
        if "(wikidata)" in wikidatalist[p]:
            end = wikidatalist[p].find(" (wikidata)")
            wikidata = wikidatalist[p][0 : end]
    wdurl = "https://www.wikidata.org/wiki/" + wikidata

    driver.get(wdurl)
    findwk = ""
    if check_exists_by_xpath("//a[@href]"):
        findwk = driver.find_elements_by_xpath("//a[@href]")
        # wikimedia
        wkmdaurl = ""
        for p in range(len(findwk)):
            href = findwk[p].get_attribute("href")
            if "https://commons.wikimedia.org/wiki/" in href:
                wkmdaurl = href
                break

        # wikipedia
        wkpdaurl = ""
        for p in range(len(findwk)):
            href = findwk[p].get_attribute("href")
            if ("https://en.wikipedia.org/wiki/" in href):
                wkpdaurl = href
                break

    # website
    lst = []
    if check_exists_by_xpath('//div[@class = wikibase-snakview-value wikibase-snakview-variation-valuesnak"]'):
        finddesc = driver.find_elements_by_xpath('//div[@class = wikibase-snakview-value wikibase-snakview-variation-valuesnak"]')
        for p in range(len(finddesc)):
            lst.append(finddesc[p].text)

    # description
    driver.get(wkpdaurl)
    finddesc = []
    if check_exists_by_xpath("//p"):
        finddesc = driver.find_elements_by_xpath("//p")

        desc = ""
        for p in range(len(finddesc)):
            desc += finddesc[p].text
            if len(desc.split()) >= 50:
                break

    # licence and attribution
    driver.get(wkmdaurl)
    findimage = []
    if check_exists_by_xpath("//a[@href]"):
        findimage = driver.find_elements_by_xpath("//a[@href]")

        for p in range(len(findimage)):
            href = findimage[p].get_attribute("href")
            if "/wiki/File:" in href:
                imageurl = href
                break

    driver.get(imageurl)
    findauth = []
    if check_exists_by_xpath('//td'):
        findauth = driver.find_elements_by_xpath('//td')

        for p in range(len(findauth)):
            if "Author" in findauth[p].text:
                author = findauth[p + 1].text
                break

    # licence
    findlce = []
    if check_exists_by_xpath('//td'):
        findlce = driver.find_elements_by_xpath('//td')

        for p in range(len(findlce)):
            if "This file is made available under the " in findlce[p].text:
                lcestr = findlce[p].text
                lcestr = lcestr[:-1]
                license = lcestr[lcestr.startswith('This file is made available under the ') and len('This file is made available under the '):]
                break

    driver.close()

    dictionary = {
        "Activity":act,
        "Description":desc,
        "Street Number":stnum,
        "Street Address":stadd,
        "City":city,
        "County":county,
        "State":state,
        "Zip Code":zip,
        "WikiData ID":wikidata,
        "Wikimedia URL": wkmdaurl,
        "Wikipedia": wkpdaurl,
        "Image URL": imageurl,
        "Author": author,
        "License": license
    }

    with open("data.json", "w") as outfile:
        json.dump(dictionary, outfile)

else:
    print("No results found")

