import sqlite3
import json
from PullRequest import PullRequest
from Constants import SQLITE_FILE


class SqliteDao:
    def __init__(self, db_file):
        self.__con = sqlite3.connect(db_file)
        self.__file = db_file
        self.close()

    def __enter__(self):
        return self

    def __exit__(self):
        self.close()

    def close(self):
        self.__con.commit()
        self.__con.close()

    def open(self):
        self.__con = sqlite3.connect(self.__file)

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
                  status: str, report: str=None):
        self.open()
        c = self.__con.cursor()
        try:
            c.execute('insert into PullRequests VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                      (pr, branch, date, e_date, feature_variables, meta_variables, passed, pr_id, num_samples, sha,
                       time_elapsed, user, email, status, report))
        except sqlite3.IntegrityError:
            print("Pull #{}, \'{}\' does not have a unique sha ({})".format(pr, branch, sha))
        self.close()

    def add_pr(self, pr: PullRequest):
        self.open()
        c = self.__con.cursor()
        c.execute('insert into PullRequests VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                  (pr.pr, pr.branch, pr.date, pr.e_date, pr.feature_variables, pr.meta_variables, pr.passed, pr.pr_id,
                   pr.num_samples, pr.sha, pr.time_elapsed, pr.user, pr.email, pr.status, pr.report.to_json()))
        self.close()

    def get_prs(self, pr_number: int) -> [PullRequest]:
        self.open()
        c = self.__con.cursor()
        c.execute('select * from PullRequests where PR={}'.format(pr_number))
        data = c.fetchall()
        self.close()
        prs = []
        if data:
            for result in data:
                pr = PullRequest(result[0], result[1], result[2], result[3], result[4], result[5], result[6],
                                 result[7], result[8], result[9], result[10], result[11], result[12], result[13],
                                 result[14])
                prs.append(pr)
        return prs

    def get_pr(self, pr_sha: str) -> PullRequest:
        self.open()
        c = self.__con.cursor()
        c.execute('select * from PullRequests where sha={}'.format(pr_sha))
        result = c.fetchone()
        self.close()
        if result:
            pr = PullRequest(result[0], result[1], result[2], result[3], result[4], result[5], result[6],
                             result[7], result[8], result[9], result[10], result[11], result[12], result[13],
                             result[14])
        else:
            pr = None
        return pr

    def get_prs_from_statement(self, sql_stmt: str) -> [PullRequest]:
        self.open()
        c = self.__con.cursor()
        c.execute(sql_stmt)
        data = c.fetchall()
        self.close()
        prs = []
        if data:
            for result in data:
                pr = PullRequest(result[0], result[1], result[2], result[3], result[4], result[5], result[6],
                                 result[7], result[8], result[9], result[10], result[11], result[12], result[13],
                                 result[14])
                prs.append(pr)
        return prs

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
                               sha, time_elapsed, user, email, status)

    def get_all(self, return_objects=False):
        self.open()
        c = self.__con.cursor()
        if not return_objects:
            c.execute('select PR, sha from PullRequests')
        else:
            c.execute('select * from PullRequests')
        data = c.fetchall()
        self.close()
        if data:
            if not return_objects:
                prs = {}
                for i in range(len(data)):
                    prs.setdefault(data[i][0], []).append(data[i][1])
            else:
                prs = []
                for result in data:
                    pr = PullRequest(result[0], result[1], result[2], result[3], result[4], result[5], result[6],
                                     result[7], result[8], result[9], result[10], result[11], result[12], result[13],
                                     result[14])
                    prs.append(pr)
        else:
            prs = None
        return prs

    def in_progress(self, pr: PullRequest) -> bool:
        self.open()
        c = self.__con.cursor()
        c.execute('select status from PullRequests where sha=\"{}\"'.format(pr.sha))
        data = c.fetchone()
        self.close()
        if data:
            if 'progress' in data[0] or 'Progress' in data[0]:
                return True
        return False

    def update(self, pr: PullRequest):
        self.open()
        c = self.__con.cursor()
        c.execute('delete from PullRequests where sha=\"{}\"'.format(pr.sha))
        self.close()
        self.add_pr(pr)


if __name__ == '__main__':
    dao = SqliteDao(SQLITE_FILE)
    # dao.import_json('../prHistory.json', True)
    pull = dao.get_pr(351)[0]
    print(pull)
    # pull.send_report(recipient='hillkimball@gmail.com')
