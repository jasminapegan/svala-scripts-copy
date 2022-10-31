import argparse
import json
import logging
import os
import pickle
import shutil
import time
import conllu
import classla
import copy

from lxml import etree

from src.annotate.annotate import annotate
from src.create_tei import construct_sentence_from_list, \
    construct_paragraph_from_list, TeiDocument, build_tei_etrees, build_links, build_complete_tei, convert_bibl
from src.read.read_and_merge import tokenize

logging.basicConfig(level=logging.INFO)


def add_edges(source_id, target_id, svala_data, edges, source_token_id, target_token_id):
    edge_id = "e-" + source_id + "-" + target_id
    labels = svala_data['edges'][edge_id]['labels']
    edges.append({'source_ids': [source_token_id], 'target_ids': [target_token_id], 'labels': labels})


def add_token(svala_i, source_i, target_i, el, source, target, edges, svala_data, sentence_string_id):
    source_id = "s" + svala_i
    target_id = "t" + svala_i
    edge_id = "e-" + source_id + "-" + target_id
    labels = svala_data['edges'][edge_id]['labels']
    sentence_string_id_split = sentence_string_id.split('.')
    source_token_id = f'{sentence_string_id_split[0]}s.{".".join(sentence_string_id_split[1:])}.{source_i}'
    target_token_id = f'{sentence_string_id_split[0]}t.{".".join(sentence_string_id_split[1:])}.{target_i}'
    token_tag = 'w' if el.tag.startswith('w') else 'pc'
    lemma = el.attrib['lemma'] if token_tag == 'w' else el.text
    source.append({'token': el.text, 'tag': token_tag, 'ana': el.attrib['ana'], 'lemma': lemma, 'id': source_token_id, 'space_after': False, 'svala_id': source_id})
    target.append({'token': el.text, 'tag': token_tag, 'ana': el.attrib['ana'], 'lemma': lemma, 'id': target_token_id, 'space_after': False, 'svala_id': target_id})
    edges.append({'source_ids': [source_token_id], 'target_ids': [target_token_id], 'labels': labels})


def add_errors(i, error, source, target, edges):
    source_edge_ids = []
    target_edge_ids = []
    podtip = error.attrib['podtip'] if 'podtip' in error.attrib else ''

    label = error.attrib['tip'] + '/' + podtip + '/' + error.attrib['kat']

    labels = [label]

    word_combination_L1 = ''
    word_combination_L2 = None
    word_combination_L3 = None
    word_combination_L4 = None
    word_combination_L5 = None

    label_L2 = ''
    label_L3 = ''
    label_L4 = ''
    label_L5 = ''

    has_error = False

    # solar5.7
    for el in error:
        if el.tag.startswith('w') or el.tag.startswith('pc'):
            ind = str(i)

            source_id = "s" + ind
            source.append({"id": source_id, "text": el.text + " "})
            source_edge_ids.append(source_id)
            i += 1

        elif el.tag.startswith('p'):
            for p_el in el:
                if p_el.tag.startswith('w') or p_el.tag.startswith('pc'):
                    ind = str(i)

                    target_id = "t" + ind
                    target.append({"id": target_id, "text": p_el.text + " "})
                    target_edge_ids.append(target_id)
                    word_combination_L1 += p_el.text + " "
                    i += 1

        elif el.tag.startswith('u2'):
            word_combination_L2 = ''
            podtip = el.attrib['podtip'] if 'podtip' in el.attrib else ''
            label_L2 = el.attrib['tip'] + '/' + podtip + '/' + el.attrib['kat']
            for el_l2 in el:
                if el_l2.tag.startswith('w') or el_l2.tag.startswith('pc'):
                    ind = str(i)

                    source_id = "s" + ind
                    source.append({"id": source_id, "text": el_l2.text + " "})
                    source_edge_ids.append(source_id)
                    i += 1

                elif el_l2.tag.startswith('p'):
                    for p_el_l2 in el_l2:
                        if p_el_l2.tag.startswith('w') or p_el_l2.tag.startswith('pc'):
                            word_combination_L2 += p_el_l2.text + " "


                elif el_l2.tag.startswith('u3'):
                    word_combination_L3 = ''
                    podtip = el_l2.attrib['podtip'] if 'podtip' in el_l2.attrib else ''
                    label_L3 = el_l2.attrib['tip'] + '/' + podtip + '/' + el_l2.attrib['kat']
                    for el_l3 in el_l2:
                        if el_l3.tag.startswith('w') or el_l3.tag.startswith('pc'):
                            ind = str(i)

                            source_id = "s" + ind
                            source.append({"id": source_id, "text": el_l3.text + " "})
                            source_edge_ids.append(source_id)
                            i += 1

                        elif el_l3.tag.startswith('p'):
                            for p_el_l3 in el_l3:
                                if p_el_l3.tag.startswith('w') or p_el_l3.tag.startswith('pc'):
                                    word_combination_L3 += p_el_l3.text + " "

                        elif el_l3.tag.startswith('u4'):
                            word_combination_L4 = ''
                            podtip = el_l3.attrib['podtip'] if 'podtip' in el_l3.attrib else ''
                            label_L4 = el_l3.attrib['tip'] + '/' + podtip + '/' + el_l3.attrib['kat']
                            for el_l4 in el_l3:
                                if el_l4.tag.startswith('w') or el_l4.tag.startswith('pc'):
                                    ind = str(i)

                                    source_id = "s" + ind
                                    source.append({"id": source_id, "text": el_l4.text + " "})
                                    source_edge_ids.append(source_id)
                                    i += 1

                                elif el_l4.tag.startswith('p'):
                                    for p_el_l4 in el_l4:
                                        if p_el_l4.tag.startswith('w') or p_el_l4.tag.startswith('pc'):
                                            word_combination_L4 += p_el_l4.text + " "

                                elif el_l4.tag.startswith('u5'):
                                    word_combination_L5 = ''
                                    podtip = el_l4.attrib['podtip'] if 'podtip' in el_l4.attrib else ''
                                    label_L5 = el_l4.attrib['tip'] + '/' + podtip + '/' + el_l4.attrib['kat']
                                    for el_l5 in el_l4:
                                        if el_l5.tag.startswith('w') or el_l5.tag.startswith('pc'):
                                            ind = str(i)

                                            source_id = "s" + ind
                                            source.append({"id": source_id, "text": el_l5.text + " "})
                                            source_edge_ids.append(source_id)
                                            i += 1

                                        elif el_l5.tag.startswith('p'):
                                            for p_el_l5 in el_l5:
                                                if p_el_l5.tag.startswith('w') or p_el_l5.tag.startswith('pc'):
                                                    word_combination_L5 += p_el_l5.text + " "
            # TODO NOT SURE IF THIS SHOULD BE COMMENTED! IF IT IS NOT THERE ARE ERRORS ON 2ND lvl of errors, where some words are duplicated
            # for p_el in el:
            #     if p_el.tag.startswith('w') or p_el.tag.startswith('pc'):
            #         ind = str(i)
            #
            #         target_id = "t" + ind
            #         target.append({"id": target_id, "text": p_el.text + " "})
            #         target_edge_ids.append(target_id)
            #         i += 1

    if word_combination_L1 == word_combination_L2 and word_combination_L2 is not None:
        if label_L2 not in labels:
            labels.append(label_L2)
        else:
            print(f"REPEATING LABEL - {label_L2} in {error.attrib['{http://www.w3.org/XML/1998/namespace}id']} - ID {i}")
        if word_combination_L1 == word_combination_L3 and word_combination_L3 is not None:
            if label_L3 not in labels:
                labels.append(label_L3)
            else:
                print(f"REPEATING LABEL - {label_L3} in {error.attrib['{http://www.w3.org/XML/1998/namespace}id']} - ID {i}")
            if word_combination_L1 == word_combination_L4 and word_combination_L4 is not None:
                if label_L4 not in labels:
                    labels.append(label_L4)
                else:
                    print(f"REPEATING LABEL - {label_L4} in {error.attrib['{http://www.w3.org/XML/1998/namespace}id']} - ID {i}")
                if word_combination_L1 == word_combination_L5 and word_combination_L5 is not None:
                    if label_L5 not in labels:
                        labels.append(label_L5)
                    else:
                        print(f"REPEATING LABEL - {label_L5} in {error.attrib['{http://www.w3.org/XML/1998/namespace}id']} - ID {i}")
                elif word_combination_L5 is not None:
                    has_error = True
            elif word_combination_L4 is not None:
                has_error = True
        elif word_combination_L3 is not None:
            has_error = True
    elif word_combination_L2 is not None:
        has_error = True
    edge_ids = sorted(source_edge_ids) + sorted(target_edge_ids)
    edge_id = "e-" + "-".join(edge_ids)
    edges[edge_id] = {"id": edge_id, "ids": edge_ids, "labels": labels, "manual": True}

    return i, has_error


def map_svala_solar2(svala_data_part, solar2_paragraph):
    svala_data_i = 0
    for sentence in solar2_paragraph:
        sentence_id = 0
        for tok in sentence:
            # if svala_data_part[svala_data_i]['text'].strip() != tok['token']:
            #     if tok['text'] == '§' and svala_data_part[svala_data_i]['token'].strip() == '§§§':
            #         wierd_sign_count += 1
            #         if wierd_sign_count < 3:
            #             continue
            #         else:
            #             tok['text'] = '§§§'
            #             wierd_sign_count = 0
            #     else:
            #         raise 'Word mismatch!'
            assert svala_data_part[svala_data_i]['text'].strip() == tok['token']
            sentence_id += 1
            tok['svala_id'] = svala_data_part[svala_data_i]['id']
            svala_data_i += 1


def process_file(args):
    if os.path.exists(args.results_folder):
        shutil.rmtree(args.results_folder)
    os.mkdir(args.results_folder)




    # READ AND MERGE svala tokenization, solar2 tokenization and obeliks tokenization
    tokenized_source_divs, tokenized_target_divs, document_edges = tokenize(args)

    # ANNOTATE WITH CLASSLA
    annotated_source_divs, annotated_target_divs = annotate(tokenized_source_divs, tokenized_target_divs, args)

    # GENERATE TEI AND WRITE OUTPUT
    write_tei(annotated_source_divs, annotated_target_divs, document_edges, args)


def main(args):
    process_file(args)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Read already processed xmls, erase entries without examples and limit gigafida examples to 1 per entry.')
    parser.add_argument('--svala_folder', default='data/KOST/svala',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    parser.add_argument('--results_folder', default='data/results/solar3.0',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    parser.add_argument('--raw_text', default='data/KOST/raw',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    parser.add_argument('--tokenization_interprocessing', default='data/processing.tokenization',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    parser.add_argument('--overwrite_tokenization', action='store_true', help='input file in (gz or xml currently). If none, then just database is loaded')
    parser.add_argument('--annotation_interprocessing', default='data/processing.annotation',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    parser.add_argument('--overwrite_annotation', action='store_true', help='input file in (gz or xml currently). If none, then just database is loaded')
    args = parser.parse_args()

    start = time.time()
    main(args)
    logging.info("TIME: {}".format(time.time() - start))
