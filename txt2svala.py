import argparse
import json
import logging
import os
import shutil
import time
import obeliks

logging.basicConfig(level=logging.INFO)

def add_token(ind, text, source, target, edges):
    source_id = "s" + ind
    source.append({"id": source_id, "text": text + " "})
    target_id = "t" + ind
    target.append({"id": target_id, "text": text + " "})
    edge_id = "e-" + source_id + "-" + target_id
    edges[edge_id] = {"id": edge_id, "ids": [source_id, target_id], "labels": [], "manual": False}

def paragraph_to_svala(paragraph):
    i = 1
    source = []
    target = []
    edges = {}
    for word in paragraph:
        add_token(str(i), word, source, target, edges)
        i += 1

    return {"source": source, "target": target, "edges": edges}


def process_file(file, args):
    file_path = os.path.join(args.input_folder, file)
    if os.path.exists(args.output_folder):
        shutil.rmtree(args.output_folder)
    os.mkdir(args.output_folder)
    print(file_path)
    with open(file_path, 'r', encoding='utf-8') as fp:
        for i, line in enumerate(fp):
            tokenized = [token.split('\t')[1] for token in obeliks.run(line).split('\n') if len(token.split('\t')) > 1]
            dictionary = paragraph_to_svala(tokenized)
            with open(os.path.join(args.output_folder, file.strip('.txt') + '-' + str(i+1) + '.json'), 'w', encoding='utf-8') as wf:
                json.dump(dictionary, wf, ensure_ascii=False, indent="")

def main(input_folder, output_folder):
    for file in os.listdir(input_folder):
        if os.path.isfile(os.path.join(input_folder, file)):
            try:
                process_file(file, args)
            except Exception as e:
                #print(f'Skipping file {file} on path {args.input_folder} - Failed to decode txt file:\n {e}')
                raise Exception(f'Failed to process txt file {file} on path {input_folder}:\n {e}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Converts raw text into svala format.')
    parser.add_argument('--input_folder', default='data/txt/input',
                        help='Path to folder containing raw texts.')
    parser.add_argument('--output_folder', default='data/txt/output',
                        help='Path to folder that will contain svala formatted texts.')
    args = parser.parse_args()

    start = time.time()
    main(args)
    logging.info("TIME: {}".format(time.time() - start))
