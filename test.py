from sys import argv
import sys
import os
import os.path
import subprocess
import re
import gzip

os.chdir(argv[1])
MIN_TEST_CASES = 8
MIN_FEATURES = 2
MAX_TITLE_SIZE = 100
NUM_SAMPLE_ROWS = 5
NUM_SAMPLE_COLUMNS = 5
CHECK_MARK = '&#9989;'
RED_X = '&#10060;'
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
REQUIRED_FILES = [KEY_DATA_NAME, KEY_META_DATA_NAME, DOWNLOAD_FILE_NAME, INSTALL_FILE_NAME, PARSE_FILE_NAME, CLEANUP_FILE_NAME, DESCRIPTION_FILE_NAME]


def check_folder():
    out_string = '### Testing Directory . . .\n\n'
    Pass = True
    fileList = os.listdir(argv[1])
    for path in fileList:
        if path[0] != '.':
            fileCheckString = str(
                subprocess.check_output(['file', '-b', path]))
            if not re.search(r"ASCII", fileCheckString) and not re.search(r"empty", fileCheckString) and not re.search(
                    r"script text", fileCheckString) and not re.search(r"directory", fileCheckString):
                out_string += "{0}\t{1} is not a text file.\n\n".format(
                    RED_X, path)
                Pass = False
        if os.path.getsize(path) > 1000000:
            out_string += RED_X + '\t' + path + ' is too large ( ' + str(
                int(os.path.getsize(path) / 1000000)) + 'MB; max size: 1MB)\n\n'
            Pass = False
    if TEST_DATA_NAME in fileList or TEST_META_DATA_NAME in fileList or ".gitignore" in fileList:
        out_string += '{0}\t Neither {1} nor {2} nor .gitignore should exist in directory.\n\n'.format(RED_X, TEST_DATA_NAME, TEST_META_DATA_NAME)
        Pass = False
    if Pass:
        out_string += '#### Results: PASS\n---\n'
        print('\t\tPASS', flush=True)
    else:
        out_string += '#### Results: **<font color=\"red\">FAIL</font>**\n---\n'
        print('\t\tFAIL', flush=True)
    return [out_string, Pass]


def test_metadata(key_file_path, test_file_path):
    numRows = 1
    testNumber = 0
    samples = set()
    outString = "### \"" + test_file_path + \
        "\" Test Cases (from rows in test file). . .\n\n"
    Pass = True
    with gzip.open(test_file_path, 'r') as testFile:
        rows = []
        variables = {}
        keyFile = open(key_file_path, 'r')
        testHeaderData = testFile.readline().decode().rstrip('\n').split('\t')
        if len(testHeaderData) is not 3:
            Pass = False
            outString += RED_X + '\t' + test_file_path + \
                ' must contain exactly 3 columns.\n\n'
        else:
            if testHeaderData[0] != "Sample":
                outString += RED_X + '\tFirst column of file must be titled \"Sample\"\n\n'
                Pass = False
            else:
                outString += CHECK_MARK + '\tFirst column of file is titled \"Sample\"\n\n'
            keyFile.readline()
            for line in testFile:
                numRows += 1
                data = line.decode().rstrip('\n').split('\t')
                rows.append(line.decode().rstrip('\n'))
                samples.add(data[0])
                if data[1] not in variables.keys():
                    variables[data[1]] = [data[2]]
                else:
                    if data[2] not in variables[data[1]]:
                        variables[data[1]].append(data[2])
            for variable in variables.keys():
                if len(variables[variable]) == 1:
                    outString += RED_X + '\tAll values for variable \"' + str(variable) + '\" are the same(\"' + str(
                        variables[variable][0]) + '\").\n\n'
                    Pass = False
                elif len(variables[variable]) == 0:
                    outString += RED_X + '\tAll values for variable \"' + \
                        str(variable) + '\" are empty.\n\n'
                    Pass = False
            del variables
            for line in keyFile:
                testNumber += 1
                if line.rstrip('\n') not in rows:
                    outString += RED_X + '\tRow ' + str(testNumber) + ': Fail\n- \"' + line.rstrip(
                        '\n') + '\" is not found.\n\n'
                    Pass = False
                else:
                    outString += CHECK_MARK + '\tRow ' + \
                        str(testNumber) + ': Success\n\n'
        if Pass:
            outString += "#### Results: PASS\n---\n"
            print('\t\tPASS', flush=True)
        else:
            outString += "#### Results: **<font color=\"red\">FAIL</font>**\n---\n"
            print('\t\tFAIL', flush=True)
        return [outString, Pass, len(testHeaderData), numRows, samples]


def is_list_unique(test_list):
    compareList = test_list
    for i in range(len(test_list)):
        del compareList[0]
        if test_list[i] in compareList:
            return False
    return True


def create_md_table(columns, rows, file_path):
    outString = '\n### First ' + \
        str(columns) + ' columns and ' + str(rows) + \
        ' rows of ' + file_path + ':\n\n'
    with gzip.open(file_path, 'r') as inFile:
        for i in range(rows):
            line = inFile.readline().decode().rstrip('\n').split('\t')
            if i == 1:
                for j in range(columns):
                    outString += '|\t---\t'
                outString += '|\n'
            outString = outString + '|'
            for j in range(columns):
                outString = outString + '\t' + line[j] + '\t|'
            outString = outString + '\n'
    outString += '\n'
    return outString


def check_zip(file_list):
    fail = False
    outString = ""
    for path in file_list:
        fileCheckString = str(subprocess.check_output(['file', '-b', path]))
        if os.path.exists(path):
            if re.search(r"gzip compressed data", fileCheckString):
                outString += CHECK_MARK + '\t' + path + ' was created and zipped correctly.\n\n'
            else:
                outString += RED_X + '\t' + path + 'exists, but was not zipped correctly.\n\n'
                fail = True
        else:
            outString += RED_X + '\t' + path + ' does not exist.\n\n'
            fail = True
    if fail:
        outString += '#### Results: **<font color=\"red\">FAIL</font>**\n---\n'
        print('\t\tFAIL', flush=True)
    else:
        outString += '#### Results: PASS\n---\n'
        print('\t\tPASS', flush=True)

    return [outString, fail]


def has_one_feature(meta_data):
    with gzip.open(meta_data, 'r') as metaDataFile:
        samples = []
        for i in range(3):
            data = metaDataFile.readline().decode().rstrip('\n').split('\t')
            if i != 0:
                samples.append(data[0])
        metaDataFile.close()
    if samples[0] == samples[1]:
        return False
    else:
        return True


def test_key_files(file_list, min_test_cases, min_features, one_feature):
    outString = "### Testing Key Files:\n\n"
    fail = False
    minSamples = 2
    for path in file_list:
        if one_feature:
            if path == KEY_META_DATA_NAME:
                min_features = 1
        keyFile = open(path, 'r')
        numTests = 0
        samples = {}
        keyFile.readline()
        for line in keyFile:
            data = line.rstrip('\n').split('\t')
            if data[0] not in samples.keys():
                samples[data[0]] = [data[1]]
            else:
                if data[1] not in samples[data[0]]:
                    samples[data[0]].append(data[1])
            numTests += 1
        keyFile.close()
        if len(samples.keys()) < minSamples:
            outString += RED_X + '\t' + path + ' does not contain enough unique samples to test (min: ' + str(
                minSamples) + ')\n\n'
            fail = True
        else:
            outString += CHECK_MARK + '\t' + path + \
                ' contains enough unique samples to test\n\n'
        for sample in samples:
            if len(samples[sample]) < min_features:
                outString += RED_X + '\t\"' + sample + '\" does not have enough features to test (min: ' + str(
                    min_features) + ')\n\n'
                fail = True
        if numTests == 0:
            outString += RED_X + '\t' + path + ' is empty\n\n'
            fail = True
        elif numTests < min_test_cases:
            outString += RED_X + '\t' + path + ' does not contain enough test cases. (' + str(
                numTests) + '; min: ' + str(min_test_cases) + ')\n\n'
            fail = True
        else:
            outString += CHECK_MARK + '\t' + path + ' contains enough test cases (' + str(numTests) + '; min: ' + str(
                min_test_cases) + ')\n\n'
    if fail:
        outString += '#### Results: **<font color=\"red\">FAIL</font>**\n---\n'
        print('\t\tFAIL', flush=True)
    else:
        outString += '#### Results: PASS\n---\n'
        print('\t\tPASS', flush=True)
    return [outString, fail]


def test_data(key_file_name, test_file_path):
    numRows = 1  # 1 to account for Column Header Row
    testNumber = 0
    Pass = True
    passedTestCases = True
    outString = '### \"' + test_file_path + \
        '\" Test Cases (from rows in test file). . .\n\n'
    testFileDict = {}
    samples = set()
    # print('\t1. Opening file...', flush=True)
    with gzip.open(test_file_path, 'r') as testFile:
        keyFile = open(key_file_name, 'r')
        # print('\t2. Testing header...', flush=True)
        testHeaderData = testFile.readline().decode().rstrip('\n').split('\t')
        if testHeaderData[0] != "Sample":
            outString += RED_X + '\tFirst column of file must be titled \"Sample\"\n\n'
            passedTestCases = False
        else:
            outString += CHECK_MARK + '\tFirst column of file is titled \"Sample\"\n\n'
        keyFile.readline().rstrip('\n').split('\t')
        numColumns = len(testHeaderData)
        # print('\t3. Load into dictionary... ', flush=True)
        for line in testFile:
            testData = line.decode().rstrip('\n').split('\t')
            testFileDict[testData[0]] = testData
            numRows += 1
            samples.add(testData[0])
        testFile.close()
        # print('\t\t3-Success', flush=True)
        for line in keyFile:
            testNumber += 1
            fail = True
            keyData = line.rstrip('\n').split('\t')
            sample = keyData[0]
            variable = keyData[1]
            value = keyData[2]
            if value == "\"\"":
                value = ""
            compareString = '||\tSample\t|\tColumn\t|\tRow\t|\n|\t---\t|\t---\t|\t---\t|\t---\t|\n|\t**Expected**\t' \
                            '|\t{0}\t|\t{1}\t|\t{2}\t|\n'.format(sample, variable, value)
            # Testing first column
            # print('\t4. Testing first column...', flush=True)
            if sample not in testFileDict.keys():
                failString = '- \"' + sample + '\" is not found in sample column.'
                # Testing if second column is in Header
                # print('\t5. Testing second column...', flush=True)
            else:
                failString = '- \"' + variable + '\" is not found in Headers'
                for key in testFileDict.keys():
                    if sample in key:
                        for i in range(len(testHeaderData)):
                            # Testing if values match
                            # print('\t6. Testing third column...', flush=True)
                            if variable == testHeaderData[i] and value == testFileDict[key][i]:
                                fail = False
                            elif variable == testHeaderData[i] and value != testFileDict[key][i]:
                                fail = True
                                failString = '\n' + compareString + '|\t**User Generated**\t|\t' + key + '\t|\t' + \
                                             testHeaderData[i] + '\t|\t' + \
                                    testFileDict[key][i] + '\t|\n'
            # print('\t7. Complete', flush=True)
            if fail:
                outString += RED_X + '\tRow ' + \
                    str(testNumber) + ': Fail\n' + failString + '\n\n'
                passedTestCases = False
            else:
                outString = outString + CHECK_MARK + \
                    '\tRow ' + str(testNumber) + ': Success\n\n'
        if passedTestCases:
            outString = outString + '#### Results: PASS\n---'
            print('\t\tPASS', flush=True)
        else:
            outString = outString + '#### Results: **<font color=\"red\">FAIL</font>**\n---'
            print('\t\tFAIL', flush=True)
            Pass = False
    # testFile.close()
    keyFile.close()
    return [outString, Pass, numColumns, numRows, samples]


def files_exist(file_list):
    Pass = True
    outString = '\n### Testing file paths:\n\n'
    for path in file_list:
        if os.path.exists(path):
            outString += CHECK_MARK + '\t' + path + ' exists.\n\n'
        else:
            outString += RED_X + '\t' + path + ' does not exist.\n\n'
            Pass = False
    if not Pass:
        outString += '#### Results: **<font color=\"red\">FAIL</font>**\n---\n'
        print('\t\tFAIL', flush=True)
    else:
        print('\t\tPASS', flush=True)
    return [outString, Pass]


def test_cleanup(original_directory):
    Pass = True
    outString = '### Testing Directory after cleanup . . .\n\n'
    currentDirectory = os.listdir(argv[1])
    for ITEM in currentDirectory:
        if ITEM not in original_directory:
            Pass = False
            outString += RED_X + '\t\"' + ITEM + \
                '\" should have been deleted during cleanup.\n\n'
    if Pass:
        outString += '#### Results: PASS\n---\n'
        print('\t\tPASS', flush=True)
    else:
        outString += '#### Results: **<font color=\"red\">FAIL</font>**\n---\n'
        print('\t\tFAIL', flush=True)
    return [outString, Pass]


def test_description(description_file_name):
    Pass = True
    outString = '### Testing Description File . . .\n\n'
    if os.path.exists(description_file_name):
        description_file = open(description_file_name, 'r')
        title = description_file.readline().rstrip('\n')
        # ID = description_file.readline().rstrip('\n').split()
        if "## " not in title:
            outString += RED_X + \
                '\tFirst line in description file should contain \"## <name of data set>\"\n\n'
            Pass = False
        # if len(ID) > 2 or ID[0] != "##":
        #    outString += redX + '\tSecond line in description file should contain \"## <data-set-ID>\". ' \
        #                       'The data set ID shouldn\'t contain any spaces.\n\n'
        #    Pass = False
        description_file.close()
        if len(title) > MAX_TITLE_SIZE + 3:
            Pass = False
            outString += RED_X + '\tTitle in ' + description_file_name + ' should not be longer than ' + \
                str(MAX_TITLE_SIZE) + ' characters\n\n'
        else:
            outString += CHECK_MARK + '\tTitle is less than ' + \
                str(MAX_TITLE_SIZE) + ' characters\n\n'
    else:
        outString += RED_X + '\t ' + description_file_name + ' does not exist\n\n'
        Pass = False
    if Pass:
        outString += '#### Results: PASS\n---\n'
        print('\t\tPASS', flush=True)
    else:
        outString += '#### Results: **<font color=\"red\">FAIL</font>**\n---\n'
        print('\t\tFAIL', flush=True)
    return [outString, Pass]


def test_bash_script(bash_script_name):
    outString = "Executing " + bash_script_name + ": "
    Pass = True
    os.system('chmod +x ./' + bash_script_name)
    results = subprocess.run(
        "./" + bash_script_name, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    if results.returncode != 0:
        outString += '\n\n' + RED_X + '\t' + bash_script_name + ' returned an error:\n~~~bash\n' + \
                     results.stderr.decode().rstrip('\n') + '\n~~~\n\n'
        Pass = False
        print('\t\tFAIL', flush=True)
    else:
        outString += "Success\n\n"
        print('\t\tPASS', flush=True)
    return [outString, Pass]


def run_install(install_script_name):
    outString = "### Running Install . . .\n\n"
    Pass = True
    if not os.path.exists(install_script_name):
        Pass = False
        outString += RED_X + "\t" + install_script_name + " does not exist.\n\n"
    else:
        results = test_bash_script(install_script_name)
        outString += results[0]
        if not results[1]:
            Pass = False
    if Pass:
        outString += "#### Results: PASS\n---\n"
    else:
        outString += "#### Results: **<font color=\"red\">FAIL</font>**\n---\n"
    return [outString, Pass]


def no_commas(file_list):
    Pass = True
    outString = "### Making sure no commas exist in either file . . .\n\n"
    for path in file_list:
        with gzip.open(path, 'r') as file:
            if "," in file.read().decode():
                Pass = False
                outString += RED_X + '\tComma(s) exist in ' + path + '\n\n'
            else:
                outString += CHECK_MARK + '\tNo Commas in ' + path + '\n\n'
        file.close()
    if Pass:
        outString += "#### Results: PASS\n---\n"
        print('\t\tPASS', flush=True)
    else:
        outString += "#### Results: **<font color=\"red\">FAIL</font>**\n---\n"
        print('\t\tFAIL', flush=True)
    return [outString, Pass]


def compare_samples(data_samples, meta_data_samples):
    Pass = True
    outString = '### Comparing samples in both files . . .\n\n'
    for item in data_samples:
        if item not in meta_data_samples:
            outString += RED_X + '\t Sample \"' + item + '\" is in \"' + TEST_DATA_NAME + '\" but not in \"' + \
                TEST_META_DATA_NAME + '\"\n\n'
            Pass = False
    for item in meta_data_samples:
        if item not in data_samples:
            outString += RED_X + '\t Sample \"' + item + '\" is in \"' + TEST_META_DATA_NAME + '\" but not in \"' + \
                TEST_DATA_NAME + '\"\n\n'
            Pass = False
    if not Pass:
        outString += '#### Results: **<font color=\"red\">FAIL</font>**\n\n---\n'
        print('\t\tFAIL', flush=True)
    else:
        outString += CHECK_MARK + '\tSamples are the same in both \"' + TEST_DATA_NAME + '\" & \"' + \
            TEST_META_DATA_NAME + '\"\n\n'
        outString += '#### Results: PASS\n\n---\n'
        print('\t\tPASS', flush=True)
    return [outString, Pass]


statusFile = open("/app/StatusReports/" + STATUS_FILE_NAME, 'w')
complete = True
# Title Status.md
statusFile.write("<h1><center>" + argv[2] + "</center></h1>\n\n")

# Check directory
print('\tTestingDirectory...', flush=True)
originalDirectory = os.listdir(argv[1])
checkFolderResults = check_folder()
statusFile.write(checkFolderResults[0])
if not checkFolderResults[1]:
    complete = False

# Test Description
print('\tTesting Description File...', flush=True)
descriptionResults = test_description(DESCRIPTION_FILE_NAME)
statusFile.write(descriptionResults[0])
if not descriptionResults[1]:
    complete = False

# Run install script
print('\tRunning Install...', flush=True)
installScript = run_install(INSTALL_FILE_NAME)
statusFile.write(installScript[0])
if not installScript[1]:
    complete = False
else:
    # Making sure path exists
    print('\tTesting file paths...', flush=True)
    filesExist = files_exist(REQUIRED_FILES)
    statusFile.write(filesExist[0])
    if filesExist[1] and complete:
        statusFile.write('*Running user code . . .*\n\n')

        # Run User-generated scripts
        print('\tExecuting ' + DOWNLOAD_FILE_NAME + '...', flush=True)
        downloadScript = test_bash_script(DOWNLOAD_FILE_NAME)
        statusFile.write(downloadScript[0])
        if not downloadScript[1]:
            complete = False
        else:
            print('\tExecuting ' + PARSE_FILE_NAME + '...', flush=True)
            parseScript = test_bash_script(PARSE_FILE_NAME)
            statusFile.write(parseScript[0])
            if not parseScript[1]:
                complete = False
            else:
                print('\tTesting output file types (gzip)...', flush=True)
                zipResults = check_zip([TEST_DATA_NAME, TEST_META_DATA_NAME])
                statusFile.write(zipResults[0])
                if zipResults[1]:
                    complete = False

                # Make Sure key files have enough Test cases and test the required minimum of features
                # First, however, check to see if metadata file has more than one feature
                print('\tTesting ' + KEY_DATA_NAME + ' & ' +
                      KEY_META_DATA_NAME + '...', flush=True)
                keyFileResults = test_key_files([KEY_DATA_NAME, KEY_META_DATA_NAME], MIN_TEST_CASES, MIN_FEATURES,
                                                has_one_feature(TEST_META_DATA_NAME))
                statusFile.write(keyFileResults[0])
                if keyFileResults[1]:
                    complete = False

                # DATA FILE
                print('\tTesting ' + TEST_DATA_NAME + '...', flush=True)
                testDataResults = test_data(KEY_DATA_NAME, TEST_DATA_NAME)
                statusFile.write(create_md_table(
                    NUM_SAMPLE_COLUMNS, NUM_SAMPLE_ROWS, TEST_DATA_NAME))
                statusFile.write(
                    '**Columns: ' + str(testDataResults[2]) + ' Rows: ' + str(testDataResults[3]) + '**\n\n---\n')
                statusFile.write(testDataResults[0])
                if not testDataResults[1]:
                    complete = False

                # METADATA FILE
                print('\tTesting ' + TEST_META_DATA_NAME + '...', flush=True)
                metaDataResults = test_metadata(
                    KEY_META_DATA_NAME, TEST_META_DATA_NAME)
                statusFile.write(create_md_table(
                    3, NUM_SAMPLE_ROWS, TEST_META_DATA_NAME))
                statusFile.write(
                    '**Columns: ' + str(metaDataResults[2]) + ' Rows: ' + str(metaDataResults[3]) + '**\n\n---\n')
                statusFile.write(metaDataResults[0])
                if not metaDataResults[1]:
                    complete = False

                # Test for commas in files
                print('\tTesting for no commas in either file...', flush=True)
                commaResults = no_commas([TEST_META_DATA_NAME, TEST_DATA_NAME])
                statusFile.write(commaResults[0])
                if not commaResults[1]:
                    complete = False

                # Compare Samples in metaData and DATA
                print('\tTesting that samples are the same in both files...', flush=True)
                sampleResults = compare_samples(
                    testDataResults[4], metaDataResults[4])
                statusFile.write(sampleResults[0])
                if not sampleResults[1]:
                    complete = False

                # Move output files
                if complete:
                    os.system('cp data.tsv.gz ../')
                    os.system('cp metadata.tsv.gz ../')

                # CLEANUP
                print('\tTesting cleanup...', flush=True)
                os.system('chmod +x ./' + CLEANUP_FILE_NAME)
                os.system('./' + CLEANUP_FILE_NAME)
                cleanupResults = test_cleanup(originalDirectory)
                statusFile.write(cleanupResults[0])
                if not cleanupResults[1]:
                    complete = False
    else:
        complete = False
statusFile.close()
# Write Status Result to top of Status File
with open('/app/StatusReports/' + STATUS_FILE_NAME, 'r') as statusFileOriginal:
    header = statusFileOriginal.readline().rstrip('\n')
    statusContents = statusFileOriginal.read()
with open('/app/StatusReports/' + STATUS_FILE_NAME, 'w') as statusComplete:
    statusComplete.write(header + '\n')
    if complete:
        statusComplete.write(
            '<h2><center> Status: Complete </center></h2>\n\n' + statusContents)
        print('\tTesting Complete: Results = Pass', flush=True)
        sys.exit()
    else:
        statusComplete.write(
            '<h2><center> Status: In Progress </center></h2>\n\n' + statusContents)
        print('\tTesting Complete: Results = Fail (See \"https://srp33.github.io/WishBuilder/StatusReports/' +
              argv[2] + '-status\" for details)', flush=True)
        sys.exit(1)
