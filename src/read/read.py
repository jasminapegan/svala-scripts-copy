import re

from src.read.hand_fixes import HAND_FIXES, apply_obeliks_handfixes, SVALA_HAND_FIXES_MERGE


def replace_nonstandard_characters(text):
    replace_chars = {
        'а': 'a',
        'і': 'i',
        'о': 'o',
        'с': 'c',
        'ﾻ': '"',
        'ﾫ': '"',
        'М': 'M',
        'ј': 'j',
        'р': 'p',
        'В': 'B',
        'Р': 'P',
        '😉': ';)',
        '😊': ':)',
        '☹': ':('
    }
    for key in replace_chars:
        text = text.replace(key, replace_chars[key])
        #text = ' '.join(text.split())  # remove duplicate spaces
    return text

def read_raw_text(path):
    print(path)
    try:
        with open(path, 'r', encoding='utf-8') as rf:
            return replace_nonstandard_characters(rf.read())
    except:
        try:
            with open(path, 'r', encoding='utf-16') as rf:
                return replace_nonstandard_characters(rf.read())
        except:
            with open(path, 'r', encoding="windows-1250") as rf:
                return replace_nonstandard_characters(rf.read())



def map_svala_tokenized(svala_data_part, tokenized_paragraph, sent_i):
    # apply handfixes for obeliks
    apply_obeliks_handfixes(tokenized_paragraph)

    paragraph_res = []
    wierd_sign_count = 0
    svala_data_i = 0
    for i in range(sent_i, len(tokenized_paragraph)):
        sentence = tokenized_paragraph[i]
        sentence_res = []
        sentence_id = 0
        for tok in sentence:
            tok['text'] = tok['text']
            tag = 'pc' if 'xpos' in tok and tok['xpos'] == 'Z' else 'w'
            if 'misc' in tok:
                assert tok['misc'] == 'SpaceAfter=No'
            space_after = not 'misc' in tok
            if len(svala_data_part) <= svala_data_i:
                # if sentence does not end add it anyway
                # TODO i error?
                if sentence_res:
                    paragraph_res.append(sentence_res)
                return i, paragraph_res
            if svala_data_part[svala_data_i]['text'] != tok['text']:
                key = svala_data_part[svala_data_i]['text']
                if key not in HAND_FIXES:
                    if key.startswith('§§§') and key.endswith('§§§'):
                        HAND_FIXES[key] = ['§', '§', '§', key[3:-3], '§', '§', '§']
                    elif key.startswith('§§§'):
                        HAND_FIXES[key] = ['§', '§', '§', key[3:]]
                    elif key.endswith('§§§'):
                        HAND_FIXES[key] = [key[:-3], '§', '§', '§']
                    elif key[-1] == '.' and key[:-1].isnumeric():
                        HAND_FIXES[key] = [key[:-1], '.']
                    elif ':' in key and len(key.split(':')) == 2:
                        nums = key.split(':')
                        if nums[0].isnumeric() and nums[1].isnumeric():
                            HAND_FIXES[key] = [nums[0], ':', nums[1]]
                        elif nums[-1] == 'h' and nums[0].isnumeric() and nums[1][:-1].isnumeric():
                            HAND_FIXES[key] = [nums[0], ':', nums[1]]
                    elif len(key.split('.')) == 2 and key[-1] != '.' and key[0] != '.':
                        nums = key.split('.')
                        if nums[0].isnumeric() and nums[1].isnumeric():
                            HAND_FIXES[key] = [nums[0], '.', nums[1]]
                        elif nums[-1] == '%' and nums[0].isnumeric() and nums[1][:-1].isnumeric():
                            HAND_FIXES[key] = [nums[0], '.', nums[1]]
                    elif ',' in key and len(key.split(',')) == 2:
                        nums = key.split(',')
                        if nums[0].isnumeric() and nums[1].isnumeric():
                            HAND_FIXES[key] = [nums[0], ',', nums[1]]
                        elif nums[-1] == '%' and nums[0].isnumeric() and nums[1][:-1].isnumeric():
                            HAND_FIXES[key] = [nums[0], ',', nums[1]]
                    elif len(key.split('.')) == 3:
                        nums = key.split('.')
                        if nums[0].isnumeric() and nums[1].isnumeric() and nums[2].isnumeric():
                            HAND_FIXES[key] = [nums[0], '.', nums[1], '.', nums[2]]
                        elif nums[-1] == '%' and nums[0].isnumeric() and nums[1][:-1].isnumeric():
                            HAND_FIXES[key] = [nums[0], '.', nums[1]]
                    elif len(key) == 2 and key[-1] == '.' and key[0].isupper():
                        HAND_FIXES[key] = [key[0], '.']
                    else:
                        if len(key) < len(tok['text']):
                            print('HAND_FIXES_MERGE:')
                            print(f", ('{tok['text'][:len(key)]}', '{tok['text'][len(key):]}'): '{tok['text']}'")
                            SVALA_HAND_FIXES_MERGE[(tok['text'][:len(key)], tok['text'][len(key):])] = tok['text']
                        else:
                            print('HAND_FIXES OLD:')
                            print(f", '{key}': ['{key[:len(tok['text'])]}', '{key[len(tok['text']):]}']")

                            print('HAND_FIXES NEW:')
                            reg = re.findall(r"[\w]+|[^\s\w]", key)
                            print(f", '{key}': {str(reg)}")

                            HAND_FIXES[key] = re.findall(r"[\w]+|[^\s\w]", key)
                        print(f'key: {key} ; tok[text]: {tok["text"]}')

                if tok['text'] == HAND_FIXES[key][wierd_sign_count]:
                    wierd_sign_count += 1
                    if wierd_sign_count < len(HAND_FIXES[key]):
                        continue
                    else:
                        tok['text'] = key
                        wierd_sign_count = 0
                elif key.lower() in ['[xkrajx]']:
                    tok['text'] = '[XKrajX]'
                elif key.lower() in ['[ximex]']:
                    tok['text'] = '[XImeX]'
                elif key.lower() in ['[xpriimekx]']:
                    tok['text'] = '[XPriimekX]'
                elif key.lower() in ['[xdatumx]']:
                    tok['text'] = '[XDatumX]'
                elif key.lower() in ['[xjezikx]']:
                    tok['text'] = '[XJezikX]'
                elif key.lower() in ['[xstudijskasmerx]', '[xstudijskassmerx]', '[xštudijskasmerx]']:
                    tok['text'] = '[XStudijskaSmerX]'
                elif key.lower() in ['[xfakultetax]']:
                    tok['text'] = '[XFakultetaX]'
                elif key.lower() in ['[xenaslovx]']:
                    tok['text'] = '[XEnaslovX]'
                elif key.lower() in ['[xsvojilnipridevnikx]']:
                    tok['text'] = '[XSvojilniPridevnikX]'
                elif key.lower() in ['[xpodjetjex]']:
                    tok['text'] = '[XPodjetjeX]'
                elif key.lower() in ['[xnaslovx]']:
                    tok['text'] = '[XNaslovX]'
                else:
                    print(f'key: "{key}" ; tok[text]: "{tok["text"]}"')
                    raise 'Word mismatch!'
            sentence_id += 1
            sentence_res.append({'token': tok['text'], 'tag': tag, 'id': sentence_id, 'space_after': space_after, 'svala_id': svala_data_part[svala_data_i]['id']})
            svala_data_i += 1
        paragraph_res.append(sentence_res)
    return sent_i, paragraph_res