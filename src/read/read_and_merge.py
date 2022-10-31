import json
import os
import pickle
import classla


from src.read.merge import merge
from src.read.read import read_raw_text, map_svala_tokenized

HAND_FIXES = {'§§§pisala': ['§', '§', '§', 'pisala'], '§§§poldne': ['§', '§', '§', 'poldne'], '§§§o': ['§', '§', '§', 'o'], '§§§mimi': ['§', '§', '§', 'mimi'], '§§§nil': ['§', '§', '§', 'nil'], '§§§ela': ['§', '§', '§', 'ela'], 'sam§§§': ['sam', '§', '§', '§'], 'globač§§§': ['globač', '§', '§', '§'], 'sin.': ['sin', '.'],  '§§§oveduje': ['§', '§', '§', 'oveduje'],  'na§§§': ['na', '§', '§', '§'], '§§§ka§§§': ['§', '§', '§', 'ka', '§', '§', '§'], '§§§e§§§': ['§', '§', '§', 'e', '§', '§', '§'], '§§§': ['§', '§', '§'], 'ljubezni.': ['ljubezni', '.'], '12.': ['12', '.'], '16.': ['16', '.'], 'st.': ['st', '.'], 'S.': ['S', '.'], 'pr.': ['pr', '.'], 'n.': ['n', '.'], '19:30': ['19', ':', '30'], '9.': ['9', '.'], '6:35': ['6', ':', '35'], 'itd.': ['itd', '.'], 'Sv.': ['Sv', '.'], 'npr.': ['npr', '.'], 'sv.': ['sv', '.'], '12:00': ['12', ':', '00'], "sram'vali": ['sram', "'", 'vali'], '18:00': ['18', ':', '00'], 'J.': ['J', '.'], '5:45': ['5', ':', '45'], '17.': ['17', '.'], '9.00h': ['9', '.', '00h'], 'H.': ['H', '.'], '1.': ['1', '.'], '6.': ['6', '.'], '7:10': ['7', ':', '10'], 'g.': ['g', '.'], 'Oz.': ['Oz', '.'], '20:00': ['20', ':', '00'], '17.4.2010': ['17.', '4.', '2010'], 'ga.': ['ga', '.'], 'prof.': ['prof', '.'], '6:45': ['6', ':', '45'], '19.': ['19', '.'], '3.': ['3', '.'], 'tj.': ['tj', '.'], 'Prof.': ['Prof', '.'], '8.': ['8', '.'], '9:18': ['9', ':', '18'], 'ipd.': ['ipd', '.'], '7.': ['7', '.'], 'št.': ['št', '.'], 'oz.': ['oz', '.'], 'R.': ['R', '.'], '13:30': ['13', ':', '30'], '5.': ['5', '.'], '...': ['.', '.', '.']}


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


def create_target(svala_data, source_tokenized):
    for i, el in enumerate(svala_data['target']):
        print(i)


def tokenize(args):
    if os.path.exists(args.tokenization_interprocessing) and not args.overwrite_tokenization:
        print('READING AND MERGING...')
        with open(args.tokenization_interprocessing, 'rb') as rp:
            tokenized_source_divs, tokenized_target_divs, document_edges = pickle.load(rp)
            return tokenized_source_divs, tokenized_target_divs, document_edges

    print('TOKENIZING...')
    # with open(args.solar_file, 'r') as fp:
    #     logging.info(args.solar_file)
    #     et = ElementTree.XML(fp.read())

    nlp_tokenize = classla.Pipeline('sl', processors='tokenize', pos_lemma_pretag=True)
    # filename_encountered = False
    i = 0
    tokenized_source_divs = []
    tokenized_target_divs = []
    document_edges = []

    text_filename = ''

    for folder, _, filenames in os.walk(args.svala_folder):
        for filename in filenames:
            svala_path = os.path.join(folder, filename)
            new_text_filename = '-'.join(filename[:-5].split('-')[:3]) + '.txt'
            if text_filename != new_text_filename:
                text_filename = new_text_filename
                text_file = read_raw_text(os.path.join(args.raw_text, text_filename))
                raw_text, source_tokenized, metadocument = nlp_tokenize.processors['tokenize']._tokenizer.tokenize(
                    text_file) if text_file else ([], [], [])
                source_sent_i = 0

            jf = open(svala_path)
            svala_data = json.load(jf)
            jf.close()


            target_res = create_target(svala_data, source_tokenized)
            source_sent_i, source_res = map_svala_tokenized(svala_data['source'], source_tokenized, source_sent_i)
            print('aaa')


    for div in et.iter('div'):
        bibl = div.find('bibl')
        file_name = bibl.get('n')
        file_name = file_name.replace('/', '_')
        print(f'{i*100/folders_count} % : {file_name}')
        i += 1
        # if file_name == 'S20-PI-slo-2-SG-D-2016_2017-30479-12.txt':
        # if file_name == 'KUS-G-slo-4-GO-E-2009-10017':
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
            # if paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id'] == 'solar17.6':
            #     print('here')
            svala_file = os.path.join(svala_path, svala_dict[paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id']])
            corrected_svala_file = os.path.join(corrected_svala_path, svala_dict[paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id']])
            add_errors_func = add_errors
            jf = open(svala_file) if not os.path.exists(corrected_svala_file) else open(corrected_svala_file)
            svala_data = json.load(jf)
            jf.close()

            source_filename = svala_dict[paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id']][:-5] + '_source.json'
            target_filename = svala_dict[paragraph.attrib['{http://www.w3.org/XML/1998/namespace}id']][:-5] + '_target.json'

            source_raw_text = os.path.join(raw_texts_path, source_filename) if os.path.exists(os.path.join(raw_texts_path, source_filename)) else None
            target_raw_text = os.path.join(raw_texts_path, target_filename) if os.path.exists(os.path.join(raw_texts_path, target_filename)) else None


            sentence_edges, tokenized_source_sentences, tokenized_target_sentences = merge(sentences, paragraph, svala_i,
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
