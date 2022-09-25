# Referencias:
#   - https://deepmimo.net/versions/v2-python/
#   - https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html
#   - https://medium.com/@nrk25693/how-to-add-your-conda-environment-to-your-jupyter-notebook-in-just-4-steps-abeab8b8d084

from turtle import position
import DeepMIMO
import pprint
import json
import numpy as np
import os
from aux_channel_functions import UE



# DeepMIMO scene characteristics
scenario_name = "I2_28B"
is_dynamic = True 
cant_dynamic_ues = 1 # Lets try first with one dynamic user
cant_scenes = 3 # Lets try just two scenes for a first try
cant_bs = 1 # Number of base station in DeepMIMO selected scenario
n_ue_rows = 701
n_ue_columns = 201
center_freq = 28 # In GHz

# Simulation parameters
out_dir = "../scenarios/I2_28B/" # Could be another scenario, so the path would be different
cant_sc = 512
TX_power = (10**(-1))*512
TX_power_sc = float(TX_power)/cant_sc
UEgroups = [(0,9),(100,149)]
dyn_UE_positions = [{"position": 7, "UEgroup": 0, "type_of_movement": "vertical"}, {"position": 110, "UEgroup": 1, "type_of_movement": "horizontal"}]
bandwidth = 0.05 # In GHz

# Load the default parameters
parameters = DeepMIMO.default_params()

# Set scenario name
parameters['scenario'] = scenario_name

# Set the main folder containing extracted scenarios
parameters['dataset_folder'] = "scenarios"
active_bs = [id for id in range(1,cant_bs+1)]
parameters['active_BS'] = np.array(active_bs)

# For OFDM channels, set - Creo que no es necesario.
parameters['activate_OFDM'] = 1

# Bandwidth in GHz
parameters['OFDM']['bandwidth'] = bandwidth

# Cyclic prefix duration of an OFDM symbol, from 0 to 1
parameters['OFDM']['cyclic_prefix_ratio'] = 0.25

# To sample first 512 subcarriers by 1 spacing between each, set
parameters['OFDM']['subcarriers_limit'] = 512
parameters['OFDM']['subcarriers_sampling'] = 1

# Ponemos una antena en TX y una también en RX
parameters['bs_antenna']['shape'] = np.array([1,5,1])
parameters['ue_antenna']['shape'] = np.array([1,2,1])

# We define the amount of rows to be used in this case being more than 201 because we have more than 2 rows
parameters['user_row_first'] = 1
parameters['user_row_last'] = 4

# Dynamic scenarios - Determines the range of dynamic scenario scenes to be loaded
# parameters['dynamic_settings']['first_scene'] = 1
# parameters['dynamic_settings']['last_scene'] = 4

pp = pprint.PrettyPrinter(indent=4)
pp.pprint(parameters)

# Generate data
dataset = DeepMIMO.generate_data(parameters)

# Create output folder
try: #
    os.mkdir(out_dir)
except:
    pass

# Create general configuration file
conf_dict = {
    "frecuency": center_freq, # In GHz
    "bandwidth": int(bandwidth*1000), # In MHz
    "n_sc": cant_sc,
    "is_dynamic": is_dynamic,
    "refresh_rate": 0,
    "sim_duration": 0,
    "n_ueg": len(UEgroups),
    "base_stations":
    [
        {
            "id": 0
        }
    ]
}
with open(out_dir + "config.json", "w") as outfile:
    json.dump(conf_dict, outfile, indent=4)

# Create PRBs associated to the subcarriers

PRBs = [range(0, cant_sc)[i * 12:(i + 1) * 12] for i in range((cant_sc + 12 - 1) // 12 )]
# print (PRBs)

# Create UEgroups channel information files for each scene

for scene in range(0, cant_scenes):
    print("the scene is "  +  str(scene))
    for idUEg, UEg in enumerate(UEgroups):
        UEg_out_dir = out_dir + "UEgroup_" + str(idUEg)
        try:
            os.mkdir(UEg_out_dir)
        except:
            pass
        first_ue = UEg[0]
        last_ue = UEg[1]
        cant_ue = last_ue - first_ue + 1 # Numbers of UE in the UEgroup

        # RX_ant = 0
        # TX_ant = 0
        SNR = np.zeros(shape = (cant_ue, len(PRBs), cant_bs))
        rank = np.zeros(shape = (cant_ue, len(PRBs), cant_bs))
        DoA = np.zeros(shape = (cant_ue, cant_bs, 2))

        # Create the UEs for each UE group
        UEs = []

        for ue in range(first_ue, last_ue):
            user = UE(idUEg, ue)
            UEs.append(user)

        UEs[3].is_dynamic = True
        UEs[3].speed = 5

        for bs in range(0,cant_bs):
            for ue in UEs:

                # info = np.absolute(dataset[bs]['user']['channel'][ue.position][RX_ant][TX_ant])

                info = np.absolute(dataset[bs]['user']['channel'][ue.position])
                # Plot Channel magnitud response por portadora OFDM:
                # print(info.shape)

                # Save DoA
                DoA[ue.position-first_ue][bs][0] = dataset[bs]['user']['paths'][ue.position]['DoA_phi'][0]
                DoA[ue.position-first_ue][bs][1] = dataset[bs]['user']['paths'][ue.position]['DoA_theta'][1]

                print ('the shape of the DoA is ')
                print (DoA[ue.position-first_ue][bs][0].shape)


                # Estimate SINR in OFDM carrier:

                N_0 = abs(10**(-16)*np.random.randn()) # Nivel de ruido 
                B = parameters['OFDM']['bandwidth'] * (10**9) # Ancho de banda del canal OFDM
                pot_senal = 0
                for PRB in PRBs:
                    rank[ue.position-first_ue][PRBs.index(PRB)][bs], antenna_comb = ue.best_rank(info[:, :, PRB], 10)
                    for subp in PRB:
                        pot_senal += TX_power_sc * (info[0:2, antenna_comb, subp]**2)
                        # print(pot_senal.shape)
                    SNR[ue.position-first_ue][PRBs.index(PRB)][bs] = np.min(np.diagonal(pot_senal / (N_0 * B/len(PRBs))))

                print("Has rank greater or equal than 2")
                print(ue.has_at_least_one_prb_with_rank_2(rank[ue.position-first_ue]))

                ue.switch_position(scene + 1, 100000, 201)

                # if ue.is_dynamic:
                #     print ("it is dynamic")
                #     # print ("has a speed of")
                #     # print (ue.speed)
                #     print(ue.position)

        # print("Lets see the info of the SNR obtained")
        # print(SNR.shape)
        # print(SNR)        
        np.savez(UEg_out_dir + "/Data_" + str(scene), SNR, rank, DoA)
        #print(20*np.log(SNR))

        