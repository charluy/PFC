def create_conf_dict(center_freq, bandwidth, cant_sc, is_dynamic, refresh_rate, sim_duration, UEgroups):
    conf_dict = {
        "frecuency": center_freq, # In GHz
        "bandwidth": int(bandwidth*1000), # In MHz
        "cant_prb" : int(cant_sc/12),
        "n_sc": cant_sc,
        "is_dynamic": is_dynamic,
        "refresh_rate": int(refresh_rate),
        "sim_duration": int(sim_duration),
    }

    conf_dict.update(create_ue_group_dict(UEgroups))

    return conf_dict

def create_ue_group_dict(UEgroups):
    ue_groups = {
        "ue_groups": {}
    } 

    for UEgroup in UEgroups:
        UEgroup_dict = {
            "UEgroup_" + str(UEgroups.index(UEgroup)):{
                "cant_ue": UEgroup[1]+1 - UEgroup[0]
            }
        }
        print(UEgroup_dict)
        ue_groups["ue_groups"].update(UEgroup_dict)

    return ue_groups

def round_up_sc_to_12_and_8(bandwidth):
    # cant_sc should be divisible by 12 and the by 8
    cant_sc = int((bandwidth*1000)/(0.015)) - int((bandwidth*1000)/(0.015))%96

    return cant_sc