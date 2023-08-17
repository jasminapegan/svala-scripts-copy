# KOST
## Instructions
- Create a new virtual environment (using i.e. `virtualenv`)
- Run `pip install -r requirements.txt`, to install necessary libraries.
- Using python console download classla models (used for annotation and part of tokenization):
```python
import classla
classla.download(lang='sl', type='standard_jos')
```
- Run `svala2tei.py` script.

### Example
```python
python svala2tei.py --svala_folder data_sample/KOST/svala_small --raw_text data_sample/KOST/raw_small --results_folder data_sample/KOST/results_small --texts_metadata data_sample/KOST/texts_metadata5.csv --authors_metadata data_sample/KOST/authors_metadata5.csv --teachers_metadata data_sample/KOST/teachers_metadata.csv --translations data_sample/KOST/translations.csv --tokenization_interprocessing data_sample/processing.tokenization --annotation_interprocessing data_sample/processing.annotation --overwrite_tokenization --overwrite_annotation
```

## Parameter descriptions
### --svala_folder
Path to directory with `*.svala` files.

### --results_folder
Destination of results folder.

### --raw_text
Path to directory that contains raw texts.

### --texts_metadata
Location of metadata csv that contains information about texts.

### --authors_metadata
Location of metadata csv that contains information about authors.

### --teachers_metadata
Location of metadata csv that contains information about teachers.

### --translations
Path to mapper that translates column names in metadata files.

### --tokenization_interprocessing
Path to file where tokenized semi processed data is stored, to be able to proceed with processsing without rerunning whole test.

### --overwrite_tokenization
Tag that forces script to redo tokenization and overrides interprocessing file.

### --annotation_interprocessing
Path to file where annotated semi processed data is stored, to be able to proceed with processsing without rerunning whole test.

### --overwrite_annotation
Tag that forces script to redo annotation and overrides interprocessing file.


##