from Cell import CellDeepMimo

DEEPMIMO_CONFIG_FILE = 'config.json'


scenario_dir = "scenarios/mateo3/"

general_config = CellDeepMimo.json_to_dict_config(scenario_dir + DEEPMIMO_CONFIG_FILE)

print(general_config)

