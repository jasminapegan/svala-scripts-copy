from collections import deque

HAND_FIXES = {'§§§pisala': ['§', '§', '§', 'pisala'], '§§§poldne': ['§', '§', '§', 'poldne'], '§§§o': ['§', '§', '§', 'o'],
              '§§§mimi': ['§', '§', '§', 'mimi'], '§§§nil': ['§', '§', '§', 'nil'], '§§§ela': ['§', '§', '§', 'ela'],
              'sam§§§': ['sam', '§', '§', '§'], 'globač§§§': ['globač', '§', '§', '§'], 'sin.': ['sin', '.'],
              '§§§oveduje': ['§', '§', '§', 'oveduje'],  'na§§§': ['na', '§', '§', '§'], '§§§ka§§§': ['§', '§', '§', 'ka', '§', '§', '§'],
              '§§§e§§§': ['§', '§', '§', 'e', '§', '§', '§'], '§§§': ['§', '§', '§'], 'ljubezni.': ['ljubezni', '.'],
              'st.': ['st', '.'], 'S.': ['S', '.'], 'pr.': ['pr', '.'], 'n.': ['n', '.'],
              '19:30': ['19', ':', '30'], '6:35': ['6', ':', '35'], 'itd.': ['itd', '.'], 'Sv.': ['Sv', '.'],
              'npr.': ['npr', '.'], 'sv.': ['sv', '.'], '12:00': ['12', ':', '00'], "sram'vali": ['sram', "'", 'vali'],
              '18:00': ['18', ':', '00'], 'J.': ['J', '.'], '5:45': ['5', ':', '45'],
              '9.00h': ['9', '.', '00h'], 'H.': ['H', '.'], '7:10': ['7', ':', '10'],
              'g.': ['g', '.'], 'Oz.': ['Oz', '.'], '20:00': ['20', ':', '00'], '17.4.2010': ['17.', '4.', '2010'],
              'ga.': ['ga', '.'], 'prof.': ['prof', '.'], '6:45': ['6', ':', '45'],
              'tj.': ['tj', '.'], 'Prof.': ['Prof', '.'], '9:18': ['9', ':', '18'], 'ipd.': ['ipd', '.'],
              'št.': ['št', '.'], 'oz.': ['oz', '.'], 'R.': ['R', '.'], '13:30': ['13', ':', '30'],
              '...': ['.', '.', '.'], 'plavali.': ['plavali', '.'], '[XImeX]': ['[', 'XImeX', ']'],
              '[XimeX]': ['[', 'XimeX', ']'], 'hipoteze:': ['hipoteze', ':'], 'prehrano?': ['prehrano', '?'],
              '68-letna': ['68', '-', 'letna'], 'pojma:': ['pojma', ':'], '[XKrajX]': ['[', 'XKrajX', ']'],
              '3/4': ['3', '/', '4'], 'I-phonea': ['I', '-', 'phonea'], 'kredita:': ['kredita', ':'],
              '[XFakultetaX]': ['[', 'XFakultetaX', ']'], 'športno-eleganten': ['športno', '-', 'eleganten'],
              '[XStudijskaSmerX]': ['[', 'XStudijskaSmerX', ']'], '[XNaslovX]': ['[', 'XNaslovX', ']'],
              '(tudi': ['(', 'tudi'], 'kupujem)': ['kupujem', ')'], '[XPriimekX]': ['[', 'XPriimekX', ']'],
              '[XPodjetjeX]': ['[', 'XPodjetjeX', ']'], 'Zagreb,': ['Zagreb', ','], 'Budimpešto.': ['Budimpešto', '.'],
              'žalost.': ['žalost', '.'], '....': ['.', '.', '.', '.'], '[XStevilkaX]': ['[', 'XStevilkaX', ']'],
              'e-naslov': ['e', '-', 'naslov'], '[XEnaslovX]': ['[', 'XEnaslovX', ']'], 'e-pošto': ['e', '-', 'pošto'],
              '[XDatumX]': ['[', 'XDatumX', ']'], 'eno-sobno': ['eno', '-', 'sobno'],
              'lgbtq-prijazna': ['lgbtq', '-', 'prijazna'], 'lgbtq-prijaznega': ['lgbtq', '-', 'prijaznega'],
              'Covid-19': ['Covid', '-', '19'], ',,,': [',', ',', ','], 'e-maila': ['e', '-', 'maila'],
              'T&d': ['T', '&', 'd'], 'Spider-Man': ['Spider', '-', 'Man'], '12-strani': ['12', '-', 'strani'],
              'turbo-folk': ['turbo', '-', 'folk'], 'Cp-čkar': ['Cp', '-', 'čkar'], '46-letnik': ['46', '-', 'letnik'],
              '40-letna': ['40', '-', 'letna'], '18-19h': ['18', '-', '19h'], '[XSvojilniPridevnikX]': ['[', 'XSvojilniPridevnikX', ']'],
              'COVID-19': ['COVID', '-', '19'], '"sims"': ['"', 'sims', '"'], '2021/22': ['2021', '/', '22'],
              '2020/21': ['2020', '/', '21'], 'leto2021/22': ['leto2021', '/', '22'], 'H&m': ['H', '&', 'm'],
              'high-street': ['high', '-', 'street'], 'H&M-u': ['H', '&', 'M-u'], 'H&M': ['H', '&', 'M'],
              'srčno-žilnih': ['srčno', '-', 'žilnih'], 'srčno-žilni': ['srčno', '-', 'žilni'], #':))': [':)', ')'],
              'You-Tube-ju': ['You', '-', 'Tube-ju'], '37,8%': ['37', ',', '8', '%'], '23,8%': ['23', ',', '8', '%'],
              '17,6%': ['17', ',', '6', '%'], '12,6%': ['12', ',', '6', '%'], '58,2%': ['58', ',', '2', '%'], '76,2%': ['76', ',', '2', '%'],
              '.000': ['.', '000'], 'slovensko-nemškem': ['slovensko', '-', 'nemškem'], '..': ['.', '.'], 'rumeno-bela': ['rumeno', '-', 'bela'],
              'košík.cz': ['košík', '.', 'cz'], '100%': ['100', '%'], ':()': [':(', ')']}
# 12.': ['12', '.'], '16.': ['16', '.'],, '1.': ['1', '.'], '6.': ['6', '.'], '8.': ['8', '.'],'7.': ['7', '.'],'5.': ['5', '.'],  '17.': ['17', '.'], '9.': ['9', '.'], '19.': ['19', '.'], '3.': ['3', '.'],
#'vrnilа': ['vrnil', 'а'], 'odločilа': ['odločil', 'а'], 'hotelа': ['hotel', 'а'], 'slišalа': ['slišal', 'а'],
#'pomislilа': ['pomislil', 'а'], 'šlа': ['šl', 'а'], 'оd': ['о', 'd'], 'pisala': ['pisala']}
# , '37,8%': ['37', ',', '8%'], '23,8%': ['23', ',', '8%'], '17,6%': ['17', ',', '6%'], '12,6%': ['12', ',', '6%'], '58,2%': ['58', ',', '2%'], '76,2%': ['76', ',', '2%']
SVALA_HAND_FIXES_MERGE = {('oz', '.'): 'oz.', ('Npr', '.'): 'Npr.', ('npr', '.'): 'npr.', ('m', '.'): 'm.', ('itn', '.'): 'itn.',
                          ('max', '.'): 'max.', ('cca', '.'): 'cca.', ('n', '.'): 'n.', #(':)', ')'): ':))',
                          ('sv', '.'): 'sv.', ('Bolha', '.com'): 'Bolha.com', ('1901', '.'): '1901.'}
                          #('https://www.gutekueche', '.at/suche?s=krautfleckerl'): 'https://www.gutekueche.at/suche?s=krautfleckerl'}
                          #('p', '.'): 'p.', ('itd', '.'): 'itd.', ('S', '.'): 'S.', ('mlad', '.'): 'mlad.', ('1', '.'): '1.',
                          #('2', '.'): '2.', ('3', '.'): '3.', ('30', '.'): '30.', ('21', '.'): '21., ('4', '.'): '4.'
OBELIKS_HAND_FIXES_MERGE = { 'oz.': ['oz', '.'], 'Npr.': ['Npr', '.'], 'itn.': ['itn', '.'], 'mlad.': ['mlad', '.'],
                            'm.': ['m', '.'], 'max.': ['max', '.'], 'itd.': ['itd', '.'], '2,12': ['2', ',12'],
                            'd.': ['d', '.'], 'o.': ['o', '.'], 'k.': ['k', '.'], 'cca.': ['cca', '.'], 'IT.': ['IT', '.'],
                            'ipd.': ['ipd', '.'], 'dr.': ['dr', '.'], 'pr.': ['pr', '.'], 'npr.': ['npr', '.'],
                            'tel.': ['tel', '.'], 'Bolha.com': ['Bolha', '.', 'com'], 'tj.': ['tj', '.'], 't.': ['t', '.'], 'i.': ['i', '.'],
                            'Air-u': ['Air', '-', 'u'], 'nepremicnine.net': ['nepremicnine', '.', 'net'], 'n.': ['n', '.'],
                            ':))': [':)', ')'], 'sv.': ['sv', '.'], 'spar-u': ['spar', '-', 'u'], 'Sv.': ['Sv', '.'],
                            'mdr.': ['mdr', '.'], 'lat.': ['lat', '.'], '49,5': ['49', ',', '5'], 'etc.': ['etc', '.'],
                            '[XStudijskaSmerX]': ['[', 'XStudijskaSmerX', ']'], 'p.': ['p', '.'], 's.': ['s', '.'], 'e.': ['e', '.'],
                             'čas.': ['čas', '.'], 'd\'Arte': ['d', '\'', 'Arte'], 'film.': ['film', '.'], 'dan.': ['dan', '.'],
                             '26.12': ['26', '.', '12'], '28.12': ['28', '.', '12'], '2.': ['2', '.'], 'prav.': ['prav', '.'],
                             'del.': ['del', '.'], '1901.': ['1901', '.'], 'p-ja': ['p', '-', 'ja'], '14.': ['14', '.'],
                             '15.': ['15', '.'], 'K.': ['K', '.'], '6.': ['6', '.'], ':()': [':(', ')'], '17.': ['17', '.'],
                             '5.': ['5', '.'], '12.': ['12', '.'], '18.': ['18', '.'], '6.30': ['6', '.', '30'], '7.30': ['7', '.', '30'],
'8.30': ['8', '.', '30'], '9.00': ['9', '.', '00'], '14.00': ['14', '.', '00'], '21.30': ['21', '.', '30'],
              'https://www.gutekueche.at/suche?s=krautfleckerl': ['https://www.gutekueche', '.at/suche?s=krautfleckerl'],
                             '80-ih': ['80', '-', 'ih'], 'astra.si': ['astra', '.', 'si'], 'žival.': ['žival', '.'],
                             'Teams-ih': ['Teams', '-', 'ih'], 'Zoom-u': ['Zoom', '-', 'u'], 'Zoom-a': ['Zoom', '-', 'a'],
                             'Mirror-a': ['Mirror', '-', 'a'], 'cerkv.': ['cerkv', '.']}
# '2.': ['2', '.'], '3.': ['3', '.'], '2015.': ['2015', '.'], 'X.': ['X', '.'], 'V.': ['V', '.'], 'M.': ['M', '.'], 'S.': ['S', '.']


def merge_svala_data_elements(svala_data_object, i, mask_len):
    final_text = ''
    involved_sources = []
    involved_targets = []
    involved_edges = []
    for el in svala_data_object.svala_data['source'][i - mask_len + 1:i + 1]:
        # check whether merge won't cause further (unnoticed) issues later
        edges = svala_data_object.links_ids_mapper[el['id']]
        if len(edges) != 1:
            raise ValueError('Incorrect number of edges!')
        edge = svala_data_object.svala_data['edges'][edges[0]]
        # TODO check if  or len(edge['labels']) != 0 has to be added
        if len(edge['source_ids']) != 1 or len(edge['target_ids']) != 1:
            raise ValueError('Possible errors - CHECK!')

        final_text += el['text']
        involved_sources.append(edge['source_ids'][0])

        involved_targets.append(edge['target_ids'][0])
        involved_edges.append(edge['id'])

    # erase merged svala elements
    svala_data_object.svala_data['source'][i - mask_len + 1]['text'] = final_text
    svala_data_object.svala_data['source'] = [el for el in svala_data_object.svala_data['source'] if
                                 el['id'] not in involved_sources[1:]]

    for el in svala_data_object.svala_data['target']:
        if el['id'] == involved_targets[0]:
            el['text'] = final_text
            break
    svala_data_object.svala_data['target'] = [el for el in svala_data_object.svala_data['target'] if
                                 el['id'] not in involved_targets[1:]]

    svala_data_object.svala_data['edges'] = {k: v for k, v in svala_data_object.svala_data['edges'].items() if
                                v['id'] not in involved_edges[1:]}
    i -= len(involved_sources[1:])
    return i


def apply_svala_handfixes(svala_data_object):
    hand_fix_mask = []
    for key in SVALA_HAND_FIXES_MERGE.keys():
        if len(key) not in hand_fix_mask:
            hand_fix_mask.append(len(key))

    remember_length = max(hand_fix_mask)
    q = deque()

    i = 0
    prev_tokens = []
    for el in svala_data_object.svala_data['source']:
        q.append(el['text'])
        if len(q) > max(remember_length, 5):
            prev_tokens.append(q.popleft())
        for mask_len in hand_fix_mask:
            list_q = list(q)
            if len(list_q) - mask_len >= 0:
                key = tuple(list_q[remember_length - mask_len:])
                if (len(key) == 2 and len(key[0]) == 1 and key[0].isupper() and key[1] == '.' and (len(prev_tokens) == 0 or prev_tokens[-1] != 'Slovenščina')) or \
                        (len(key) == 2 and key[0].isnumeric() and key[1] in '.%') or \
                        (len(key) == 2 and key[0].isnumeric() and key[1][0] in '.' and key[1][1:].isnumeric()) or \
                        key in SVALA_HAND_FIXES_MERGE:
                    i = merge_svala_data_elements(svala_data_object, i, mask_len)
        i += 1


def apply_obeliks_handfixes(tokenized_paragraph):
    for t_i in range(len(tokenized_paragraph)):
        sen = tokenized_paragraph[t_i]
        i = 0
        error = False
        for idx, tok in enumerate(sen):
            # if tok['text'] == ',,,':
            #     tok['text'] = ','
            if tok['text'] in OBELIKS_HAND_FIXES_MERGE:
                error = True
                break
            elif tok['text'][-1] in '.%' and tok['text'][:-1].isnumeric():
                OBELIKS_HAND_FIXES_MERGE[tok['text']] = [tok['text'][:-1], tok['text'][-1]]
                error = True
                #break
            elif len(tok['text'].strip().split('.')) == 2 and '.' not in (tok['text'][0], tok['text'][-1]):
                nums = tok['text'].split('.')
                if nums[0].isnumeric() and nums[1].isnumeric():
                    OBELIKS_HAND_FIXES_MERGE[tok['text']] = [nums[0], '.', nums[1]]
                    error = True
                    #break
            elif len(tok['text'].split(',')) == 2:
                nums = tok['text'].split(',') # changed
                if nums[0].isnumeric() and nums[1].isnumeric():
                    OBELIKS_HAND_FIXES_MERGE[tok['text']] = [nums[0], ',', nums[1]]
                    error = True
                    #break
            elif len(tok['text'].split('.')) == 3:
                nums = tok['text'].split('.')
                if nums[0].isnumeric() and nums[1].isnumeric() and nums[2].isnumeric():
                    OBELIKS_HAND_FIXES_MERGE[tok['text']] = [nums[0], '.', nums[1], '.', nums[2]]
                    error = True
                    #break
            elif len(tok['text']) == 2 and tok['text'][-1] == '.' and tok['text'][0].isupper():
                OBELIKS_HAND_FIXES_MERGE[tok['text']] = [tok['text'][0], '.']
                error = True
                #break
            elif len(tok['text']) == 3 and tok['text'][0] == '[' and tok['text'][1][0] == tok['text'][1][-1] == 'X' and tok['text'][2] == ']':
                OBELIKS_HAND_FIXES_MERGE[tok['text']] = ['[', tok['text'][1], ']']
                error = True
                #break
            elif len(tok['text']) == 5 and tok['text'][0] == 'X' and tok['text'][1] == '[' and tok['text'][3] == ']' and tok['text'][4] == 'X':
                OBELIKS_HAND_FIXES_MERGE[tok['text']] = ['[', tok['text'][1], ']']
                error = True
            i += 1
        if error:
            new_sen = []
            new_id = 1
            for t in sen:
                if t['text'] in OBELIKS_HAND_FIXES_MERGE:
                    for ex_t in OBELIKS_HAND_FIXES_MERGE[t['text']]:
                        new_sen.append({'id': tuple([new_id]), 'text': ex_t})
                        new_id += 1
                else:
                    new_sen.append({'id': tuple([new_id]), 'text': t['text']})
                    new_id += 1
            tokenized_paragraph[t_i] = new_sen
