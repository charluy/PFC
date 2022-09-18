import itertools
import numpy as np
import math

class UE: 

    def __init__(self, UE_group, position, is_dynamic = False, speed = 0, type_of_movement = 'vertical', antenas = 1):
        self.position = position
        self.is_dynamic = is_dynamic
        self.speed = speed
        self.UE_group = UE_group
        self.type_of_movement = type_of_movement
        self.antenas = antenas


    def is_dynamic_UE(self):

        # returns true if the UE is part of the dynamic UEs
        return self.is_dynamic

    def switch_position(self, scene, scenario_column_size, scenario_rows_size):

        # Updates the position a dynamic UE moves to
        if (self.type_of_movement == 'vertical'):
            steps_to_move = math.floor(self.convert_speed_to_steps_per_scene(0.001, 0.01)*scene)*scenario_rows_size
            self.position = scenario_column_size - (self.position + steps_to_move)%scenario_column_size if(self.position + steps_to_move > scenario_column_size) else (self.position + steps_to_move)%scenario_column_size

        if (self.type_of_movement == 'horizontal'):
            steps_to_move = math.floor(self.convert_speed_to_steps_per_scene(0.001, 0.01)*scene)
            self.position = scenario_rows_size - (self.position + steps_to_move)%scenario_rows_size if(self.position + steps_to_move > scenario_rows_size) else (self.position + steps_to_move)%scenario_rows_size
            

    def convert_speed_to_steps_per_scene(self, scene_duration, ue_separation):

        # Returns the steps per scene a dynamic UE moves

        steps_per_scene = self.speed * scene_duration / ue_separation

        return steps_per_scene

    def user_rank(self, channel_matrix, threshold):
        # print("The matrix shape is ")
        # print(channel_matrix.shape)
        average_matrix = np.mean(channel_matrix, axis = 2)
        # print("The average matrix is")
        # print(average_matrix)
        s,v,d = np.linalg.svd(average_matrix)
        # print("The S matrix is")
        # print(s)
        # print("The V Matrix is ")
        # print(v)
        # print("The D matrix is ")
        # print(d)
        max_element = np.max(v)
        # print("The max element is")
        # print(max_element)
        rank = self.matrix_rank(v, max_element, threshold)
        # print("the rank is ")
        # print(rank)
        return rank

    def best_rank(self, channel_matrix, threshold):
        rank = 1
        comb_best_rank = []
        for comb in itertools.combinations(range(channel_matrix.shape[1]), 2):
            rank = self.user_rank(channel_matrix[:, comb, :], threshold) if self.user_rank(channel_matrix[:, comb, :], threshold) > 1 else 1
            comb_best_rank = comb
            if rank > 1:
                break
        
        return rank, comb_best_rank
            

    def matrix_rank(self , v, max_element, threshold):
        rank = 0
        for element in v:
            if element >= max_element/threshold:
                rank = rank + 1
        
        return rank


    def has_at_least_one_prb_with_rank_2(self, ranks):

        has_rank_2 = False

        for i in range(0, len(ranks)):
            has_rank_2 = ranks[i][0] == 2

        return has_rank_2


