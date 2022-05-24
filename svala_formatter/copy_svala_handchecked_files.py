import argparse
import json
import logging
import os
import shutil
import time

def read_json(file):
    jf = open(file)
    svala_data = json.load(jf)
    jf.close()
    return svala_data


def compare_files(corrected_file, original_file):
    # count_differences(corrected_file['source'], original_file['source'])
    target = False
    source = False

    source_modifications = 0
    for corrected_source, original_source in zip(corrected_file['source'], original_file['source']):
        if corrected_source != original_source:
            source_modifications += 1

    target_modifications = 0
    for corrected_target, original_target in zip(corrected_file['target'], original_file['target']):
        if corrected_target != original_target:
            target_modifications += 1

    if target_modifications > 0:
        target = True
    if source_modifications > 0:
        source = True

    return target, source


def main(args):
    # create mapper to corrected files
    corrected_files_mapper = {}
    filename_encountered = False
    for foldername in os.listdir(args.corrected_folder):
        orig_name = 'KUS' + foldername.split('KUS')[1]
        # if orig_name == 'KUS-G-slo-4-GO-E-2009-10105':
        #     filename_encountered = True
        # if not filename_encountered:
        #     continue
        corrected_files_mapper[orig_name] = foldername

    filename_encountered = False
    for foldername in os.listdir(args.original_folder):
        # if foldername == 'KUS-G-slo-4-GO-E-2009-10105':
        #     filename_encountered = True
        # if not filename_encountered:
        #     continue
        for filename in os.listdir(os.path.join(args.original_folder, foldername)):
            fixed = False
            of = os.path.join(args.original_folder, foldername, filename)
            copy_filename = filename
            if filename.endswith('_problem.json'):
                copy_filename = filename[:-13] + '.json'
            if filename.endswith('_popravljeno.json'):
                copy_filename = filename[:-13] + '.json'
            cpf = os.path.join(args.copied_folder, foldername, copy_filename)
            cpfol = os.path.join(args.copied_folder, foldername)
            if filename.endswith('_problem.json'):
                new_filename = filename[:-13] + '_popravljeno.json'
                if os.path.exists(os.path.join(args.corrected_folder, corrected_files_mapper[foldername], new_filename)):
                    fixed = True
                    filename = new_filename
            cf = os.path.join(args.corrected_folder, corrected_files_mapper[foldername], filename)
            cor_files = read_json(cf)
            ori_files = read_json(of)
            target, source = compare_files(cor_files, ori_files)
            if target or source or fixed:
                if not os.path.exists(cpfol):
                    os.mkdir(cpfol)
                shutil.copyfile(cf, cpf)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Read already processed xmls, erase entries without examples and limit gigafida examples to 1 per entry.')
    parser.add_argument('--copied_folder', default='data/solar.svala.fixed.1.0.1',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    parser.add_argument('--corrected_folder', default='data/solar.svala.1.0.1.corrected',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    parser.add_argument('--original_folder', default='data/solar.svala1.0.1.original',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    args = parser.parse_args()

    start = time.time()
    main(args)
    logging.info("TIME: {}".format(time.time() - start))
