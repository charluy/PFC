# Referencias:
#   - https://deepmimo.net/versions/v2-python/
#   - https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html
#   - https://medium.com/@nrk25693/how-to-add-your-conda-environment-to-your-jupyter-notebook-in-just-4-steps-abeab8b8d084

import DeepMIMO
import pprint
import json
import numpy as np
import os

# DeepMIMO scene characteristics
scenario_name = "I2_28B"
is_dynamic = False
cant_bs = 1 # Number of base station in DeepMIMO selected scenario
n_ue_rows = 701
n_ue_columns = 201
center_freq = 28 # In GHz

# Simulation parameters
out_dir = "../scenarios/I2_28B/"
cant_sc = 512
TX_power = (10**(-1))*512
TX_power_sc = float(TX_power)/cant_sc
UEgroups = [(0,9),(100,149)]
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
parameters['bs_antenna']['shape'] = np.array([1,1,1])
parameters['ue_antenna']['shape'] = np.array([1,1,1])

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

# Create UEgroups channel information files
for idUEg, UEg in enumerate(UEgroups):
    UEg_out_dir = out_dir + "UEgroup_" + str(idUEg)
    try:
        os.mkdir(UEg_out_dir)
    except:
        pass
    first_ue = UEg[0]
    last_ue = UEg[1]
    cant_ue = last_ue - first_ue + 1 # Numbers of UE in the UEgroup

    RX_ant = 0
    TX_ant = 0
    SNR = np.zeros(shape = (cant_ue, cant_bs))
    for bs in range(0,cant_bs):
        for ue in range(first_ue, last_ue+1):

            # List containing channel magnitude response in each OFDM sub-carrier:
            info = np.absolute(dataset[bs]['user']['channel'][ue][RX_ant][TX_ant])

            # Plot Channel magnitud response por portadora OFDM:
            # print(info.shape)

            # Estimate SINR in OFDM carrier:

            N_0 = abs(10**(-16)*np.random.randn()) # Nivel de ruido 
            B = parameters['OFDM']['bandwidth'] * (10**9) # Ancho de banda del canal OFDM
            pot_senal = 0
            for subp in range(0,512):
                pot_senal += TX_power_sc * (info[subp]**2)
            SNR[ue-first_ue][bs] = pot_senal / (N_0 * B)
            
    np.save(UEg_out_dir + "/SNR_0", SNR)
    #print(20*np.log(SNR))
