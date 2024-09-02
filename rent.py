import googlemaps.client
from selenium import webdriver
from selenium.webdriver.common.by import By
import json
import googlemaps
from googlemaps.distance_matrix import distance_matrix
import time
from os import path
import random
import glob

def store_rent_results_pages(url_template : str, max):
    file_name = "rentresults_{}.txt".format(int(time.time()))
    with open(file_name, "w", -1, "utf-8") as file:
        for i in range(1, max + 1):
            url = url_template.format(i)
            hrefs = get_rent_results(url)
            if (len(hrefs) == 0):
                return
            print("writing results")
            file.writelines(["{}\n".format(x) for x in hrefs])
            time.sleep(random.random() + 1)
    return file_name

def get_rent_results(url):
    print("getting results from {}".format(url))
    with webdriver.Chrome() as driver:
        driver.get(url)
        links = driver.find_elements(by=By.CSS_SELECTOR, value="div[class^='_container'] div[class^='_list_'] a")
        return [a.get_attribute("href") for a in links]

def store_rent_data_from_results(results_file_name):
    with open(results_file_name, "r", -1, "utf-8") as file:
        lines = file.readlines()
        for line in lines:
            url = line.strip()
            id = url[-7:]
            if (path.exists("rent_{}.json".format(id))):
                print("skipping listing {}".format(id))
                continue
            store_rent_data(url)
            time.sleep(random.random() + 0.5)

def store_rent_data(url, driver = None):
    close_driver = False
    if (driver is None):
        close_driver = True
        driver = webdriver.Chrome()
    try:
        driver.get(url)
        print("getting rent listing data {}".format(url))
        element = driver.find_element(by=By.CSS_SELECTOR, value="#__NEXT_DATA__")
        data_string = element.get_attribute("textContent")
        data = json.loads(data_string)
        id = data["props"]["pageProps"]["path"]["listing"]["id"]
        with open("rent_{}.json".format(id), "w", -1, "utf-8") as file:
            print("writing listing data")
            file.write(data_string)
        return id
    finally:
        if (close_driver):
            driver.close()

def get_rent_location(id):
    with open("rent_{}.json".format(id), "r", -1, "utf-8") as file:
        data = json.load(file)
        location = data["props"]["pageProps"]["path"]["listing"]["location"]
        lat_lng = "{},{}".format(location["lat"], location["lng"])
        return lat_lng

def get_rent_price(id):
    with open("rent_{}.json".format(id), "r", -1, "utf-8") as file:
        data = json.load(file)
        price = data["props"]["pageProps"]["path"]["listing"]["price"]
        return price

def store_all_distances_from_results(results_file_name, key, destination):
    client = googlemaps.Client(key)
    with open(results_file_name, "r", -1, "utf-8") as file:
        lines = file.readlines()
        for line in lines:
            url = line.strip()
            id = url[-7:]
            if (path.exists("matrix_{}.json".format(id))):
                print("skipping listing {}".format(id))
                continue
            origin = get_rent_location(id)
            store_distance(id, origin, destination, client=client)
            time.sleep(0.1)

def store_distance(id, origin, destination, key=None, client=None):
    if (client is None):
        if (key is not None):
            client = googlemaps.Client(key=key)
    if (client is None):
        raise Exception("No client")
    print("getting distance for {} to {}".format(id, destination))
    matrix = distance_matrix(client, origin, destination, "driving", None, None, "metric", None, None, None, None, None, "SA")
    with open("matrix_{}.json".format(id), "w", -1, "utf-8") as file:
        json.dump(matrix, file)
    return matrix['rows'][0]['elements'][0]['duration']['value']

def get_distance(id):
    with open("matrix_{}.json".format(id), "r", -1, "utf-8") as file:
        matrix = json.load(file)
        return matrix['rows'][0]['elements'][0]['duration']['value']

def export(results_file_name):
    with open("export_{}.csv".format(results_file_name), "w", -1, "utf-8") as csv:
        csv.write("id,distance,price\n")
        with open(results_file_name, "r", -1, "utf-8") as file:
            lines = file.readlines()
            for line in lines:
                url = line.strip()
                id = url[-7:]
                csv.write("{},{},{}\n".format(id, get_distance(id), get_rent_price(id)))

if __name__ == '__main__':
    search_url = "https://RENT_SITE/شقق-للإيجار/الرياض/{}?beds=eq,2&price=lte,55000,gte,30000&wc=eq,2&ac=eq,1"
    search_results_file = store_rent_results_pages(search_url, 20)

    store_rent_data_from_results(search_results_file)

    work = "WORK_ADDRESS"
    google_key = "GOOGLE_MAPS_KEY"
    store_all_distances_from_results(search_results_file, google_key, work)

    export(search_results_file)