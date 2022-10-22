def create_conf_dict(center_freq, bandwidth, cant_sc, is_dynamic, refresh_rate, sim_duration, UEgroups):
    conf_dict = {
        "frecuency": center_freq, # In GHz
        "bandwidth": int(bandwidth*1000), # In MHz
        "cant_prb" : int(bandwidth*1000/(12*0.15)),
        "n_sc": cant_sc,
        "is_dynamic": is_dynamic,
        "refresh_rate": refresh_rate,
        "sim_duration": sim_duration,
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