import argparse
import json
import logging
import os
import pickle
import shutil
import time
from xml.etree import ElementTree
from conllu import TokenList
import conllu
import classla
import copy

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


def create_edges_list(target_ids, links_ids_mapper):
    target_edges = []
    target_edges_set = []
    for target_sentence in target_ids:
        target_sentence_edges = []
        for target_id in target_sentence:
            target_sentence_edges.extend(links_ids_mapper[target_id])
        target_edges.append(target_sentence_edges)
        target_edges_set.append(set(target_sentence_edges))

    return target_edges, target_edges_set


SKIP_IDS = ['solar2284s.1.1.1']

def create_edges(svala_data, source_par, target_par):
    if source_par and source_par[0]:
        if source_par[0][0]['id'] in SKIP_IDS:
            return []
        # print(source_par[0][0]['id'])
        # if source_par[0][0]['id'] == 'solar2150s.4.14.1':
        #     print('pause!')
    # if target_par and target_par[0]:
    #     print(target_par[0][0]['id'])
    #     if target_par[0][0]['id'] == 'solar2150t.4.1.1':
    #         print('pause!')
    source_mapper = {el['svala_id']: el['id'] for source in source_par for el in source}
    target_mapper = {el['svala_id']: el['id'] for target in target_par for el in target}

    source_ids = [[el['svala_id'] for el in source] for source in source_par]
    target_ids = [[el['svala_id'] for el in target] for target in target_par]

    source_sentence_ids = [set([el['svala_id'] for el in source]) for source in source_par]
    target_sentence_ids = [set([el['svala_id'] for el in target]) for target in target_par]

    # create links to ids mapper
    links_ids_mapper = {}
    edges_of_one_type = set()

    # delete empty edge
    if 'e-' in svala_data['edges']:
        del (svala_data['edges']['e-'])

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
        if not has_source or not has_target or (len(svala_data['source']) == 1 and svala_data['source'][0]['text'] == ' ') \
                or (len(svala_data['target']) == 1 and svala_data['target'][0]['text'] == ' '):
            edges_of_one_type.add(k)

    # delete edge with space
    save_deleted_edges = {}
    if len(svala_data['source']) == 1 and svala_data['source'][0]['text'] == ' ':
        for edg in links_ids_mapper[svala_data['source'][0]['id']]:
            save_deleted_edges[edg] = svala_data['edges'][edg]
            del (svala_data['edges'][edg])
            del (links_ids_mapper[svala_data['source'][0]['id']])
    if len(svala_data['target']) == 1 and svala_data['target'][0]['text'] == ' ':
        for edg in links_ids_mapper[svala_data['target'][0]['id']]:
            save_deleted_edges[edg] = svala_data['edges'][edg]
            del (svala_data['edges'][edg])
            del (links_ids_mapper[svala_data['target'][0]['id']])

    # create edge order
    edges_order = []
    edges_processed = set()
    active_target_sentence_i = 0

    # create target edges
    target_edges, target_edges_set = create_edges_list(target_ids, links_ids_mapper)
    source_edges, source_edges_set = create_edges_list(source_ids, links_ids_mapper)

    last_target_edge = ''

    for active_source_sentence_i, active_source_sentence in enumerate(source_edges):
        for source_edge in active_source_sentence:
            # print(source_edge)
            # if 'e-s7-t8' == source_edge:
            #     print('aaa')
            if source_edge in edges_of_one_type:
                if source_edge not in edges_processed:
                    edges_order.append(source_edge)
                    edges_processed.add(source_edge)

            elif target_edges_set and source_edge in target_edges_set[active_target_sentence_i]:

                # if 'e-s119-t119' == source_edge:
                #     print('aaa')
                if source_edge not in edges_processed:
                    edges_order.append(source_edge)
                    edges_processed.add(source_edge)
                last_target_edge = source_edge
            # when source is connected to two targets
            elif source_edge not in target_edges_set[active_target_sentence_i]:
                # add missing edges from target
                while source_edge not in target_edges_set[active_target_sentence_i]:
                    for target_edge in target_edges[active_target_sentence_i]:
                        if target_edge in edges_of_one_type:
                            if target_edge not in edges_processed:
                                edges_order.append(target_edge)
                                edges_processed.add(target_edge)
                            last_target_edge = target_edge
                    active_target_sentence_i += 1
                    if source_edge in target_edges_set[active_target_sentence_i]:
                        if source_edge not in edges_processed:
                            edges_order.append(source_edge)
                            edges_processed.add(source_edge)

            else:
                raise 'Impossible!!!'
        if not target_edges_set or not target_edges_set[0] or active_target_sentence_i >= len(target_edges):
            continue
        if len(target_edges[active_target_sentence_i]) == 0:
            active_target_sentence_i += 1
            continue

        if last_target_edge == target_edges[active_target_sentence_i][-1] or (len(target_edges[active_target_sentence_i]) > 1 and last_target_edge == target_edges[active_target_sentence_i][-2] and (target_edges[active_target_sentence_i][-1] in edges_of_one_type or (target_edges[active_target_sentence_i][-1] not in edges_of_one_type and target_edges[active_target_sentence_i][-1] in source_edges_set[active_source_sentence_i]))):
            for target_edge in target_edges[active_target_sentence_i]:
                if target_edge in edges_of_one_type:
                    if target_edge not in edges_processed:
                        edges_order.append(target_edge)
                        edges_processed.add(target_edge)
                    last_target_edge = target_edge
            active_target_sentence_i += 1
            continue
        target_edge_in_next_source_edge_sentence = False
        for target_edge in target_edges[active_target_sentence_i]:
            if active_source_sentence_i + 1 < len(source_edges_set) and target_edge in source_edges_set[active_source_sentence_i + 1]:
                target_edge_in_next_source_edge_sentence = True
                break
        if target_edge_in_next_source_edge_sentence:
            pass
        elif not target_edge_in_next_source_edge_sentence:
            target_edge_in_next_source_edge_sentence = False
            while not target_edge_in_next_source_edge_sentence:
                # if active_target_sentence_i >= len(target_edges_set):
                #     break
                for target_edge in target_edges[active_target_sentence_i]:
                    if target_edge in edges_of_one_type:
                        if target_edge not in edges_processed:
                            edges_order.append(target_edge)
                            edges_processed.add(target_edge)
                        last_target_edge = target_edge

                # if there is no next source sentence
                if active_source_sentence_i + 1 >= len(source_edges_set):
                    target_edge_in_next_source_edge_sentence = True

                # if last_target_edge only in target stop regularly
                if last_target_edge == target_edges[active_target_sentence_i][-1]:
                    target_edge_in_next_source_edge_sentence = True

                # test if target_edge in next source
                for target_edge in target_edges[active_target_sentence_i]:
                    if active_source_sentence_i + 1 < len(source_edges_set) and target_edge in source_edges_set[
                        active_source_sentence_i + 1]:
                        target_edge_in_next_source_edge_sentence = True
                        break
                active_target_sentence_i += 1

    if not source_edges:
        for active_target_sentence in target_edges:
            for target_edge in active_target_sentence:
                if target_edge not in edges_processed:
                    edges_order.append(target_edge)
                    edges_processed.add(target_edge)

    # # DEBUG stuff
    # for edge_order in edges_order:
    #     if edges_order.count(edge_order) > 1:
    #     # if edge_order not in a:
    #         print(f'ERROR {edge_order}')
    #
    # for edge_order in edges_order:
    #     if edge_order not in svala_data['edges']:
    #         print(f'ERROR {edge_order}')
    #
    # for key in svala_data['edges'].keys():
    #     if key not in edges_order:
    #         print(f'ERROR {key}')
    #
    # a = len(svala_data['edges'])
    # b = len(edges_order)
    if len(svala_data['edges']) != len(edges_order):
        for k, v in save_deleted_edges.items():
            svala_data['edges'][k] = v


    assert len(svala_data['edges']) == len(edges_order)

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

    if edges:
        sentence_edges.append(edges)

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

            for p_el in el:
                if p_el.tag.startswith('w') or p_el.tag.startswith('pc'):
                    ind = str(svala_i)

                    target_id = "t" + ind

                    add_error_token_source_target_only(p_el, target, sentence_string_id, target_i, False, target_id)

                    target_i += 1
                    svala_i += 1
                elif p_el.tag.startswith('c') and len(target) > 0:
                    target[-1]['space_after'] = True
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


def process_solar2_paragraph(sentences, paragraph, svala_i, svala_data, add_errors_func):
    par_source = []
    par_target = []

    source_conllus = []
    target_conllus = []

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

        source_conllu = ''
        if len(source) > 0:
            source_conllu = create_conllu(source, sentence_string_id)
        target_conllu = ''
        if len(target) > 0:
            target_conllu = create_conllu(target, sentence_string_id)

        source_conllus.append(source_conllu)
        target_conllus.append(target_conllu)

    sentence_edges = create_edges(svala_data, par_source, par_target)

    return sentence_edges, source_conllus, target_conllus


def read_raw_text(path):
    with open(path, 'r') as rf:
        return rf.read()

HAND_FIXES = {'§§§pisala': ['§', '§', '§', 'pisala'], '§§§poldne': ['§', '§', '§', 'poldne'], '§§§o': ['§', '§', '§', 'o'], '§§§mimi': ['§', '§', '§', 'mimi'], '§§§nil': ['§', '§', '§', 'nil'], '§§§ela': ['§', '§', '§', 'ela'], 'sam§§§': ['sam', '§', '§', '§'], 'globač§§§': ['globač', '§', '§', '§'], 'sin.': ['sin', '.'],  '§§§oveduje': ['§', '§', '§', 'oveduje'],  'na§§§': ['na', '§', '§', '§'], '§§§ka§§§': ['§', '§', '§', 'ka', '§', '§', '§'], '§§§e§§§': ['§', '§', '§', 'e', '§', '§', '§'], '§§§': ['§', '§', '§'], 'ljubezni.': ['ljubezni', '.'], '12.': ['12', '.'], '16.': ['16', '.'], 'st.': ['st', '.'], 'S.': ['S', '.'], 'pr.': ['pr', '.'], 'n.': ['n', '.'], '19:30': ['19', ':', '30'], '9.': ['9', '.'], '6:35': ['6', ':', '35'], 'itd.': ['itd', '.'], 'Sv.': ['Sv', '.'], 'npr.': ['npr', '.'], 'sv.': ['sv', '.'], '12:00': ['12', ':', '00'], "sram'vali": ['sram', "'", 'vali'], '18:00': ['18', ':', '00'], 'J.': ['J', '.'], '5:45': ['5', ':', '45'], '17.': ['17', '.'], '9.00h': ['9', '.', '00h'], 'H.': ['H', '.'], '1.': ['1', '.'], '6.': ['6', '.'], '7:10': ['7', ':', '10'], 'g.': ['g', '.'], 'Oz.': ['Oz', '.'], '20:00': ['20', ':', '00'], '17.4.2010': ['17.', '4.', '2010'], 'ga.': ['ga', '.'], 'prof.': ['prof', '.'], '6:45': ['6', ':', '45'], '19.': ['19', '.'], '3.': ['3', '.'], 'tj.': ['tj', '.'], 'Prof.': ['Prof', '.'], '8.': ['8', '.'], '9:18': ['9', ':', '18'], 'ipd.': ['ipd', '.'], '7.': ['7', '.'], 'št.': ['št', '.'], 'oz.': ['oz', '.'], 'R.': ['R', '.'], '13:30': ['13', ':', '30'], '5.': ['5', '.']}

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
    return paragraph_res


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


def update_ids(pretag, in_list):
    for el in in_list:
        el['id'] = f'{pretag}.{el["id"]}'


def process_obeliks_paragraph(sentences, paragraph, svala_i, svala_data, add_errors_func, source_raw_text, target_raw_text, nlp_tokenize):
    if source_raw_text is not None:
        text = read_raw_text(source_raw_text)
        raw_text, source_tokenized, metadocument = nlp_tokenize.processors['tokenize']._tokenizer.tokenize(text) if text else ([], [], [])
        source_res = map_svala_tokenized(svala_data['source'], source_tokenized)

    if target_raw_text is not None:
        text = read_raw_text(target_raw_text)
        raw_text, target_tokenized, metadocument = nlp_tokenize.processors['tokenize']._tokenizer.tokenize(text) if text else ([], [], [])
        target_res = map_svala_tokenized(svala_data['target'], target_tokenized)

    par_source = []
    par_target = []
    sentences_len = len(sentences)
    source_conllus = []
    target_conllus = []
    if source_raw_text is not None:
        sentences_len = max(sentences_len, len(source_res))
    if target_raw_text is not None:
        sentences_len = max(sentences_len, len(target_res))
    for sentence_id in range(sentences_len):
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
                if el.tag.startswith('w'):
                    if source_raw_text is None:
                        add_source(str(svala_i), source_i, sentence_string_id_split, source, el)
                    if target_raw_text is None:
                        add_target(str(svala_i), target_i, sentence_string_id_split, target, el)

                    svala_i += 1
                    source_i += 1
                    target_i += 1
                elif el.tag.startswith('pc'):
                    if source_raw_text is None:
                        add_source(str(svala_i), source_i, sentence_string_id_split, source, el)
                    if target_raw_text is None:
                        add_target(str(svala_i), target_i, sentence_string_id_split, target, el)

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
        source_conllu = ''
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

        target_conllu = ''
        if len(target) > 0:
            target_conllu = create_conllu(target, sentence_string_id)

        if source_raw_text is None or len(source_conllus) < len(par_source):
            source_conllus.append(source_conllu)

        if target_raw_text is None or len(target_conllus) < len(par_target):
            target_conllus.append(target_conllu)

    # reannotate svala_ids
    if source_raw_text is None:
        map_svala_solar2(svala_data['source'], par_source)
    if target_raw_text is None:
        map_svala_solar2(svala_data['target'], par_target)

    sentence_edges = create_edges(svala_data, par_source, par_target)

    return sentence_edges, source_conllus, target_conllus

def tokenize(args):
    if os.path.exists(args.tokenization_interprocessing) and not args.overwrite_tokenization:
        print('READING AND MERGING...')
        with open(args.tokenization_interprocessing, 'rb') as rp:
            tokenized_source_divs, tokenized_target_divs, document_edges = pickle.load(rp)
            return tokenized_source_divs, tokenized_target_divs, document_edges

    print('TOKENIZING...')
    with open(args.solar_file, 'r') as fp:
        logging.info(args.solar_file)
        et = ElementTree.XML(fp.read())

    nlp_tokenize = classla.Pipeline('sl', processors='tokenize', pos_lemma_pretag=True)
    # filename_encountered = False
    i = 0
    folders_count = 5484
    tokenized_source_divs = []
    tokenized_target_divs = []
    document_edges = []

    for div in et.iter('div'):
        bibl = div.find('bibl')
        file_name = bibl.get('n')
        file_name = file_name.replace('/', '_')
        print(f'{i*100/folders_count} % : {file_name}')
        i += 1
        # if file_name == 'S20-PI-slo-2-SG-D-2016_2017-30479-12.txt':
        # if file_name == 'KUS-PI-slo-5-CE-E-2009-30137':
        # # # if i*100/folders_count > 40:
        #     filename_encountered = True
        # # # # if i*100/folders_count > 41:
        # # # #     filename_encountered = False
        # if not filename_encountered:
        #     continue

        svala_path = os.path.join(args.svala_folder, file_name)
        corrected_svala_path = os.path.join(args.corrected_svala_folder, file_name)
        raw_texts_path = os.path.join(args.svala_generated_text_folder, file_name)

        svala_list = [[fname[:-13], fname] if 'problem' in fname else [fname[:-5], fname] for fname in os.listdir(svala_path)] if os.path.isdir(svala_path) else []
        svala_dict = {e[0]: e[1] for e in svala_list}

        if os.path.exists(corrected_svala_path):
            corrected_svala_list = [[fname[:-13], fname] if 'problem' in fname else [fname[:-5], fname] for fname in os.listdir(corrected_svala_path)]
            corrected_svala_dict = {e[0]: e[1] for e in corrected_svala_list}

            svala_dict.update(corrected_svala_dict)

        assert len(svala_dict) != 0

        tokenized_source_paragraphs = []
        tokenized_target_paragraphs = []
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
            add_errors_func = add_errors if not os.path.exists(corrected_svala_file) else add_errors1_0_1
            jf = open(svala_file) if not os.path.exists(corrected_svala_file) else open(corrected_svala_file)
            svala_data = json.load(jf)
            jf.close()

            source_filename = svala_dict[paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id']][:-5] + '_source.json'
            target_filename = svala_dict[paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id']][:-5] + '_target.json'

            source_raw_text = os.path.join(raw_texts_path, source_filename) if os.path.exists(os.path.join(raw_texts_path, source_filename)) else None
            target_raw_text = os.path.join(raw_texts_path, target_filename) if os.path.exists(os.path.join(raw_texts_path, target_filename)) else None

            if not (source_raw_text or target_raw_text):
                sentence_edges, tokenized_source_sentences, tokenized_target_sentences = process_solar2_paragraph(sentences, paragraph, svala_i, svala_data, add_errors_func)

            else:
                sentence_edges, tokenized_source_sentences, tokenized_target_sentences = process_obeliks_paragraph(sentences, paragraph, svala_i,
                                                                                           svala_data, add_errors_func, source_raw_text, target_raw_text, nlp_tokenize)

            tokenized_source_paragraphs.append(tokenized_source_sentences)
            tokenized_target_paragraphs.append(tokenized_target_sentences)
            paragraph_edges.append(sentence_edges)

        tokenized_source_divs.append(tokenized_source_paragraphs)
        tokenized_target_divs.append(tokenized_target_paragraphs)
        document_edges.append(paragraph_edges)

    with open(args.tokenization_interprocessing, 'wb') as wp:
        pickle.dump((tokenized_source_divs, tokenized_target_divs, document_edges), wp)

    return tokenized_source_divs, tokenized_target_divs, document_edges

def annotate(tokenized_source_divs, tokenized_target_divs, args):
    if os.path.exists(args.annotation_interprocessing) and not args.overwrite_annotation:
        print('READING...')
        with open(args.annotation_interprocessing, 'rb') as rp:
            annotated_source_divs, annotated_target_divs = pickle.load(rp)
            return annotated_source_divs, annotated_target_divs

    nlp = classla.Pipeline('sl', pos_use_lexicon=True, pos_lemma_pretag=False, tokenize_pretokenized="conllu",
                           type='standard_jos')

    annotated_source_divs = []
    complete_source_conllu = ''
    print('ANNOTATING SOURCE...')
    for i, div in enumerate(tokenized_source_divs):
        print(f'{str(i*100/len(tokenized_source_divs))}')
        annotated_source_pars = []
        for par in div:
            annotated_source_sens = []
            for sen in par:
                source_conllu_annotated = nlp(sen).to_conll() if sen else ''
                annotated_source_sens.append(source_conllu_annotated)
                complete_source_conllu += source_conllu_annotated
            annotated_source_pars.append(annotated_source_sens)
        annotated_source_divs.append(annotated_source_pars)

    annotated_target_divs = []
    complete_target_conllu = ''
    print('ANNOTATING TARGET...')
    for i, div in enumerate(tokenized_target_divs):
        print(f'{str(i * 100 / len(tokenized_target_divs))}')
        annotated_target_pars = []
        for par in div:
            annotated_target_sens = []
            for sen in par:
                target_conllu_annotated = nlp(sen).to_conll() if sen else ''
                annotated_target_sens.append(target_conllu_annotated)
                complete_target_conllu += target_conllu_annotated
            annotated_target_pars.append(annotated_target_sens)
        annotated_target_divs.append(annotated_target_pars)

    with open(os.path.join(args.results_folder, f"source.conllu"), 'w') as sf:
        sf.write(complete_source_conllu)

    with open(os.path.join(args.results_folder, f"target.conllu"), 'w') as sf:
        sf.write(complete_target_conllu)

    with open(args.annotation_interprocessing, 'wb') as wp:
        pickle.dump((annotated_source_divs, annotated_target_divs), wp)

    return annotated_source_divs, annotated_target_divs


def write_tei(annotated_source_divs, annotated_target_divs, document_edges, args):
    print('BUILDING LINKS...')
    etree_links = build_links(document_edges)

    with open(os.path.join(args.results_folder, f"links.xml"), 'w') as tf:
        tf.write(etree.tostring(etree_links, pretty_print=True, encoding='utf-8').decode())

    with open(os.path.join(args.results_folder, f"links.json"), 'w') as jf:
        json.dump(document_edges, jf, ensure_ascii=False, indent="  ")


    print('WRITTING TEI...')
    etree_source_documents = []
    etree_target_documents = []
    etree_source_divs = []
    etree_target_divs = []

    with open(args.solar_file, 'r') as fp:
        logging.info(args.solar_file)
        et = ElementTree.XML(fp.read())

    # filename_encountered = False
    i = 0
    folders_count = 5484

    div_i = 0
    for div in et.iter('div'):
        bibl = div.find('bibl')
        file_name = bibl.get('n')
        file_name = file_name.replace('/', '_')
        print(f'{i * 100 / folders_count} % : {file_name}')
        i += 1

        # if i * 100 / folders_count > 50:
        #     filename_encountered = True
        # # if file_name == 'KUS-G-slo-4-GO-E-2009-10071':
        # #     filename_encountered = True
        # if i * 100 / folders_count > 51:
        #     filename_encountered = False
        #
        # if file_name == 'KUS-G-slo-1-LJ-E-2009_2010-10540':
        #     # div_i -= 1
        #     continue
        #
        # if file_name == 'KUS-SI-slo-2-NM-E-2009_2010-20362' or file_name == 'KUS-OS-slo-9-SG-R-2009_2010-40129' or file_name == 'KUS-OS-slo-7-SG-R-2009_2010-40173':
        #     # div_i -= 1
        #     continue
        #
        # if not filename_encountered:
        #     div_i+=1
        #
        #     continue


        etree_source_paragraphs = []
        etree_target_paragraphs = []
        # paragraph_edges = []

        paragraphs = div.findall('p')
        par_i = 0
        for paragraph in paragraphs:

            etree_source_sentences = []
            etree_target_sentences = []

            for sentence_id, source_conllu_annotated in enumerate(annotated_source_divs[div_i][par_i]):
                if len(source_conllu_annotated) > 0:
                    source_conllu_parsed = conllu.parse(source_conllu_annotated)[0]
                if len(source_conllu_annotated) > 0:
                    etree_source_sentences.append(construct_sentence_from_list(str(sentence_id + 1), source_conllu_parsed, True))


            for sentence_id, target_conllu_annotated in enumerate(annotated_target_divs[div_i][par_i]):
                if len(target_conllu_annotated) > 0:
                    target_conllu_parsed = conllu.parse(target_conllu_annotated)[0]
                if len(target_conllu_annotated) > 0:
                    etree_target_sentences.append(construct_sentence_from_list(str(sentence_id + 1), target_conllu_parsed, False))

            etree_source_paragraphs.append(construct_paragraph_from_list(paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id'].split('.')[0], paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id'].split('.')[1], etree_source_sentences, True))
            etree_target_paragraphs.append(construct_paragraph_from_list(paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id'].split('.')[0], paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id'].split('.')[1], etree_target_sentences, False))

            par_i += 1

        etree_bibl = convert_bibl(bibl)
        etree_source_divs.append((etree_source_paragraphs, copy.deepcopy(etree_bibl), paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id'].split('.')[0] + 's'))
        etree_target_divs.append((etree_target_paragraphs, copy.deepcopy(etree_bibl), paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id'].split('.')[0] + 't'))

        div_i += 1

    print('APPENDING DOCUMENT...')
    etree_source_documents.append(
        TeiDocument(paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id'].split('.')[0] + 's',
                    etree_source_divs, etree_target_divs))
    etree_target_documents.append(
        TeiDocument(paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id'].split('.')[0] + 't',
                    etree_target_divs, etree_source_divs))

    print('BUILDING TEI DOCUMENTS...')
    etree_source = build_tei_etrees(etree_source_documents)
    etree_target = build_tei_etrees(etree_target_documents)

    print('Writting all but complete')
    with open(os.path.join(args.results_folder, f"source.xml"), 'w') as sf:
        sf.write(etree.tostring(etree_source[0], pretty_print=True, encoding='utf-8').decode())

    with open(os.path.join(args.results_folder, f"target.xml"), 'w') as tf:
        tf.write(etree.tostring(etree_target[0], pretty_print=True, encoding='utf-8').decode())

    print('COMPLETE TREE CREATION...')
    complete_etree = build_complete_tei(copy.deepcopy(etree_source), copy.deepcopy(etree_target), etree_links)
    # complete_etree = build_complete_tei(etree_source, etree_target, etree_links)

    print('WRITING COMPLETE TREE')
    with open(os.path.join(args.results_folder, f"complete.xml"), 'w') as tf:
        tf.write(etree.tostring(complete_etree, pretty_print=True, encoding='utf-8').decode())

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
