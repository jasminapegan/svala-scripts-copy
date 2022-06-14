import argparse
import copy
import logging
import os
import shutil
import time
from xml.etree import ElementTree
import json

logging.basicConfig(level=logging.INFO)


def add_token(ind, el, source, target, edges):
    source_id = "s" + ind
    source.append({"id": source_id, "text": el.text + " "})
    target_id = "t" + ind
    target.append({"id": target_id, "text": el.text + " "})
    edge_id = "e-" + source_id + "-" + target_id
    edges[edge_id] = {"id": edge_id, "ids": [source_id, target_id], "labels": [], "manual": False}


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


def save_file(paragraph_error, output_folder_loc, error_folder_loc, paragraph, dictionary, essay_problematic, dictionary_i):
    if not paragraph_error:
        if not os.path.exists(output_folder_loc):
            os.mkdir(output_folder_loc)
        if not os.path.exists(error_folder_loc):
            os.mkdir(error_folder_loc)
        file_name = paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id'] + '.json' if dictionary_i == 1 else paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id'] + '_P' + str(dictionary_i) + '.json'
        with open(os.path.join(output_folder_loc, file_name), 'w') as wf:
            json.dump(dictionary, wf, ensure_ascii=False, indent="")
        with open(os.path.join(error_folder_loc, file_name), 'w') as wf:
            json.dump(dictionary, wf, ensure_ascii=False, indent="")
    else:
        essay_problematic = True
        if not os.path.exists(error_folder_loc):
            os.mkdir(error_folder_loc)
        file_name = paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id'] + '_problem.json' if dictionary_i == 1 else paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id'] + '_P' + str(dictionary_i) + '_problem.json'
        with open(os.path.join(error_folder_loc, file_name),
                  'w') as wf:
            json.dump(dictionary, wf, ensure_ascii=False, indent="")

    return essay_problematic


def process_file(et, args):
    if os.path.exists(args.output_folder):
        shutil.rmtree(args.output_folder)
    if os.path.exists(args.error_folder):
        shutil.rmtree(args.error_folder)
    os.mkdir(args.output_folder)
    os.mkdir(args.error_folder)
    # folders_count = 5484
    for i, div in enumerate(et.iter('div')):
        bibl = div.find('bibl')
        file_name = bibl.get('n')
        file_name = file_name.replace('/', '_')
        # print(f'{i * 100 / folders_count} % : {file_name}')
        # if file_name == 'KUS-G-slo-1-LJ-E-2009_2010-10540':
        #     print('asd')
        # else:
        #     continue
        output_folder_loc = os.path.join(args.output_folder, file_name)
        error_folder_loc = os.path.join(args.error_folder, file_name)

        essay_problematic = False

        paragraphs = div.findall('p')
        for paragraph in paragraphs:
            sentences = paragraph.findall('s')
            i = 1
            dictionary_i = 1

            source = []
            target = []
            edges = {}
            paragraph_error = False
            for sentence in sentences:
                for el in sentence:
                    if el.tag.startswith('w'):
                        add_token(str(i), el, source, target, edges)
                        i += 1
                    elif el.tag.startswith('pc'):
                        add_token(str(i), el, source, target, edges)
                        i += 1
                    elif el.tag.startswith('u'):
                        i, has_error = add_errors(i, el, source, target, edges)
                        if has_error:
                            paragraph_error = True

                # add part of dictionary
                if i > dictionary_i * 10000000000000:
                    essay_problematic = save_file(paragraph_error, output_folder_loc, error_folder_loc, paragraph, {"source": source, "target": target, "edges": edges}, essay_problematic, dictionary_i)
                    dictionary_i += 1
                    source = []
                    target = []
                    edges = {}
                    paragraph_error = False

            essay_problematic = save_file(paragraph_error, output_folder_loc, error_folder_loc, paragraph, {"source": source, "target": target, "edges": edges}, essay_problematic, dictionary_i)

        if not essay_problematic:
            shutil.rmtree(error_folder_loc)


def main(args):
    with open(args.input_file, 'r') as fp:
        logging.info(args.input_file)
        et = ElementTree.XML(fp.read())
        process_file(et, args)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Read already processed xmls, erase entries without examples and limit gigafida examples to 1 per entry.')
    parser.add_argument('--input_file', default='data/Solar2.0/solar2.xml',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    parser.add_argument('--output_folder', default='data/solar.svala',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    parser.add_argument('--error_folder', default='data/solar.svala.error',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    args = parser.parse_args()

    start = time.time()
    main(args)
    logging.info("TIME: {}".format(time.time() - start))
