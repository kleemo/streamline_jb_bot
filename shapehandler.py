# -*- coding: utf-8 -*-
"""
Name: Shape Handler
Description: is responsible to deal with the creation and adaption of the shapes
"""

# import custom classes
import point_calc as pc
import numpy as np
from shapely.geometry import Polygon, LineString

class Shapehandler:
    def __init__(self):
        self.current_rotation = 0
        self.current_diameter = (0,0)
        self.previous_vector = []
        self.previous_points = []
        self.parameters = { #new parameters
            "shape": "none",
            "diameter": (0,0),
            "growth_direction": (0, 0),
            "pattern": "none",
            "pattern_spacing":2, #between 3 and 6
            "pattern_height":8, #between 2 and 5
            "pattern_width":4, #between 2 and 5
            "rotation": 0,
            "inactive": False,
            "feature_vector": [],
            "center_points": [(0,0), (30,10),(40,-20),(-30,20)],
            "repetitions": 1,
        }
    
    
    
    def scale(self, points, factor):
        # scale an entire shape
        for i in range(len(points)):
            points[i] =  points[i] * factor

        return points
    
    
    def update_parameters(self, data):
        self.parameters["shape"] = data["shape"]
        self.parameters["diameter"] = data["diameter"]
        self.parameters["growth_direction"] = data["growth_direction"]
        self.parameters["pattern"] = data["pattern"]
        self.parameters["rotation"] = data["rotation"]
        self.parameters["pattern_height"] = data["pattern_height"]
        self.parameters["pattern_width"] = data["pattern_width"]
        self.parameters["inactive"] = data["inactive"]
        self.parameters["feature_vector"] = data["feature_vector"]
        #self.parameters["center_points"] = data["center_points"]
        self.parameters["pattern_spacing"] = int(data["pattern_spacing"])
        #initialize the current diameter only at the very beginning
        if set(self.current_diameter) == {0}:
            self.current_diameter = self.parameters["diameter"]
        # scale the pattern intensity with reduced diameter
        if max(self.current_diameter[0], self.current_diameter[1]) < 25 and self.parameters["pattern_height"] > 6:
            self.parameters["pattern_height"] = 6
        if max(self.current_diameter[0], self.current_diameter[1]) < 15 and self.parameters["pattern_height"] > 4:
            self.parameters["pattern_height"] = 4
        #reduce number of center points if applicable
        if len(self.parameters["center_points"]) > data["center_points"]:
            self.parameters["center_points"] = self.parameters["center_points"][:data["center_points"]]
        print("Updated parameters: ", self.parameters)
    
    def generate_rectangle(self,displacement):
        points = []
        length = self.current_diameter[0]
        heigth = self.current_diameter[1]

        for k in range(len(self.parameters["center_points"])):
            guide_points = []
            center = self.parameters["center_points"][k]
            guide_points.append(pc.point(center[0]-length/2, center[1] -heigth/2, 0))
            guide_points.append(pc.point(center[0]+length/2, center[1] -heigth/2, 0))
            guide_points.append(pc.point(center[0]+length/2, center[1]+heigth/2, 0))
            guide_points.append(pc.point(center[0]-length/2, center[1]+heigth/2, 0))
            guide_points.append(pc.point(center[0]-length/2, center[1]-heigth/2, 0))

            for i in range(len(guide_points)-1):
                start = guide_points[i]
                end = guide_points[i+1]
                # Calculate the direction vector
                direction = pc.normalize(pc.vector(start, end))
                distance = pc.distance(start, end)
                num_points = int(len(displacement)/4)  # Number of points to generate for the line
                segment_length = distance / num_points
                for j in range(0,num_points):
                    new_point = start + j * segment_length * direction
                    perpendicular = np.array([-direction[1], direction[0], 0])
                    points.append(new_point + (perpendicular * displacement[(i*num_points)+j][1]) + (direction * displacement[(i*num_points)+j][0]))
                    if i == 0 and j == 0:
                        start_ = new_point + (perpendicular * displacement[(i*num_points)+j][1]) + (direction * displacement[(i*num_points)+j][0])
                    
            points.append(start_)
        # Add the last point to close the rectangle
        return points
    
    def generate_circle(self,displacement):
        points = []	
        radius_x = self.current_diameter[0] / 2
        radius_y = self.current_diameter[1] / 2
        num_points = len(displacement)  # Number of points to generate for the circle
        num_centers = len(self.parameters["center_points"])

        for j in range(num_centers):
            center = self.parameters["center_points"][j] 
            start = pc.point(0, 0, 0)
            for i in range(num_points):
                angle = (2 * np.pi * i) / num_points
                #angle = 2 * np.pi * i / num_points
                x = center[0] + radius_x * np.cos(angle)
                y = center[1] + radius_y * np.sin(angle)
                new_point = pc.point(x, y, 0)
                direction = pc.normalize(pc.vector(pc.point(center[0],center[1],0), new_point))
                perpendicular = np.array([-direction[1], direction[0], 0])
                points.append(new_point + (direction * displacement[i][1]) + (perpendicular * displacement[i][0]))
                if i == 0:
                    start = new_point + (direction * displacement[i][1]) + (perpendicular * displacement[i][0])
            points.append(start)    
             
        print("points len: ", len(points))
        return points
    
    def generate_path(self):
         displacement = []
         resolution = 120

         max_diameter = max(self.current_diameter[0], self.current_diameter[1])
         scaling_factor = 0
         if max_diameter < 15:
             scaling_factor = 5
         elif max_diameter < 20:
             scaling_factor = 4
         elif max_diameter < 30:
             scaling_factor = 3
         elif max_diameter < 40:
             scaling_factor = 2
         elif max_diameter < 50:
             scaling_factor = 1
         scaled_spacing = max(int(self.parameters["pattern_spacing"] + scaling_factor),1)

         multiplicator = 1
         for i in range(resolution):
            x = self.parameters["pattern_width"] * 0.5
            y = self.parameters["pattern_height"] * 0.5
            if i % scaled_spacing == 0:
                x = -x
                multiplicator *= -1
            goal = (x,y * multiplicator)

            if len(self.previous_vector) < resolution:
                displacement.append(goal)
                self.previous_vector.append(goal)  
            else:
                vector = pc.normalize(pc.vector(np.array(self.previous_vector[i]),np.array(goal)))#(goal[0] - self.previous_vector[i][0], goal[1] - self.previous_vector[i][1])
                # Multiply the vector by a factor (e.g., 0.1)
                scaled_vector = (vector[0] * 0.5, vector[1] * 0.5)
                new_displacement = (self.previous_vector[i][0] + scaled_vector[0], self.previous_vector[i][1] + scaled_vector[1])
                displacement.append(new_displacement)
                self.previous_vector[i] = new_displacement
            
         #print("displacement: ", displacement)
         return displacement
    
    def generate_next_layer(self,layer):
        # draw the same shape for given number of layers
        if layer % self.parameters["repetitions"] != 0:
            return self.previous_points
        
        points = []
        displacement = self.generate_path()
        # gradually update center points shift
        center = self.parameters["center_points"][0]
        center_distance = pc.distance(center,self.parameters["growth_direction"])
        if center_distance > 0.05:
            print("center_distance: ", center_distance)
            direction = pc.normalize(pc.vector(np.array(center), np.array(self.parameters["growth_direction"])))
            for i in range(len(self.parameters["center_points"])):
                self.parameters["center_points"][i] += (direction * 0.3)
                if i % 2 == 0:
                    direction[0] *= -1
                else:
                    direction[1] *= -1

                
        # gradually update diameter
        diameter_distance = pc.distance(self.current_diameter,self.parameters["diameter"])
        if diameter_distance > 1:
            direction = pc.normalize(pc.vector(np.array(self.current_diameter), np.array(self.parameters["diameter"])))
            self.current_diameter += direction 
            print("current_diameter: ", self.current_diameter)

        if self.parameters["shape"] == "rectangle":
            points = self.generate_rectangle(displacement)
        elif self.parameters["shape"] == "circle":
            points = self.generate_circle(displacement)

        #appply rotation of layer
        if self.parameters["rotation"] > self.current_rotation:
            self.current_rotation += 0.5
            #apply rotation to pattern line
        # Calculate the average x and y coordinates
        center_of_mass_x = sum(point[0] for point in self.parameters["center_points"]) / len(self.parameters["center_points"])
        center_of_mass_y = sum(point[1] for point in self.parameters["center_points"]) / len(self.parameters["center_points"])

        for i in range(len(points)):
            points[i] = pc.rotate(points[i],pc.point(center_of_mass_x,center_of_mass_y,0) , self.current_rotation)
            
        self.previous_points = points
        return points
    
    def generate_infill(self, points, spacing=10, angle=0):
        """
        Generate a simple linear infill for a given outline.
    
        Args:
        points (list): List of points defining the outline.
        spacing (float): Spacing between infill lines.
        angle (float): Angle of the infill lines in degrees (default is 0 for horizontal lines).
    
        Returns:
        list: List of line segments representing the infill.
        """
        # split the points into seperate polygons
        polygon = []
        for i in range(len(points)-1):
            point = points[i]
            point_next = points[i+1]
            distance = pc.distance(point, point_next)
            p = (point[0], point[1])
            polygon.append(p)
            if distance >= 10:  # Example threshold: 10 units
                break
        print("polygon len: ", len(polygon))
        print("points len: ", len(points))
        #print("polygon: ", polygon)

        # Remove duplicate points
        polygon = list(dict.fromkeys(polygon))
        
        # Ensure the polygon is closed
        if polygon[0] != polygon[-1]:
            polygon.append(polygon[0])

        # Create a polygon from the outline points
        outline_polygon = Polygon(polygon)

        # Validate the outline polygon
        if not outline_polygon.is_valid:
            print("Outline polygon is invalid. Attempting to fix...")
            outline_polygon = outline_polygon.buffer(0)
            if not outline_polygon.is_valid:
                print("Failed to fix the outline polygon. Skipping infill generation.")
                return []

        # Get the bounding box of the outline
        min_x, min_y, max_x, max_y = outline_polygon.bounds

        # Generate parallel lines within the bounding box
        infill_lines = []
        y = min_y
        while y <= max_y:
            line = LineString([(min_x, y), (max_x, y)])
            infill_lines.append(line)
            y += spacing

        # Clip the lines to the outline
        clipped_lines = [line.intersection(outline_polygon) for line in infill_lines]

        # Filter out empty or invalid lines
        clipped_lines = [line for line in clipped_lines if not line.is_empty]

        if len(clipped_lines) > 6:
            clipped_lines = clipped_lines[2:-2]  # Limit to 6 lines
        elif len(clipped_lines) > 2:
            clipped_lines = clipped_lines[1:-1]

        # Convert the clipped lines to a list of points
        infill_points = []
        for line in clipped_lines:
            if line.geom_type == 'LineString':
                for coord in line.coords:
                    infill_points.append(coord)
            elif line.geom_type == 'MultiLineString':
                for segment in line.geoms:
                    for coord in segment.coords:
                        infill_points.append(coord)
        print("infill_points len: ", len(infill_points))
        #print("infill_points: ", infill_points)
        return infill_points

    @staticmethod
    def is_inside_ellipse(point, center, radius):
        """
        Check if a point is inside an ellipse.
        """
        x, y = point[0], point[1]
        cx, cy = center[0], center[1]
        rx, ry = radius[0], radius[1]
        # Ellipse equation: ((x - cx)^2 / rx^2) + ((y - cy)^2 / ry^2) <= 1
        return ((x - cx)**2 / rx**2) + ((y - cy)**2 / ry**2) <= 0.99 #add extra tolerance to rounding errors

    @staticmethod
    def sort_points_counterclockwise(points, center):
        """
        Sort points in counterclockwise order around a center.
        """
        cx, cy = center[0], center[1]
        return sorted(points, key=lambda p: np.arctan2(p[1] - cy, p[0] - cx))
    
def find_intersection_angles(center1, radius1, center2, radius2):
    """
    Approximate the intersection angles of two ellipses.
    Returns a list of angles (in radians) where the ellipses intersect.
    """
    intersection_angles = []
    num_samples = 360  # Increase for higher precision
    for angle in np.linspace(0, 2 * np.pi, num_samples):
        # Point on the first ellipse
        x1 = center1[0] + radius1[0] * np.cos(angle)
        y1 = center1[1] + radius1[1] * np.sin(angle)

        # Check if this point is inside the second ellipse
        if ((x1 - center2[0])**2 / radius2[0]**2) + ((y1 - center2[1])**2 / radius2[1]**2) <= 0.9:
            intersection_angles.append(angle)

    return intersection_angles
    
def calculate_visible_ranges(center, radius, other_ellipses):
    """
    Calculate the largest visible angular range of an ellipse.
    """
    visible_ranges = [(0, 2 * np.pi)]  # Start with the full range

    for other_center, other_radius in other_ellipses:
        intersection_angles = find_intersection_angles(center, radius, other_center, other_radius)
        if intersection_angles:
            # Sort the intersection angles
            intersection_angles.sort()

            # Split the current visible ranges based on the intersection angles
            new_ranges = []
            for start, end in visible_ranges:
                for angle in intersection_angles:
                    if start < angle < end:
                        new_ranges.append((start, angle))
                        start = angle
                new_ranges.append((start, end))
            visible_ranges = new_ranges
            # Handle ranges that wrap around 0 radians
    wrapped_ranges = []
    for start, end in visible_ranges:
        if start > end:  # Range wraps around 0
            wrapped_ranges.append((start, 2 * np.pi))  # First part of the range
            wrapped_ranges.append((0, end))  # Second part of the range
        else:
            wrapped_ranges.append((start, end))

    # Find the largest range
    largest_range = max(wrapped_ranges, key=lambda r: (r[1] - r[0]) % (2 * np.pi))

    return [largest_range]  # Return only the largest range
