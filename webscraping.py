from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By


from parsel import Selector

# from bs4 import BeautifulSoup
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



sleep(2)


class LocationScraper:
    def __init__(self, city, country) -> None:
        self.driver = webdriver.Chrome()
        self.city = city
        self.country = country
        self.geolocator = Nominatim(user_agent="location_test1", timeout=10)
        rel_coords = self.geolocator.geocode(f"{self.city}, {self.country}")
        sleep(2)
        self.rel_coords = [rel_coords.latitude, rel_coords.longitude]
        pass

    def community_finder(self) -> dict:
        """
            Finds all communities within the given city.

            Output:
                communities : <dict> Contains all communities and their locations
        """
        self.driver.get(url = f"https://www.google.com/maps/search/neighbourhoods+in+{self.city}+{self.country}/")
        
        communities = dict()

        results_par, results_sel = self.scroller(self.driver)

        for (el, par) in zip(results_sel, results_par):
            if el.accessible_name not in communities.keys():
                communities[el.accessible_name] = par.xpath('./a/@href').get()
            else:
                ## If duplicate names found
                count = 2
                new_name = el.accessible_name+" @@ "+str(count)
                
                ## cycling through different names
                while new_name in communities.keys():
                    count+=1
                    new_name = el.accessible_name+" @@ "+str(count)
                
                communities[el.accessible_name] = par.xpath('./a/@href').get()
            
        
        return communities
    

    def search_POIs(self, POI_type: str = "parks") -> dict:
        """
            Given a Point of interest it will return all locations found 
            with the search in the city and more information on them.

            Input:
                POI_type : <str> A category of a location such as park, 
                                    malls, restaurants, bars, etc. 

            Output:
            TODO: Need to change to Dataframe for easier input into DBs
                loc_dict : <dict> For every location found in city with 
                                information:
                                    - Google maps URL :      'link'
                                    - Rating :               'rating'
                                    - # of reviews :         'reviews'
                                    - Address :              'location'
                                    - Price ($-$$$$) :       'price'
                                    - Category :             'category'
                                    - Hours of operation :   'hours'
                                    - Coordinates (Longitude and Latitude) : 'coords' 
        """

        self.driver.get(url = f"https://www.google.com/maps/search/{POI_type}+in+{self.city}+{self.country}/")
        search_box = self.driver.find_element(By.CLASS_NAME, "tactile-searchbox-input")
        search_box.send_keys(POI_type)

        # Finds all results in the area
        results_par, results_sel = self.scroller(self.driver)

        loc_dict= {}
        all_entries = set()

        # Failure tracker
        details_low_failures = dict()


        for (el, par) in zip(results_sel, results_par):
            if el.accessible_name not in all_entries:
                all_entries.add(el.accessible_name)

                parsed_data=self.get_POI_details_low(el.text)
                if parsed_data is not None:
                    parsed_data['link']= par.xpath('./a/@href').get()
                    loc_dict[el.accessible_name] =parsed_data
                    
                else:
                    details_low_failures[el.accessible_name] = par.xpath('./a/@href').get()
                    all_entries.remove(el.accessible_name)
            else:
                ## If duplicate names found
                count = 2
                new_name = el.accessible_name+" @@ " + str(count)
                
                ## cycling through different names
                while new_name in loc_dict.keys():
                    count+=1
                    new_name = el.accessible_name+" @@ " + str(count)
                
                all_entries.add(new_name)

                parsed_data=self.get_POI_details_low(el.text)
                if parsed_data is not None:
                    parsed_data['link']= par.xpath('./a/@href').get()
                    loc_dict[new_name] =parsed_data
                    
                else:
                    details_low_failures[new_name] = par.xpath('./a/@href').get()
                    all_entries.remove(new_name)

        details_high_failures = dict()
        loc_dict, details_high_failures = self.get_POI_details_high(loc_dict)

        print(f"\nDetails Low Fails: {len(details_low_failures)}")
        for i in details_low_failures.keys():
            print(i, end="  |  ")
        
        print(f"\nDetails High Fails: {len(details_high_failures)}")
        for i in details_high_failures.keys():
            print(i, end="  |  ")

        print(f"\nNumber of {POI_type} found: {len(loc_dict)}")

        return loc_dict

    def get_POI_details_low(self, data_str: str) -> dict:
        """
            Parses out information from searched list of items.

            Input:
                data_str : <str> containing:
                                Category they call themselves as,
                                Location,
                                Rating out of 5,
                                Number of reviews,
                                Price in number of '$' symbols ranging from $-$$$$
            
            Output:
                loc_low : <dict> with the following keys:
                                ['category', 'rating', 'reviews', 'price']
        """
        t_split = data_str.split('\n')

        if any("store" in s for s in t_split):
            return None

        loc_low = {}

        try:
            if t_split[0]=="Ad":
                rating_price = t_split[4].split(' · ')
                loc_low['category'], _ = t_split[5].split(' · ')
            else:
                rating_price = t_split[1].split(' · ')
                loc_low['category'], _ = t_split[2].split(' · ')

            loc_low['rating'], loc_low['reviews'] = rating_price[0][:-1].split('(')
            loc_low['rating'] = loc_low['rating'].replace("Ad ", "")
            try:
                loc_low['price'] = rating_price[1]
            except:
                loc_low['price']='NA'
        except:
            return None
        
        return loc_low

    def get_POI_details_high(self, loc_dict:dict) -> dict:
        """
            Takes all the POI's found and finds their 
            hours, coordinates, and address

            Input:
                loc_dict : <dict> Contains all POI details

            Output:
                loc_dict: <dict> Contains all POI details
                            Add following info to each location, 
                            with keys:
                            ['hours', 'coords', 'location']
        """
        location_driver = webdriver.Chrome()

        failures = dict()

        for key in loc_dict.keys():
            curr_url = loc_dict[key]['link']
            location_driver.get(url=curr_url)
            response = Selector(location_driver.page_source)

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
            day_hours_split = day_h.split(", ")
            if len(day_hours_split) >2:
                # holiday check
                day, hours, _ = day_hours_split
                day = day.split('(')[0]
                print("got in here")
                with open("./tests/holiday_hours.txt", "w") as f:
                    f.write(response)
            else:  
                day, hours = day_hours_split
            day = day.replace(' ', '')
            if hours =="Open 24 hours":
                all_hours[day]=hours
            elif hours != "Closed":
                open_t, close_t = hours.split(" to ")
                all_hours[day]={"Open": self.military_time(open_t), "Close": self.military_time(close_t)}
            else:
                all_hours[day]="Closed"

        return all_hours

    def military_time(self, time:str)->str:
        """
            Converts 12 hour time to 24 hour clock

            Input:
                time : <str> 12 hour time, In format "5 p.m." or "6:30 a.m."
            
            Output:
                out_time : <str> 24 hour time, In format "17:00" or "6:30"
        """
        time, mered = time.split(' ')
        offset=0
        if mered =='p.m.':
            offset = 12
        
        if ':' in time:
            hours, mins = time.split(':')
            hours = int(hours) + offset
            out_time = str(hours)+':'+mins
        else:
            hours = int(time) + offset
            out_time = str(hours)+':00'
        return out_time

    def get_address(self, response)->str:
        """
            Retreives POI's address with given html.

            Input:
                response : <html> POI's google maps page
            
            Output:
                address : <str> Address of POI
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
                response : <html> POI's google maps page
            
            Output:
                coordinates : <list> Contains latitude and longitude of POI
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
                driver : <selenium.webdriver.chrome>
            Output:
                results_par : <list[parsel.selector]>
                results_sel : <list[selenium.webdriver.remote.webelement]>

        """
        html = driver.find_element(By.XPATH, '//div[contains(@aria-label, "Results for")]')
        # while True:
        #     html.send_keys(Keys.END)

        #     end = driver.find_elements(By.XPATH, '//div[contains(@aria-label, "Results for")]/div/div')[-1]
        #     if end.text == "You've reached the end of the list.":
        #         break
        
        page_content = driver.page_source
        response = Selector(page_content)
        results_sel = driver.find_elements(By.XPATH, '//div[contains(@aria-label, "Results for")]/div/div[./a]')
        results_par = response.xpath('//div[contains(@aria-label, "Results for")]/div/div[./a]')
        return results_par, results_sel
    


city = 'Calgary'
country = 'Canada'
location_type = "parks"

temp = LocationScraper(city, country)



data = temp.search_POIs(POI_type=location_type)

print("Break Point")


