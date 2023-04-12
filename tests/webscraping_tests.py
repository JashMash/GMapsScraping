import sys, os
sys.path.append(f"{os.getcwd()}")

import unittest
from webscraping import LocationScraper

from parsel import Selector

class WebScrapeTests(unittest.TestCase):
    """
        Test cases to check functionality of
        the class "LocationScraper"

        Test cases:
            + def get_POI_details_low(self, data_str: str) -> dict:
                - base functionality
            + def get_POI_details_high(self, loc_dict: dict) -> dict:
                - base functionality
            + def get_hours(self, response) -> dict:
                - Holiday hours
                - 24 hours
            
            # TODO
            + def military_time(self, time:str) -> str
                - Time doesnt contain AM or PM 
                - AM times are below 12
                - PM times are above 12
                - All times have mintutes even if they are passed as just hours
            
    """
    city = "Calgary"
    country = "Canada"
    test_class = LocationScraper(city, country)

    def test_base_low_details(self):
        """
            TEST: Basic functionality test of "get_POI_details_low()" 
        """

        with open("tests/low_base_case_carburn_park.txt", "r", encoding="utf8") as f:
            base_data = f.read()

        result = self.test_class.get_POI_details_low(base_data)

        expected = {'category': 'Park', 'rating': '4.7', 'reviews': '1,863', 
                    'price': 'NA'}

        self.assertEqual(result, expected)


    def test_base_high_details(self):
        """
            TEST: Basic functionality test of "get_POI_details_high()" 
        """

        base_data = {1:{'link': 'https://www.google.com/maps/place/Carburn+Park/data=!4m7!3m6!1s0x537170ccf0ae1a79:0xcd71bb48719d5858!8m2!3d50.9743178!4d-114.0326618!16s%2Fg%2F1trtt_9_!19sChIJeRqu8MxwcVMRWFidcUi7cc0?authuser=0&hl=en&rclk=1'}}

        result, failures = self.test_class.get_POI_details_high(base_data)
        
        expected = {1:{'link': 'https://www.google.com/maps/place/Carburn+Park/data=!4m7!3m6!1s0x537170ccf0ae1a79:0xcd71bb48719d5858!8m2!3d50.9743178!4d-114.0326618!16s%2Fg%2F1trtt_9_!19sChIJeRqu8MxwcVMRWFidcUi7cc0?authuser=0&hl=en&rclk=1', 
                    'hours': {'Tuesday': {'Open': '5:00', 'Close': '23:00'}, 
                              'Wednesday': {'Open': '5:00', 'Close': '23:00'}, 
                              'Thursday': {'Open': '5:00', 'Close': '23:00'}, 
                              'Friday': {'Open': '5:00', 'Close': '23:00'}, 
                              'Saturday': {'Open': '5:00', 'Close': '23:00'}, 
                              'Sunday': {'Open': '5:00', 'Close': '23:00'}, 
                              'Monday': {'Open': '5:00', 'Close': '23:00'}}, 
                    'location': '67 Riverview Dr SE, Calgary, AB T2C 4H8 ', 
                    'coords': [50.974312499999996, -114.0326875]}}
        self.assertEqual(result, expected)


    def test_holiday_hours(self):
        """
            TEST: Will it return appropriate time format 
                    even in case of a holiday string format
        """
        
        with open("tests/holiday_hours.html", "r", encoding="utf8") as f:
            holiday_data = f.read()

        holiday_data = Selector(holiday_data)

        result = self.test_class.get_hours(holiday_data)

        expected = {'Friday': {'Open': '5:00', 'Close': '23:00'}, 
                           'Saturday': {'Open': '5:00', 'Close': '23:00'}, 
                           'Sunday': {'Open': '5:00', 'Close': '23:00'}, 
                           'Monday': {'Open': '5:00', 'Close': '23:00'}, 
                           'Tuesday': {'Open': '5:00', 'Close': '23:00'}, 
                           'Wednesday': {'Open': '5:00', 'Close': '23:00'}, 
                           'Thursday': {'Open': '5:00', 'Close': '23:00'}}
        
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main()