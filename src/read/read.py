
HAND_FIXES = {'§§§pisala': ['§', '§', '§', 'pisala'], '§§§poldne': ['§', '§', '§', 'poldne'], '§§§o': ['§', '§', '§', 'o'], '§§§mimi': ['§', '§', '§', 'mimi'], '§§§nil': ['§', '§', '§', 'nil'], '§§§ela': ['§', '§', '§', 'ela'], 'sam§§§': ['sam', '§', '§', '§'], 'globač§§§': ['globač', '§', '§', '§'], 'sin.': ['sin', '.'],  '§§§oveduje': ['§', '§', '§', 'oveduje'],  'na§§§': ['na', '§', '§', '§'], '§§§ka§§§': ['§', '§', '§', 'ka', '§', '§', '§'], '§§§e§§§': ['§', '§', '§', 'e', '§', '§', '§'], '§§§': ['§', '§', '§'], 'ljubezni.': ['ljubezni', '.'], '12.': ['12', '.'], '16.': ['16', '.'], 'st.': ['st', '.'], 'S.': ['S', '.'], 'pr.': ['pr', '.'], 'n.': ['n', '.'], '19:30': ['19', ':', '30'], '9.': ['9', '.'], '6:35': ['6', ':', '35'], 'itd.': ['itd', '.'], 'Sv.': ['Sv', '.'], 'npr.': ['npr', '.'], 'sv.': ['sv', '.'], '12:00': ['12', ':', '00'], "sram'vali": ['sram', "'", 'vali'], '18:00': ['18', ':', '00'], 'J.': ['J', '.'], '5:45': ['5', ':', '45'], '17.': ['17', '.'], '9.00h': ['9', '.', '00h'], 'H.': ['H', '.'], '1.': ['1', '.'], '6.': ['6', '.'], '7:10': ['7', ':', '10'], 'g.': ['g', '.'], 'Oz.': ['Oz', '.'], '20:00': ['20', ':', '00'], '17.4.2010': ['17.', '4.', '2010'], 'ga.': ['ga', '.'], 'prof.': ['prof', '.'], '6:45': ['6', ':', '45'], '19.': ['19', '.'], '3.': ['3', '.'], 'tj.': ['tj', '.'], 'Prof.': ['Prof', '.'], '8.': ['8', '.'], '9:18': ['9', ':', '18'], 'ipd.': ['ipd', '.'], '7.': ['7', '.'], 'št.': ['št', '.'], 'oz.': ['oz', '.'], 'R.': ['R', '.'], '13:30': ['13', ':', '30'], '5.': ['5', '.'], '...': ['.', '.', '.']}


def read_raw_text(path):
    with open(path, 'r') as rf:
        return rf.read()


def map_svala_tokenized(svala_data_part, tokenized_paragraph, sent_i):
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
                return i, paragraph_res
            if svala_data_part[svala_data_i]['text'].strip() != tok['text']:
                key = svala_data_part[svala_data_i]['text'].strip()
                if key not in HAND_FIXES:
                    print(f'key: {key} ; tok[text]: {tok["text"]}')
                    if key.startswith('§§§') and key.endswith('§§§'):
                        HAND_FIXES[key] = ['§', '§', '§', key[3:-3], '§', '§', '§']
                    elif key.startswith('§§§'):
                        HAND_FIXES[key] = ['§', '§', '§', key[3:]]
                    elif key.endswith('§§§'):
                        HAND_FIXES[key] = [key[:-3], '§', '§', '§']
                    else:
                        raise 'Word mismatch!'

                if tok['text'] == HAND_FIXES[key][wierd_sign_count]:
                    wierd_sign_count += 1
                    if wierd_sign_count < len(HAND_FIXES[key]):
                        continue
                    else:
                        tok['text'] = key
                        wierd_sign_count = 0
                else:
                    print(f'key: {key} ; tok[text]: {tok["text"]}')
                    raise 'Word mismatch!'
            sentence_id += 1
            sentence_res.append({'token': tok['text'], 'tag': tag, 'id': sentence_id, 'space_after': space_after, 'svala_id': svala_data_part[svala_data_i]['id']})
            svala_data_i += 1
        paragraph_res.append(sentence_res)
    return sent_i, paragraph_res