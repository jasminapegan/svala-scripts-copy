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
    # corrected_files_mapper = {}
    # for foldername in os.listdir(args.original_folder):
    #     orig_name = 'KUS' + foldername.split('KUS')[1]
    #     corrected_files_mapper[orig_name] = foldername
    if os.path.exists(args.copied_folder):
        shutil.rmtree(args.copied_folder)

    os.makedirs(args.copied_folder)

    for foldername in os.listdir(args.original_folder):
        os.makedirs(os.path.join(args.copied_folder, foldername))
        for filename in os.listdir(os.path.join(args.original_folder, foldername)):
            of = os.path.join(args.original_folder, foldername, filename)
            copy_filename_split = filename.split('_')
            assert len(copy_filename_split) == 3 or len(copy_filename_split) == 2
            if len(copy_filename_split) == 3:
                copy_filename = copy_filename_split[0] + '_' + copy_filename_split[2]
            elif len(copy_filename_split) == 2:
                copy_filename = copy_filename_split[0] + '_' + copy_filename_split[1]
            else:
                raise 'Impossible!'

            cf = os.path.join(args.copied_folder, foldername, copy_filename)
            shutil.copyfile(of, cf)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Read already processed xmls, erase entries without examples and limit gigafida examples to 1 per entry.')
    parser.add_argument('--copied_folder', default='data/svala_generated_text.formatted',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    parser.add_argument('--original_folder', default='data/svala_generated_text.handchecks',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    args = parser.parse_args()

    start = time.time()
    main(args)
    logging.info("TIME: {}".format(time.time() - start))
