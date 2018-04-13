class PullRequest:
    def __init__(self, pr: int, branch: str, date: str, e_date: float, feature_variables: int, meta_variables: int,
                 passed: bool, pr_id: int, num_samples: int, sha: str, time_elapsed: str, user: str, email: str,
                 status: str, report: str=''):
        self.pr = pr
        self.branch = branch
        self.date = date
        self.e_date = e_date
        self.feature_variables = feature_variables
        self.meta_variables = meta_variables
        self.passed = passed
        self.pr_id = pr_id
        self.num_samples = num_samples
        self.sha = sha
        self.time_elapsed = time_elapsed
        self.user = user
        self.email = email
        self.status = status
        self.report = report

    def __str__(self) -> str:
        out = "Pull Request Number: #{}\nBranch: {}\nDate: {}\neDate: {}\nNumber of Feature Variables: {}\n" \
              "Number of Metadata Variables: {}\nPassed: {}\nPull Request ID: {}\nNumber of Samples: {}\nSha: " \
              "{}\nTime Elapsed: {}\nUser: {}\nEmail: {}\nStatus: {}" \
            .format(self.pr, self.branch, self.date, self.e_date, self.feature_variables, self.meta_variables,
                    self.passed, self.pr_id, self.num_samples, self.sha, self.time_elapsed, self.user, self.email,
                    self.status)
        return out