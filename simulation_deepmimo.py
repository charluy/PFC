"""
    This is the simulation script for deepMIMO scenarios.
"""

import simpy
from UE import *
from UE import UeGroupDeepMimo
from Cell import CellDeepMimo
from Results import *
from utilities import Format

DEEPMIMO_CONFIG_FILE = 'config.json'

#------------------------------------------------------------------------------------------------------
#              Cell & Simulation parameters
#------------------------------------------------------------------------------------------------------

scenario_dir = "scenarios/mateo3/"

deep_mimo_parameters = CellDeepMimo.json_to_dict_config(scenario_dir + DEEPMIMO_CONFIG_FILE)

cant_prbs_base = deep_mimo_parameters.get('cant_prb') ###
frequency_range = deep_mimo_parameters.get('frecuency_range') ###
bandwidth = deep_mimo_parameters.get('bandwidth') ###
is_dynamic = deep_mimo_parameters.get('is_dynamic')
scene_duration = deep_mimo_parameters.get('refresh_rate') # 
simulation_duration = deep_mimo_parameters.get('sim_duration') ###


band = 'B1'
"""String with used band for simulation. In TDD mode it is important to set correctly a band from the next list: n257, n258, n260, n261."""

tdd = False
"""Boolean indicating if the cell operates in TDD mode."""

buf = 81920
"""Integer with the maximum Bytes the UE Bearer buffer can tolerate before dropping packets."""

schedulerInter = 'Default'
"""String indicating the Inter Slice Scheduler to use."""

debMode = True # to show queues information by TTI during simulation
"""Boolean indicating if debugging mode is active. In that case, an html log file will be generated with schedulers operation.
Note that in simulations with a high number of UEs this file can turn quite heavy."""

measInterv = 100.0 # interval between meassures
"""Time interval (in milliseconds) between meassures for statistics reports."""

interSliceSchGr = 3000.0 # interSlice scheduler time granularity
"""Inter slice scheduler time granularity in milliseconds."""

#-----------------------------------------------------------------
#              Simulation process activation
#-----------------------------------------------------------------

env = simpy.Environment()
"""Environment instance needed by simpy for runing PEM methods"""

cell1 = CellDeepMimo(
    cell_id = 'c1',
    bandwidth = bandwidth,
    frequency_range = frequency_range,
    debug_mode = debMode,
    bearer_buffer_size = buf,
    tdd = tdd,
    granularity = interSliceSchGr,
    schInter = schedulerInter,
    cant_prbs_base = cant_prbs_base
)
"""Cell instance for running the simulation"""

interSliceSche1 = cell1.interSliceSched
"""interSliceScheduler instance"""

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
    schedulerType = 'NUM',
    mmMd = 'MU',
    lyrs = 4,
    cell = cell1,
    t_sim = simulation_duration,
    measInterv = measInterv,
    env = env,
    ueg_dir = scenario_dir + 'UEgroup_0',
    is_dynamic = is_dynamic,
    scene_duration = 8000
)
"""Group of users with defined traffic profile for which the sumulation will run."""

UEgroups = [UEgroup0]
"""UE group list for the configured simulation"""

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

procCell = env.process(cell1.updateStsts(env,interv=measInterv,tSim=simulation_duration))
procInter = env.process(interSliceSche1.resAlloc(env))
for ueG in UEgroups:
    ueG.activateSliceScheds(interSliceSche1,env)

#----------------------------------------------------------------
env.run(until=simulation_duration)
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
    UEg.printSliceResults(interSliceSche1,simulation_duration,[bandwidth],measInterv)
print (Format.CBOLD+Format.CBLUE+'\n--------------------------------------------------'+Format.CEND)
