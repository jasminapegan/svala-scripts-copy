import copy
import json
import os
from lxml import etree
import conllu

from src.create_tei import construct_sentence_from_list, \
    construct_paragraph_from_list, TeiDocument, build_tei_etrees, build_links, build_complete_tei, convert_bibl


def form_paragraphs(annotated_source_divs):
    etree_source_divs = []
    for div_i, div_tuple in enumerate(annotated_source_divs):
        div_name, div = div_tuple
        # file_name = file_name.replace('/', '_')
        # print(f'{i * 100 / folders_count} % : {file_name}')

        etree_source_paragraphs = []

        for par_i, paragraph_tuple in enumerate(div):
            par_name, paragraph = paragraph_tuple
            etree_source_sentences = []

            for sentence_id, sentence in enumerate(paragraph):
                if len(sentence) > 0:
                    conllu_parsed = conllu.parse(sentence)[0]
                    etree_source_sentences.append(
                        construct_sentence_from_list(str(sentence_id + 1), conllu_parsed, True))

            etree_source_paragraphs.append(construct_paragraph_from_list(div_name, par_name, etree_source_sentences))

        etree_source_divs.append((etree_source_paragraphs, div_name))

    return etree_source_divs, div_name

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

    print('WRITING SOURCE FILES...')
    etree_source_divs, source_div_name = form_paragraphs(annotated_source_divs)

    print('WRITING TARGET FILES...')
    etree_target_divs, target_div_name = form_paragraphs(annotated_target_divs)

    print('APPENDING DOCUMENT...')
    etree_source_documents.append(
        TeiDocument(source_div_name,
                    etree_source_divs, etree_target_divs))
    etree_target_documents.append(
        TeiDocument(target_div_name,
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
