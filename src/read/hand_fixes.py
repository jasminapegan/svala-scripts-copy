from collections import deque
from constants.svala_hand_fixes_merge import SVALA_HAND_FIXES_MERGE
from constants.obeliks_hand_fixes_merge import OBELIKS_HAND_FIXES_MERGE

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

    remember_length = max(hand_fix_mask, default=0)
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
