import re

from src.read.hand_fixes import HAND_FIXES, apply_obeliks_handfixes, SVALA_HAND_FIXES_MERGE


def read_raw_text(path):
    print(path)
    # if path == "data/KOST/raw/L-1819-110.txt":
    #     print('here')
    try:
        with open(path, 'r', encoding='utf-8') as rf:
            return rf.read()
    except:
        try:
            with open(path, 'r', encoding='utf-16') as rf:
                return rf.read()
        except:
            with open(path, 'r', encoding="windows-1250") as rf:
                return rf.read()



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
                    else:
                        if len(key) < len(tok['text']):
                            print('HAND_FIXES_MERGE:')
                            print(f", ('{tok['text'][:len(key)]}', '{tok['text'][len(key):]}'): '{tok['text']}'")
                            SVALA_HAND_FIXES_MERGE[(tok['text'][:len(key)], tok['text'][len(key):])] = tok['text']
                            a = SVALA_HAND_FIXES_MERGE
                        else:
                            print('HAND_FIXES OLD:')
                            print(f", '{key}': ['{key[:len(tok['text'])]}', '{key[len(tok['text']):]}']")

                            print('HAND_FIXES NEW:')
                            reg = re.findall(r"[\w]+|[^\s\w]", key)
                            print(f", '{key}': {str(reg)}")

                            # HAND_FIXES[key] = [key[:len(tok['text'])], key[len(tok['text']):]]
                            HAND_FIXES[key] = re.findall(r"[\w]+|[^\s\w]", key)
                        print(f'key: {key} ; tok[text]: {tok["text"]}')
                        # raise ValueError('Word mismatch!')

                if tok['text'] == HAND_FIXES[key][wierd_sign_count]:
                    wierd_sign_count += 1
                    if wierd_sign_count < len(HAND_FIXES[key]):
                        continue
                    else:
                        tok['text'] = key
                        wierd_sign_count = 0
                elif key in ['[XKrajX]']:
                    tok['text'] = '[XKrajX]'
                elif key in ['[XImeX]']:
                    tok['text'] = '[XImeX]'
                else:
                    print(f'key: {key} ; tok[text]: {tok["text"]}')
                    raise 'Word mismatch!'
            sentence_id += 1
            sentence_res.append({'token': tok['text'], 'tag': tag, 'id': sentence_id, 'space_after': space_after, 'svala_id': svala_data_part[svala_data_i]['id']})
            svala_data_i += 1
        paragraph_res.append(sentence_res)
    return sent_i, paragraph_res