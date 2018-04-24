from tests import *
from GithubDao import GithubDao
from SqliteDao import SqliteDao
from private import GH_TOKEN
import shutil
import time

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
    start = time.time()
    if pr.branch not in os.listdir(TESTING_LOCATION):
        os.mkdir('{}{}'.format(TESTING_LOCATION, pr.branch))
    else:
        raise EnvironmentError("Directory {}{} Already Exists".format(TESTING_LOCATION, pr.branch))
    pr.status = 'In progress'
    pr.email = git_dao.get_email(pr.sha)
    # sql_dao.update(pr)
    files, download_urls = git_dao.get_files_changed(pr)
    valid, description_only = check_files_changed(pr, files)

    if valid:
        pr.report.valid_files = True
        if description_only:
            git_dao.merge(pr)
            geney_convert(pr)
            pr.set_updated()
        else:
            # Download Files from Github and put them in the testing directory
            for file in download_urls:
                git_dao.download_file(file, TESTING_LOCATION)
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
    pr.time_elapsed = time.strftime("%Hh:%Mm:%Ss", time.gmtime(time.time() - start))
    pr.date = time.strftime("%D", time.gmtime(time.time()))
    pr.e_date = time.time()
    if pr.check_if_passed():
        print("All test passed")
        # geney_convert(pr)
    cleanup(pr)


def cleanup(pr):
    shutil.rmtree("{}{}".format(TESTING_LOCATION, pr.branch))
    pr.send_report(recipient='hillkimball@gmail.com')
    print("Done!")


if __name__ == '__main__':
    # new_pr = check_history()
    # while new_pr:
    #     test(new_pr)
    #     new_pr = check_history()
    pull = PullRequest(351, 'TCGA_BreastCancer_DNAMethylation', '', 0, 1, 1, False, 1, 0,
                       '18172c2dcfaa81fa5ef116ed86fbfd04a067f863', '', '', '', '')
    test(pull)
    print(pull)
    print(pull.get_report_markdown())
