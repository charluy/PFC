import shutil

file_in = "SNR_0.npy"
for i in range(1,31):
    file_out = f"SNR_{i}.npy"
    shutil.copyfile(file_in, file_out)
