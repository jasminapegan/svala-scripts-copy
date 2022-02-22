import argparse
import json
import logging
import os
import shutil
import time
from xml.etree import ElementTree

from lxml import etree

from src.create_tei import construct_tei_etrees, construct_tei_documents_from_list, construct_sentence_from_list, \
    construct_paragraph_from_list, TeiDocument, build_tei_etrees

logging.basicConfig(level=logging.INFO)


def add_token(svala_i, source_i, target_i, el, source, target, edges, svala_data, sentence_string_source_id, sentence_string_target_id):
    source_id = "s" + svala_i
    target_id = "t" + svala_i
    edge_id = "e-" + source_id + "-" + target_id
    source_token_id = sentence_string_source_id + f'.{source_i}'
    target_token_id = sentence_string_target_id + f'.{target_i}'
    token_tag = 'w' if el.tag.startswith('w') else 'pc'
    lemma = el.attrib['lemma'] if token_tag == 'w' else el.text
    source.append({'token': el.text, 'tag': token_tag, 'ana': el.attrib['ana'], 'lemma': lemma, 'id': source_token_id, 'space_after': False})
    target.append({'token': el.text, 'tag': token_tag, 'ana': el.attrib['ana'], 'lemma': lemma, 'id': target_token_id, 'space_after': False})
    edges.append({'source_ids': [source_token_id], 'target_ids': [target_token_id], 'labels': svala_data['edges'][edge_id]['labels']})


def add_error_token(el, out_list, sentence_string_id, out_list_i, out_list_ids):
    source_token_id = sentence_string_id + f'.{out_list_i}'
    token_tag = 'w' if el.tag.startswith('w') else 'pc'
    lemma = el.attrib['lemma'] if token_tag == 'w' else el.text
    out_list.append({'token': el.text, 'tag': token_tag, 'ana': el.attrib['ana'], 'lemma': lemma, 'id': source_token_id, 'space_after': False})
    out_list_ids.append(source_token_id)


def add_errors(svala_i, source_i, target_i, error, source, target, edges, svala_data, sentence_string_source_id, sentence_string_target_id):
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

            add_error_token(el, source, sentence_string_source_id, source_i, source_ids)

            source_i += 1
            svala_i += 1

        elif el.tag.startswith('c'):
            source[-1]['space_after'] = True

        elif el.tag.startswith('p'):
            for p_el in el:
                if p_el.tag.startswith('w') or p_el.tag.startswith('pc'):
                    ind = str(svala_i)

                    target_id = "t" + ind
                    target_edge_ids.append(target_id)

                    add_error_token(p_el, target, sentence_string_target_id, target_i, target_ids)

                    target_i += 1
                    svala_i += 1

                elif p_el.tag.startswith('c'):
                    target[-1]['space_after'] = True

        elif el.tag.startswith('u2'):
            for el_l2 in el:
                if el_l2.tag.startswith('w') or el_l2.tag.startswith('pc'):
                    ind = str(svala_i)

                    source_id = "s" + ind
                    source_edge_ids.append(source_id)

                    add_error_token(el_l2, source, sentence_string_source_id, source_i, source_ids)

                    source_i += 1
                    svala_i += 1

                elif el_l2.tag.startswith('c'):
                    source[-1]['space_after'] = True

                elif el_l2.tag.startswith('u3'):
                    for el_l3 in el_l2:
                        if el_l3.tag.startswith('w') or el_l3.tag.startswith('pc'):
                            ind = str(svala_i)

                            source_id = "s" + ind
                            source_edge_ids.append(source_id)

                            add_error_token(el_l3, source, sentence_string_source_id, source_i, source_ids)

                            source_i += 1
                            svala_i += 1

                        elif el_l3.tag.startswith('c'):
                            source[-1]['space_after'] = True

                        elif el_l3.tag.startswith('u4'):
                            for el_l4 in el_l3:
                                if el_l4.tag.startswith('w') or el_l4.tag.startswith('pc'):
                                    ind = str(svala_i)

                                    source_id = "s" + ind
                                    source_edge_ids.append(source_id)

                                    add_error_token(el_l4, source, sentence_string_source_id, source_i, source_ids)

                                    source_i += 1
                                    svala_i += 1
                                elif el_l4.tag.startswith('c'):
                                    source[-1]['space_after'] = True

                                elif el_l4.tag.startswith('u5'):
                                    for el_l5 in el_l4:
                                        if el_l5.tag.startswith('w') or el_l5.tag.startswith('pc'):
                                            ind = str(svala_i)

                                            source_id = "s" + ind
                                            source_edge_ids.append(source_id)

                                            add_error_token(el_l5, source, sentence_string_source_id, source_i, source_ids)

                                            source_i += 1
                                            svala_i += 1
                                        elif el_l5.tag.startswith('c'):
                                            source[-1]['space_after'] = True

            for p_el in el:
                if p_el.tag.startswith('w') or p_el.tag.startswith('pc'):
                    ind = str(svala_i)

                    target_id = "t" + ind
                    target_edge_ids.append(target_id)

                    add_error_token(p_el, target, sentence_string_target_id, target_i, target_ids)

                    target_i += 1
                    svala_i += 1
                elif p_el.tag.startswith('c'):
                    target[-1]['space_after'] = True


    edge_ids = sorted(source_edge_ids) + sorted(target_edge_ids)
    edge_id = "e-" + "-".join(edge_ids)
    edges.append({'source_ids': source_ids, 'target_ids': target_ids, 'labels': svala_data['edges'][edge_id]['labels']})

    return svala_i, source_i, target_i


def process_file(et, args):
    if os.path.exists(args.results_folder):
        shutil.rmtree(args.results_folder)
    os.mkdir(args.results_folder)
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
            edges = []
            for sentence_id, sentence in enumerate(sentences):
                source = []
                target = []

                sentence_id += 1
                source_i = 1
                target_i = 1
                sentence_string_source_id = paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id'] + f's.{sentence_id}'
                sentence_string_target_id = paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id'] + f't.{sentence_id}'
                for el in sentence:
                    if el.tag.startswith('w'):
                        add_token(str(svala_i), source_i, target_i, el, source, target, edges, svala_data, sentence_string_source_id, sentence_string_target_id)
                        svala_i += 1
                        source_i += 1
                        target_i += 1
                    elif el.tag.startswith('pc'):
                        add_token(str(svala_i), source_i, target_i, el, source, target, edges, svala_data, sentence_string_source_id, sentence_string_target_id)
                        svala_i += 1
                        source_i += 1
                        target_i += 1
                    elif el.tag.startswith('u'):
                        svala_i, source_i, target_i = add_errors(svala_i, source_i, target_i, el, source, target, edges, svala_data, sentence_string_source_id, sentence_string_target_id)
                    elif el.tag.startswith('c'):
                        source[-1]['space_after'] = True
                        target[-1]['space_after'] = True

                etree_source_sentences.append(construct_sentence_from_list(str(sentence_id), source))
                etree_target_sentences.append(construct_sentence_from_list(str(sentence_id), target))

            etree_source_paragraph = construct_paragraph_from_list(paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id'].split('.')[1] + 's', etree_source_sentences)
            etree_source_document = TeiDocument(paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id'].split('.')[0], [etree_source_paragraph])
            etree_source = build_tei_etrees([etree_source_document])

            etree_target_paragraph = construct_paragraph_from_list(paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id'].split('.')[1] + 't', etree_target_sentences)
            etree_target_document = TeiDocument(paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id'].split('.')[0], [etree_target_paragraph])
            etree_target = build_tei_etrees([etree_target_document])

            with open(os.path.join(args.results_folder, f"{paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id']}_source"), 'w') as sf:
                sf.write(etree.tostring(etree_source[0], pretty_print=True, encoding='utf-8').decode())

            with open(os.path.join(args.results_folder, f"{paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id']}_target"), 'w') as tf:
                tf.write(etree.tostring(etree_target[0], pretty_print=True, encoding='utf-8').decode())

            with open(os.path.join(args.results_folder, f"{paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id']}_errors"), 'w') as jf:
                json.dump(edges, jf, ensure_ascii=False, indent="  ")

        break


def main(args):
    with open(args.solar_file, 'r') as fp:
        logging.info(args.solar_file)
        et = ElementTree.XML(fp.read())
        process_file(et, args)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Read already processed xmls, erase entries without examples and limit gigafida examples to 1 per entry.')
    parser.add_argument('--solar_file', default='data/Solar2.0/solar2.xml',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    parser.add_argument('--txt_file', default='data/txt/input',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    parser.add_argument('--svala_folder', default='data/solar.svala.error.small',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    parser.add_argument('--results_folder', default='data/results/solar3.0',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    args = parser.parse_args()

    start = time.time()
    main(args)
    logging.info("TIME: {}".format(time.time() - start))
