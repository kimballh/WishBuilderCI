MIN_TEST_CASES = 8
MIN_FEATURES = 2
MIN_SAMPLES = 2
MAX_TITLE_SIZE = 300
NUM_SAMPLE_ROWS = 5
NUM_SAMPLE_COLUMNS = 5
CHECK_MARK = '&#9989;'
RED_X = '&#10060;'
WARNING_SYMBOL = "<p><font color=\"orange\" size=\"+2\">&#9888;\t</font>"
KEY_DATA_NAME = 'test_data.tsv'
KEY_META_DATA_NAME = 'test_metadata.tsv'
TEST_DATA_NAME = 'data.tsv.gz'
TEST_META_DATA_NAME = 'metadata.tsv.gz'
STATUS_FILE_NAME = argv[2] + '-status.md'
DOWNLOAD_FILE_NAME = 'download.sh'
INSTALL_FILE_NAME = 'install.sh'
PARSE_FILE_NAME = 'parse.sh'
CLEANUP_FILE_NAME = 'cleanup.sh'
DESCRIPTION_FILE_NAME = 'description.md'
CONFIG_FILE_NAME = 'config.yaml'
REQUIRED_FILES = [KEY_DATA_NAME, KEY_META_DATA_NAME, DOWNLOAD_FILE_NAME, INSTALL_FILE_NAME, PARSE_FILE_NAME, CLEANUP_FILE_NAME, DESCRIPTION_FILE_NAME, CONFIG_FILE_NAME]
REQUIRED_CONFIGS = ['title', 'featureDescription', 'featureDescriptionPlural']
# These are the executables that will be ran to produce the data and metadata files (They are executed in this order)
USER_SCRIPTS = [INSTALL_FILE_NAME, DOWNLOAD_FILE_NAME, PARSE_FILE_NAME]
KEY_FILES = [KEY_DATA_NAME, KEY_META_DATA_NAME]