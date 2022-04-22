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

from lxml import etree

from src.create_tei import construct_sentence_from_list, \
    construct_paragraph_from_list, TeiDocument, build_tei_etrees, build_links, build_complete_tei, convert_bibl

logging.basicConfig(level=logging.INFO)


def add_token(svala_i, source_i, target_i, el, source, target, edges, svala_data, sentence_string_id):
    source_id = "s" + svala_i
    target_id = "t" + svala_i
    edge_id = "e-" + source_id + "-" + target_id
    labels = svala_data['edges'][edge_id]['labels']
    sentence_string_id_split = sentence_string_id.split('.')
    source_token_id = f'{sentence_string_id_split[0]}s.{".".join(sentence_string_id_split[1:])}.{source_i}'
    target_token_id = f'{sentence_string_id_split[0]}t.{".".join(sentence_string_id_split[1:])}.{source_i}'
    token_tag = 'w' if el.tag.startswith('w') else 'pc'
    lemma = el.attrib['lemma'] if token_tag == 'w' else el.text
    source.append({'token': el.text, 'tag': token_tag, 'ana': el.attrib['ana'], 'lemma': lemma, 'id': source_token_id, 'space_after': False})
    target.append({'token': el.text, 'tag': token_tag, 'ana': el.attrib['ana'], 'lemma': lemma, 'id': target_token_id, 'space_after': False})
    edges.append({'source_ids': [source_token_id], 'target_ids': [target_token_id], 'labels': labels})


def add_error_token(el, out_list, sentence_string_id, out_list_i, out_list_ids, is_source):
    sentence_string_id_split = sentence_string_id.split('.')

    source_token_id = f'{sentence_string_id_split[0]}s.{".".join(sentence_string_id_split[1:])}.{out_list_i}' if is_source \
        else f'{sentence_string_id_split[0]}t.{".".join(sentence_string_id_split[1:])}.{out_list_i}'
    token_tag = 'w' if el.tag.startswith('w') else 'pc'
    lemma = el.attrib['lemma'] if token_tag == 'w' else el.text
    out_list.append({'token': el.text, 'tag': token_tag, 'ana': el.attrib['ana'], 'lemma': lemma, 'id': source_token_id, 'space_after': False})
    out_list_ids.append(source_token_id)


def add_errors(svala_i, source_i, target_i, error, source, target, edges, svala_data, sentence_string_id):
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

            add_error_token(el, source, sentence_string_id, source_i, source_ids, True)

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

                    add_error_token(p_el, target, sentence_string_id, target_i, target_ids, False)

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

                    add_error_token(el_l2, source, sentence_string_id, source_i, source_ids, True)

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

                            add_error_token(el_l3, source, sentence_string_id, source_i, source_ids, True)

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

                                    add_error_token(el_l4, source, sentence_string_id, source_i, source_ids, True)

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

                                            add_error_token(el_l5, source, sentence_string_id, source_i, source_ids, True)

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

    edge_ids = sorted(source_edge_ids) + sorted(target_edge_ids)
    edge_id = "e-" + "-".join(edge_ids)
    edges.append({'source_ids': source_ids, 'target_ids': target_ids, 'labels': svala_data['edges'][edge_id]['labels']})

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


def process_file(et, args, nlp):
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
    for div in et.iter('div'):
        bibl = div.find('bibl')
        file_name = bibl.get('n')
        file_name = file_name.replace('/', '_')

        svala_path = os.path.join(args.svala_folder, file_name)
        # skip files that are not svala annotated (to enable short examples)
        if not os.path.isdir(svala_path):
            continue

        svala_list = [[fname[:-13], fname] if 'problem' in fname else [fname[:-5], fname] for fname in os.listdir(svala_path)]
        svala_dict = {e[0]: e[1] for e in svala_list}

        etree_source_paragraphs = []
        etree_target_paragraphs = []
        paragraph_edges = []

        paragraphs = div.findall('p')
        for paragraph in paragraphs:
            sentences = paragraph.findall('s')
            svala_i = 1

            # read json
            svala_file = os.path.join(svala_path, svala_dict[paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id']])
            jf = open(svala_file)
            svala_data = json.load(jf)
            jf.close()

            etree_source_sentences = []
            etree_target_sentences = []

            sentence_edges = []

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
                        svala_i, source_i, target_i = add_errors(svala_i, source_i, target_i, el, source, target, edges, svala_data, sentence_string_id)
                    elif el.tag.startswith('c'):
                        if len(source) > 0:
                            source[-1]['space_after'] = True
                        if len(target) > 0:
                            target[-1]['space_after'] = True

                sentence_edges.append(edges)
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
                complete_target_conllu += target_conllu_annotated

                if len(source) > 0:
                    source_conllu_parsed = conllu.parse(source_conllu_annotated)[0]
                if len(target) > 0:
                    target_conllu_parsed = conllu.parse(target_conllu_annotated)[0]

                if len(source) > 0:
                    etree_source_sentences.append(construct_sentence_from_list(str(sentence_id), source_conllu_parsed, True))
                if len(target) > 0:
                    etree_target_sentences.append(construct_sentence_from_list(str(sentence_id), target_conllu_parsed, False))

            etree_source_paragraphs.append(construct_paragraph_from_list(paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id'].split('.')[0], paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id'].split('.')[1], etree_source_sentences, True))
            etree_target_paragraphs.append(construct_paragraph_from_list(paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id'].split('.')[0], paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id'].split('.')[1], etree_target_sentences, False))
            paragraph_edges.append(sentence_edges)

        etree_bibl = convert_bibl(bibl)

        etree_source_divs.append((etree_source_paragraphs, copy.deepcopy(etree_bibl)))
        etree_target_divs.append((etree_target_paragraphs, copy.deepcopy(etree_bibl)))
        document_edges.append(paragraph_edges)

    etree_source_documents.append(TeiDocument(paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id'].split('.')[0] + 's', etree_source_divs))
    etree_target_documents.append(TeiDocument(paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id'].split('.')[0] + 't', etree_target_divs))

    etree_source = build_tei_etrees(etree_source_documents)
    etree_target = build_tei_etrees(etree_target_documents)

    etree_links = build_links(document_edges)

    complete_etree = build_complete_tei(copy.deepcopy(etree_source), copy.deepcopy(etree_target), etree_links)

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
        et = ElementTree.XML(fp.read())
        process_file(et, args, nlp)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Read already processed xmls, erase entries without examples and limit gigafida examples to 1 per entry.')
    parser.add_argument('--solar_file', default='data/Solar2.0/solar2.xml',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    parser.add_argument('--svala_folder', default='data/solar.svala.error.small',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    parser.add_argument('--results_folder', default='data/results/solar3.0',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    args = parser.parse_args()

    start = time.time()
    main(args)
    logging.info("TIME: {}".format(time.time() - start))
