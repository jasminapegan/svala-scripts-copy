from collections import deque

from src.read.hand_fixes import SVALA_HAND_FIXES_MERGE


class SvalaData():
    def __init__(self, svala_data):
        for el in svala_data['source']:
            el['text'] = el['text'].strip()
            if el['text'] == '':
                print('What?')
        for el in svala_data['target']:
            el['text'] = el['text'].strip()
            if el['text'] == '':
                print('What?')
        self.svala_data = svala_data
        self.links_ids_mapper, self.edges_of_one_type = self.create_ids_mapper(svala_data)

    @staticmethod
    def create_ids_mapper(svala_data):
        # create links to ids mapper
        links_ids_mapper = {}
        edges_of_one_type = set()

        for k, v in svala_data['edges'].items():
            has_source = False
            has_target = False
            v['source_ids'] = []
            v['target_ids'] = []
            for el in v['ids']:
                # create edges of one type
                if el[0] == 's':
                    v['source_ids'].append(el)
                    has_source = True
                if el[0] == 't':
                    v['target_ids'].append(el)
                    has_target = True

                # create links_ids_mapper
                if el not in links_ids_mapper:
                    links_ids_mapper[el] = []
                links_ids_mapper[el].append(k)
            if not has_source or not has_target or (
                    len(svala_data['source']) == 1 and svala_data['source'][0]['text'] == ' ') \
                    or (len(svala_data['target']) == 1 and svala_data['target'][0]['text'] == ' '):
                edges_of_one_type.add(k)

        return links_ids_mapper, edges_of_one_type
