import os
import pickle
import classla


def annotate(tokenized_source_divs, tokenized_target_divs, args):
    if os.path.exists(args.annotation_interprocessing) and not args.overwrite_annotation:
        print('READING ANNOTATIONS...')
        with open(args.annotation_interprocessing, 'rb') as rp:
            annotated_source_divs, annotated_target_divs = pickle.load(rp)
            return annotated_source_divs, annotated_target_divs

    nlp = classla.Pipeline('sl', pos_use_lexicon=True, pos_lemma_pretag=False, tokenize_pretokenized="conllu",
                           type='standard_jos')

    annotated_source_divs = []
    complete_source_conllu = ''
    print('ANNOTATING SOURCE...')
    for i, div_tuple in enumerate(tokenized_source_divs):
        print(f'{str(i*100/len(tokenized_source_divs))}')
        div_name, div = div_tuple
        annotated_source_pars = []
        for par_tuple in div:
            par_name, par = par_tuple
            annotated_source_sens = []
            for sen in par:
                source_conllu_annotated = nlp(sen).to_conll() if sen else ''
                annotated_source_sens.append(source_conllu_annotated)
                complete_source_conllu += source_conllu_annotated
            annotated_source_pars.append((par_name, annotated_source_sens))
        annotated_source_divs.append((div_name, annotated_source_pars))

    annotated_target_divs = []
    complete_target_conllu = ''
    print('ANNOTATING TARGET...')
    for i, div_tuple in enumerate(tokenized_target_divs):
        print(f'{str(i * 100 / len(tokenized_target_divs))}')
        div_name, div = div_tuple
        annotated_target_pars = []
        for par_tuple in div:
            par_name, par = par_tuple
            annotated_target_sens = []
            for sen in par:
                # if sen.count('\n') <= 2:
                #     print('HERE!!!!')
                target_conllu_annotated = nlp(sen).to_conll() if sen and sen.count('\n') > 2 else ''
                annotated_target_sens.append(target_conllu_annotated)
                complete_target_conllu += target_conllu_annotated
            annotated_target_pars.append((par_name, annotated_target_sens))
        annotated_target_divs.append((div_name, annotated_target_pars))

    with open(os.path.join(args.results_folder, f"source.conllu"), 'w', encoding="utf-8") as sf:
        sf.write(complete_source_conllu)

    with open(os.path.join(args.results_folder, f"target.conllu"), 'w', encoding="utf-8") as sf:
        sf.write(complete_target_conllu)

    with open(args.annotation_interprocessing, 'wb') as wp:
        pickle.dump((annotated_source_divs, annotated_target_divs), wp)

    return annotated_source_divs, annotated_target_divs
