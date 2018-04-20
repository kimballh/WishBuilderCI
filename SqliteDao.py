import sqlite3
import json
from PullRequest import PullRequest

SQLITE_FILE = './history.sql'


class SqliteDao:
    def __init__(self, directory):
        self.__con = sqlite3.connect(directory)
        self.__directory = directory
        self.close()

    def __enter__(self):
        return self

    def __exit__(self):
        self.close()

    def close(self):
        self.__con.commit()
        self.__con.close()

    def open(self):
        self.__con = sqlite3.connect(self.__directory)

    def create_db(self):
        self.open()
        c = self.__con.cursor()
        c.execute('drop table if exists PullRequests')
        c.execute("CREATE TABLE PullRequests(PR int not null, branch text, date text, eDate float, "
                  "featureVariables int, metaVariables int, passed boolean, prID int, numSamples int, "
                  "sha text not null PRIMARY KEY , timeElapsed text, user text, email text, status text, report text)")
        self.close()

    def insert_pr(self, pr: int, branch: str, date: str, e_date: float, feature_variables: int, meta_variables: int,
                  passed: bool, pr_id: int, num_samples: int, sha: str, time_elapsed: str, user: str, email: str,
                  status: str, report: str):
        self.open()
        c = self.__con.cursor()
        c.execute('insert into PullRequests VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                  (pr, branch, date, e_date, feature_variables, meta_variables, passed, pr_id, num_samples, sha,
                   time_elapsed, user, email, status, report))
        self.close()

    def add_pr(self, pr: PullRequest):
        self.open()
        c = self.__con.cursor()
        c.execute('insert into PullRequests VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                  (pr.pr, pr.branch, pr.date, pr.e_date, pr.feature_variables, pr.meta_variables, pr.passed, pr.pr_id,
                   pr.num_samples, pr.sha, pr.time_elapsed, pr.user, pr.email, pr.status, pr.report.to_json()))
        self.close()

    def get_pr(self, pr: int):
        self.open()
        c = self.__con.cursor()
        c.execute('select * from PullRequests where PR={PR}'.format(PR=pr))
        data = c.fetchone()
        self.close()
        if data:
            pr = PullRequest(data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8], data[9],
                             data[10], data[11], data[12], data[13], data[14])
            return pr
        else:
            return None

    def import_json(self, file: str, recreate=False):
        import uuid
        if recreate:
            self.create_db()
        with open(file) as fp:
            pr_history = json.load(fp)
            for pull in pr_history.keys():
                branch = pr_history[pull]['branch']
                date = pr_history[pull]['date']
                e_date = pr_history[pull]['eDate']
                feature_variables = pr_history[pull]['featureVariables']
                meta_variables = pr_history[pull]['metaVariables']
                passed = pr_history[pull]['passed']
                pr_id = pr_history[pull]['prID']
                pr = pr_history[pull]['prNum']
                num_samples = pr_history[pull]['samples']
                sha = pr_history[pull]['sha']
                time_elapsed = pr_history[pull]['timeElapsed']
                user = pr_history[pull]['user']

                if time_elapsed == 'update' or time_elapsed == 'updated':
                    status = 'update'
                    time_elapsed = 'N/A'
                elif time_elapsed == 'In Progress' or time_elapsed == 'Failed':
                    status = time_elapsed
                    time_elapsed = 'N/A'
                else:
                    if passed:
                        status = 'Passed'
                    else:
                        status = 'Failed'

                if user == 'glenrs':
                    email = 'grexsumsion@gmail.com'
                elif user == 'btc36':
                    email = 'benjamincookson94@gmail.com'
                elif user == 'kimballh':
                    email = 'hillkimball@gmail.com'
                else:
                    email = None

                if sha == 'null':
                    sha = str(uuid.uuid4())

                self.insert_pr(pr, branch, date, e_date, feature_variables, meta_variables, passed, pr_id, num_samples,
                               sha, time_elapsed, user, email, status, '')

    def get_all(self):
        prs = {}
        self.open()
        c = self.__con.cursor()
        c.execute('select PR, sha from PullRequests')
        data = c.fetchall()
        self.close()
        for i in range(len(data)):
            prs.setdefault(data[i][0], []).append(data[i][1])
        return prs

    def in_progress(self, pr: PullRequest) -> bool:
        self.open()
        c = self.__con.cursor()
        c.execute('select status from PullRequests where sha=\"{}\"'.format(pr.sha))
        data = c.fetchone()
        self.close()
        if 'progress' in data[0] or 'Progress' in data[0]:
            return True
        else:
            return False

    def update(self, pr: PullRequest):
        self.open()
        c = self.__con.cursor()
        c.execute('delete from PullRequests where sha=\"{}\"'.format(pr.sha))
        self.close()
        self.add_pr(pr)


if __name__ == '__main__':
    dao = SqliteDao(SQLITE_FILE)
    dao.import_json('./prHistory.json', True)
