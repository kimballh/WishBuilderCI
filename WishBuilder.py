from PullRequest import PullRequest
from GithubDao import GithubDao
from SqliteDao import SqliteDao
from private import GH_TOKEN
from Constants import *
from sys import argv
import sys
import os
import os.path
import subprocess
import re
import gzip
import datetime
import yaml

SQLITE_FILE = './prHistory.sql'
WB_DIRECTORY = '/app'
TESTING_LOCATION = '../'
root = os.getcwd()

sql_dao = SqliteDao(SQLITE_FILE)
git_dao = GithubDao('https://api.github.com/repos/srp33/WishBuilder/', GH_TOKEN)


def check_history():
    history = sql_dao.get_all()
    prs = git_dao.get_prs()

    for pr in prs:
        if pr.pr in history.keys():
            if pr.sha not in history[pr.pr] and not sql_dao.in_progress(pr):
                return pr
        else:
            return pr
    return None


def test(pr: PullRequest):
    os.mkdir('{}{}'.format(TESTING_LOCATION, pr.branch))
    pr.status = 'In progress'
    pr.email = git_dao.get_email(pr.sha)
    # sql_dao.update(pr)
    valid, description_only, download_urls = git_dao.check_files(pr)
    if valid:
        pr.report.valid_files = True
        if description_only:
            git_dao.merge(pr)
            geney_convert(pr)
            pr.set_updated()
        else:
            # Download Files from Github and put them in the testing directory
            for file in download_urls:
                git_dao.download_file(file, '{}{}/'.format(TESTING_LOCATION, pr.branch))
            # Run tests
            test_folder(pr)
            test_config(pr)
            test_files(pr)
            original_directory = os.listdir(os.getcwd())
            # if this test doesn't pass, it is pointless to move on, because the output files will be wrong
            if test_scripts(pr):
                test_key_files(pr)
                # Test Data
                num_columns_data, num_rows_data, data_samples = test_data(pr)
                pr.report.data_preview = create_md_table(NUM_SAMPLE_COLUMNS, NUM_SAMPLE_ROWS, TEST_DATA_NAME)
                pr.report.data_preview += '**Columns: {} Rows: {}**\n\n---\n'.format(num_columns_data, num_rows_data)
                # Test Metadata
                num_columns_metadata, num_rows_metadata, metadata_samples, bad_variables = test_metadata(pr)
                pr.report.meta_data_preview = create_md_table(NUM_SAMPLE_COLUMNS, NUM_SAMPLE_ROWS, TEST_META_DATA_NAME)
                pr.report.data_preview += '**Columns: {} Rows: {}**\n\n---\n'\
                    .format(num_columns_metadata, num_rows_metadata)
                compare_samples(data_samples, metadata_samples, pr)
                test_cleanup(original_directory, pr)
                with open(CONFIG_FILE_NAME, 'a') as configFile:
                    configFile.write('numSamples: {0}\nmetaVariables: {1}\nfeatureVariables: {2}'.
                                     format(pr.num_samples, pr.meta_variables, pr.feature_variables))
    else:
        pr.report.valid_files = False
    if pr.check_if_passed():
        print('Passed!')
    else:
        print('Failed!')







def test_folder(pr: PullRequest):
    report = '### Testing Directory . . .\n\n'
    passed = True
    file_list = os.listdir('{}{}'.format(TESTING_LOCATION, pr.branch))
    for path in file_list:
        if path[0] != '.':
            file_check_string = str(
                subprocess.check_output(['file', '-b', path]))
            if not re.search(r"ASCII", file_check_string) and not re.search(r"empty", file_check_string) and not \
                    re.search(r"script text", file_check_string) and not re.search(r"directory", file_check_string):
                report += "{0}\t{1} is not a text file.\n\n".format(RED_X, path)
                passed = False
        if os.path.getsize(path) > 1000000:
            report += RED_X + '\t' + path + ' is too large ( ' + str(int(os.path.getsize(path) / 1000000)) + \
                      'MB; max size: 1MB)\n\n'
            passed = False
    if TEST_DATA_NAME in file_list or TEST_META_DATA_NAME in file_list or ".gitignore" in file_list:
        report += '{0}\t Neither {1} nor {2} nor .gitignore should exist in directory.\n\n'\
            .format(RED_X, TEST_DATA_NAME, TEST_META_DATA_NAME)
        passed = False
    if passed:
        report += '#### Results: PASS\n---\n'
        print('\t\tPASS', flush=True)
    else:
        report += '#### Results: **<font color=\"red\">FAIL</font>**\n---\n'
        print('\t\tFAIL', flush=True)
    pr.report.directory_test_report = report
    pr.report.pass_directory_test = passed
    return passed


def test_config(pr: PullRequest):
    passed = True
    report = '### Testing Configuration File . . .\n\n'
    if os.path.exists(CONFIG_FILE_NAME):
        with open(CONFIG_FILE_NAME, 'r') as stream:
            configs = yaml.load(stream)
            for config in REQUIRED_CONFIGS:
                if config not in configs.keys():
                    passed = False
                    report += RED_X + '\t' + CONFIG_FILE_NAME + ' does not contain a configuration for \"'\
                              + config + '\".\n\n'
            if passed:
                report += CHECK_MARK + '\t' + CONFIG_FILE_NAME + ' contains all necessary configurations.\n\n'
            if 'title' in configs:
                if len(configs['title']) > MAX_TITLE_SIZE:
                    passed = False
                    report += RED_X + '\tDataset Title cannot exceed ' + str(MAX_TITLE_SIZE) + ' characters.\n\n'
                else:
                    report += CHECK_MARK + '\tTitle is less than ' + str(MAX_TITLE_SIZE) + ' characters\n\n'
    else:
        report += RED_X + '\t ' + CONFIG_FILE_NAME + ' does not exist\n\n'
        passed = False
    if os.path.exists(DESCRIPTION_FILE_NAME):
        with open(DESCRIPTION_FILE_NAME, 'r') as description_file:
            if len(description_file.read()) < 10:
                passed = False
                report += RED_X + '\t' + DESCRIPTION_FILE_NAME + ' must contain a description of the dataset.\n\n'
            else:
                report += CHECK_MARK + '\t' + DESCRIPTION_FILE_NAME + ' contains a description.\n\n'
    else:
        report += RED_X + '\t ' + DESCRIPTION_FILE_NAME + ' does not exist\n\n'
        passed = False
    if passed:
        report += '#### Results: PASS\n---\n'
        print('\t\tPASS', flush=True)
    else:
        report += '#### Results: **<font color=\"red\">FAIL</font>**\n---\n'
        print('\t\tFAIL', flush=True)
    pr.report.configuration_test_report = report
    pr.report.pass_configuration_test = passed
    return passed


def test_files(pr: PullRequest):
    cwd = os.getcwd()
    os.chdir('{}{}'.format(TESTING_LOCATION, pr.branch))
    passed = True
    report = '\n### Testing file paths:\n\n'
    for path in REQUIRED_FILES:
        if os.path.exists(path):
            report += CHECK_MARK + '\t' + path + ' exists.\n\n'
        else:
            report += RED_X + '\t' + path + ' does not exist.\n\n'
            passed = False
    if passed:
        report += '#### Results: PASS\n---\n'
        print('\t\tPASS', flush=True)
    else:
        report += '#### Results: **<font color=\"red\">FAIL</font>**\n---\n'
        print('\t\tFAIL', flush=True)
    pr.report.pass_file_test = passed
    pr.report.file_test_report = report
    os.chdir(cwd)
    return passed


def test_scripts(pr: PullRequest):
    report = "### Running user scripts . . .\n\n"
    passed = True
    for script in USER_SCRIPTS:
        result, successful = test_bash_script(script)
        report += result
        if not successful:
            passed = False
            break
    result, successful = check_zip()
    report += result
    if not successful:
        passed = False
    if passed:
        report += "#### Results: PASS\n---\n"
    else:
        report += "#### Results: **<font color=\"red\">FAIL</font>**\n---\n"
    pr.report.pass_script_test = passed
    pr.report.script_test_report = report
    return passed


def test_bash_script(bash_script_name):
    report = "Executing " + bash_script_name + ": "
    passed = True
    os.system('chmod +x ./' + bash_script_name)
    results = subprocess.run(
        "./" + bash_script_name, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    if results.returncode != 0:
        report += '\n\n' + RED_X + '\t' + bash_script_name + ' returned an error:\n~~~bash\n' + \
                     results.stderr.decode().rstrip('\n') + '\n~~~\n\n'
        passed = False
        print('\t\tFAIL', flush=True)
    else:
        report += "Success\n\n"
        print('\t\tPASS', flush=True)
    return report, passed


def check_zip():
    passed = True
    report = ""
    for path in [TEST_DATA_NAME, TEST_META_DATA_NAME]:
        file_type = str(subprocess.check_output(['file', '-b', path]))
        if os.path.exists(path):
            if re.search(r"gzip compressed data", file_type):
                report += CHECK_MARK + '\t' + path + ' was created and zipped correctly.\n\n'
            else:
                report += RED_X + '\t' + path + 'exists, but was not zipped correctly.\n\n'
                passed = False
        else:
            report += RED_X + '\t' + path + ' does not exist.\n\n'
            passed = False
    return report, passed


def test_key_files(pr: PullRequest):
    report = "### Testing Key Files:\n\n"
    passed = True
    MIN_SAMPLES = 2
    for path in KEY_FILES:
        if has_one_feature(TEST_META_DATA_NAME):
            if path == KEY_META_DATA_NAME:
                MIN_FEATURES = 1
        key_file = open(path, 'r')
        num_tests = 0
        samples = {}
        key_file.readline()
        for line in key_file:
            num_tests += 1
            data = line.rstrip('\n').split('\t')
            if len(data) is not 3 and len(data) is not 0:
                passed = False
                report += RED_X + '\tRow ' + str(num_tests) + ' of \"' + path + '\" should contain exactly three columns.\n\n'
            elif len(data) is not 0:
                if data[0] not in samples.keys():
                    samples[data[0]] = [data[1] + data[2]]
                else:
                    if data[1] + data[2] not in samples[data[0]]:
                        samples[data[0]].append(data[1] + data[2])
        key_file.close()
        if len(samples.keys()) < MIN_SAMPLES:
            report += RED_X + '\t' + path + ' does not contain enough unique samples to test (min: ' + str(
                MIN_SAMPLES) + ')\n\n'
            passed = False
        else:
            report += CHECK_MARK + '\t' + path + \
                ' contains enough unique samples to test\n\n'
        for sample in samples:
            if len(samples[sample]) < MIN_FEATURES:
                report += RED_X + '\t\"' + sample + '\" does not have enough features to test (min: ' + str(
                    MIN_FEATURES) + ')\n\n'
                passed = False
        if num_tests == 0:
            report += RED_X + '\t' + path + ' is empty\n\n'
            passed = False
        elif num_tests < MIN_TEST_CASES:
            report += RED_X + '\t' + path + ' does not contain enough test cases. (' + str(
                num_tests) + '; min: ' + str(MIN_TEST_CASES) + ')\n\n'
            passed = False
        else:
            report += CHECK_MARK + '\t' + path + ' contains enough test cases (' + str(num_tests) + '; min: ' + str(
                MIN_TEST_CASES) + ')\n\n'
    if passed:
        report += '#### Results: PASS\n---\n'
        print('\t\tPASS', flush=True)
    else:
        report += '#### Results: **<font color=\"red\">FAIL</font>**\n---\n'
        print('\t\tFAIL', flush=True)
    pr.report.key_test_report = report
    pr.report.pass_key_test = passed


def has_one_feature(meta_data):
    if meta_data in os.listdir(os.getcwd()):
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
    else:
        return False


def test_data(pr: PullRequest):
    no_commas = True
    num_rows = 1  # 1 to account for Column Header Row
    num_columns = 0
    test_number = 0
    passed = True
    report = '### \"' + TEST_DATA_NAME + '\" Test Cases (from rows in test file). . .\n\n'
    key_file_dict = {}
    samples = set()
    tested_rows = []
    column_headers = []
    key_samples = []
    results = {}

    with gzip.open(TEST_DATA_NAME, 'r') as testFile:
        key_file = open(KEY_DATA_NAME, 'r')
        test_header_data = testFile.readline().decode().rstrip('\n').split('\t')
        for column in test_header_data:
            if column not in column_headers:
                column_headers.append(column)
            else:
                passed = False
                report += RED_X + '\t' + column + ' is in ' + TEST_DATA_NAME + ' column headers more than once\n\n'
                report += '#### Results: **<font color=\"red\">FAIL</font>**\n---'
                print('\t\tFAIL', flush=True)
                return [report, passed, num_columns, num_rows, samples, num_columns - 1]
        if test_header_data[0] != "Sample":
            report += RED_X + '\tFirst column of file must be titled \"Sample\"\n\n'
        else:
            report += CHECK_MARK + '\tFirst column of file is titled \"Sample\"\n\n'
        key_file.readline().rstrip('\n').split('\t')
        num_columns = len(test_header_data)
        for line in key_file:
            test_number += 1
            keyData = line.rstrip('\n').split('\t')
            key_samples.append(keyData[0])
            keyData.append(str(test_number))
            if len(keyData) != 4:
                report += RED_X + '\tRow ' + str(test_number) + ' of \"' + KEY_DATA_NAME + \
                          '\" does not contain 3 columns\n\n'
                passed = False
            else:
                if keyData[0] in key_file_dict.keys():
                    key_file_dict[keyData[0]].extend([keyData])
                else:
                    key_file_dict.setdefault(keyData[0], []).extend([keyData])
        key_file.close()
        for line in testFile:
            num_rows += 1
            if "," in line.decode():
                no_commas = False
            testData = line.decode().rstrip('\n').split('\t')
            samples.add(testData[0])
            if testData[0] in key_file_dict.keys():
                for list_ in key_file_dict[testData[0]]:
                    row = list_[3]
                    tested_rows.append(row)
                    if list_[1] in test_header_data:
                        variableIndex = test_header_data.index(list_[1])
                        if list_[2] == testData[variableIndex]:
                            results[int(row)] = CHECK_MARK + '\tRow ' + row + ': Success\n\n'
                            # report += CHECK_MARK + '\tRow ' + row + ': Success\n\n'
                        else:
                            passed = False
                            fail_string = RED_X + '\tRow: ' + row + ' - FAIL\n\n'
                            fail_string += '||\tSample\t|\tColumn\t|\tRow\t|\n|\t---\t|\t---\t|\t---\t|\t---\t|\n|' \
                                           '\t**Expected**\t|\t{0}\t|\t{1}\t|\t{2}\t|\n'\
                                .format(testData[0], list_[1], list_[2])
                            fail_string += '|\t**User Generated**\t|\t{0}\t|\t{1}\t|\t{2}\t|\n\n'\
                                .format(testData[0], list_[1], testData[variableIndex])
                            results[int(row)] = fail_string
                    else:
                        results[int(row)] = RED_X + '\tRow: ' + row + ' - ' + list_[1] + ' is not found in \"' + \
                                            TEST_DATA_NAME + '\" column headers\n\n'
                        passed = False
        testFile.close()
        if len(tested_rows) < test_number:
            passed = False
            for i in range(test_number):
                if str(i + 1) not in tested_rows:
                    results[i + 1] = RED_X + '\tRow: ' + str(i + 1) + ' - Sample \"' + key_samples[i] + \
                                     '\" is not found in ' + TEST_DATA_NAME + '\n\n'
        for i in range(len(results.keys())):
            report += results[i + 1]
        if passed:
            report += '#### Results: PASS\n---'
            print('\t\tPASS', flush=True)
        else:
            report = report + '#### Results: **<font color=\"red\">FAIL</font>**\n---'
            print('\t\tFAIL', flush=True)
            passed = False
    pr.report.data_tests_report = report
    pr.report.pass_data_tests = passed
    pr.feature_variables = num_columns - 1
    return num_columns, num_rows, samples


def test_metadata(pr: PullRequest):
    num_column_errors = 0
    no_commas = True
    num_rows = 1
    test_number = 0
    tests = []
    passed_tests = []
    samples = set()
    passed = True
    bad_variables = []
    num_variables = 0
    report = "### \"" + TEST_META_DATA_NAME + \
        "\" Test Cases (from rows in test file). . .\n\n"

    key_file = open(KEY_META_DATA_NAME, 'r')
    key_file.readline()
    for line in key_file:
        test_number += 1
        tests.append(line.rstrip('\n'))
    with gzip.open(TEST_META_DATA_NAME, 'r') as testFile:
        variables = {}
        test_header_data = testFile.readline().decode().rstrip('\n').split('\t')
        if len(test_header_data) is not 3:
            passed = False
            report += RED_X + '\t' + TEST_META_DATA_NAME + \
                ' must contain exactly 3 columns.\n\n'
        else:
            if test_header_data[0] != "Sample":
                report += RED_X + '\tFirst column of file must be titled \"Sample\"\n\n'
                passed = False
            else:
                report += CHECK_MARK + '\tFirst column of file is titled \"Sample\"\n\n'
            for line in testFile:
                num_rows += 1
                if "," in line.decode():
                    no_commas = False
                data = line.decode().rstrip('\n').split('\t')
                if (len(data) != 3 or data[2] == "") and num_column_errors < 10:
                    num_column_errors += 1
                    if len(data) != 3:
                        report += RED_X + '\tRow ' + str(num_rows) + ' of ' + TEST_META_DATA_NAME + \
                                  ' must contain exactly 3 columns\n\n'
                    if data[2] == "":
                        report += RED_X + '\tRow ' + str(num_rows) + ' of ' + TEST_META_DATA_NAME + \
                                  ' cannot contain an empty value.\n\n'
                row = line.decode().rstrip('\n')
                if row in tests:
                    passed_tests.append(tests.index(row))
                samples.add(data[0])
                if data[1] not in variables.keys():
                    variables[data[1]] = [data[2]]
                else:
                    if data[2] not in variables[data[1]]:
                        variables[data[1]].append(data[2])
            for variable in variables.keys():
                if len(variables[variable]) == 1:
                    bad_variables.append(variable)
                    report += WARNING_SYMBOL + 'The value for variable \"{}\" for all samples is the same (\"{}\").' \
                                               ' This variable has been removed from {}</p>\n\n'\
                        .format(variable, variables[variable][0], TEST_META_DATA_NAME)
                elif len(variables[variable]) == 0:
                    bad_variables.append(variable)
                    report += WARNING_SYMBOL + 'All values for variable \"{}\" are empty. This variable has been ' \
                                               'removed from {}</p>\n\n'.format(variable, TEST_META_DATA_NAME)
            num_variables = len(variables.keys()) - len(bad_variables)
            del variables
            for i in range(test_number):
                if i in passed_tests:
                    report += CHECK_MARK + '\tRow ' + str(i + 1) + ': Success\n\n'
                else:
                    passed = False
                    report += RED_X + '\tRow ' + str(i + 1) + ': Fail\n- \"' + tests[i] + '\" is not found.\n\n'
    testFile.close()
    if passed:
        report += "#### Results: PASS\n---\n"
        print('\t\tPASS', flush=True)
    else:
        report += "#### Results: **<font color=\"red\">FAIL</font>**\n---\n"
        print('\t\tFAIL', flush=True)

    pr.report.meta_tests_report = report
    pr.report.pass_meta_tests = passed
    pr.meta_variables = num_variables
    return len(test_header_data), num_rows, samples, bad_variables


def create_md_table(columns, rows, file_path):
    table = '\n### First ' + \
        str(columns) + ' columns and ' + str(rows) + \
        ' rows of ' + file_path + ':\n\n'
    with gzip.open(file_path, 'r') as inFile:
        for i in range(rows):
            line = inFile.readline().decode().rstrip('\n').split('\t')
            if i == 1:
                for j in range(columns):
                    table += '|\t---\t'
                table += '|\n'
            table = table + '|'
            for j in range(columns):
                table = table + '\t' + line[j] + '\t|'
            table = table + '\n'
    table += '\n'
    return table


def compare_samples(data_samples, meta_data_samples, pr: PullRequest):
    passed = True
    report = '### Comparing samples in both files . . .\n\n'
    num_errors = 0
    for item in data_samples:
        if item not in meta_data_samples:
            num_errors += 1
            if num_errors < 10:
                passed = False
                report += RED_X + '\t Sample \"' + item + '\" is in \"' + TEST_DATA_NAME + '\" but not in \"' + \
                    TEST_META_DATA_NAME + '\"\n\n'
    for item in meta_data_samples:
        if item not in data_samples:
            num_errors += 1
            if num_errors < 10:
                passed = False
                report += RED_X + '\t Sample \"' + item + '\" is in \"' + TEST_META_DATA_NAME + '\" but not in \"' + \
                    TEST_DATA_NAME + '\"\n\n'
    if num_errors >= 10:
        report += RED_X + '\t More errors are not being printed...\n\n'
        report += '<font color=\"red\">Total sample mismatch errors: ' + str(num_errors) + '</font>\n\n'
    if not passed:
        report += '#### Results: **<font color=\"red\">FAIL</font>**\n\n---\n'
        print('\t\tFAIL', flush=True)
    else:
        report += CHECK_MARK + '\tSamples are the same in both \"' + TEST_DATA_NAME + '\" & \"' + \
            TEST_META_DATA_NAME + '\"\n\n'
        report += '#### Results: PASS\n\n---\n'
        print('\t\tPASS', flush=True)
    pr.report.sample_comparison_report = report
    pr.report.pass_sample_comparison = passed
    pr.num_samples = len(data_samples)
    return passed


def test_cleanup(original_directory, pr: PullRequest):
    os.system('chmod +x ./' + CLEANUP_FILE_NAME)
    os.system('./' + CLEANUP_FILE_NAME)
    passed = True
    report = '### Testing Directory after cleanup . . .\n\n'
    current_directory = os.listdir(argv[1])
    for file in current_directory:
        if file not in original_directory:
            passed = False
            report += RED_X + '\t\"' + file + \
                '\" should have been deleted during cleanup.\n\n'
    if passed:
        report += '#### Results: PASS\n---\n'
        print('\t\tPASS', flush=True)
    else:
        report += '#### Results: **<font color=\"red\">FAIL</font>**\n---\n'
        print('\t\tFAIL', flush=True)
    pr.report.cleanup_report = report
    pr.report.pass_cleanup = passed
    return passed


def geney_convert(pr, simple=False, targz=False):
    print('Converting dataset to Geney format...', flush=True)
    source_directory = '{}/CompleteDataSets/{}'.format(WB_DIRECTORY, pr.branch)
    output_directory = '{}/GeneyDataSets/{}'.format(WB_DIRECTORY, pr.branch)
    if simple:
        os.system('python3 /app/GeneyTypeConverter/type_converter.py -s {} {}'.format(source_directory,
                                                                                      output_directory))
    else:
        os.system('python3 /app/GeneyTypeConverter/type_converter.py {} {}'.format(source_directory, output_directory))
    os.system('chmod 777 ' + output_directory)
    if targz:
        os.system('tar -czf {0}.tar.gz {0}'.format(output_directory))
        os.system('chmod 777 {}.tar.gz'.format(output_directory))


if __name__ == '__main__':
    # new_pr = check_history()
    # while new_pr:
    #     test(new_pr)
    #     new_pr = check_history()
    pr = PullRequest(351, 'TCGA_BreastCancer_DNAMethylation', '', 0, 1, 1, False, 1, 0, '18172c2dcfaa81fa5ef116ed86fbfd04a067f863', '', '', '', '')
    test(pr)
    print(pr)
