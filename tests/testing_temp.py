import sys, os

from parsel import Selector

sys.path.append(f"{os.getcwd()}")


import unittest
from webscraping import LocationScraper


city = 'Calgary'
country = 'Canada'
temp = LocationScraper(city, country)
def test_holiday_hours():
    with open("tests/holiday_hours.html", "r", encoding="utf8") as f:
        holiday_data = f.read()

    holiday_data = Selector(holiday_data)

    result = temp.get_hours(holiday_data)

    results_par = holiday_data.xpath('//div[contains(@aria-label, ". Hide open hours")]')
    unformated_hours = results_par.xpath('./@aria-label').get()

    # Removing unnecessary data
    unformated_hours = unformated_hours.replace('\u202f', ' ')
    unformated_hours = unformated_hours.split(". Hide")[0]


    all_day_hours = unformated_hours.split(';')

    print("What it contains:")
    print(all_day_hours)

    print(result)

    expected_result = {'Friday': {'Open': '5:00', 'Close': '23:00'}, 'Saturday': {'Open': '5:00', 'Close': '23:00'}, 'Sunday': {'Open': '5:00', 'Close': '23:00'}, 'Monday': {'Open': '5:00', 'Close': '23:00'}, 'Tuesday': {'Open': '5:00', 'Close': '23:00'}, 'Wednesday': {'Open': '5:00', 'Close': '23:00'}, 'Thursday': {'Open': '5:00', 'Close': '23:00'}}
    print(expected_result)
    return

print("breakpoint")



def test_POI_search():
    location_type="parks"

    data = temp.search_POIs(POI_type=location_type)

test_POI_search()