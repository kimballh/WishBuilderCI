from PullRequest import PullRequest
from GithubDao import GithubDao
from SqliteDao import SqliteDao
from private import GH_TOKEN
import os

SQLITE_FILE = './prHistory.sql'
WB_DIRECTORY = '/app'

root = os.getcwd()

sql_dao = SqliteDao(SQLITE_FILE)
git_dao = GithubDao('https://api.github.com/repos/srp33/WishBuilder/', GH_TOKEN)


def check_history():
    history = sql_dao.get_all()
    prs = git_dao.get_prs()

    for pr in prs:
        if pr.pr in history.keys():
            if history[pr.pr] != pr.sha and not sql_dao.in_progress(pr):
                return pr
        else:
            return pr
    return None


def test(pr: PullRequest):
    pr.status = 'In progress'
    sql_dao.update(pr)
    valid, description_only = git_dao.check_files(pr)
    if valid:
        if description_only:
            git_dao.merge(pr)
            geney_convert(pr)


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
    new_pr = check_history()
    while new_pr:
        test(new_pr)
        new_pr = check_history()