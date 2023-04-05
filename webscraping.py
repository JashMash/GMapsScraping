from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By


from parsel import Selector

from bs4 import BeautifulSoup
import requests

from time import sleep


# for stupid way to get store hours
from datetime import datetime
import pytz

# Converting Open/plus code to Long and Lat
from utils.openlocationcode import * # didnt really work

# Converting address to long and lat
from geopy.geocoders import Nominatim


SCROLL_PAUSE_TIME = 0.5


driver = webdriver.Chrome()

# driver.get("https://www.google.com/maps/@51.0593836,-114.0974328,10.79z")


class LocationData:
    name: str
    location: str
    rating: int
    reviews: int
    category: str
    price: str
    url: str
    hours: list
    coords: list
    

sleep(2)


page_content = driver.page_source
response = Selector(page_content)
class LocationScraper:
    def __init__(self, city, country) -> None:
        self.city = city
        self.country = country
        self.geolocator = Nominatim(user_agent="location_conversion_test")
        rel_coords = self.geolocator.geocode(f"{self.city}, {self.country}")
        self.rel_coords = [rel_coords.latitude, rel_coords.longitude]
        pass

    def communities_finder(self):
        driver.get(url = f"https://www.google.com/maps/search/neighbourhoods+in+{self.city}+{self.country}/")
        
        hoods = set()

        results = self.scroller(driver)

        # results = driver.find_elements(By.XPATH, '//div[contains(@aria-label, "Results for")]/div/div[./a]')

        for el in results:
            if el.accessible_name not in hoods:
                hoods.add(el.accessible_name)
        return hoods
    

    def search_locations(self, community: str= "", location_type: str = "parks"):
        driver.get(url = f"https://www.google.com/maps/search/{location_type}+in+{community}+{self.city}+{self.country}/")
        search_box = driver.find_element(By.CLASS_NAME, "tactile-searchbox-input")
        search_box.send_keys(location_type)

        results_par, results_sel = self.scroller(driver)

        loc_dict= {}
        all_entries = set()
        links =[]

        # for el in results_par:
        #     driver.get(url = el.xpath('./a/@href').get())
        #     # page = requests.get(el.xpath('./a/@href'))
        #     # soup = BeautifulSoup(page.content, "html.parser")
        #     soup = BeautifulSoup(driver.page_source, "html.parser")
        #     print(self.__parse_place(soup))

        fail_count=0
        fail_names = set()
        fail_dict = dict()
        for (el, par) in zip(results_sel, results_par):
            if el.accessible_name not in all_entries:
                all_entries.add(el.accessible_name)

                parsed_data=self.get_location_details_low(el.text)
                if parsed_data is not None:
                    parsed_data['link']= par.xpath('./a/@href').get()
                    # parsed_data['Hours'] = self.get_hours(parsed_data['link'])
                    loc_dict[el.accessible_name] =parsed_data
                    
                else:
                    fail_count+=1
                    fail_names.add(el.accessible_name)
                    fail_dict[el.accessible_name] = par.xpath('./a/@href').get()
                    all_entries.remove(el.accessible_name)
            else:
                ## for some reason if they have the same name
                count = 2
                name = el.accessible_name+" @@ "+str(count)
                
                ## cycling through different names
                while name in loc_dict.keys():
                    count+=1
                    name = el.accessible_name+" @@ "+str(count)

                parsed_data=self.get_location_details_low(el.text)
                if parsed_data is not None:
                    parsed_data['link']= par.xpath('./a/@href').get()
                    # parsed_data['Hours'] = self.get_hours(parsed_data['link'])
                    loc_dict[name] =parsed_data
                    
                else:
                    fail_count+=1
                    fail_names.add(name)
                    fail_dict[name] = par.xpath('./a/@href').get()

        special_failures = dict()
        loc_dict, special_failures = self.get_location_details_high(loc_dict)

        print(f"\nFAILED TO FIND DATA FOR: {fail_count}")
        for i in fail_names:
            print(i, end="  |  ")
        
        print(f"\nSPECIAL FAILS: {len(special_failures)}")
        for i in special_failures.keys():
            print(i, end="  |  ")

        print(f"\nNumber of {location_type} found: {len(loc_dict)}")

        return loc_dict

    def get_location_details_low(self, data_str: str) -> dict:
        """
            Takes in a string and parses out the following:
            
                Category they call themselves as,
                Location,
                Rating out of 5,
                Number of reviews,
                Price in number of '$' symbols ranging from 1-4
            
            Returns as a dict with the keys:
            ['category','location', 'rating', 'price']
        """
        t_split = data_str.split('\n')

        if any("store" in s for s in t_split):
            return None

        res = {}

        try:
            if t_split[0]=="Ad":
                rating_price = t_split[4].split(' · ')
                res['category'], res['location'] = t_split[5].split(' · ')
            else:
                rating_price = t_split[1].split(' · ')
                res['category'], res['location'] = t_split[2].split(' · ')

            res['rating'], res['reviews'] = rating_price[0][:-1].split('(')
            res['rating'] = res['rating'].replace("Ad ", "")
            try:
                res['price'] = rating_price[1]
            except:
                res['price']='NA'
        except:
            return None
        
        return res

    def get_location_details_high(self, loc_dict:dict) -> dict:
        """
            This takes all the locations found and find their 
            hours and coordinates

            adds dict keys to each location, keys:
            ['hours', 'coords']
        """
        driver2 = webdriver.Chrome()

        failures = dict()

        for key in loc_dict.keys():
            curr_url = loc_dict[key]['link']
            driver2.get(url=curr_url)
            response = Selector(driver2.page_source)

            # GET HOURS
            loc_dict[key]['hours'] = self.get_hours(response)
            if loc_dict[key]['hours'] =='NA':
                failures[key]={"link":loc_dict[key]['link'], "fail":['hours']}

            # GET location
            loc_dict[key]['location'] = self.get_address(response)
            if loc_dict[key]['location'] =='NA':
                if key in failures:
                    failures[key]['fail'].append('location')
                else:
                    failures[key]={"link":loc_dict[key]['link'], "fail":['location']}

            # GET Long & Latitude
            loc_dict[key]['coords'] = self.get_coords(response)
            if loc_dict[key]['coords'] =='NA':
                if key in failures:
                    failures[key]['fail'].append('coords')
                else:
                    failures[key]={"link":loc_dict[key]['link'], "fail":['coords']}
        return loc_dict, failures

    def get_hours(self, response) -> dict:
        """
            Uses link passed in with the location dictionary
            to find hours.

            and returns in the format of a dictionary:

            hours = { '<day>': {'Open': <time a.m./p.m.>, 'Close': <time a.m./p.m.>}
                        ....}
        
        """

        # current_dateTime = datetime.now(pytz.timezone("Canada/Mountain"))
        # day = current_dateTime.strftime("%A")     

        try:
            results_par = response.xpath('//div[contains(@aria-label, ". Hide open hours")]')
            unformated_hours = results_par.xpath('./@aria-label').get()

            # Removing unnecessary data
            unformated_hours = unformated_hours.replace('\u202f', ' ')
            unformated_hours = unformated_hours.split(". Hide")[0]
        except:
            all_hours = "NA"
            return all_hours

        all_day_hours = unformated_hours.split(';')

        all_hours= {}
        for day_h in all_day_hours:
            day, hours = day_h.split(", ")
            day = day.replace(' ', '')
            if hours =="Open 24 hours":
                all_hours[day]=hours
            elif hours != "Closed":
                open, close = hours.split(" to ")
                all_hours[day]={"Open": open, "Close": close}
            else:
                all_hours[day]="Closed"

        return all_hours

    def get_address(self, response)->str:
        """
            Retreives POI's address with given html.

            Input:
                response : <html> Loaction's google maps page
            
            Output:
        """
        results_par = response.xpath('//button[@data-item-id = "address"]')
        unformated_address = results_par.xpath('./@aria-label').get()

        ## unsure if it will fail
        if len(unformated_address.split(": "))>2:
            raise ValueError("Check why this one has more than one occurance of ': '...")
        address = unformated_address.split(": ")[1]
        return address

    def get_coords(self, response)->list:
        """
            Takes the url response, finds the Plus Code for the POI and relative coordinates
            (city's coordinates) and determines POI's coordinates.

            Input:
                response : <html> Loaction's google maps page
            
            Output:
                coordinates : <list> Contains latitude and longitude
        """
        
        results_par = response.xpath('//button[contains(@aria-label, "Plus code:")]')
        
        if results_par is not None:
            unformated_plus_code = results_par.xpath('./@aria-label').get()
            plus_code = unformated_plus_code.split(" ")[2]

            if len(plus_code)<= 7: ## When its a short code
                # Utils/openlocationcode.py 
                full_code = recoverNearest(plus_code, self.rel_coords[0], self.rel_coords[1])
            else:
                raise ValueError("Woah found one thats a longer code, check into why")
                full_code = plus_code

            # Utils/openlocationcode.py 
            coords = decode(full_code)

        return [coords.latitudeCenter, coords.longitudeCenter]


    def scroller(self, driver):
        """
            Scrolls to the end of results in map area being searched.
            
            Returns the all search results in 2 formats since the 2 formats contain slightly
            different information.

            Input:

            Output:
                results_par : 
                results_sel : <parcel

        """
        html = driver.find_element(By.XPATH, '//div[contains(@aria-label, "Results for")]')
        while True:
            html.send_keys(Keys.END)

            end = driver.find_elements(By.XPATH, '//div[contains(@aria-label, "Results for")]/div/div')[-1]
            if end.text == "You've reached the end of the list.":
                break
        
        page_content = driver.page_source
        response = Selector(page_content)
        results_sel = driver.find_elements(By.XPATH, '//div[contains(@aria-label, "Results for")]/div/div[./a]')
        results_par = response.xpath('//div[contains(@aria-label, "Results for")]/div/div[./a]')
        return results_par, results_sel
    

# def dict_reader(loc_dict):
#     driver2 = webdriver.Chrome()

#     current_dateTime = datetime.now(pytz.timezone("Canada/Mountain"))
#     # print(current_dateTime.strftime("%A"))
#     day = current_dateTime.strftime("%A")
    
#     for i in loc_dict.keys():
#         driver2.get(url=loc_dict[i]['link'])
#         response = Selector(driver2.page_source)
#         results_sel = driver2.find_elements(By.XPATH, '//div[contains(@aria-label, "'+ day +',")]')

#         results_par = response.xpath('//div[contains(@aria-label, "'+ day +',")]')
#         potential_hours = results_par.xpath('./@aria-label').get()
#         ind = 6
#         while ind < len(potential_hours):
#             if potential_hours[i-6:i] == "\u202f":
#                 potential_hours[i-6:i]= " "
#                 i-=5
            

#         print("Found data")


city = 'calgary'
country = 'Canada'
community = 'Evergreen'
location_type = "parks"

temp = LocationScraper(city, country)

# hoods = temp.communities_finder()

data = temp.search_locations(location_type=location_type)

dict_reader(data)

print("Communities:")
count = 0
for i in data:
    print(f"{i}", end="  |  ")
    if count == 5:
        # print("")
        count=0
    else:
        count+=1

# print("did this work?")