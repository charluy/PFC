"""
    This is the simulation script for deepMIMO scenarios.
"""

import simpy
from UE import *
from UE import (
    UeGroupDeepMimo
)
from Cell import CellDeepMimo
from Results import *
import json
from utilities import Format

DEEPMIMO_CONFIG_FILE = 'config.json'

#------------------------------------------------------------------------------------------------------
#              Cell & Simulation parameters
#------------------------------------------------------------------------------------------------------

scenario_dir = "scenarios/mateo3/"

deep_mimo_parameters = CellDeepMimo.json_to_dict_config(scenario_dir + DEEPMIMO_CONFIG_FILE)

cant_prbs_base = deep_mimo_parameters.get('cant_prb')

# bandwidth = general_config["bandwidth"]
# center_freq = general_config["frecuency"]
# is_dynamic = general_config["is_dynamic"]
# scene_duration = general_config["refresh_rate"]
# t_sim_file = general_config["sim_duration"]

# t_sim_default = 60000 # (ms)
# t_sim = t_sim_file if is_dynamic else t_sim_default
# """Simulation duration in milliseconds."""

bw = [10] # MHz (FR1: 5, 10, 15, 20, 25, 30, 40, 50, 60, 80, 90, 100; FR2: 50, 100, 200, 400)
"""List containing each CC's bandwidth for the simulation. """
fr = 'FR1' # TODO: FR1 or FR2
"""String with frequency range (FR) to use. 'FR1' for FR1, or 'FR2' for FR2."""
band = 'B1'
"""String with used band for simulation. In TDD mode it is important to set correctly a band from the next list: n257, n258, n260, n261."""
tdd = False
"""Boolean indicating if the cell operates in TDD mode."""
buf = 81920 #10240 #
"""Integer with the maximum Bytes the UE Bearer buffer can tolerate before dropping packets."""
schedulerInter = 'Default'# RRp for improved Round Robin, PFXX for Proportional Fair
"""String indicating the Inter Slice Scheduler to use. For only one Slice simulations use ''.
If the simulation includes more than one slice, set '' for Round Robin, 'RRp' for Round Robin Plus,
or 'PFXY' for Proportional Fair with X=numExp and Y=denExp."""
#                   Simulation parameters

t_sim = 20000 # (ms)
"""Simulation duration in milliseconds."""

debMode = True # to show queues information by TTI during simulation
"""Boolean indicating if debugging mode is active. In that case, an html log file will be generated with schedulers operation.
Note that in simulations with a high number of UEs this file can turn quite heavy."""
measInterv = 1000.0 # interval between meassures
"""Time interval (in milliseconds) between meassures for statistics reports."""
interSliceSchGr = 3000.0 # interSlice scheduler time granularity
"""Inter slice scheduler time granularity in milliseconds."""

#-----------------------------------------------------------------
#              Simulation process activation
#-----------------------------------------------------------------

env = simpy.Environment()
"""Environment instance needed by simpy for runing PEM methods"""

cell1 = CellDeepMimo(
    'c1', bw, fr, debMode, buf, tdd, interSliceSchGr, schedulerInter, cant_prbs_base
)
"""Cell instance for running the simulation"""

interSliceSche1 = cell1.interSliceSched
"""interSliceScheduler instance"""

#           DIFFERENT TRAFFIC PROFILES SETTING

# UEgroup0 = UeGroupDeepMimo(
#     3,0,5000,0,10,0,'eMBB',20,'','MM','MU',4,cell1,t_sim,measInterv,env, scenario_dir+'UEgroup_0', True, scene_duration=8000
# )

UEgroup0 = UeGroupDeepMimo(
    nuDL = 3,
    nuUL = 0,
    pszDL = 5000,
    pszUL = 0,
    parrDL = 10,
    parrUL = 0,
    label = 'eMBB',
    dly = 20,
    avlty = '',
    schedulerType = 'MM',
    mmMd = 'MU',
    lyrs = 4,
    cell = cell1,
    t_sim = t_sim,
    measInterv = measInterv,
    env = env,
    ueg_dir = scenario_dir+'UEgroup_0',
    is_dynamic = True,
    scene_duration = 8000
)


"""Group of users with defined traffic profile, capabilities and service requirements for which the sumulation will run.

More than one can be instantiated in one simulation.
For each one of them, the UEgroup instance must be added in the UEgroups list.

UEgroupN = UEgroup(UEg_dir,nuDL,nuUL,pszDL,pszUL,parrDL,parrUL,label,dly,avlty,schedulerType,mimo_mode,layers,cell,hdr,t_sim,measInterv,env,is_dynamic,scene_duration):

label: must contain substring according to the type of service: eMBB, mMTC, URLLC\n
schedulerType: RR: Rounf Robin, PF: Proportional Fair (10, 11)\n
mimo_mode: SU, MU\n
layers: in SU-MIMO is the number of layers/UE, in MU-MIMO is the number of simultaneous UE to serve with the same resources\n
sinr: is a string starting starting with S if all ues have the same sinr or D if not. The value next will be the initial sinr of each ue or the maximum."""

#UEgroup2 = UEgroup(3,3,800000,300,1,10,'eMBB-1',10,'','RR','',1,cell1,t_sim,measInterv,env,'D37')

# Set UEgroups list according to the defined groups!!!
UEgroups = [UEgroup0]
"""UE group list for the configured simulation"""

#           Slices creation
for ueG in UEgroups:
    interSliceSche1.createSlice(
        ueG.req['reqDelay'],
        ueG.req['reqThroughputDL'],
        ueG.req['reqThroughputUL'],
        ueG.req['reqAvailability'],
        ueG.num_usersDL,
        ueG.num_usersUL,
        band,
        debMode,
        ueG.mmMd,
        ueG.lyrs,
        ueG.label,
        ueG.sch
    )

#      Schedulers activation (inter/intra)

procCell = env.process(cell1.updateStsts(env,interv=measInterv,tSim=t_sim))
procInter = env.process(interSliceSche1.resAlloc(env))
for ueG in UEgroups:
    ueG.activateSliceScheds(interSliceSche1,env)

#----------------------------------------------------------------
env.run(until=t_sim)
#----------------------------------------------------------------

#      Closing statistic and debugging files

for slice in list(cell1.slicesStsts.keys()):
    cell1.slicesStsts[slice]['DL'].close()
    cell1.slicesStsts[slice]['UL'].close()
for slice in list(interSliceSche1.slices.keys()):
        interSliceSche1.slices[slice].schedulerDL.dbFile.close()
        if slice != 'LTE':
            interSliceSche1.slices[slice].schedulerUL.dbFile.close()

#----------------------------------------------------------------
#                          RESULTS
#----------------------------------------------------------------
# Show average PLR and Throughput in any case simulation and plots
for UEg in UEgroups:
    print (Format.CBOLD+Format.CBLUE+'\n--------------------------------------------------'+Format.CEND)
    print (Format.CBOLD+Format.CBLUE+'                 SLICE: '+UEg.label+'                  '+Format.CEND)
    print (Format.CBOLD+Format.CBLUE+'--------------------------------------------------\n'+Format.CEND)
    UEg.printSliceResults(interSliceSche1,t_sim,bw,measInterv)
print (Format.CBOLD+Format.CBLUE+'\n--------------------------------------------------'+Format.CEND)
