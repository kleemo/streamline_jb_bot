class LocationHandler:
    def __init__(self):
        self.locations = []
        self.distances = []

    def handle_location(self, new_location):
        self.locations.append(new_location)
        if len(self.locations) > 1:
            new_distance = self.calculate_distance(self.locations[-2], new_location)
            self.distances.append(new_distance)
            return new_distance
        return 0
    
    def calculate_distance(self, location1, location2):
        dist_long = abs(location1["longitude"] - location2["longitude"])
        dist_lat = abs(location1["latitude"] - location2["latitude"])
        dist = (dist_long**2 + dist_lat**2)**0.5
        return dist