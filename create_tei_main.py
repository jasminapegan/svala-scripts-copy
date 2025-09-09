import argparse
import json
import logging
import os
import sys
import time
import traceback

import classla

from constants import replacements, svala_hand_fixes_merge, obeliks_hand_fixes_merge
import svala2tei
import txt2svala

from constants import hand_fixes

logging.basicConfig(level=logging.DEBUG)

def main(args):
    start = time.time()

    # preload nlp annotator and tokenizer for speed
    annotator = classla.Pipeline('sl', pos_use_lexicon=True, pos_lemma_pretag=False, tokenize_pretokenized="conllu",
                                 type='standard_jos', use_gpu=True)
    tokenizer = classla.Pipeline('sl', processors='tokenize', pos_lemma_pretag=True, use_gpu=True)

    parser_txt2svala = argparse.ArgumentParser(description='Converts raw text into svala format.')
    parser_txt2svala.add_argument('--input_folder', default=args.txt_folder)
    parser_txt2svala.add_argument('--output_folder', default=args.svala_folder)
    args_txt2svala = parser_txt2svala.parse_args()

    if args.txt_folder is not None:
        print('CONVERTING TXT > SVALA ...')
        txt2svala.main(args_txt2svala)

    svala2tei.main(args, annotator=annotator, tokenizer=tokenizer)

    logging.info("TIME: {}".format(time.time() - start))


def get_filename(exception, args):
    for x in exception.split(' '):
        if x.endswith('.txt'):
            return os.path.join(args.txt_folder, x)
        elif x.endswith('.json'):
            return os.path.join(args.svala_folder, x)

def persist_dictionary(filename: str, dictionary: dict, variable: str):
    with open(filename, 'w') as f:
        json_data = json.dumps(dictionary, indent=4)
        f.write(f"{variable} = {json_data}")


def handle_handfix_none(handfix, filename):
    if handfix is None:
        print('Auto handfix not detected, insert manually? [Y/N]')
        option_manual = sys.stdin.read(1).strip()

        if option_manual.lower() == 'y':
            os.system(f'notepad.exe constants/{filename}')
            return False
        else:
            return True
    else:
        return False


def handfix_options(auto_replace):
    print(f'Use automatic [A] or manual [M] replacement? Auto handfix: {auto_replace}')
    option_handfix = "".join(sys.stdin.read(2)).strip()

    if option_handfix.lower() == 'a':
        pass
    elif option_handfix.lower() == 'm':
        print('Enter comma-separated handfix as in example for 90%: \'90,%\'')
        auto_replace = "".join(sys.stdin.read(2)).split(',')
    else:
        print(f'Unknown option {option_handfix}, skipping replacement')
        return

    print(f'Handfix options: [S] split into {auto_replace}; [M] merge - svala {auto_replace} [O] merge - obeliks {auto_replace}')
    option_handfix = "".join(sys.stdin.read(2)).strip()

    if option_handfix.lower() == 's':
        print('Adding hand fix ...')
        hand_fixes.HAND_FIXES.update([auto_replace])
        print('Persisting hand fixes ...')
        persist_dictionary('constants/hand_fixes.py', hand_fixes.HAND_FIXES, 'HAND_FIXES')

    elif option_handfix.lower() == 'm':
        print('Adding svala merge hand fix ...')
        svala_hand_fixes_merge.SVALA_HAND_FIXES_MERGE.update(tuple(auto_replace), ''.join(auto_replace))
        print('Persisting hand fixes ...')
        persist_dictionary('constants/svala_hand_fixes_merge.py', svala_hand_fixes_merge.SVALA_HAND_FIXES_MERGE,
                           'SVALA_HAND_FIXES_MERGE')

    elif option_handfix.lower() == 'o':
        print('Adding obeliks merge hand fix ...')
        obeliks_hand_fixes_merge.OBELIKS_HAND_FIXES_MERGE.update(''.join(auto_replace), list(auto_replace))
        print('Persisting hand fixes ...')
        persist_dictionary('constants/obeliks_hand_fixes_merge.py', obeliks_hand_fixes_merge.OBELIKS_HAND_FIXES_MERGE,
                           'OBELIKS_HAND_FIXES_MERGE')

    else:
        print(f'Unknown option {option_handfix}, skipping replacement')


if __name__ == '__main__':
    base_dir = 'data/KOST'
    parser = argparse.ArgumentParser(
        description='Merges svala data, raw data and metadata into TEI format (useful for corpora like KOST).')
    parser.add_argument('--txt_folder', default=f'{base_dir}/Neoznacena besedila',
                        help='TXT files location, only set if creating TEI from TXT')
    parser.add_argument('--svala_folder', default=f'{base_dir}/svala_1_0',
                        help='Path to directory that contains svala files.')
    parser.add_argument('--results_folder', default=f'{base_dir}/results_1_0',
                        help='Path to results directory.')
    parser.add_argument('--raw_text', default=f'{base_dir}/Neoznacena besedila',
                        help='Path to directory that contains raw text files.')
    parser.add_argument('--metadata_excel', default=f'{base_dir}/KOST 2.0, 25-08.xlsm',
                        help='KOST metadata location')
    parser.add_argument('--tokenization_interprocessing', default=f'{base_dir}/processing.tokenization',
                        help='Path to file that containing tokenized data.')
    parser.add_argument('--overwrite_tokenization', action='store_true', help='Force retokenization without having to manually delete tokenization file.')
    parser.add_argument('--annotation_interprocessing', default=f'{base_dir}/processing.annotation',
                        help='Path to file that containing annotated data.')
    parser.add_argument('--overwrite_annotation', action='store_true', help='Force reannotation without having to manually delete tokenization file.')

    args = parser.parse_args()

    start = time.time()

    success = False
    while not success:
        try:
            main(args)
            success = True
        except Exception as e:
            auto_replace = None
            if 'Possible replacement' in str(e):
                auto_replace = tuple(str(e).split('Possible replacement: ')[1].strip().split(','))
            elif 'Not in metadata' in str(e):
                print(f'''Check metadata excel for metadata and author of text {str(e).split(":")[1]}. Common reasons:
- missing author metadata
- missing text metadata
- typo in author name
Edit the metadata excel and press any key to continue.''')
                os.system(f'excel.exe \"{args.metadata_excel}\"')
                option = sys.stdin.read(1).strip()
                continue

            print(f'''
    Failed to create TEI:
    {traceback.format_exc()}
    
    Select option:
    A - add to exceptions: 
    R - add to symbol replacements: {auto_replace}
    H - add to hand fixes - manual or auto: {auto_replace}
    E - open in editor
    Q - quit
            ''')
            option = sys.stdin.read(1).strip()

            if option.lower() == 'a':
                print('Adding exception ...')

            elif option.lower() == 'r':
                if handle_handfix_none(auto_replace, 'replacements.py'):
                    continue

                print('Adding symbol replacement ...')
                replacements.replace_chars.update([auto_replace])
                print('Persisting replacements ...')
                persist_dictionary('constants/replacements.py', replacements.replace_chars, 'replace_chars')

            elif option.lower() == 'h':
                handfix_options(auto_replace)

            elif option.lower() == 'e':
                print('Opening in editor ...')
                filename = get_filename(str(e), args)

                if not filename:
                    print(f"file {filename} not found")
                    continue

                os.system(f'notepad.exe \"{filename}\"')

            elif option.lower() == 'q':
                print('Quitting ...')
                success = True

            else:
                print(f'Invalid option: \'{option}\'. Try again')

    logging.info("TIME: {}".format(time.time() - start))
