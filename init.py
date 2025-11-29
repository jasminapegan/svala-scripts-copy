import os
import sys

import classla

if __name__ == '__main__':

    # download models
    classla.download(lang='sl', type='standard_jos')

    # create data dir
    project = sys.argv[1]
    base_data_dir = f'data/{project}'
    if not os.path.exists(base_data_dir):
        os.makedirs(base_data_dir)
        os.makedirs(f'{base_data_dir}/raw')
        os.makedirs(f'{base_data_dir}/svala')
        os.makedirs(f'{base_data_dir}/results')
