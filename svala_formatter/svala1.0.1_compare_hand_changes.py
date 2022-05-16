import argparse
import json
import logging
import os
import time
from xml.etree import ElementTree


def read_json(file):
    jf = open(file)
    svala_data = json.load(jf)
    jf.close()
    return svala_data


# def count_differences(corrected_input, original_input):
#     modifications = 0
#     corrected_dict = {el['id']: el['text'] for el in corrected_input}
#     original_dict = {el['id']: el['text'] for el in original_input}
#     a = sorted(corrected_dict)
#     corrected_dict = dict(sorted(corrected_dict.items(), key=lambda item: int(item[0][1:])))
#     original_dict = dict(sorted(original_dict.items(), key=lambda item: int(item[0][1:])))
#     for corrected_source, original_source in zip(corrected_input['source'], original_file['source']):
#         if corrected_source != original_source:
#             modifications += 1
#
#     return modifications

def compare_files(corrected_file, original_file):
    # count_differences(corrected_file['source'], original_file['source'])

    source_modifications = 0
    for corrected_source, original_source in zip(corrected_file['source'], original_file['source']):
        if corrected_source != original_source:
            source_modifications += 1

    target_modifications = 0
    for corrected_target, original_target in zip(corrected_file['target'], original_file['target']):
        if corrected_target != original_target:
            target_modifications += 1

    if target_modifications > 0 or source_modifications > 0:
        return True

    return False


def main(args):
    # create mapper to corrected files
    corrected_files_mapper = {}
    for foldername in os.listdir(args.corrected_folder):
        orig_name = 'KUS' + foldername.split('KUS')[1]
        corrected_files_mapper[orig_name] = foldername

    for foldername in os.listdir(args.original_folder):
        for filename in os.listdir(os.path.join(args.original_folder, foldername)):
            of = os.path.join(args.original_folder, foldername, filename)
            if filename.endswith('_problem.json'):
                new_filename = filename[:-13] + '_popravljeno.json'
                if os.path.exists(os.path.join(args.corrected_folder, corrected_files_mapper[foldername], new_filename)):
                    filename = new_filename
            cf = os.path.join(args.corrected_folder, corrected_files_mapper[foldername], filename)
            if compare_files(read_json(cf), read_json(of)):
                print(corrected_files_mapper[foldername] + '/' + filename)



if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Read already processed xmls, erase entries without examples and limit gigafida examples to 1 per entry.')
    parser.add_argument('--corrected_folder', default='data/solar.svala.1.0.1.corrected.small',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    parser.add_argument('--original_folder', default='data/solar.svala.1.0.1.original.small',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    # parser.add_argument('--corrected_folder', default='data/solar.svala.1.0.1.corrected',
    #                     help='input file in (gz or xml currently). If none, then just database is loaded')
    # parser.add_argument('--original_folder', default='data/solar.svala1.0.1.original',
    #                     help='input file in (gz or xml currently). If none, then just database is loaded')
    args = parser.parse_args()

    start = time.time()
    main(args)
    logging.info("TIME: {}".format(time.time() - start))
