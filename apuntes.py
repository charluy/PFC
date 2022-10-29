
import numpy as np

for time in range(0,2):
    npz = np.load(f'scenarios/mateo3/UEgroup_0/Data_{time}.npz')
    snr = npz['SNR'][0:3,:]
    snr = [np.mean(snr[ue,:]) for ue in range(0,snr.shape[0])]
    print(f"SNR promedio para ues del 0 al 2:\n\t {snr}")

#####################################################################

from Scheds_Inter import InterSliceSchedulerDeepMimo

# ba, fr, dm, tdd, gr, cant_prbs_base
iss = InterSliceSchedulerDeepMimo([10], 'FR1', False, True, 3000, 2*8)
