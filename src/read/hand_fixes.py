from collections import deque

HAND_FIXES = {'§§§pisala': ['§', '§', '§', 'pisala'], '§§§poldne': ['§', '§', '§', 'poldne'], '§§§o': ['§', '§', '§', 'o'], '§§§mimi': ['§', '§', '§', 'mimi'], '§§§nil': ['§', '§', '§', 'nil'], '§§§ela': ['§', '§', '§', 'ela'], 'sam§§§': ['sam', '§', '§', '§'], 'globač§§§': ['globač', '§', '§', '§'], 'sin.': ['sin', '.'],  '§§§oveduje': ['§', '§', '§', 'oveduje'],  'na§§§': ['na', '§', '§', '§'], '§§§ka§§§': ['§', '§', '§', 'ka', '§', '§', '§'], '§§§e§§§': ['§', '§', '§', 'e', '§', '§', '§'], '§§§': ['§', '§', '§'], 'ljubezni.': ['ljubezni', '.'], '12.': ['12', '.'], '16.': ['16', '.'], 'st.': ['st', '.'], 'S.': ['S', '.'], 'pr.': ['pr', '.'], 'n.': ['n', '.'], '19:30': ['19', ':', '30'], '9.': ['9', '.'], '6:35': ['6', ':', '35'], 'itd.': ['itd', '.'], 'Sv.': ['Sv', '.'], 'npr.': ['npr', '.'], 'sv.': ['sv', '.'], '12:00': ['12', ':', '00'], "sram'vali": ['sram', "'", 'vali'], '18:00': ['18', ':', '00'], 'J.': ['J', '.'], '5:45': ['5', ':', '45'], '17.': ['17', '.'], '9.00h': ['9', '.', '00h'], 'H.': ['H', '.'], '1.': ['1', '.'], '6.': ['6', '.'], '7:10': ['7', ':', '10'], 'g.': ['g', '.'], 'Oz.': ['Oz', '.'], '20:00': ['20', ':', '00'], '17.4.2010': ['17.', '4.', '2010'], 'ga.': ['ga', '.'], 'prof.': ['prof', '.'], '6:45': ['6', ':', '45'], '19.': ['19', '.'], '3.': ['3', '.'], 'tj.': ['tj', '.'], 'Prof.': ['Prof', '.'], '8.': ['8', '.'], '9:18': ['9', ':', '18'], 'ipd.': ['ipd', '.'], '7.': ['7', '.'], 'št.': ['št', '.'], 'oz.': ['oz', '.'], 'R.': ['R', '.'], '13:30': ['13', ':', '30'], '5.': ['5', '.'], '...': ['.', '.', '.'], 'plavali.': ['plavali', '.'], '[XImeX]': ['[', 'XImeX', ']'], '[XimeX]': ['[', 'XimeX', ']'], 'hipoteze:': ['hipoteze', ':'], 'prehrano?': ['prehrano', '?'], '68-letna': ['68', '-', 'letna'], 'pojma:': ['pojma', ':'], '[XKrajX]': ['[', 'XKrajX', ']'], '3/4': ['3', '/', '4'], 'I-phonea': ['I', '-', 'phonea'], 'kredita:': ['kredita', ':'], '[XFakultetaX]': ['[', 'XFakultetaX', ']'], 'športno-eleganten': ['športno', '-', 'eleganten'], '[XStudijskaSmerX]': ['[', 'XStudijskaSmerX', ']'], '[XNaslovX]': ['[', 'XNaslovX', ']'], '(tudi': ['(', 'tudi'], 'kupujem)': ['kupujem', ')'], '[XPriimekX]': ['[', 'XPriimekX', ']'], '[XPodjetjeX]': ['[', 'XPodjetjeX', ']'], 'Zagreb,': ['Zagreb', ','], 'Budimpešto.': ['Budimpešto', '.'], 'žalost.': ['žalost', '.'], '....': ['.', '.', '.', '.'], '[XStevilkaX]': ['[', 'XStevilkaX', ']'], 'e-naslov': ['e', '-', 'naslov'], '[XEnaslovX]': ['[', 'XEnaslovX', ']'], 'e-pošto': ['e', '-', 'pošto'], '[XDatumX]': ['[', 'XDatumX', ']'], 'eno-sobno': ['eno', '-', 'sobno'], 'lgbtq-prijazna': ['lgbtq', '-', 'prijazna'], 'lgbtq-prijaznega': ['lgbtq', '-', 'prijaznega'], 'Covid-19': ['Covid', '-', '19'], ',,,': [',', ',', ','], 'e-maila': ['e', '-', 'maila'], 'T&d': ['T', '&', 'd'], 'Spider-Man': ['Spider', '-', 'Man'], '12-strani': ['12', '-', 'strani'], 'turbo-folk': ['turbo', '-', 'folk'], 'Cp-čkar': ['Cp', '-', 'čkar'], '46-letnik': ['46', '-', 'letnik'], '40-letna': ['40', '-', 'letna'], '18-19h': ['18', '-', '19h'], '[XSvojilniPridevnikX]': ['[', 'XSvojilniPridevnikX', ']'], 'COVID-19': ['COVID', '-', '19'], '"sims"': ['"', 'sims', '"'], '2021/22': ['2021', '/', '22'], '2020/21': ['2020', '/', '21'], 'leto2021/22': ['leto2021', '/', '22'], 'H&m': ['H', '&', 'm'], 'high-street': ['high', '-', 'street'], 'H&M-u': ['H', '&', 'M-u'], 'H&M': ['H', '&', 'M'], 'srčno-žilnih': ['srčno', '-', 'žilnih'], 'srčno-žilni': ['srčno', '-', 'žilni'], ':))': [':)', ')'], 'You-Tube-ju': ['You', '-', 'Tube-ju'], '37,8%': ['37', ',', '8%'], '23,8%': ['23', ',', '8%'], '17,6%': ['17', ',', '6%'], '12,6%': ['12', ',', '6%'], '58,2%': ['58', ',', '2%'], '76,2%': ['76', ',', '2%']}
# , '37,8%': ['37', ',', '8%'], '23,8%': ['23', ',', '8%'], '17,6%': ['17', ',', '6%'], '12,6%': ['12', ',', '6%'], '58,2%': ['58', ',', '2%'], '76,2%': ['76', ',', '2%']
SVALA_HAND_FIXES_MERGE = {('oz', '.'): 'oz.', ('Npr', '.'): 'Npr.', ('npr', '.'): 'npr.', ('1', '.'): '1.', ('2', '.'): '2.', ('3', '.'): '3.', ('m', '.'): 'm.', ('itn', '.'): 'itn.', ('max', '.'): 'max.', ('4', '.'): '4.', ('cca', '.'): 'cca.', ('30', '.'): '30.', ('mlad', '.'): 'mlad.', (':)', ')'): ':))', ('sv', '.'): 'sv.', ('p', '.'): 'p.'}
OBELIKS_HAND_FIXES_MERGE = {'2015.': ['2015', '.']}


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
    for el in svala_data_object.svala_data['source']:
        q.append(el['text'])
        if len(q) > remember_length:
            q.popleft()
        for mask_len in hand_fix_mask:
            list_q = list(q)
            if len(list_q) - mask_len >= 0:
                key = tuple(list_q[remember_length - mask_len:])
                if key in SVALA_HAND_FIXES_MERGE:
                    i = merge_svala_data_elements(svala_data_object, i, mask_len)
        i += 1


def apply_obeliks_handfixes(tokenized_paragraph):
    for t_i in range(len(tokenized_paragraph)):
        sen = tokenized_paragraph[t_i]
        i = 0
        error = False
        for tok in sen:
            # if tok['text'] == ',,,':
            #     tok['text'] = ','
            if tok['text'] in OBELIKS_HAND_FIXES_MERGE:
                error = True
                break
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
