import argparse
import logging
import os
import sys
import time
import traceback

import classla

from constants import replacements, svala_hand_fixes_merge, obeliks_hand_fixes_merge, hand_fixes
import svala2tei
import txt2svala

logging.basicConfig(level=logging.INFO)


def main(args, annotator, tokenizer):
    start = time.time()

    # prepare paths
    basedir = os.path.join('data', args.project_name)
    svala_folder = os.path.join(basedir, 'svala')
    results_folder = os.path.join(basedir, 'results')
    raw_text = os.path.join(basedir, 'raw')

    if args.only_txt:
        print('CONVERTING TXT > SVALA ...')
        if svala_folder is None:
            raise Exception('Path to svala_folder is not set!')

        args_txt2svala = argparse.Namespace(
            input_folder=raw_text,
            output_folder=svala_folder
        )
        txt2svala.main(args_txt2svala)

    # prepare args
    args_svala2tei = argparse.Namespace(
        svala_folder=svala_folder,
        results_folder=results_folder,
        raw_text=raw_text,
        metadata_excel=os.path.join(basedir, args.metadata_excel),
        tokenization_interprocessing=os.path.join(basedir, 'processing.tokenization'),
        overwrite_tokenization=True,
        annotation_interprocessing=os.path.join(basedir, 'processing.annotation'),
        overwrite_annotation=True,
        only_txt=args.only_txt
    )

    svala2tei.main(args_svala2tei, annotator=annotator, tokenizer=tokenizer, fake_missing_data=args.fake_missing_data)

    logging.info("TIME: {}".format(time.time() - start))


def get_filename(exception, args, current_file, svala_file):
    raw_folder = os.path.join('data', args.project_name, 'raw')
    svala_folder = os.path.join('data', args.project_name, 'svala')

    filename = ''
    for x in exception.split(' '):
        if x.endswith('.txt'):
            filename = os.path.join(raw_folder, x)
            break
        elif x.endswith('.json'):
            filename = os.path.join(svala_folder, x)
            break

    print(f'Possible current file: {filename} or {current_file}')
    if filename:
        return filename
    elif current_file:
        return current_file
    elif svala_file:
        return os.path.join(args.svala_folder, svala_file)
    else:
        print('Couldn\'t find current file name')


def persist_dictionary(filename: str, dictionary: dict, variable: str):
    with open(filename, 'w', encoding='utf8') as f:
        json_data = repr(dictionary)
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
    if auto_replace:
        print(f'Use automatic [A] or manual [M] replacement? Auto handfix: {auto_replace}')
        option_handfix = "".join(sys.stdin.read(2)).strip()
    else:
        option_handfix = 'm'

    if option_handfix.lower() == 'a':
        pass
    elif option_handfix.lower() == 'm':
        print('Enter comma-separated handfix as in example for 90%: \'90,%\'')
        sys.stdin.readline()
        auto_replace = "".join(sys.stdin.readline().strip()).split(',')
    else:
        print(f'Unknown option {option_handfix}, skipping replacement')
        return

    print(f'Handfix options: [S] split into {auto_replace}; [M] merge - svala {auto_replace} [O] merge - obeliks {auto_replace}')
    option_handfix = "".join(sys.stdin.read(2)).strip()

    if option_handfix.lower() == 's':
        print('Adding hand fix ...')
        hand_fixes.HAND_FIXES.update([(''.join(auto_replace), auto_replace)])
        print('Persisting hand fixes ...')
        persist_dictionary('constants/hand_fixes.py', hand_fixes.HAND_FIXES, 'HAND_FIXES')

    elif option_handfix.lower() == 'm':
        print('Adding svala merge hand fix ...')
        svala_hand_fixes_merge.SVALA_HAND_FIXES_MERGE.update([(tuple(auto_replace), ''.join(auto_replace))])
        print('Persisting hand fixes ...')
        persist_dictionary('constants/svala_hand_fixes_merge.py', svala_hand_fixes_merge.SVALA_HAND_FIXES_MERGE,
                           'SVALA_HAND_FIXES_MERGE')

    elif option_handfix.lower() == 'o':
        print('Adding obeliks merge hand fix ...')
        obeliks_hand_fixes_merge.OBELIKS_HAND_FIXES_MERGE.update([(''.join(auto_replace), auto_replace)])
        print('Persisting hand fixes ...')
        persist_dictionary('constants/obeliks_hand_fixes_merge.py', obeliks_hand_fixes_merge.OBELIKS_HAND_FIXES_MERGE,
                           'OBELIKS_HAND_FIXES_MERGE')

    else:
        print(f'Unknown option {option_handfix}, skipping replacement')


def find_mismatched_chars(a, b):
    for ca, cb in zip(a, b):
        if ca != cb:
            # weird = non-ASCII, normal = ASCII
            if ord(ca) > 127 and ord(cb) <= 127:
                return (ca, cb)
            if ord(cb) > 127 and ord(ca) <= 127:
                return (cb, ca)
            else:
                print(f'Both characters {(ca, cb)} are non-ASCII!')
                return (ca, cb)
    return None  # no difference


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Merges svala data, raw data and metadata into TEI format (useful for corpora like KOST).')
    parser.add_argument('--project_name', default='KOST',
                        help='project name given at initialization (folder name inside \'data\' dir)')
    parser.add_argument('--metadata_excel', default='KOST.xlsm',
                        help='project metadata excel filename inside \'data/projectname\' dir, e.g. KOST.xlsm')
    parser.add_argument('--only_txt', action='store_true',
                        help='Generate TEI from only txt files')
    parser.add_argument('--fake_missing_data', action='store_true',
                        help='Generate data from TXTs that are missing matching JSONs')

    args = parser.parse_args()

    start = time.time()

    # preload nlp annotator and tokenizer for speed
    print("Loading annotator and tokenizer ...")
    annotator = classla.Pipeline('sl', pos_use_lexicon=True, pos_lemma_pretag=False, tokenize_pretokenized="conllu",
                                 type='standard_jos', use_gpu=True)
    tokenizer = classla.Pipeline('sl', processors='tokenize', pos_lemma_pretag=True, use_gpu=True)

    success = False
    option = None

    while not success:
        current_file = None

        try:
            main(args, annotator, tokenizer)
            success = True
        except Exception as e:
            auto_replace = None
            auto_char_replace = None
            svala_file = None
            if 'Word mismatch' in str(e):
                svala_file = str(e).split('Word mismatch in')[1].split('at')[0].strip()
                w1, w2 = str(e).split(':')[1].strip().split(',')
                auto_char_replace = find_mismatched_chars(w1.strip(), w2.strip())
            if 'Possible replacement' in str(e):
                auto_replace = tuple(str(e).split('Possible replacement: ')[1].strip().split(','))
            elif 'Not in metadata' in str(e):
                print(f'''Check metadata excel for metadata and author of text {str(e).split(":")[1]}. Common reasons:
- missing author metadata
- missing text metadata
- typo in author name
Edit the metadata excel and press Enter to continue.''')
                os.system(f'excel.exe \"{args.metadata_excel}\"')
                option = sys.stdin.read(1).strip()
                continue

            # get name of failed file
            filename = get_filename(str(e), args, current_file, svala_file)

            fix_options = ""
            if auto_char_replace:
                fix_options += f"\tR - add to symbol replacements: {auto_char_replace}\n"
            if auto_replace:
                fix_options += f"\tH - add to hand fixes - manual or auto: {auto_replace}\n"
            else:
                fix_options += f"\tH - add to hand fixes - manual or auto: [auto replacement not available]\n"
            if filename:
                fix_options += f"\tE - open in editor: {filename}\n"
            fix_options += "\tQ - quit"

            print(f'''
    Failed to create TEI:
    {traceback.format_exc()}
    
    Select option: 
    {fix_options}
    ''')
            option = sys.stdin.read(1).strip()

            if option.lower() == 'r':
                if handle_handfix_none(auto_char_replace, 'replacements.py'):
                    continue

                print('Adding symbol replacement ...')
                replacements.replace_chars.update([auto_char_replace])
                print('Persisting replacements ...')
                persist_dictionary('constants/replacements.py', replacements.replace_chars, 'replace_chars')

            elif option.lower() == 'h':
                handfix_options(auto_replace)

            elif option.lower() == 'e':
                print('Opening in editor ...')

                if not filename or not os.path.isfile(filename):
                    print(f"file {filename} not found")
                    continue

                os.system(f'notepad.exe \"{filename}\"')

            elif option.lower() == 'q':
                print('Quitting ...')
                success = True

            else:
                print(f'Invalid option: \'{option}\'. Try again')

    logging.info("TIME: {}".format(time.time() - start))
