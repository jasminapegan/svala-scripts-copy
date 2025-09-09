import os
import classla

# download models
classla.download(lang='sl', type='standard_jos')

# create data dir
base_data_dir = 'data/KOST'
if not os.path.exists(base_data_dir):
    os.makedirs(base_data_dir)
    os.makedirs('data/KOST/raw')
    os.makedirs('data/KOST/svala')
    os.makedirs('data/KOST/results')