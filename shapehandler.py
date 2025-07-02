# -*- coding: utf-8 -*-
"""
Name: Shape Handler
Description: is responsible to deal with the creation and adaption of the shapes
"""

# import custom classes
import point_calc as pc
import numpy as np
import random
from shapely.geometry import Polygon, LineString
LINE_CONST = 8

class Shapehandler:
    def __init__(self):
        self.current_rotation = 0
        self.current_diameter = []
        self.previous_vector = [] #for line pattern transition
        self.previous_z_vector = [] #for non planar print
        self.previous_shapes = [] #for layer repeat
        self.current_layer = 0 
        self.infill_cache = {}  # key: index, value: {'polygon': polygon, 'infill': infill_points}
        self.irregularity_vector = []
        self.shape_options = { 
            "transition_rate":1,
            "base_shape": "circle",
            "diameter": [],
            "rotation": 0,
            "center_points": [],
            "growth_directions": [],
            "repetitions": 1,
            "free_hand_form":[],
        }
        self.line_options = {
            "pattern_range": 60,
            "pattern_start":50,
            "transition_rate":0.5,
            "pattern": "rect",
            "amplitude": 1,
            "frequency":1,
            "resolution":240,
            "irregularity":0,
            "glitch":"none",
        }
        self.z_plane = {
            "frequency": 20,
            "amplitude": 10,
            "non_planar": "no",
        }

    def remove_center_point(self, index, layer):
        if layer > 0:
            del self.shape_options["center_points"][index]
            del self.shape_options["growth_directions"][index]
            del self.shape_options["diameter"][index]
            del self.current_diameter[index]
             # Remove the infill at the deleted index
            if index in self.infill_cache:
                del self.infill_cache[index]
            # Shift all higher infill_cache keys down by one
            new_cache = {}
            for k, v in self.infill_cache.items():
                if k > index:
                    new_cache[k - 1] = v
                elif k < index:
                    new_cache[k] = v
            self.infill_cache = new_cache

    def update_parameters(self, shape_parameters, line_parameters, z_plane, layer):
        self.shape_options["base_shape"] = shape_parameters["base_shape"]
        self.shape_options["diameter"] = shape_parameters["diameter"]
        self.shape_options["rotation"] = shape_parameters["rotation"]
        self.shape_options["growth_directions"] = shape_parameters["growth_directions"]
        self.shape_options["transition_rate"] = shape_parameters["transition_rate"]
        self.shape_options["free_hand_form"] = shape_parameters["free_hand_form"]

        self.z_plane = z_plane

        self.line_options["pattern"] = line_parameters["pattern"]
        self.line_options["amplitude"] = line_parameters["amplitude"]
        self.line_options["frequency"] = line_parameters["frequency"]
        self.line_options["transition_rate"] = line_parameters["transition_rate"]
        self.line_options["pattern_range"] = line_parameters["pattern_range"]
        self.line_options["pattern_start"] = line_parameters["pattern_start"]
        self.line_options["glitch"] = line_parameters["glitch"]
        #regenerate random irregularity of line only when irregularity parameter changes
        if self.line_options["irregularity"] != line_parameters["irregularity"] or self.irregularity_vector == []:
            self.line_options["irregularity"] = line_parameters["irregularity"]
            sparsity = 0.7  # 80% zeros
            small_noise_chance = 0.15  # 15% small noise
            new_irregularity = []
            i = 0
            while i < self.line_options["resolution"]:
                random_steps = int(random.uniform(2,12))
                random_irregularity = random.random()
                for j in range(random_steps):
                    new_irregularity.append(random_irregularity)
                    i+=1
            self.irregularity_vector = new_irregularity

        
        #initialize the current diameter only at the very beginning
        #initialize center points 
        if layer == 0:
            self.shape_options["center_points"] = shape_parameters["center_points"]
            self.current_diameter = shape_parameters["diameter"]
        print("Updated shape_options: ", self.shape_options)
        print("Updated line_options: ", self.line_options)
    
    def generate_rectangle(self,displacement, cx, cy, dx, dy):
        points = []
        length = dx
        heigth = dy
        corners = [
        pc.point(cx-length/2, cy-heigth/2, 0),
        pc.point(cx+length/2, cy-heigth/2, 0),
        pc.point(cx+length/2, cy+heigth/2, 0),
        pc.point(cx-length/2, cy+heigth/2, 0)
        ]
        guide_points = corners 
        guide_points.append(corners[0])
        glitch_prob = random.random()
        glitch_pos_j = int(random.uniform(0,int(len(displacement)/4)))
        glitch_pos_i = int(random.uniform(0,len(guide_points)-1))

        for i in range(len(guide_points)-1):
            start = guide_points[i]
            end = guide_points[i+1]
                # Calculate the direction vector
            direction = pc.normalize(pc.vector(start, end))
            perpendicular = np.array([-direction[1], direction[0], 0])
            distance = pc.distance(start, end)
            num_points = int(len(displacement)/4)  # Number of points to generate for the line
            segment_length = distance / num_points
            new_point = start
            for j in range(0,num_points):
                jdx = (i*num_points) + j
                new_point = start + j * segment_length * direction  # Point along the outline
                patterned_point = (
                    new_point
                    + direction * displacement[jdx][0]      # Tangential offset
                    + perpendicular * displacement[jdx][1]  # Normal offset
                    )
                points.append(patterned_point)
                #insert glitch if appropriate
                if self.line_options["glitch"] == "mesh" and glitch_prob > 0.7 and j== glitch_pos_j and i== glitch_pos_i:
                    points.append(new_point + perpendicular*-10)
                    points.append(new_point + perpendicular*-10 + direction*5)

                    
        points.append(points[0])  # Close the rectangle by adding the first point again
        if len(points) > 4: #retrace the begining of the shape twice for better closure
            points.append(points[1])
            points.append(points[2])
        return points
    
    def generate_circle(self,displacement, cx,cy,dx,dy):
        points = []	
        radius_x = dx / 2
        radius_y = dy / 2
        num_points = len(displacement)  # Number of points to generate for the circle
        glitch_prob = random.random()
        glitch_pos_i = int(random.uniform(0,num_points))
        for i in range(num_points):
            angle = np.pi*2- ((2 * np.pi * i) / num_points)
            #angle = 2 * np.pi * i / num_points
            x = cx + radius_x * np.cos(angle)
            y = cy + radius_y * np.sin(angle)
            new_point = pc.point(x, y, 0)
            direction = pc.normalize(pc.vector(pc.point(cx,cy,0), new_point))
            perpendicular = np.array([-direction[1], direction[0], 0])
            points.append(new_point + (direction * displacement[i][1]) + (perpendicular * displacement[i][0]))
            #insert glitch if appropriate
            if self.line_options["glitch"] == "mesh" and glitch_prob > 0.7 and i== glitch_pos_i:
                points.append(new_point + direction*10)
                points.append(new_point + direction*10 + perpendicular*5)
           
        points.append(points[0])  # Close the circle by adding the first point again
        if len(points) > 4: #retrace the begining of the shape twice for better closure
            points.append(points[1])
            points.append(points[2])
        return points
    
    def generate_triangle(self, displacement, cx, cy,dx,dy):
        points = []
        # Define the vertices of the triangle
        vertices = [
            pc.point(cx, cy + dy / 2, 0),  # Top vertex
            pc.point(cx - dx / 2, cy - dx/ 2, 0),  # Bottom left vertex
            pc.point(cx + dx / 2, cy - dy / 2, 0)   # Bottom right vertex
        ]
        guide_points = vertices#ordered_vertices
        guide_points.append(vertices[0])
        glitch_prob = random.random()
        glitch_pos_j = int(random.uniform(0,int(len(displacement)/4)))
        glitch_pos_i = int(random.uniform(0,len(guide_points)-1))
        for i in range(len(guide_points)-1):
            start = guide_points[i]
            end = guide_points[i+1]
                # Calculate the direction vector
            direction = pc.normalize(pc.vector(start, end))
            distance = pc.distance(start, end)
            num_points = int(len(displacement)/3)  # Number of points to generate for the line
            segment_length = distance / num_points
            new_point = start
            for j in range(0,num_points):
                new_point = start + j * segment_length * direction
                perpendicular = np.array([-direction[1], direction[0], 0])
                points.append(new_point + (perpendicular * displacement[(i*num_points)+j][1]) + (direction * displacement[(i*num_points)+j][0]))
                #insert glitch if appropriate
                if self.line_options["glitch"] == "mesh" and glitch_prob > 0.7 and j== glitch_pos_j and i== glitch_pos_i:
                    points.append(new_point + perpendicular*-10)
                    points.append(new_point + perpendicular*-10 + direction*5)
                    
        points.append(points[0])  # Close the rectangle by adding the first point again
        if len(points) > 4: #retrace the begining of the shape twice for better closure
            points.append(points[1])
            points.append(points[2])
        # Add the last point to close the rectangle
        return points
    
    def generate_freeform(self,displacement,cx,cy,dx,dy):
        points = []
        vertecies = []
        if len(self.shape_options["free_hand_form"]) <= 1:
            return []
        for i in range(len(self.shape_options["free_hand_form"])):
            vertecies.append(pc.point(self.shape_options["free_hand_form"][i][0]*dx + cx,-self.shape_options["free_hand_form"][i][1]*dy + cy,0)) 
        
        glitch_prob = random.random()
        glitch_pos_j = int(random.uniform(0,int(len(displacement)/4)))
        glitch_pos_i = int(random.uniform(0,len(vertecies)-1))
        for i in range(len(vertecies)-1):
            start = vertecies[i]
            end = vertecies[i+1]
                # Calculate the direction vector
            direction = pc.normalize(pc.vector(start, end))
            distance = pc.distance(start, end)
            num_points = int(len(displacement)/(len(vertecies)-1))  # Number of points to generate for the line
            segment_length = distance / num_points
            new_point = start
            for j in range(0,num_points):
                new_point = start + j * segment_length * direction
                perpendicular = np.array([-direction[1], direction[0], 0])
                points.append(new_point + (perpendicular * displacement[(i*num_points)+j][1]) + (direction * displacement[(i*num_points)+j][0]))
                #insert glitch if appropriate
                if self.line_options["glitch"] == "mesh" and glitch_prob > 0.7 and j== glitch_pos_j and i== glitch_pos_i:
                    points.append(new_point + perpendicular*10)
                    points.append(new_point + perpendicular*10 + direction*5)
                    
        points.append(points[0])  # Close the rectangle by adding the first point again
        if len(points) > 4: #retrace the begining of the shape twice for better closure
            points.append(points[1])
            points.append(points[2])

        return points
    
    def generate_loop(self,num_points, height):
        points = []
        for i in range(num_points):
            angle =  2*np.pi - ((2 * np.pi * i) / num_points)
            x = height* np.cos(angle)
            y = height* np.sin(angle)
            points.append([x,y])
        return points
    def generate_stairs(self,num_points, height):
        points = []
        corner_points = [[-1,-height/2],[0,-height/2],[0,-height/2],[0,-height/2],[-1,height/2],[0,height/2],[0,height/2],[0,height/2]]
        gidx = -1
        for i in range(num_points):
            if i % (num_points/LINE_CONST) == 0:
                gidx = gidx + 1
            points.append(corner_points[gidx])
        return points
    def generate_zigzag(self,num_points,height):
        points = []
        half = num_points/2
        for i in range(num_points):
            if i < half:
                points.append([0,-height/2 + height *((i+1)*(1/half))])
            else:
                points.append([0,height/2 - height *((i+1-half)*(1/half))])
        return points
    def generate_wave(self,num_points,height):
        points = []
        for i in range(num_points):
            angle =  (2 * np.pi * i) / num_points
            x = 0
            y = height* np.sin(angle)
            points.append([x,y])
        return points
    def generate_nobs(self,num_points,height):
        points = []
        index = 0
        if self.current_layer%2 == 0:
            index = int(num_points/2)
        for i in range(num_points):
            if i == index:
                if self.shape_options["base_shape"] == "circle" or self.shape_options["base_shape"] == "freehand":
                    points.append([-1,height])
                else:
                    points.append([-1,-height])
            else:
                points.append([0,0])
        return points
    
    def generate_path(self):
         displacement = []
         resolution = self.line_options["resolution"]
         h = self.line_options["amplitude"]
         pattern = self.line_options["pattern"]
         aplication_range = self.map_parameter_to_range(self.line_options["pattern_range"],0,resolution,0,100)
         pattern_start = self.map_parameter_to_range(self.line_options["pattern_start"],0,resolution-1,1,100)
         guides = []
         for i in range(resolution):
            idx = i
            bundle_size = LINE_CONST*self.line_options["frequency"]
            if i%bundle_size == 0:
                if pattern == "circ":
                    guides = self.generate_loop(bundle_size,h/2)
                if pattern == "rect":
                    guides = self.generate_stairs(bundle_size,h)
                if pattern == "tri":
                    guides = self.generate_zigzag(bundle_size,h)
                if pattern == "wav":
                    guides = self.generate_wave(bundle_size,h)
                if pattern == "nobs":
                    guides = self.generate_nobs(bundle_size,h)
            goal = (0,0)
            if pattern == "str":
                goal = (0,0)
            elif (i >= pattern_start and i < (pattern_start + aplication_range)) or (i < (aplication_range-(resolution - pattern_start))):
                x = guides[i%bundle_size][0] 
                y = guides[i%bundle_size][1] 
                irregularity = self.line_options["irregularity"] * (self.irregularity_vector[i] * self.line_options["amplitude"])
                if self.shape_options["base_shape"] == "circle" or self.shape_options["base_shape"] == "freehand":
                    irregularity *= -1
                goal = (x,y + irregularity)

            if len(self.previous_vector) < resolution:
                displacement.append(goal)
                self.previous_vector.append(goal)
            elif pattern == "nobs":
                displacement.append(goal) 
            else:
                vector = pc.normalize(pc.vector(np.array(self.previous_vector[idx]),np.array(goal)))#(goal[0] - self.previous_vector[i][0], goal[1] - self.previous_vector[i][1])
                # Multiply the vector by a factor (e.g., 0.1)
                scaled_vector = (vector[0] * self.line_options["transition_rate"], vector[1] * self.line_options["transition_rate"])
                new_displacement = (self.previous_vector[idx][0] + scaled_vector[0], self.previous_vector[idx][1] + scaled_vector[1])
                x, y = new_displacement
                if abs(x) < self.line_options["transition_rate"]/2:
                    x = 0
                if abs(y) < self.line_options["transition_rate"]/2:
                    y = 0
                new_displacement = (x, y)
                displacement.append(new_displacement)
                self.previous_vector[idx] = new_displacement
         return displacement
    
    def generate_next_layer(self,layer):
        # draw the same shape for given number of layers (layer reptition)
        self.current_layer = layer
        if layer % self.shape_options["repetitions"] != 0:
            return self.previous_shapes
        
        shapes = []
        displacement = self.generate_path() #distortion of outline depending on line pattern
        
        # gradually update center points shift
        for i in range(len(self.shape_options["center_points"])):
            center = self.shape_options["center_points"][i]
            center_distance = pc.distance(center,self.shape_options["growth_directions"][i])
            if center_distance > 0.05:
                direction = pc.normalize(pc.vector(np.array(center), np.array(self.shape_options["growth_directions"][i])))
                self.shape_options["center_points"][i] += (direction * 0.4)
                
        # gradually update diameters
        for i in range(len(self.shape_options["diameter"])):
            diameter_distance = pc.distance(self.current_diameter[i],self.shape_options["diameter"][i])
            if diameter_distance > 1:
                direction = pc.normalize(pc.vector(np.array(self.current_diameter[i]), np.array(self.shape_options["diameter"][i])))
                self.current_diameter[i] += (direction * self.shape_options["transition_rate"]) 

        #generate points of the outlines for each center point
        for i in range(len(self.shape_options["center_points"])):
            center = self.shape_options["center_points"][i]
            cx = center[0]
            cy = center[1]
            points = []
            if self.shape_options["base_shape"] == "rectangle":
                points = self.generate_rectangle(displacement, cx, cy,self.current_diameter[i][0],self.current_diameter[i][1])
            elif self.shape_options["base_shape"] == "circle":
                points = self.generate_circle(displacement, cx, cy,self.current_diameter[i][0],self.current_diameter[i][1])
            elif self.shape_options["base_shape"] == "triangle":
                points = self.generate_triangle(displacement, cx, cy,self.current_diameter[i][0],self.current_diameter[i][1])
            elif self.shape_options["base_shape"] == "freehand":
                points = self.generate_freeform(displacement,cx,cy,self.current_diameter[i][0],self.current_diameter[i][1])
            shapes.append(points)

        #apply layer rotation
        self.current_rotation += self.shape_options["rotation"]
        #center_of_mass_x = sum(point[0] for point in self.shape_options["center_points"]) / len(self.shape_options["center_points"])
        #center_of_mass_y = sum(point[1] for point in self.shape_options["center_points"]) / len(self.shape_options["center_points"])
        for i in range(len(shapes)):
            points = shapes[i]
            z_displacement = self.generate_z_displacement()
            for j in range(len(points)):
                points[j] = pc.rotate(points[j],pc.point(self.shape_options["center_points"][i][0],self.shape_options["center_points"][i][1],0) , self.current_rotation)
                points[j][2] = z_displacement[j%len(z_displacement)]
            
        self.previous_shapes = shapes
        return shapes
    
    def generate_infill(self, spacing=10, angle=0, clip_start=0, clip_end=0, index=None):
        polygon = []
        
        cx = self.shape_options["center_points"][index][0]
        cy = self.shape_options["center_points"][index][1]
        displacement= [(0, 0)] * self.line_options["resolution"]
        if self.shape_options["base_shape"] == "rectangle":
                polygon = self.generate_rectangle(displacement, cx, cy,self.current_diameter[index][0], self.current_diameter[index][1])
        elif self.shape_options["base_shape"] == "circle":
                polygon = self.generate_circle(displacement, cx, cy,self.current_diameter[index][0], self.current_diameter[index][1])
        elif self.shape_options["base_shape"] == "triangle":
                polygon = self.generate_triangle(displacement, cx, cy,self.current_diameter[index][0], self.current_diameter[index][1])
        elif self.shape_options["base_shape"] == "freehand":
                polygon = self.generate_freeform(displacement, cx, cy,self.current_diameter[index][0], self.current_diameter[index][1])
        for j in range(len(polygon)):
                polygon[j] = pc.rotate(polygon[j],pc.point(cx,cy,0) , self.current_rotation)
        polygon = [tuple(p) for p in polygon]
        polygon = list(dict.fromkeys(polygon))
        if polygon[0] != polygon[-1]:
            polygon.append(polygon[0])

        cache_key = index if index is not None else 'default'
        cached = self.infill_cache.get(cache_key)
        if cached:
            old_polygon = cached['polygon']
            old_infill = cached['infill']
            # If the polygon has changed, transform the infill
            if old_polygon != polygon:
                # Compute affine transform from old_polygon to new polygon
                matrix = self.compute_affine_transform(old_polygon, polygon)
                adjusted_infill = self.apply_affine_transform(old_infill, matrix)
                self.infill_cache[cache_key] = {'polygon': polygon, 'infill': adjusted_infill}
                if clip_end > 0:
                    if len(adjusted_infill) > (clip_start + clip_end):
                        return adjusted_infill[clip_start:-clip_end]
                    else:
                        return []
                else:
                    if len(adjusted_infill) > clip_start:
                        return adjusted_infill[clip_start:]
                    else:
                        return []
            else:
                if clip_end > 0:
                    if len(old_infill) > (clip_start + clip_end):
                        return old_infill[clip_start:-clip_end]
                    else:
                        return []
                else:
                    if len(old_infill) > clip_start:
                        return old_infill[clip_start:]
                    else:
                        return []

        # ... your existing infill generation code ...
        outline_polygon = Polygon(polygon)
        if not outline_polygon.is_valid:
            outline_polygon = outline_polygon.buffer(0)
            if not outline_polygon.is_valid:
                print("Failed to fix the outline polygon. Skipping infill generation.")
                return []

        min_x, min_y, max_x, max_y = outline_polygon.bounds
        infill_lines = []
        y = min_y
        while y <= max_y:
            line = LineString([(min_x, y), (max_x, y)])
            infill_lines.append(line)
            y += spacing

        clipped_lines = [line.intersection(outline_polygon) for line in infill_lines]
        clipped_lines = [line for line in clipped_lines if not line.is_empty]

        infill_points = []
        for line in clipped_lines:
            if line.geom_type == 'LineString':
                coords = list(line.coords)
                if len(coords) >= 2:
                    # Only use endpoints
                    infill_points.append(np.array(coords[0]))
                    infill_points.append(np.array(coords[-1]))
            elif line.geom_type == 'MultiLineString':
                # For MultiLineString, treat all segments as one line by flattening their coordinates
                all_coords = []
                for segment in line.geoms:
                    all_coords.extend(segment.coords)
                if len(all_coords) >= 2:
                    infill_points.append(np.array(all_coords[0]))
                    infill_points.append(np.array(all_coords[-1]))

        self.infill_cache[cache_key] = {'polygon': polygon, 'infill': infill_points}
        if clip_end > 0:
            if len(infill_points) > (clip_start + clip_end):
                return infill_points[clip_start:-clip_end]
            else:
                return []
        else:
            if len(infill_points) > clip_start:
                return infill_points[clip_start:]
            else:
                return []
            
    def z_wave(self,num_points,h):
        # Half points for up, half for down (handle odd/even)
        up_count = num_points // 2
        down_count = num_points - up_count
        up = np.linspace(0, 1, up_count, endpoint=False)
        down = np.linspace(1, 0, down_count)
        points = np.concatenate([up, down])
        # Scale by h if needed
        points = h * points
        return points.tolist()
            
    def generate_z_displacement(self):
        displacement = []
        resolution = self.line_options["resolution"]
        # Calculate bundle_size as the largest divisor of resolution <= LINE_CONST * self.z_plane["frequency"]
        target_bundle = LINE_CONST * self.z_plane["frequency"]
        bundle_size =  max([d for d in range(1, resolution + 1) if resolution % d == 0 and d <= target_bundle])
        guides = []
        for i in range(resolution):
            if i % bundle_size == 0:
                h = self.z_plane["amplitude"]
                if self.current_layer < 2:
                    h = 0
                guides = self.z_wave(bundle_size, h)
            if self.z_plane["non_planar"] == "yes":
                goal = guides[i % bundle_size]
            else:
                goal = 0

            # Smooth transition towards goal, similar to generate_path
            if len(self.previous_z_vector) < resolution:
                new_z = goal
                self.previous_z_vector.append(new_z)
            else:
                prev_z = self.previous_z_vector[i]
                # Move a fraction towards the goal (smoothing factor)
                delta = goal - prev_z
                step = self.line_options["transition_rate"] * delta
                # Cap the step size for smoother initial movement
                if abs(step) > 0.5:
                    step = np.sign(step) * 0.5
                if abs(step) < self.line_options["transition_rate"] / 25:
                    step = 0
                new_z = prev_z + step
                # Optional: snap to zero if very close
                if abs(new_z) < self.line_options["transition_rate"]:
                    new_z = 0
                self.previous_z_vector[i] = new_z
            displacement.append(new_z)
        return displacement
    
#functions to draw realistic UI preview 

    def simulate_line_pattern(self):
         displacement = []
         resolution = self.line_options["resolution"]
         h = self.line_options["amplitude"]
         pattern = self.line_options["pattern"]
         aplication_range = self.map_parameter_to_range(self.line_options["pattern_range"],0,resolution,0,100)
         pattern_start = self.map_parameter_to_range(self.line_options["pattern_start"],0,resolution-1,1,100)
         guides = []
         for i in range(resolution):
            bundle_size = LINE_CONST*self.line_options["frequency"]
            if i%bundle_size == 0:
                if pattern == "circ":
                    guides = self.generate_loop(bundle_size,h/2)
                if pattern == "rect":
                    guides = self.generate_stairs(bundle_size,h)
                if pattern == "tri":
                    guides = self.generate_zigzag(bundle_size,h)
                if pattern == "wav":
                    guides = self.generate_wave(bundle_size,h)
                if pattern == "nobs":
                    guides = self.generate_nobs(bundle_size,h)
            goal = (0,0)
            if pattern == "str":
                goal = (0,0)
            elif (i >= pattern_start and i < (pattern_start + aplication_range)) or (i < (aplication_range-(resolution - pattern_start))):
                x = guides[i%bundle_size][0] 
                y = guides[i%bundle_size][1] 
                irregularity = self.line_options["irregularity"] * (self.irregularity_vector[i] * self.line_options["amplitude"])
                goal = (x,y + irregularity)

            displacement.append(goal)
         return displacement
    
    def simulate_z_displacement(self):
        displacement = []
        resolution = self.line_options["resolution"]
        # Calculate bundle_size as the largest divisor of resolution <= LINE_CONST * self.z_plane["frequency"]
        target_bundle = LINE_CONST * self.z_plane["frequency"]
        bundle_size =  max([d for d in range(1, resolution + 1) if resolution % d == 0 and d <= target_bundle])
        guides = []
        for i in range(resolution):
            if i % bundle_size == 0:
                guides = self.z_wave(bundle_size, self.z_plane["amplitude"])
            if self.z_plane["non_planar"] == "yes":
                goal = guides[i % bundle_size]
            else:
                goal = 0
            displacement.append(goal)
        return displacement
    
    def simulate_infill(self, spacing=10, clip_start = 0, clip_end = 0):
        inflill = []
        points = self.generate_next_layer(layer=0)[0]
        print("points len ", len(points))
        inflill = self.generate_infill(spacing = spacing, clip_end=clip_end, clip_start=clip_start,polygon=points)
        #todo reset to initial state?

        return inflill
    
#helper functions

    @staticmethod
    def map_parameter_to_range(value, min_value, max_value, input_min, input_max):
        """
        Maps a value from one range to another.
        """
        # Ensure the input range is valid
        if input_min >= input_max:
            raise ValueError("Input min must be less than input max")
        
        # Ensure the output range is valid
        if min_value >= max_value:
            raise ValueError("Output min must be less than output max")
        
        # Normalize the value to a 0-1 range based on the input range
        normalized_value = (value - input_min) / (input_max - input_min)
        
        # Map the normalized value to the output range
        mapped_value = min_value + normalized_value * (max_value - min_value)
        
        return mapped_value
    @staticmethod
    def compute_affine_transform(src, dst):
        """
        Compute 3D affine transform (rotation, scale, translation) from src to dst.
        src and dst are (N, 3) arrays of 3D points.
        Returns a 4x4 transformation matrix.
        """
        src = np.array(src)
        dst = np.array(dst)

        if src.shape[1] != 3 or dst.shape[1] != 3:
            raise ValueError("Expected 3D points (x, y, z)")

        # Pad with ones for affine computation
        src_pad = np.hstack([src, np.ones((len(src), 1))])  # (N, 4)
        # Solve for transformation: src_pad @ matrix ≈ dst
        matrix, _, _, _ = np.linalg.lstsq(src_pad, dst, rcond=None)  # matrix: (4, 3)

        # Convert to a full 4x4 affine transformation matrix
        full_matrix = np.eye(4)
        full_matrix[:3, :] = matrix.T  # (3, 4)

        return full_matrix

       
    @staticmethod
    def apply_affine_transform(points, matrix):
        """
        Apply a 4x4 affine transformation matrix to a list of (x, y, z) points.
        """
        pts = np.array(points)
        if pts.shape[1] != 3:
            raise ValueError("Expected 3D points (x, y, z)")

        if matrix.shape != (4, 4):
            raise ValueError(f"Expected 4x4 transformation matrix, got {matrix.shape}")

        # Add 1s for homogeneous coordinates
        pts_pad = np.hstack([pts, np.ones((len(pts), 1))])  # (N, 4)
        transformed = pts_pad @ matrix.T  # (N, 4)

        return transformed[:, :3]  # Drop the homogeneous coordinate



