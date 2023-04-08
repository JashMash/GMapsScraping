## Google maps scraping

This is a repo created from an interest to find general information <br/>
for different types of locations in cities. 

Locations such as:
- Bars
- Restuarants
- Malls
- Parks
- Museums

Information such as:
- Google maps URL
- Rating
- Number of reviews
- Address
- Price ($-$$$$)
- Category
- Hours of operation
- Coordinates (Longitude and Latitude) 


### Primary class is:<br/>
    class LocationScraper

&nbsp;&nbsp;&nbsp;&nbsp;Initialization: <br/>

		def __init__(self, city, country)

&nbsp;&nbsp;&nbsp;&nbsp;Current primary functions:<br/>
        
        def search_POIs(self, POI_type: str = "bars") -> dict
            - Searches for all locations that appear when the 
              POI_type is searched for in google maps when located
              over the city and country specified

        def community_finder(self) -> dict
            - Searches for all communities located in the city
              this is for later purposes of categorizing searches
