import argparse
import json
import logging
import os
import shutil
import time
from xml.etree import ElementTree
from conllu import TokenList
import conllu
import classla
import copy
from classla.pipeline.tokenize_processor import TokenizeProcessor

from lxml import etree

from src.create_tei import construct_sentence_from_list, \
    construct_paragraph_from_list, TeiDocument, build_tei_etrees, build_links, build_complete_tei, convert_bibl

logging.basicConfig(level=logging.INFO)


def add_source(svala_i, source_i, sentence_string_id_split, source, el):
    source_id = "s" + svala_i
    source_token_id = f'{sentence_string_id_split[0]}s.{".".join(sentence_string_id_split[1:])}.{source_i}'
    token_tag = 'w' if el.tag.startswith('w') else 'pc'
    source.append({'token': el.text, 'tag': token_tag, 'ana': el.attrib['ana'], 'id': source_token_id,
                   'space_after': False, 'svala_id': source_id})

def add_target(svala_i, target_i, sentence_string_id_split, target, el):
    target_id = "t" + svala_i
    target_token_id = f'{sentence_string_id_split[0]}t.{".".join(sentence_string_id_split[1:])}.{target_i}'
    token_tag = 'w' if el.tag.startswith('w') else 'pc'
    target.append({'token': el.text, 'tag': token_tag, 'ana': el.attrib['ana'], 'id': target_token_id,
                   'space_after': False, 'svala_id': target_id})

def add_edges(source_id, target_id, svala_data, edges, source_token_id, target_token_id):
    edge_id = "e-" + source_id + "-" + target_id
    labels = svala_data['edges'][edge_id]['labels']
    edges.append({'source_ids': [source_token_id], 'target_ids': [target_token_id], 'labels': labels})

def create_edges(svala_data, source_par, target_par):
    source_mapper = {el['svala_id']: el['id'] for source in source_par for el in source}
    target_mapper = {el['svala_id']: el['id'] for target in target_par for el in target}

    source_ids = [el['svala_id'] for source in source_par for el in source]
    target_ids = [el['svala_id'] for target in target_par for el in target]

    source_sentence_ids = [set([el['svala_id'] for el in source]) for source in source_par]
    target_sentence_ids = [set([el['svala_id'] for el in target]) for target in target_par]

    # create links to ids mapper
    links_ids_mapper = {}
    edges_of_one_type = set()
    for k, v in svala_data['edges'].items():
        has_source = False
        has_target = False
        for el in v['ids']:
            # create edges of one type
            if el[0] == 's':
                has_source = True
            if el[0] == 't':
                has_target = True

            # create links_ids_mapper
            if el not in links_ids_mapper:
                links_ids_mapper[el] = []
            links_ids_mapper[el].append(k)
        if not has_source or not has_target:
            edges_of_one_type.add(k)


    # create edge order
    edges_order = []
    edges_processed = set()
    s_i = 0
    t_i = 0
    check_s_i = True
    while s_i < len(source_ids) or t_i < len(target_ids):
        # take care of getting ids over desired s_i/t_i
        if check_s_i and s_i >= len(source_ids):
            check_s_i = False

        if not check_s_i and t_i >= len(target_ids):
            check_s_i = True

        if check_s_i:
            id_of_interest = source_ids[s_i]
            s_i += 1
            check_s_i = not check_s_i
        else:
            id_of_interest = target_ids[t_i]
            t_i += 1
            check_s_i = not check_s_i

        any_addition = False
        if id_of_interest not in links_ids_mapper:
            print('NOOOOO')
        for edge_id in links_ids_mapper[id_of_interest]:
            if edge_id not in edges_processed and edge_id not in edges_of_one_type:
                any_addition = True
                edges_order.append(edge_id)
                edges_processed.add(edge_id)
        if not any_addition:
            check_s_i = not check_s_i

    sentence_edges = []
    source_sent_id = 0
    target_sent_id = 0
    # actually add edges
    edges = []
    for edge_id in edges_order:
        labels = svala_data['edges'][edge_id]['labels']
        source_ids = [source_mapper[el] for el in svala_data['edges'][edge_id]['ids'] if el in source_mapper]
        target_ids = [target_mapper[el] for el in svala_data['edges'][edge_id]['ids'] if el in target_mapper]
        ids = svala_data['edges'][edge_id]['ids']

        source_ok = [el[0] == 't' or el in source_sentence_ids[source_sent_id] for el in ids] if source_sentence_ids else []
        source_ok_all = all(source_ok)

        if not source_ok_all:
            source_sent_id += 1

        target_ok = [el[0] == 's' or el in target_sentence_ids[target_sent_id] for el in ids] if target_sentence_ids else []
        target_ok_all = all(target_ok)

        if not target_ok_all:
            target_sent_id += 1

        if not source_ok_all or not target_ok_all:
            sentence_edges.append(edges)
            edges = []
        edges.append({'source_ids': source_ids, 'target_ids': target_ids, 'labels': labels})

    return sentence_edges

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


def add_error_token(el, out_list, sentence_string_id, out_list_i, out_list_ids, is_source, s_t_id):
    sentence_string_id_split = sentence_string_id.split('.')

    source_token_id = f'{sentence_string_id_split[0]}s.{".".join(sentence_string_id_split[1:])}.{out_list_i}' if is_source \
        else f'{sentence_string_id_split[0]}t.{".".join(sentence_string_id_split[1:])}.{out_list_i}'
    token_tag = 'w' if el.tag.startswith('w') else 'pc'
    lemma = el.attrib['lemma'] if token_tag == 'w' else el.text
    out_list.append({'token': el.text, 'tag': token_tag, 'ana': el.attrib['ana'], 'lemma': lemma, 'id': source_token_id, 'space_after': False, 'svala_id': s_t_id})
    out_list_ids.append(source_token_id)


def add_error_token_source_target_only(el, out_list, sentence_string_id, out_list_i, is_source, s_t_id):
    sentence_string_id_split = sentence_string_id.split('.')

    source_token_id = f'{sentence_string_id_split[0]}s.{".".join(sentence_string_id_split[1:])}.{out_list_i}' if is_source \
        else f'{sentence_string_id_split[0]}t.{".".join(sentence_string_id_split[1:])}.{out_list_i}'
    token_tag = 'w' if el.tag.startswith('w') else 'pc'
    out_list.append({'token': el.text, 'tag': token_tag, 'ana': el.attrib['ana'], 'id': source_token_id, 'space_after': False, 'svala_id': s_t_id})


def add_errors1_0_1(svala_i, source_i, target_i, error, source, target, svala_data, sentence_string_id, edges=None):
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

            # TODO NOT SURE IF THIS SHOULD BE COMMENTED! IF IT IS NOT THERE ARE ERRORS ON 2ND lvl of errors, where some words are duplicated
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

    if edges is not None:
        edge_ids = sorted(source_edge_ids) + sorted(target_edge_ids)
        edge_id = "e-" + "-".join(edge_ids)
        edges.append({'source_ids': source_ids, 'target_ids': target_ids, 'labels': svala_data['edges'][edge_id]['labels']})

    return svala_i, source_i, target_i


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

            # TODO NOT SURE IF THIS SHOULD BE COMMENTED! IF IT IS NOT THERE ARE ERRORS ON 2ND lvl of errors, where some words are duplicated
            # for p_el in el:
            #     if p_el.tag.startswith('w') or p_el.tag.startswith('pc'):
            #         ind = str(svala_i)
            #
            #         target_id = "t" + ind
            #         target_edge_ids.append(target_id)
            #
            #         add_error_token(p_el, target, sentence_string_id, target_i, target_ids, False)
            #
            #         target_i += 1
            #         svala_i += 1
            #     elif p_el.tag.startswith('c') and len(target) > 0:
            #         target[-1]['space_after'] = True

    if edges is not None:
        edge_ids = sorted(source_edge_ids) + sorted(target_edge_ids)
        edge_id = "e-" + "-".join(edge_ids)
        edges.append({'source_ids': source_ids, 'target_ids': target_ids, 'labels': svala_data['edges'][edge_id]['labels']})

    return svala_i, source_i, target_i


def add_errors_source_target_only(svala_i, source_i, target_i, error, source, target, svala_data, sentence_string_id):
    # solar5.7
    for el in error:
        if el.tag.startswith('w') or el.tag.startswith('pc'):
            ind = str(svala_i)

            source_id = "s" + ind

            add_error_token_source_target_only(el, source, sentence_string_id, source_i, True, source_id)

            source_i += 1
            svala_i += 1

        elif el.tag.startswith('c') and len(source) > 0:
            source[-1]['space_after'] = True

        elif el.tag.startswith('p'):
            for p_el in el:
                if p_el.tag.startswith('w') or p_el.tag.startswith('pc'):
                    ind = str(svala_i)

                    target_id = "t" + ind

                    add_error_token_source_target_only(p_el, target, sentence_string_id, target_i, False, target_id)

                    target_i += 1
                    svala_i += 1

                elif p_el.tag.startswith('c') and len(target) > 0:
                    target[-1]['space_after'] = True

        elif el.tag.startswith('u2'):
            for el_l2 in el:
                if el_l2.tag.startswith('w') or el_l2.tag.startswith('pc'):
                    ind = str(svala_i)

                    source_id = "s" + ind

                    add_error_token_source_target_only(el_l2, source, sentence_string_id, source_i, True, source_id)

                    source_i += 1
                    svala_i += 1

                elif el_l2.tag.startswith('c') and len(source) > 0:
                    source[-1]['space_after'] = True

                elif el_l2.tag.startswith('u3'):
                    for el_l3 in el_l2:
                        if el_l3.tag.startswith('w') or el_l3.tag.startswith('pc'):
                            ind = str(svala_i)

                            source_id = "s" + ind

                            add_error_token_source_target_only(el_l3, source, sentence_string_id, source_i, True, source_id)

                            source_i += 1
                            svala_i += 1

                        elif el_l3.tag.startswith('c') and len(source) > 0:
                            source[-1]['space_after'] = True

                        elif el_l3.tag.startswith('u4'):
                            for el_l4 in el_l3:
                                if el_l4.tag.startswith('w') or el_l4.tag.startswith('pc'):
                                    ind = str(svala_i)

                                    source_id = "s" + ind

                                    add_error_token_source_target_only(el_l4, source, sentence_string_id, source_i, True, source_id)

                                    source_i += 1
                                    svala_i += 1
                                elif el_l4.tag.startswith('c') and len(source) > 0:
                                    source[-1]['space_after'] = True

                                elif el_l4.tag.startswith('u5'):
                                    for el_l5 in el_l4:
                                        if el_l5.tag.startswith('w') or el_l5.tag.startswith('pc'):
                                            ind = str(svala_i)

                                            source_id = "s" + ind

                                            add_error_token_source_target_only(el_l5, source, sentence_string_id, source_i, True, source_id)

                                            source_i += 1
                                            svala_i += 1
                                        elif el_l5.tag.startswith('c') and len(source) > 0:
                                            source[-1]['space_after'] = True

            # TODO NOT SURE IF THIS SHOULD BE COMMENTED! IF IT IS NOT THERE ARE ERRORS ON 2ND lvl of errors, where some words are duplicated
            for p_el in el:
                if p_el.tag.startswith('w') or p_el.tag.startswith('pc'):
                    ind = str(svala_i)

                    target_id = "t" + ind

                    add_error_token_source_target_only(p_el, target, sentence_string_id, target_i, False, target_id)

                    target_i += 1
                    svala_i += 1
                elif p_el.tag.startswith('c') and len(target) > 0:
                    target[-1]['space_after'] = True

    # edge_ids = sorted(source_edge_ids) + sorted(target_edge_ids)
    # edge_id = "e-" + "-".join(edge_ids)
    # edges.append({'source_ids': source_ids, 'target_ids': target_ids, 'labels': svala_data['edges'][edge_id]['labels']})

    return svala_i, source_i, target_i


def create_conllu(interest_list, sentence_string_id):
    conllu_result = TokenList([{"id": token_i + 1, "form": token['token'], "lemma": None, "upos": None, "xpos": None, "feats": None,
                "head": None, "deprel": None, "deps": None, "misc": "SpaceAfter=No"} if not token['space_after']
               else {"id": token_i + 1, "form": token['token'], "lemma": None, "upos": None, "xpos": None,
                     "feats": None, "head": None, "deprel": None, "deps": None, "misc": None} for token_i, token in
               enumerate(interest_list)])
    # Delete last SpaceAfter
    misc = conllu_result[len(conllu_result) - 1]['misc'] if len(conllu_result) > 0 else None
    if misc is not None:
        misc_split = misc.split('|')
        if misc is not None and misc == 'SpaceAfter=No':
            conllu_result[len(conllu_result) - 1]['misc'] = None
        elif misc is not None and 'SpaceAfter=No' in misc_split:
            conllu_result[len(conllu_result) - 1]['misc'] = '|'.join([el for el in misc_split if el != 'SpaceAfter=No'])
    conllu_result.metadata = {"sent_id": sentence_string_id}

    return conllu_result.serialize()


def process_solar2_paragraph(sentences, paragraph, svala_i, svala_data, add_errors_func, nlp, complete_source_conllu, complete_target_conllu):
    etree_source_sentences = []
    etree_target_sentences = []

    sentence_edges = []

    par_source = []
    par_target = []

    for sentence_id, sentence in enumerate(sentences):
        source = []
        target = []
        edges = []

        sentence_id += 1
        source_i = 1
        target_i = 1
        sentence_string_id = paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id'] + f'.{sentence_id}'
        for el in sentence:
            if el.tag.startswith('w'):
                add_token(str(svala_i), source_i, target_i, el, source, target, edges, svala_data, sentence_string_id)
                svala_i += 1
                source_i += 1
                target_i += 1
            elif el.tag.startswith('pc'):
                add_token(str(svala_i), source_i, target_i, el, source, target, edges, svala_data, sentence_string_id)
                svala_i += 1
                source_i += 1
                target_i += 1
            elif el.tag.startswith('u'):
                svala_i, source_i, target_i = add_errors_func(svala_i, source_i, target_i, el, source, target,
                                                              svala_data, sentence_string_id)
            elif el.tag.startswith('c'):
                if len(source) > 0:
                    source[-1]['space_after'] = True
                if len(target) > 0:
                    target[-1]['space_after'] = True

        par_source.append(source)
        par_target.append(target)

        # sentence_edges.append(edges)
        if len(source) > 0:
            source_conllu = create_conllu(source, sentence_string_id)
        if len(target) > 0:
            target_conllu = create_conllu(target, sentence_string_id)

        if len(source) > 0:
            source_conllu_annotated = nlp(source_conllu).to_conll()
        if len(target) > 0:
            target_conllu_annotated = nlp(target_conllu).to_conll()

        if len(source) > 0:
            complete_source_conllu += source_conllu_annotated
        if len(target) > 0:
            complete_target_conllu += target_conllu_annotated

        if len(source) > 0:
            source_conllu_parsed = conllu.parse(source_conllu_annotated)[0]
        if len(target) > 0:
            target_conllu_parsed = conllu.parse(target_conllu_annotated)[0]

        if len(source) > 0:
            etree_source_sentences.append(construct_sentence_from_list(str(sentence_id), source_conllu_parsed, True))
        if len(target) > 0:
            etree_target_sentences.append(construct_sentence_from_list(str(sentence_id), target_conllu_parsed, False))

    sentence_edges = create_edges(svala_data, par_source, par_target)

    return etree_source_sentences, etree_target_sentences, sentence_edges


def read_raw_text(path):
    with open(path, 'r') as rf:
        return rf.read()

def map_svala_tokenized(svala_data_part, tokenized_paragraph):
    paragraph_res = []
    svala_data_i = 0
    wierd_sign_count = 0
    for sentence in tokenized_paragraph:
        sentence_res = []
        sentence_id = 0
        for tok in sentence:
            tag = 'pc' if 'xpos' in tok and tok['xpos'] == 'Z' else 'w'
            if 'misc' in tok:
                assert tok['misc'] == 'SpaceAfter=No'
            space_after = not 'misc' in tok
            if svala_data_part[svala_data_i]['text'].strip() != tok['text']:
                if tok['text'] == '§' and svala_data_part[svala_data_i]['text'].strip() == '§§§':
                    wierd_sign_count += 1
                    if wierd_sign_count < 3:
                        continue
                    else:
                        tok['text'] = '§§§'
                        wierd_sign_count = 0
                else:
                    raise 'Word mismatch!'
            sentence_id += 1
            sentence_res.append({'token': tok['text'], 'tag': tag, 'id': sentence_id, 'space_after': space_after, 'svala_id': svala_data_part[svala_data_i]['id']})
            svala_data_i += 1
        paragraph_res.append(sentence_res)
    return paragraph_res


def map_svala_solar2(svala_data_part, solar2_paragraph):
    paragraph_res = []
    svala_data_i = 0
    wierd_sign_count = 0
    for sentence in solar2_paragraph:
        sentence_res = []
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


def update_ids(pretag, in_list):
    for el in in_list:
        el['id'] = f'{pretag}.{el["id"]}'


def process_obeliks_paragraph(sentences, paragraph, svala_i, svala_data, add_errors_func, nlp, complete_source_conllu, complete_target_conllu, source_raw_text, target_raw_text, nlp_tokenize):
    etree_source_sentences = []
    etree_target_sentences = []

    sentence_edges = []
    if source_raw_text is not None:
        text = read_raw_text(source_raw_text)
        raw_text, source_tokenized, metadocument = nlp_tokenize.processors['tokenize']._tokenizer.tokenize(text) if text else [], [], []
        # source_tokenized = nlp_tokenize()
        source_res = map_svala_tokenized(svala_data['source'], source_tokenized)

    if target_raw_text is not None:
        text = read_raw_text(target_raw_text)
        raw_text, target_tokenized, metadocument = nlp_tokenize.processors['tokenize']._tokenizer.tokenize(text) if text else [], [], []
        target_res = map_svala_tokenized(svala_data['target'], target_tokenized)

    # TODO RETURN IF SOURCE AND TARGET ARE NOT NONE
    par_source = []
    par_target = []
    sentences_len = len(sentences)
    if source_raw_text is not None:
        sentences_len = max(sentences_len, len(source_res))
    if target_raw_text is not None:
        sentences_len = max(sentences_len, len(target_res))
    for sentence_id in range(sentences_len):
        # assert sentence_id < len(sentences)

        # sentence_id += 1
    # for sentence_id, sentence in enumerate(sentences):
        source = []
        target = []
        sentence_id += 1
        source_i = 1
        target_i = 1
        sentence_string_id = paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id'] + f'.{sentence_id}'
        sentence_string_id_split = sentence_string_id.split('.')

        if sentence_id - 1 < len(sentences):
            sentence = sentences[sentence_id - 1]
            for el in sentence:
                # if source_i == 101:
                #     print('HMM')
                if el.tag.startswith('w'):
                    if source_raw_text is None:
                        add_source(str(svala_i), source_i, sentence_string_id_split, source, el)
                    if target_raw_text is None:
                        add_target(str(svala_i), target_i, sentence_string_id_split, target, el)
                    # add_edges(source_id, target_id, svala_data, edges, source_token_id, target_token_id)

                    svala_i += 1
                    source_i += 1
                    target_i += 1
                elif el.tag.startswith('pc'):
                    if source_raw_text is None:
                        add_source(str(svala_i), source_i, sentence_string_id_split, source, el)
                    if target_raw_text is None:
                        add_target(str(svala_i), target_i, sentence_string_id_split, target, el)
                    # add_edges(source_id, target_id, svala_data, edges, source_token_id, target_token_id)

                    svala_i += 1
                    source_i += 1
                    target_i += 1
                elif el.tag.startswith('u'):
                    if source_raw_text is None or target_raw_text is None:
                        svala_i, source_i, target_i = add_errors_source_target_only(svala_i, source_i, target_i, el, source, target, svala_data, sentence_string_id)
                    else:
                        svala_i, source_i, target_i = add_errors_func(svala_i, source_i, target_i, el, source, target,
                                                                      svala_data, sentence_string_id)
                elif el.tag.startswith('c'):
                    if len(source) > 0:
                        source[-1]['space_after'] = True
                    if len(target) > 0:
                        target[-1]['space_after'] = True

        if source_raw_text is not None and sentence_id - 1 < len(source_res):
            source = source_res[sentence_id - 1]
            update_ids(f'{sentence_string_id_split[0]}s.{".".join(sentence_string_id_split[1:])}', source)
            par_source.append(source)
        if len(source) > 0:
            source_conllu = create_conllu(source, sentence_string_id)
        if target_raw_text is not None and sentence_id - 1 < len(target_res):
            target = target_res[sentence_id - 1]
            update_ids(f'{sentence_string_id_split[0]}t.{".".join(sentence_string_id_split[1:])}', target)
            par_target.append(target)

        if source_raw_text is None:
            par_source.append(source)
        if target_raw_text is None:
            par_target.append(target)

        if len(target) > 0:
            target_conllu = create_conllu(target, sentence_string_id)

        if len(source) > 0:
            source_conllu_annotated = nlp(source_conllu).to_conll()
        if len(target) > 0:
            target_conllu_annotated = nlp(target_conllu).to_conll()

        if len(source) > 0:
            complete_source_conllu += source_conllu_annotated
        if len(target) > 0:
            complete_target_conllu += target_conllu_annotated

        if len(source) > 0:
            source_conllu_parsed = conllu.parse(source_conllu_annotated)[0]
        if len(target) > 0:
            target_conllu_parsed = conllu.parse(target_conllu_annotated)[0]

        if len(source) > 0:
            etree_source_sentences.append(construct_sentence_from_list(str(sentence_id), source_conllu_parsed, True))
        if len(target) > 0:
            etree_target_sentences.append(construct_sentence_from_list(str(sentence_id), target_conllu_parsed, False))

    # reannotate svala_ids
    if source_raw_text is None:
        map_svala_solar2(svala_data['source'], par_source)
    if target_raw_text is None:
        map_svala_solar2(svala_data['target'], par_target)

    sentence_edges = create_edges(svala_data, par_source, par_target)

    return etree_source_sentences, etree_target_sentences, sentence_edges

def process_file(et, args, nlp, nlp_tokenize):
    if os.path.exists(args.results_folder):
        shutil.rmtree(args.results_folder)
    os.mkdir(args.results_folder)
    etree_source_documents = []
    etree_target_documents = []
    etree_source_divs = []
    etree_target_divs = []

    complete_source_conllu = ''
    complete_target_conllu = ''

    document_edges = []
    filename_encountered = False
    i = 0
    folders_count = 5484
    for div in et.iter('div'):
        bibl = div.find('bibl')
        file_name = bibl.get('n')
        file_name = file_name.replace('/', '_')
        print(f'{i*100/folders_count} % : {file_name}')
        i += 1
        # if file_name == 'S20-PI-slo-2-SG-D-2016_2017-30479-12.txt':
        #     filename_encountered = True
        # if not filename_encountered:
        #     continue

        svala_path = os.path.join(args.svala_folder, file_name)
        corrected_svala_path = os.path.join(args.corrected_svala_folder, file_name)
        raw_texts_path = os.path.join(args.svala_generated_text_folder, file_name)
        # skip files that are not svala annotated (to enable short examples)
        if not os.path.isdir(svala_path):
            continue

        svala_list = [[fname[:-13], fname] if 'problem' in fname else [fname[:-5], fname] for fname in os.listdir(svala_path)]
        svala_dict = {e[0]: e[1] for e in svala_list}

        if os.path.exists(corrected_svala_path):
            corrected_svala_list = [[fname[:-13], fname] if 'problem' in fname else [fname[:-5], fname] for fname in os.listdir(corrected_svala_path)]
            corrected_svala_dict = {e[0]: e[1] for e in corrected_svala_list}

            svala_dict.update(corrected_svala_dict)

        etree_source_paragraphs = []
        etree_target_paragraphs = []
        paragraph_edges = []

        paragraphs = div.findall('p')
        for paragraph in paragraphs:
            sentences = paragraph.findall('s')
            svala_i = 1

            # read json
            # if paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id'] == 'solar5.7':
            #     print('here')
            svala_file = os.path.join(svala_path, svala_dict[paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id']])
            corrected_svala_file = os.path.join(corrected_svala_path, svala_dict[paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id']])
            # if os.path.exists(corrected_svala_file):
            #     print('aaa')
            add_errors_func = add_errors if not os.path.exists(corrected_svala_file) else add_errors1_0_1
            jf = open(svala_file) if not os.path.exists(corrected_svala_file) else open(corrected_svala_file)
            svala_data = json.load(jf)
            jf.close()

            source_filename = svala_dict[paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id']][:-5] + '_source.json'
            target_filename = svala_dict[paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id']][:-5] + '_target.json'

            source_raw_text = os.path.join(raw_texts_path, source_filename) if os.path.exists(os.path.join(raw_texts_path, source_filename)) else None
            target_raw_text = os.path.join(raw_texts_path, target_filename) if os.path.exists(os.path.join(raw_texts_path, target_filename)) else None

            if not (source_raw_text or target_raw_text):
                etree_source_sentences, etree_target_sentences, sentence_edges = process_solar2_paragraph(sentences, paragraph, svala_i, svala_data, add_errors_func, nlp,
                                         complete_source_conllu, complete_target_conllu)

            else:
                etree_source_sentences, etree_target_sentences, sentence_edges = process_obeliks_paragraph(sentences, paragraph, svala_i,
                                                                                                          svala_data, add_errors_func, nlp, complete_source_conllu, complete_target_conllu, source_raw_text, target_raw_text, nlp_tokenize)

            etree_source_paragraphs.append(construct_paragraph_from_list(paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id'].split('.')[0], paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id'].split('.')[1], etree_source_sentences, True))
            etree_target_paragraphs.append(construct_paragraph_from_list(paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id'].split('.')[0], paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id'].split('.')[1], etree_target_sentences, False))
            paragraph_edges.append(sentence_edges)

        etree_bibl = convert_bibl(bibl)

        etree_source_divs.append((etree_source_paragraphs, copy.deepcopy(etree_bibl)))
        etree_target_divs.append((etree_target_paragraphs, copy.deepcopy(etree_bibl)))
        document_edges.append(paragraph_edges)

    print('APPENDING DOCUMENT...')
    etree_source_documents.append(TeiDocument(paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id'].split('.')[0] + 's', etree_source_divs))
    etree_target_documents.append(TeiDocument(paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id'].split('.')[0] + 't', etree_target_divs))

    print('BUILDING TEI DOCUMENTS...')
    etree_source = build_tei_etrees(etree_source_documents)
    etree_target = build_tei_etrees(etree_target_documents)

    print('BUILDING LINKS...')
    etree_links = build_links(document_edges)

    print('BUILDING COMPLETE TEI...')
    complete_etree = build_complete_tei(copy.deepcopy(etree_source), copy.deepcopy(etree_target), etree_links)

    print('WRITING FILES')
    with open(os.path.join(args.results_folder, f"source.conllu"), 'w') as sf:
        sf.write(complete_source_conllu)

    with open(os.path.join(args.results_folder, f"target.conllu"), 'w') as sf:
        sf.write(complete_target_conllu)

    with open(os.path.join(args.results_folder, f"source.xml"), 'w') as sf:
        sf.write(etree.tostring(etree_source[0], pretty_print=True, encoding='utf-8').decode())

    with open(os.path.join(args.results_folder, f"target.xml"), 'w') as tf:
        tf.write(etree.tostring(etree_target[0], pretty_print=True, encoding='utf-8').decode())

    with open(os.path.join(args.results_folder, f"links.xml"), 'w') as tf:
        tf.write(etree.tostring(etree_links, pretty_print=True, encoding='utf-8').decode())

    with open(os.path.join(args.results_folder, f"complete.xml"), 'w') as tf:
        tf.write(etree.tostring(complete_etree, pretty_print=True, encoding='utf-8').decode())

    with open(os.path.join(args.results_folder, f"links.json"), 'w') as jf:
        json.dump(document_edges, jf, ensure_ascii=False, indent="  ")


def main(args):
    with open(args.solar_file, 'r') as fp:
        logging.info(args.solar_file)
        nlp = classla.Pipeline('sl', pos_use_lexicon=True, pos_lemma_pretag=False, tokenize_pretokenized="conllu", type='standard_jos')
        nlp_tokenize = classla.Pipeline('sl', processors='tokenize', pos_lemma_pretag=True)
        et = ElementTree.XML(fp.read())
        process_file(et, args, nlp, nlp_tokenize)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Read already processed xmls, erase entries without examples and limit gigafida examples to 1 per entry.')
    parser.add_argument('--solar_file', default='data/Solar2.0/solar2.xml',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    parser.add_argument('--svala_folder', default='data/solar.svala',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    parser.add_argument('--corrected_svala_folder', default='data/solar.svala.fixed.1.0.1_2',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    parser.add_argument('--results_folder', default='data/results/solar3.0',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    parser.add_argument('--svala_generated_text_folder', default='data/svala_generated_text.formatted',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    args = parser.parse_args()

    start = time.time()
    main(args)
    logging.info("TIME: {}".format(time.time() - start))
