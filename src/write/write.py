import copy
import json
import os
from lxml import etree
import conllu

from src.create_tei import construct_sentence_from_list, \
    construct_paragraph_from_list, TeiDocument, build_tei_etrees, build_links, build_complete_tei, convert_bibl


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

    # with open(args.solar_file, 'r') as fp:
    #     logging.info(args.solar_file)
    #     et = ElementTree.XML(fp.read())

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
