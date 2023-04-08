import sys

sys.path.insert()

import unittest
import webscraping

class WebScrapeTests(unittest.TestCase):
    """
        Test cases to check functionality of
        the class "LocationScraper"

        Test cases:
            + def get_hours(self, response) -> dict:
                - Holiday hours
                - 24 hours
    """
    city = "Calgary"
    country = "Canada"

    def test_holiday_hours(self):
        """
            TEST: if the functions can hold more than 127
                    duplicates
        """


        with open("holiday_hours.html", 'r') as f:
            holiday_data = f.read()

        # expected_result = 

        # data = 
        
        self.assertEqual(byte_decomp(byte_compress(data)), data)

if __name__ == '__main__':
    unittest.main()