from tests import *
from GithubDao import GithubDao
from SqliteDao import SqliteDao
from private import GH_TOKEN
import shutil
import time
from multiprocessing import Pool, Queue, Process

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


def get_new_prs():
    history = sql_dao.get_all()
    prs = git_dao.get_prs()
    new_prs = []
    for pr in prs:
        if pr.pr in history.keys():
            if pr.sha not in history[pr.pr]:
                new_prs.append(pr)
        else:
            new_prs.append(pr)
    return new_prs


def test(pr: PullRequest):
    start = time.time()
    if pr.branch not in os.listdir(TESTING_LOCATION):
        os.mkdir('{}{}'.format(TESTING_LOCATION, pr.branch))
    else:
        raise EnvironmentError("Directory {}{} Already Exists".format(TESTING_LOCATION, pr.branch))
    pr.status = 'In progress'
    pr.email = git_dao.get_email(pr.sha)
    sql_dao.update(pr)
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
    pr.check_if_passed()
    sql_dao.update(pr)
    if pr.passed:
        geney_convert(pr)
    cleanup(pr)


def cleanup(pr):
    shutil.rmtree("{}{}".format(TESTING_LOCATION, pr.branch))
    pr.send_report(recipient='hillkimball@gmail.com')
    print("Done!")


def wait(job):
    print("Finished {}".format(job), flush=True)
    time.sleep(5)


def simulate_test(pr: PullRequest):
    print("Starting job: {}".format(pr.branch), flush=True)
    time.sleep(20)
    print("testing {}...".format(pr.branch), flush=True)
    time.sleep(20)
    print("finished {}".format(pr.branch), flush=True)


def queue_pr(pr: PullRequest, local_history: []):
    if pr.sha not in local_history:
        queue.append(pr)


if __name__ == '__main__':
    processes = []
    queue = []
    history = []
    while True:
        print("Check for prs", flush=True)
        new_prs = get_new_prs()
        for pull in new_prs:
            queue_pr(pull, history)
        while len(queue) > 0:
            for p in processes:
                if not p.is_alive():
                    processes.remove(p)
            if len(processes) < MAX_NUM_PROCESSES:
                new_pr = queue.pop()
                history.append(new_pr.sha)
                p = Process(target=simulate_test, args=(new_pr,))
                processes.append(p)
                p.start()
            time.sleep(5)
        time.sleep(600)

