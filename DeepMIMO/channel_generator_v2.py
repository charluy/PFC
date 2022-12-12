# Referencias:
#   - https://deepmimo.net/versions/v2-python/
#   - https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html
#   - https://medium.com/@nrk25693/how-to-add-your-conda-environment-to-your-jupyter-notebook-in-just-4-steps-abeab8b8d084

#from DeepMIMO.aux_channel_functions import create_conf_dict
from turtle import position
import DeepMIMO
import pprint
import json
import numpy as np
import os
from aux_functions import create_conf_dict, round_up_sc_to_12_and_8
from UE import UE

# Constants
BW_PRB = 180000
THRESHOLD_RANK = 100

# DeepMIMO scene characteristics
scenario_name = "I2_28B"
is_dynamic = True 
cant_dynamic_ues = 1 # Lets try first with one dynamic user
n_ue_rows = 201
n_ue_columns = 701
center_freq = 28 # In GHz
ue_separation = 0.01

# Simulation parameters
out_dir = "../scenarios/test_bug_fixes/" # Could be another scenario, so the path would be different
bandwidth = 0.05 # In GHz
cant_sc = round_up_sc_to_12_and_8(bandwidth)
TX_power_sc = 6*(10**(-3))  # float(TX_power)/cant_sc
N_0 = abs(10**(-18)) # Noise level
UEgroups = [(0, 1)]
dyn_UE_positions = [{"position": 0, "UEgroup": 0, "type_of_movement": "vertical"}]
cant_scenes = 20
refresh_rate = 0.1 # In seconds
bs = 0

# Load the default parameters
parameters = DeepMIMO.default_params()

# Set scenario name
parameters['scenario'] = scenario_name

# Set the main folder containing extracted scenarios
parameters['dataset_folder'] = "scenarios"
active_bs = [1]  # id for id in range(1,cant_bs+1)
parameters['active_BS'] = np.array(active_bs)

# For OFDM channels, set - Creo que no es necesario.
parameters['activate_OFDM'] = 1

# Bandwidth in GHz
parameters['OFDM']['bandwidth'] = bandwidth

# Cyclic prefix duration of an OFDM symbol, from 0 to 1
parameters['OFDM']['cyclic_prefix_ratio'] = 0.25

# To sample first 512 subcarriers by 1 spacing between each, set
parameters['OFDM']['subcarriers_limit'] = cant_sc
parameters['OFDM']['subcarriers_sampling'] = 1

# Ponemos una antena en TX y una también en RX
parameters['bs_antenna']['shape'] = np.array([1,5,1])
parameters['ue_antenna']['shape'] = np.array([1,2,1])

# Restrict the number of paths to 1
parameters['num_paths'] = 1

# We define the amount of rows to be used in this case being more than 201 because we have more than 2 rows
parameters['user_row_first'] = 1
parameters['user_row_last'] = 10

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
conf_dict = create_conf_dict(center_freq, bandwidth, cant_sc, is_dynamic, refresh_rate*1000, cant_scenes*refresh_rate*1000, UEgroups)

with open(out_dir + "config.json", "w") as outfile:
    json.dump(conf_dict, outfile, indent=4)

# Create PRBs associated to the subcarriers

PRBs = [range(0, cant_sc)[i * 12:(i + 1) * 12] for i in range((cant_sc + 12 - 1) // 12 )]
# print (PRBs)

# Create UEgroups channel information files for each scene

for idUEg, UEg in enumerate(UEgroups):
    UEg_out_dir = out_dir + "UEgroup_" + str(idUEg)
    try:
        os.mkdir(UEg_out_dir)
    except:
        pass
    first_ue = UEg[0]
    last_ue = UEg[1]
    cant_ue = last_ue - first_ue + 1 # Numbers of UE in the UEgroup

    SNR = np.zeros(shape = (cant_ue, len(PRBs)))
    rank = np.ones(shape = (cant_ue, len(PRBs)))
    # print("the shape of the rank is")
    # print(rank.shape)
    DoA = np.zeros(shape = (cant_ue, 2))

    # Create the UEs for each UE group
    UEs = []

    for ue in range(first_ue, last_ue+1):
        user = UE(idUEg, ue)
        user.is_dynamic = True
        user.type_of_movement = 'horizontal'
        user.i_position = ue + 5
        user.speed = 0.22
        UEs.append(user)

    for scene in range(0, cant_scenes):
        print("the scene is "  +  str(scene))

        for ue in UEs:

            # info = np.absolute(dataset[bs]['user']['channel'][ue.position][RX_ant][TX_ant])

            info = np.absolute(dataset[bs]['user']['channel'][ue.position])
            # Plot Channel magnitud response por portadora OFDM:
            # print(info.shape)

            # Save DoA
            DoA[UEs.index(ue)][0] = dataset[bs]['user']['paths'][ue.position]['DoA_phi']
            DoA[UEs.index(ue)][1] = dataset[bs]['user']['paths'][ue.position]['DoA_theta']

            # print ('the shape of the DoA is ')
            # print (DoA[ue.position-first_ue].shape)


            # Estimate SINR in OFDM carrier:

            pot_senal = 0
            for PRB in PRBs:
                rank[UEs.index(ue)][PRBs.index(PRB)], antenna_comb = ue.best_rank(info[:, :, PRB], THRESHOLD_RANK , np.max(parameters['ue_antenna']['shape']))
                # print(f"the antenna comb is {antenna_comb}")
                print(f"the rank is {rank}")
                for subp in PRB:
                    pot_senal += TX_power_sc * (info[0:np.max(parameters['ue_antenna']['shape']), antenna_comb, subp]**2)
                

                SNR[UEs.index(ue)][PRBs.index(PRB)] = 10*np.log10(np.min(np.diagonal(pot_senal))/ (N_0 * BW_PRB))
                print(SNR[UEs.index(ue)][PRBs.index(PRB)])

                # print("\n-------\n")

                if (SNR[UEs.index(ue)][PRBs.index(PRB)] < 0):
                    print(f"la potencia es {pot_senal}")
                    SNR[UEs.index(ue)][PRBs.index(PRB)] = 0.5

                if (SNR[UEs.index(ue)][PRBs.index(PRB)] > 40):
                    print(f"mas que 40 la potencia es {pot_senal}")


            # print("Has rank greater or equal than 2")
            # print(ue.has_at_least_one_prb_with_rank_2(rank[ue.position-first_ue]))

            ue.switch_position(scene + 1, n_ue_columns, n_ue_rows, refresh_rate, ue_separation)

        np.savez(UEg_out_dir + "/Data_" + str(scene), SNR=SNR, rank=rank , DoA=DoA)

    