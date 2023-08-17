import argparse
import re
import sys
from conversion_utils.jos_msds_and_properties import Converter, Msd
from conversion_utils.translate_conllu_jos import get_syn_map

from lxml import etree

kost_translations = {
    "Author": "Author",
    "Sex": "Sex",
    "Year of birth": "YearOfBirth",
    "Country": "Country",
    "Employment status": "EmploymentStatus",
    "Completed education": "CompletedEducation",
    "Current school": "CurrentSchool",
    "First language": "FirstLang",
    "Knowledge of other languages": "OtherLang",
    "Duration of Slovene language learning": "DurSlvLearning",
    "Experience with Slovene before current program": "ExpSlv",
    "Language proficiency in Slovene": "ProficSlv",
    "Life in Slovenija before this current program": "LifeSlovenia",
    "Location of Slovene language learning": "LocSlvLearning",
    "Creation date": "CreationDate",
    "Teacher": "Teacher",
    "Academic year": "AcademicYear",
    "Grade": "Grade",
    "Input type": "InputType",
    "Program type": "ProgramType",
    "Program subtype": "ProgramSubtype",
    "Slovene textbooks used": "SloveneTextbooks",
    "Study cycle": "StudyCycle",
    "Study year": "StudyYear",
    "Task setting": "TaskSetting",
    "Topic": "Topic",
    "Instruction": "Instruction"
}

labels_mapper = {
	"B/GLAG/moči_morati": "B/GLAG/moči-morati",
	"B/MEN/besedna_družina": "B/MEN/besedna-družina",
	"B/MEN/glagol_bz": "B/MEN/glagol-bz",
	"B/MEN/polnopomenska_v_zaimek": "B/MEN/polnopomenska-v-zaimek",
	"B/MEN/prislov_pridevnik_bz": "B/MEN/prislov-pridevnik-bz",
	"B/MEN/samostalnik_bz": "B/MEN/samostalnik-bz",
	"B/MEN/veznik_zaimek": "B/MEN/veznik-zaimek",
	"B/MEN/zaimek_v_polnopomensko": "B/MEN/zaimek-v-polnopomensko",
	"B/PRED/glag_zveze": "B/PRED/glagolske-zveze",
	"B/PRED/lokacijske_dvojnice": "B/PRED/lokacijske-dvojnice",
	"B/PRED/neglag_zveze": "B/PRED/neglagolske-zveze",
	"B/SAM/lastno_občno": "B/SAM/lastno-občno",
	"B/SAM/napačno_lastno": "B/SAM/napačno-lastno",
	"B/SAM/občno_besedišče": "B/SAM/občno-besedišče",
	"B/VEZ/in_pa_ter": "B/VEZ/in-pa-ter",
	"B/VEZ/sprememba_odnosa": "B/VEZ/sprememba-odnosa",
	"B/ZAIM/ki_kateri": "B/ZAIM/ki-kateri",
	"B/ZAIM/povratna_svojilnost": "B/ZAIM/povratna-svojilnost",
	"Č/PREDL/sz": "Č/PRED/sz",
	"N//necitljivo": "N//nečitljivo",
	"O/DOD/besede-mati_hči": "O/DOD/besede-mati-hči",
	"O/KAT/oblika_zaimka": "O/KAT/oblika-zaimka",
	"O/PAR/glagolska_končnica": "O/PAR/glagolska-končnica",
	"O/PAR/glagolska_osnova": "O/PAR/glagolska-osnova",
	"O/PAR/neglagolska_končnica": "O/PAR/neglagolska-končnica",
	"O/PAR/neglagolska_osnova": "O/PAR/neglagolska-osnova",
	"O/PAR/neobstojni_vokal": "O/PAR/neobstojni-vokal",
	"O/PAR/preglas_in_cč": "O/PAR/preglas-in-cč",
	"P/ZAP/mala_velika": "P/ZAP/mala-velika",
	"S/BR/naslonski_niz-prirednost_podrednost": "S/BR/naslonski-niz-prirednost-podrednost",
	"S/BR/naslonski_niz-znotraj": "S/BR/naslonski-niz-znotraj",
	"S/BR/povedek-prislovno_določilo": "S/BR/povedek-prislovno-določilo",
	"S/BR/znotraj_stavčnega_člena": "S/BR/znotraj-stavčnega-člena",
	"S/DOD/pomensko_prazni": "S/DOD/pomensko-prazni",
	"S/IZPUST/samostalnik-lastno_ime": "S/IZPUST/samostalnik-lastno-ime",
	"S/IZPUST/samostalnik-občno_ime": "S/IZPUST/samostalnik-občno-ime",
	"S/ODVEČ/pomensko-prazni": "S/DOD/pomensko-prazni",
	"S/ODVEČ/samostalnik-lastno_ime": "S/ODVEČ/samostalnik-lastno-ime",
	"S/ODVEČ/samostalnik-občno_ime": "S/ODVEČ/samostalnik-občno-ime",
	"S/ODVEČ/veznik-pa_drugo": "S/ODVEČ/veznik-pa-drugo",
	"S/ODVEČ/veznik-pa_vezniki": "S/ODVEČ/veznik-pa-vezniki",
	"S/ODVEČ/vsebina-drugo": "S/DOD/vsebina-drugo",
	"S/STR/besedna_zveza_stavek": "S/STR/besedna-zveza-stavek",
	"S/STR/deljenje_stavkov": "S/STR/deljenje-stavkov",
	"S/STR/ločilo_veznik": "S/STR/ločilo-veznik",
	"S/STR/preoblikovanje_stavka": "S/STR/preoblikovanje-stavka",
	"S/STR/svojina_od": "S/STR/svojina-od",
	"S/STR/svojina_rodilnik": "S/STR/svojina-rodilnik",
	"S/STR/združevanje_stavkov": "S/STR/združevanje-stavkov",
	"Z/LOC/clenek+veznik": "Z/LOČ/nerazvrščeno",
	"Z/LOC/DRUGO": "Z/LOČ/nerazvrščeno",
	"Z/LOC/glede": "Z/LOČ/nerazvrščeno",
	"Z/LOC/hiperkorekcija": "Z/LOČ/nerazvrščeno",
	"Z/LOC/NERAZ": "Z/LOČ/nerazvrščeno",
	"Z/LOC/NEREL": "Z/LOČ/nerazvrščeno",
	"Z/LOC/polstavek": "Z/LOČ/vzorec-vejica-pristavki",
	"Z/LOC/pridevniski-niz": "Z/LOČ/vzorec-vejica-pridevniški-niz",
	"Z/LOC/primerjavaKOT": "Z/LOČ/vzorec-vejica-kot",
	"Z/LOC/primerjaveKOT": "Z/LOČ/vzorec-vejica-kot",
	"Z/LOC/prirednaBZ": "Z/LOČ/vzorec-vejica-priredja-zvez",
	"Z/LOC/priredni-odvisniki": "Z/LOČ/vzorec-vejica-priredja-odvisnikov",
	"Z/LOC/se-posebej": "Z/LOČ/vzorec-vejica-pristavki",
	"Z/LOC/VEJ-elipsa": "Z/LOČ/vzorec-vejica-elipsa-povedka",
	"Z/LOC/VEJ-stavki": "Z/LOČ/vzorec-vejica-stavki",
	"Z/LOC/VEJ-stclen": "Z/LOČ/vzorec-vejica-stavčni-členi",
	"Z/LOC/VEJ-veznik": "Z/LOČ/vzorec-vejica-vezniki",
	"Z/LOC/VEJ-vrivki": "Z/LOČ/vzorec-vejica-pristavki",
	"Z/LOC/vrinjen-odvisnik": "Z/LOČ/vzorec-vejica-vrinjen-odvisnik",
	"Z/LOC/z-imenom": "Z/LOČ/nerazvrščeno",
	"Z/MV/hiperkorekcija_ločila": "Z/MV/hiperkorekcija-ločila",
	"Z/MV/občna_imena": "Z/MV/občna-imena",
	"Z/MV/osebna_imena": "Z/MV/osebna-imena",
	"Z/MV/premi_govor": "Z/MV/premi-govor",
	"Z/MV/stvarna_imena": "Z/MV/stvarna-imena",
	"Z/MV/začetek_povedi": "Z/MV/začetek-povedi",
	"Z/MV/zemljepisna_imena": "Z/MV/zemljepisna-imena"
}

class Sentence:
    def __init__(self, _id, no_ud=False, is_source=None):
        self._id = _id
        self.items = []
        self.links = []
        self.no_ud = no_ud
        self.is_source = is_source

        # JOS-SYN translations from English to Slovene
        self.syn_map = get_syn_map()

    def add_item(self, word_id, token, lemma, upos, upos_other, xpos, head, deprel, no_space_after, ner):
        self.items.append([word_id, token, lemma, upos, upos_other, xpos, head, deprel, no_space_after, ner])

    def add_link(self, link_ref, link_type):
        self.links.append([link_ref, link_type])

    def as_xml(self, id_prefix=None):
        if id_prefix:
            xml_id = id_prefix + '.' + self._id
        else:
            xml_id = self._id
        base = etree.Element('s')
        set_xml_attr(base, 'id', xml_id)

        linkGrp = etree.Element(f'linkGrp')
        linkGrp.attrib[f'corresp'] = f'#{xml_id}'
        linkGrp.attrib[f'targFunc'] = 'head argument'
        linkGrp.attrib[f'type'] = 'JOS-SYN'

        ner_seg = None

        for item in self.items:
            word_id, token, lemma, upos, upos_other, xpos, head, deprel, no_space_after, ner = item

            if xpos in {'U', 'Z'}:  # hmm, safe only as long as U is unused in English tagset and Z in Slovenian one
                to_add = etree.Element('pc')
            else:
                to_add = etree.Element('w')

            to_add.set('ana', 'mte:' + xpos)
            if not self.no_ud:
                if upos_other != '_':
                    to_add.set('msd', f'UPosTag={upos}|{upos_other}')
                else:
                    to_add.set('msd', f'UPosTag={upos}')

            if xpos not in {'U', 'Z'}:
                to_add.set('lemma', lemma)

            set_xml_attr(to_add, 'id', "{}.{}".format(xml_id, word_id))
            to_add.text = token

            if no_space_after:
                to_add.set('join', 'right')

            # handle ner subclass
            if ner[0] == 'B':
                if ner_seg is not None:
                    base.append(ner_seg)
                    del ner_seg

                ner_seg = etree.Element('seg')
                ner_seg.set('type', f'name')
                ner_seg.set('subtype', f'{ner.split("-")[-1].lower()}')
            elif ner[0] == 'O':
                if ner_seg is not None:
                    base.append(ner_seg)
                    del ner_seg
                    ner_seg = None

            if ner_seg is None:
                base.append(to_add)
            else:
                ner_seg.append(to_add)

            # handle links
            link = etree.Element(f'link')
            link.attrib['ana'] = f'jos-syn:{self.syn_map[deprel]}'
            link.attrib['target'] = f'#{xml_id}.{head} #{xml_id}.{word_id}' if head != 0 else f'#{xml_id} #{xml_id}.{word_id}'
            linkGrp.append(link)

        if ner_seg is not None:
            base.append(ner_seg)

        base.append(linkGrp)

        return base


class Paragraph:
    def __init__(self, _id, _doc_id):
        self._id = _id if _id is not None else 'no-id'
        self._doc_id = _doc_id if _doc_id is not None else ''
        self.sentences = []

    def add_sentence(self, sentence):
        self.sentences.append(sentence)

    def as_xml(self, id_prefix=None):
        if id_prefix:
            xml_id = id_prefix + '.' + self._id
        else:
            if self._doc_id:
                xml_id = self._doc_id + '.' + self._id
            else:
                xml_id = self._id

        p = etree.Element('p')
        set_xml_attr(p, 'id', xml_id)

        for sent in self.sentences:
            p.append(sent.as_xml(id_prefix=xml_id))
        return p


class TeiDocument:
    def __init__(self, _id, divs=list(), corresp_divs=list()):
        self._id = _id
        self.divs = divs
        self.corresp_divs = corresp_divs

    def as_xml(self):
        root = etree.Element('TEI')
        root.set('xmlns', 'http://www.tei-c.org/ns/1.0')
        set_xml_attr(root, 'lang', 'sl')

        xml_id = self._id
        if xml_id is not None:
            set_xml_attr(root, 'id', xml_id)

        tei_header = etree.SubElement(root, 'teiHeader')

        text = etree.SubElement(root, 'text')
        body = etree.SubElement(text, 'body')
        encoding_desc = etree.SubElement(tei_header, 'encodingDesc')
        tags_decl = etree.SubElement(encoding_desc, 'tagsDecl')
        namespace = etree.SubElement(tags_decl, 'namespace')
        namespace.set('name', 'http://www.tei-c.org/ns/1.0')
        for tag in ['p', 's', 'pc', 'w']:
            count = int(text.xpath('count(.//{})'.format(tag)))
            tag_usage = etree.SubElement(namespace, 'tagUsage')
            tag_usage.set('gi', tag)
            tag_usage.set('occurs', str(count))

        for (paras, div_id, metadata), (_, corresp_div_id, _) in zip(self.divs, self.corresp_divs):
            div = etree.Element('div')
            set_xml_attr(div, 'id', div_id)
            div.set('corresp', f'#{corresp_div_id}')
            bibl = create_bibl(metadata)
            div.append(bibl)
            for para in paras:
                div.append(para.as_xml())
            body.append(div)

        return root

    def add_paragraph(self, paragraph):
        self.paragraphs.append(paragraph)


def create_bibl(metadata):
    bibl = etree.Element('bibl')
    bibl.set('n', metadata['Text ID'])
    for k, v in metadata.items():
        if k == 'Text ID' or not v:
            continue
        note = etree.Element('note')
        if k not in kost_translations:
            # print(k)
            key = ''.join([el.capitalize() for el in k.split()])
        else:
            key = kost_translations[k]
        note.set('ana', f'#{key}')
        note.text = f'{v}'
        bibl.append(note)
    return bibl

def convert_bibl(bibl):
    etree_bibl = etree.Element('bibl')
    etree_bibl.set('n', bibl.get('n'))
    for bibl_el in bibl:
        etree_bibl_el = etree.Element(bibl_el.tag)
        if bibl_el.tag == 'note' and 'type' in bibl_el.attrib and bibl_el.attrib['type'] == 'errs' and bibl_el.text == 'DA-NEVNESENO':
            etree_bibl_el.text = 'NEVNESENO'
        else:
            etree_bibl_el.text = bibl_el.text
        for att, val in bibl_el.attrib.items():
            if '{http://www.w3.org/XML/1998/namespace}' in att:
                set_xml_attr(etree_bibl_el, att.split('{http://www.w3.org/XML/1998/namespace}')[-1], val)
            else:
                etree_bibl_el.set(att, val)
        etree_bibl.append(etree_bibl_el)
    return etree_bibl


def build_tei_etrees(documents):
    elements = []
    for document in documents:
        elements.append(document.as_xml())
    return elements


def build_complete_tei(etree_source, etree_target, etree_links):
    print('P1')
    root = etree.Element('TEI')
    root.set('xmlns', 'http://www.tei-c.org/ns/1.0')
    print('P2')
    tei_header = etree.Element('teiHeader')
    text = etree.Element('text')
    group = etree.Element('group')
    print('P3')
    group.insert(len(group),
                      list(etree_source[0])[1])
    print('P4')
    group.insert(len(group),
                 list(etree_target[0])[1])
    print('P5')
    text.insert(len(text),
                 group)
    print('P6')
    root.insert(len(root),
                tei_header)
    print('P7')
    root.insert(len(root),
                text)
    print('P8')
    root.insert(len(root),
                etree_links)
    print('P9')
    return root


def build_links(all_edges):
    body = etree.Element('standOff')

    for document_edges in all_edges:
        # mine paragraphs
        for paragraph_edges in document_edges:
            p = etree.Element('linkGrp')
            corresp_source_id = ''
            corresp_target_id = ''

            for token_edges in paragraph_edges:
                if not corresp_source_id and len(token_edges['source_ids']) > 0:
                    random_source_id = token_edges['source_ids'][0]
                    corresp_source_id = '#'
                    corresp_source_id += '.'.join(random_source_id.split('.')[:2])
                if not corresp_target_id and len(token_edges['target_ids']) > 0:
                    random_target_id = token_edges['target_ids'][0]
                    corresp_target_id = '#'
                    corresp_target_id += '.'.join(random_target_id.split('.')[:2])

                link = etree.Element('link')
                # translate labels
                labels_list = []
                for label in token_edges['labels']:
                    if label in labels_mapper:
                        labels_list.append(labels_mapper[label])
                    else:
                        labels_list.append(label)
                labels = '|'.join(labels_list) if len(labels_list) > 0 else 'ID'
                link.set('type', labels)
                link.set('target', ' '.join(['#' + source for source in token_edges['source_ids']] + ['#' + source for source in token_edges['target_ids']]))

                p.append(link)
            corresp = []
            if corresp_source_id:
                corresp.append(corresp_source_id)
            if corresp_target_id:
                corresp.append(corresp_target_id)
            p.set('type', 'CORR')
            targFunc = []
            if corresp_source_id:
                targFunc.append('orig')
            if corresp_target_id:
                targFunc.append('reg')
            p.set('targFunc', f'{" ".join(targFunc)}')
            p.set('corresp', f'{" ".join(corresp)}')
            body.append(p)
    return body


def set_xml_attr(node, attribute, value):
    node.attrib['{http://www.w3.org/XML/1998/namespace}' + attribute] = value


def parse_metaline(line):
    tokens = line.split('=', 1)
    key = tokens[0].replace('#', '').strip()
    if len(tokens) > 1 and not tokens[1].isspace():
        val = tokens[1].strip()
    else:
        val = None
    return (key, val)


def is_metaline(line):
    if re.match('# .+ =.*', line):
        return True
    return False


def construct_paragraph_from_list(doc_id, para_id, etree_source_sentences):
    para = Paragraph(para_id, doc_id)

    for sentence in etree_source_sentences:
        para.add_sentence(sentence)

    return para


def construct_sentence_from_list(sent_id, object_list, is_source):
    sentence = Sentence(sent_id)
    converter = Converter()
    for tokens in object_list:
        word_id = f"{tokens['id']}" if is_source else f"{tokens['id']}"
        token = tokens['form']
        lemma = tokens['lemma']
        upos = tokens['upos']
        xpos = converter.properties_to_msd(converter.msd_to_properties(Msd(tokens['xpos'], 'en'), 'sl', lemma), 'sl').code
        upos_other = '|'.join([f'{k}={v}' for k, v in tokens['feats'].items()]) if tokens['feats'] else '_'
        head = tokens['head']
        deprel = tokens['deprel']
        no_space_after = 'SpaceAfter' in tokens['misc'] and tokens['misc']["SpaceAfter"] == "No"
        ner = tokens['misc']['NER']

        sentence.add_item(
            word_id,
            token,
            lemma,
            upos,
            upos_other,
            xpos,
            head,
            deprel,
            no_space_after,
            ner
        )

    return sentence


def construct_sentence(sent_id, lines):
    sentence = Sentence(sent_id)
    for line in lines:
        if line.startswith('#') or line.isspace():
            continue
        line = line.replace('\n', '')
        tokens = line.split('\t')
        word_id = tokens[0]
        token = tokens[1]
        lemma = tokens[2]
        upos = tokens[3]
        xpos = tokens[4]
        upos_other = tokens[5]
        depparse_link = tokens[6]
        depparse_link_name = tokens[7]
        misc = tokens[9]

        sentence.add_item(
            token,
            lemma,
            upos,
            upos_other,
            xpos,
            misc)

        sentence.add_link(
            depparse_link,
            depparse_link_name)
    return sentence

