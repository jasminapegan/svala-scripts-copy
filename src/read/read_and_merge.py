import json
import logging
import os
import pickle
import queue
import string
from collections import deque

import classla

from src.read.hand_fixes import apply_svala_handfixes
from src.read.merge import merge, create_conllu, create_edges
from src.read.read import read_raw_text, map_svala_tokenized
from src.read.svala_data import SvalaData

alphabet = list(map(chr, range(97, 123)))

def add_error_token(el, out_list, sentence_string_id, out_list_i, out_list_ids, is_source, s_t_id):
    sentence_string_id_split = sentence_string_id.split('.')

    source_token_id = f'{sentence_string_id_split[0]}s.{".".join(sentence_string_id_split[1:])}.{out_list_i}' if is_source \
        else f'{sentence_string_id_split[0]}t.{".".join(sentence_string_id_split[1:])}.{out_list_i}'
    token_tag = 'w' if el.tag.startswith('w') else 'pc'
    lemma = el.attrib['lemma'] if token_tag == 'w' else el.text
    out_list.append({'token': el.text, 'tag': token_tag, 'ana': el.attrib['ana'], 'lemma': lemma, 'id': source_token_id, 'space_after': False, 'svala_id': s_t_id})
    out_list_ids.append(source_token_id)


def add_errors(svala_i, source_i, target_i, error, source, target, svala_data, sentence_string_id, edges=None):
    source_edge_ids = []
    target_edge_ids = []
    source_ids = []
    target_ids = []

    # solar5.7
    for el in error:
        if el.tag.startswith('w') or el.tag.startswith('pc'):
            ind = str(svala_i)

            source_id = "s" + ind
            source_edge_ids.append(source_id)

            add_error_token(el, source, sentence_string_id, source_i, source_ids, True, source_id)

            source_i += 1
            svala_i += 1

        elif el.tag.startswith('c') and len(source) > 0:
            source[-1]['space_after'] = True

        elif el.tag.startswith('p'):
            for p_el in el:
                if p_el.tag.startswith('w') or p_el.tag.startswith('pc'):
                    ind = str(svala_i)

                    target_id = "t" + ind
                    target_edge_ids.append(target_id)

                    add_error_token(p_el, target, sentence_string_id, target_i, target_ids, False, target_id)

                    target_i += 1
                    svala_i += 1

                elif p_el.tag.startswith('c') and len(target) > 0:
                    target[-1]['space_after'] = True

        elif el.tag.startswith('u2'):
            for el_l2 in el:
                if el_l2.tag.startswith('w') or el_l2.tag.startswith('pc'):
                    ind = str(svala_i)

                    source_id = "s" + ind
                    source_edge_ids.append(source_id)

                    add_error_token(el_l2, source, sentence_string_id, source_i, source_ids, True, source_id)

                    source_i += 1
                    svala_i += 1

                elif el_l2.tag.startswith('c') and len(source) > 0:
                    source[-1]['space_after'] = True

                elif el_l2.tag.startswith('u3'):
                    for el_l3 in el_l2:
                        if el_l3.tag.startswith('w') or el_l3.tag.startswith('pc'):
                            ind = str(svala_i)

                            source_id = "s" + ind
                            source_edge_ids.append(source_id)

                            add_error_token(el_l3, source, sentence_string_id, source_i, source_ids, True, source_id)

                            source_i += 1
                            svala_i += 1

                        elif el_l3.tag.startswith('c') and len(source) > 0:
                            source[-1]['space_after'] = True

                        elif el_l3.tag.startswith('u4'):
                            for el_l4 in el_l3:
                                if el_l4.tag.startswith('w') or el_l4.tag.startswith('pc'):
                                    ind = str(svala_i)

                                    source_id = "s" + ind
                                    source_edge_ids.append(source_id)

                                    add_error_token(el_l4, source, sentence_string_id, source_i, source_ids, True, source_id)

                                    source_i += 1
                                    svala_i += 1
                                elif el_l4.tag.startswith('c') and len(source) > 0:
                                    source[-1]['space_after'] = True

                                elif el_l4.tag.startswith('u5'):
                                    for el_l5 in el_l4:
                                        if el_l5.tag.startswith('w') or el_l5.tag.startswith('pc'):
                                            ind = str(svala_i)

                                            source_id = "s" + ind
                                            source_edge_ids.append(source_id)

                                            add_error_token(el_l5, source, sentence_string_id, source_i, source_ids, True, source_id)

                                            source_i += 1
                                            svala_i += 1
                                        elif el_l5.tag.startswith('c') and len(source) > 0:
                                            source[-1]['space_after'] = True

    if edges is not None:
        edge_ids = sorted(source_edge_ids) + sorted(target_edge_ids)
        edge_id = "e-" + "-".join(edge_ids)
        edges.append({'source_ids': source_ids, 'target_ids': target_ids, 'labels': svala_data['edges'][edge_id]['labels']})

    return svala_i, source_i, target_i


def create_target(svala_data_object, source_tokenized):
    source_tokenized_dict = {}
    for i, sent in enumerate(source_tokenized):
        for tok in sent:
            tok['sent_id'] = i + 1
            source_tokenized_dict[tok['svala_id']] = tok


    links_ids_mapper, edges_of_one_type = svala_data_object.links_ids_mapper, svala_data_object.edges_of_one_type

    curr_sententence = 1
    source_curr_sentence = 1

    target_tokenized = []
    target_sent_tokenized = []
    tok_i = 1

    for i, token in enumerate(svala_data_object.svala_data['target']):
        edge_id = links_ids_mapper[token['id']]
        if len(edge_id) > 1:
            print('Whaat?')
        edge_id = edge_id[0]
        edge = svala_data_object.svala_data['edges'][edge_id]
        source_word_ids = []
        target_word_ids = []
        for word_id in edge['ids']:
            if word_id[0] == 's':
                source_word_ids.append(word_id)
            if word_id[0] == 't':
                target_word_ids.append(word_id)

        token_text = token['text']
        new_sentence = False
        if len(source_word_ids) == 1:
            source_id = source_word_ids[0]
            source_token = source_tokenized_dict[source_id]

            if source_token['sent_id'] != source_curr_sentence:
                source_curr_sentence = source_token['sent_id']
                if source_token['id'] == 1 and len(target_sent_tokenized) > 1:
                    target_tokenized.append(target_sent_tokenized)
                    target_sent_tokenized = []
                    curr_sententence += 1
                    tok_i = 1

            # check if words are equal and update
            if token_text == source_token['token']:
                target_token = {
                    'token': source_token['token'],
                    'tag': source_token['tag'],
                    'id': tok_i,
                    'space_after': source_token['space_after'],
                    'svala_id': token['id'],
                    'sent_id': curr_sententence,
                }
            else:

                # Check for punctuation mismatch.
                if token_text in string.punctuation:
                    tag = 'pc'
                else:
                    tag = 'w'

                target_token = {
                    'token': token_text,
                    'tag': tag,
                    'id': tok_i,
                    'space_after': source_token['space_after'],
                    'svala_id': token['id'],
                    'sent_id': curr_sententence,
                }

        else:
            space_after = True
            if token_text in string.punctuation:
                tag = 'pc'
                if token_text in '!?.,):;]}':
                    if len(target_sent_tokenized) == 0:
                        raise ValueError('Sentence lenght = 0!')
                    target_sent_tokenized[-1]['space_after'] = False
                    if token_text in '!?.':
                        new_sentence = True

                        # Handle cases like `...`
                        if len(svala_data_object.svala_data['target']) > i + 1 and svala_data_object.svala_data['target'][i+1]['text'] in '.?!':
                            new_sentence = False
                elif token_text in '([{':
                    space_after = False
            else:
                tag = 'w'

            target_token = {
                'token': token_text,
                'tag': tag,
                'id': tok_i,
                'space_after': space_after,
                'svala_id': token['id'],
                'sent_id': curr_sententence,
            }
        target_sent_tokenized.append(target_token)
        if new_sentence:
            target_tokenized.append(target_sent_tokenized)
            target_sent_tokenized = []
            curr_sententence += 1
            tok_i = 0
        tok_i += 1
    target_tokenized.append(target_sent_tokenized)
    return target_tokenized


def fake_svala_data(source_tokenized):
    source_res, target_res, generated_edges = [], [], {}

    edge_id = 0
    for sent in source_tokenized:
        source_sent = []
        target_sent = []
        for tok in sent:
            tok_id = tok['id'][0]
            tok_tag = 'w' if 'xpos' not in tok or tok['xpos'] != 'Z' else 'pc'
            source_svala_id = 's' + str(edge_id)
            target_svala_id = 't' + str(edge_id)
            space_after = not ('misc' in tok and tok['misc'] == 'SpaceAfter=No')
            source_sent.append({
                'token': tok['text'],
                'tag': tok_tag,
                'id': tok_id,
                'space_after': space_after,
                'svala_id': source_svala_id
            })
            target_sent.append({
                'token': tok['text'],
                'tag': tok_tag,
                'id': tok_id,
                'space_after': space_after,
                'svala_id': target_svala_id
            })
            generated_edges[f'e-{source_svala_id}-{target_svala_id}'] = {
                'id': f'e-{source_svala_id}-{target_svala_id}',
                'ids': [source_svala_id, target_svala_id],
                'labels': [],
                'manual': False,
                'source_ids': [source_svala_id],
                'target_ids': [target_svala_id]
            }
            edge_id += 1
        source_res.append(source_sent)
        target_res.append(target_sent)


    return source_res, target_res, generated_edges


def tokenize(args):
    if os.path.exists(args.tokenization_interprocessing) and not args.overwrite_tokenization:
        print('READING TOKENIZATION...')
        with open(args.tokenization_interprocessing, 'rb') as rp:
            tokenized_source_divs, tokenized_target_divs, document_edges = pickle.load(rp)
            return tokenized_source_divs, tokenized_target_divs, document_edges

    print('TOKENIZING...')
    nlp_tokenize = classla.Pipeline('sl', processors='tokenize', pos_lemma_pretag=True)
    tokenized_divs = {}

    all_js_filenames = [sorted(filenames) for folder, _, filenames in os.walk(args.svala_folder)][0]

    for text_folder, _, text_filenames in os.walk(args.raw_text):
        text_filenames = sorted(text_filenames)
        for text_filename_i, text_filename in enumerate(text_filenames):
            text_file = read_raw_text(os.path.join(args.raw_text, text_filename))
            raw_text, source_tokenized, metadocument = nlp_tokenize.processors['tokenize']._tokenizer.tokenize(
                text_file) if text_file else ([], [], [])
            source_sent_i = 0

            filenames = [filename for filename in all_js_filenames if filename.startswith(text_filename[:-4])]
            # new_text_filename = '-'.join(filename[:-5].split('-')[:3]) + '.txt'
            if filenames:
                for filename in filenames:
                    svala_path = os.path.join(args.svala_folder, filename)
                    jf = open(svala_path, encoding='utf-8')
                    print(svala_path)
                    svala_data = json.load(jf)
                    jf.close()

                    svala_data_object = SvalaData(svala_data)

                    apply_svala_handfixes(svala_data_object)

                    source_sent_i, source_res = map_svala_tokenized(svala_data_object.svala_data['source'], source_tokenized, source_sent_i)

                    target_res = create_target(svala_data_object, source_res)

                    if text_filename not in tokenized_divs:
                        tokenized_divs[text_filename] = []

                    tokenized_divs[text_filename].append((filename, source_res, target_res, svala_data_object.svala_data['edges']))


            else:
                filename = text_filename[:-4] + '.json'
                source_res, target_res, generated_edges = fake_svala_data(source_tokenized)
                if text_filename not in tokenized_divs:
                    tokenized_divs[text_filename] = []
                tokenized_divs[text_filename].append((filename, source_res, target_res, generated_edges))

            logging.info(f'Tokenizing at {text_filename_i * 100 / len(text_filenames)} %')

    tokenized_source_divs = []
    tokenized_target_divs = []
    document_edges = []

    for div_id in tokenized_divs.keys():
        paragraph_edges = []
        tokenized_source_paragraphs = []
        tokenized_target_paragraphs = []
        for tokenized_para in tokenized_divs[div_id]:
            paragraph_name, source_res, target_res, edges = tokenized_para
            split_para_name = paragraph_name[:-5].split('-')
            div_name = '-'.join(split_para_name[:-1]) if len(split_para_name) == 4 else '-'.join(split_para_name)
            par_name = split_para_name[-1] if len(split_para_name) == 4 else '1'
            assert not par_name.isnumeric() or par_name not in alphabet, Exception('Incorrect paragraph name!')
            if par_name in alphabet:
                par_name = str(alphabet.index(par_name) + 10)

            source_paragraphs = []
            target_paragraphs = []
            sen_source = []
            sen_target = []
            for sen_i, sen in enumerate(source_res):
                source_sen_name = f'{div_name}s.{par_name}.{str(sen_i + 1)}'
                source_conllu = create_conllu(sen, source_sen_name)
                source_paragraphs.append(source_conllu)
                sen_source.append((sen, source_sen_name))

            for sen_i, sen in enumerate(target_res):
                target_sen_name = f'{div_name}t.{par_name}.{str(sen_i + 1)}'
                target_conllu = create_conllu(sen, target_sen_name)
                target_paragraphs.append(target_conllu)
                sen_target.append((sen, target_sen_name))
            tokenized_source_paragraphs.append((par_name, source_paragraphs))
            tokenized_target_paragraphs.append((par_name, target_paragraphs))
            paragraph_edges.append(create_edges(edges, sen_source, sen_target))

        tokenized_source_divs.append((div_name+'s', tokenized_source_paragraphs))
        tokenized_target_divs.append((div_name+'t', tokenized_target_paragraphs))

        document_edges.append(paragraph_edges)

    with open(args.tokenization_interprocessing, 'wb') as wp:
        pickle.dump((tokenized_source_divs, tokenized_target_divs, document_edges), wp)

    return tokenized_source_divs, tokenized_target_divs, document_edges
