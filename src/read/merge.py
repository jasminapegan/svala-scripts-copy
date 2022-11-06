from src.read.read import read_raw_text, map_svala_tokenized
from conllu import TokenList


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


def create_edges(raw_edges, source_par, target_par):
    source_mapper = {el['svala_id']: el['id'] for source in source_par for el in source}
    target_mapper = {el['svala_id']: el['id'] for target in target_par for el in target}

    # actually add edges
    edges = []
    for _, edge in raw_edges.items():
        labels = edge['labels']
        source_ids = [source_mapper[el] for el in edge['ids'] if el in source_mapper]
        target_ids = [target_mapper[el] for el in edge['ids'] if el in target_mapper]

        edges.append({'source_ids': source_ids, 'target_ids': target_ids, 'labels': labels})

    return edges


def update_ids(pretag, in_list):
    for el in in_list:
        el['id'] = f'{pretag}.{el["id"]}'


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


def add_error_token_source_target_only(el, out_list, sentence_string_id, out_list_i, is_source, s_t_id):
    sentence_string_id_split = sentence_string_id.split('.')

    source_token_id = f'{sentence_string_id_split[0]}s.{".".join(sentence_string_id_split[1:])}.{out_list_i}' if is_source \
        else f'{sentence_string_id_split[0]}t.{".".join(sentence_string_id_split[1:])}.{out_list_i}'
    token_tag = 'w' if el.tag.startswith('w') else 'pc'
    out_list.append({'token': el.text, 'tag': token_tag, 'ana': el.attrib['ana'], 'id': source_token_id, 'space_after': False, 'svala_id': s_t_id})


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


def merge(sentences, paragraph, svala_i, svala_data, add_errors_func, source_raw_text, target_raw_text, nlp_tokenize):
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

    sentence_edges = create_edges(svala_data, par_source, par_target)

    return sentence_edges, source_conllus, target_conllus
