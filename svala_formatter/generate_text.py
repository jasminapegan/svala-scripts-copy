import argparse
import json
import logging
import os
import re
import time

problematic_words = ['...', '-', '—', '"', "'"]
left_word = [',', '.', '!', '?', ':', ';', ')', '„']
right_word = ['(', '”']
ok_words = []


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


def mine_text(cor_files):
    text = ''
    has_space = False
    is_problematic = False
    errors = []
    left_asterix = 0
    right_asterix = 0
    for corrected_source in cor_files:
        word = corrected_source['text'].strip()
        if re.match("^[a-zA-Z0-9ČĆŽŠĐčćžšđ§]+$", word):
            if has_space:
                text += ' '
            text += word
            has_space = True
        elif word in problematic_words:
            if has_space:
                text += ' '
            text += word
            is_problematic = True
            has_space = True
        elif word in left_word:
            if word == '„':
                left_asterix += 1
            text += word
            has_space = True
        elif word in right_word:
            if word == '”':
                right_asterix += 1
            if has_space:
                text += ' '
            text += word
            has_space = False
        else:
            if has_space:
                text += ' '
            text += word
            is_problematic = True
            has_space = True
            errors.append(word)

    if left_asterix != right_asterix:
        is_problematic = True

    if len(text) > 0 and text[-1] == ' ':
        text = text[:-1]
    return text, is_problematic, errors


def write_file(is_problematic, foldername, filename, text, is_target):
    if is_target:
        new_filename = filename[:-5] + '_target.json'
    else:
        new_filename = filename[:-5] + '_source.json'

    if is_problematic:
        folder_path = os.path.join(args.problematic_folder, foldername)
        file_path = os.path.join(args.problematic_folder, foldername, new_filename)
    else:
        folder_path = os.path.join(args.unproblematic_folder, foldername)
        file_path = os.path.join(args.unproblematic_folder, foldername, new_filename)
    if not os.path.exists(folder_path):
        os.mkdir(folder_path)
    with open(file_path, 'w', encoding='utf-8') as wf:
        wf.write(text)


def main(args):
    errors_count = 0
    all_errors = set()

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
            cor_files = read_json(cf)
            ori_files = read_json(of)
            target, source = compare_files(cor_files, ori_files)
            if target:
                text, is_problematic, errors = mine_text(cor_files['target'])
                write_file(is_problematic, foldername, filename, text, True)
                for er in errors:
                    all_errors.add(er)
                    errors_count += 1

            if source:
                text, is_problematic, errors = mine_text(cor_files['source'])
                write_file(is_problematic, foldername, filename, text, False)
                for er in errors:
                    all_errors.add(er)
                    errors_count += 1

            print(corrected_files_mapper[foldername] + '/' + filename)

    print(errors_count)
    print(all_errors)
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Read already processed xmls, erase entries without examples and limit gigafida examples to 1 per entry.')
    parser.add_argument('--unproblematic_folder', default='data/svala_generated_text/unproblematic',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    parser.add_argument('--problematic_folder', default='data/svala_generated_text/problematic',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    parser.add_argument('--corrected_folder', default='data/solar.svala.1.0.1.corrected',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    parser.add_argument('--original_folder', default='data/solar.svala1.0.1.original',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    args = parser.parse_args()

    start = time.time()
    main(args)
    logging.info("TIME: {}".format(time.time() - start))
