import numpy as np


class UE: 

    def __init__(self, UE_group, position, is_dynamic = False, speed = 0, type_of_movement = 'vertical'):
        self.position = position
        self.is_dynamic = is_dynamic
        self.speed = speed
        self.UE_group = UE_group
        self.type_of_movement = type_of_movement


    def is_dynamic_UE(self):

        # returns true if the UE is part of the dynamic UEs
        return self.is_dynamic

    def switch_position(self, scene, scenario_size, scenario_columns_size):

        # Updates the position a dynamic UE moves to

        if (self.type_of_movement == 'vertical'):
            self.position = (self.position + ((self.convert_speed_to_steps_per_scene(self)*scene).astype(int))*scenario_columns_size)%scenario_size

        if (self.type_of_movement == 'horizontal'):
            self.position = (self.position + (self.convert_speed_to_steps_per_scene(self)*scene).astype(int))%scenario_columns_size
            

    def convert_speed_to_steps_per_scene(self, scene_duration, ue_separation):

        # Returns the steps per scene a dynamic UE moves

        steps_per_scene = self.speed * scene_duration / ue_separation

        return steps_per_scene
