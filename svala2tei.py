import argparse
import logging
import os
import shutil
import time
from line_profiler_pycharm import profile

from src.annotate.annotate import annotate
from src.read.read_and_merge import tokenize
from src.write.write import write_tei, process_metadata

logging.basicConfig(level=logging.DEBUG)
@profile
def process_file(args, annotator=None, tokenizer=None):
    if os.path.exists(args.results_folder):
        shutil.rmtree(args.results_folder)
    os.makedirs(args.results_folder)

    # READ AND MERGE svala tokenization, solar2 tokenization and obeliks tokenization
    tokenized_source_divs, tokenized_target_divs, document_edges = tokenize(args, tokenizer=tokenizer)

    # ANNOTATE WITH CLASSLA
    annotated_source_divs, annotated_target_divs = annotate(tokenized_source_divs, tokenized_target_divs, args,
                                                            annotator=annotator)

    # GENERATE TEI AND WRITE OUTPUT
    write_tei(annotated_source_divs, annotated_target_divs, document_edges, args)


def main(args, annotator=None, tokenizer=None):
    process_file(args, annotator=annotator, tokenizer=tokenizer)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Merges svala data, raw data and metadata into TEI format (useful for corpora like KOST).')
    parser.add_argument('--svala_folder', default='data_sample/test/svala_small',
                        help='Path to directory that contains svala files.')
    parser.add_argument('--results_folder', default='data_sample/test/results_small',
                        help='Path to results directory.')
    parser.add_argument('--raw_text', default='data_sample/test/raw_small',
                        help='Path to directory that contains raw text files.')
    parser.add_argument('--texts_metadata', default='data_sample/test/texts_metadata5.csv',
                        help='KOST metadata location')
    parser.add_argument('--authors_metadata', default='data_sample/test/authors_metadata5.csv',
                        help='KOST authors location')
    parser.add_argument('--teachers_metadata', default='data_sample/test/teachers_metadata.csv',
                        help='KOST teachers location')
    parser.add_argument('--translations', default='data_sample/test/translations.csv',
                        help='KOST Slovenian-English column names translations for TEI metadata')
    parser.add_argument('--tokenization_interprocessing', default='data_sample/test/processing.tokenization',
                        help='Path to file that containing tokenized data.')
    parser.add_argument('--overwrite_tokenization', action='store_true', help='Force retokenization without having to manually delete tokenization file.')
    parser.add_argument('--annotation_interprocessing', default='data_sample/test/processing.annotation',
                        help='Path to file that containing annotated data.')
    parser.add_argument('--overwrite_annotation', action='store_true', help='Force reannotation without having to manually delete tokenization file.')
    args = parser.parse_args()

    start = time.time()
    main(args)
    logging.info("TIME: {}".format(time.time() - start))
