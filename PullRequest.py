from Report import Report
from datetime import datetime, timedelta
import markdown
import smtplib
import mimetypes
from email.message import EmailMessage
from private import WISHBUILDER_EMAIL, WISHBUILDER_PASS

class PullRequest:
    def __init__(self, pr: int, branch: str, date: str, e_date: float, feature_variables: int, meta_variables: int,
                 passed: bool, pr_id: int, num_samples: int, sha: str, time_elapsed: str, user: str, email: str,
                 status: str, report: str = None):
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
        self.report = Report(report)

    def __str__(self) -> str:
        out = "Pull Request Number: #{}\nBranch: {}\nDate: {}\neDate: {}\nNumber of Feature Variables: {}\n" \
              "Number of Metadata Variables: {}\nPassed: {}\nPull Request ID: {}\nNumber of Samples: {}\nSha: " \
              "{}\nTime Elapsed: {}\nUser: {}\nEmail: {}\nStatus: {}" \
            .format(self.pr, self.branch, self.date, self.e_date, self.feature_variables, self.meta_variables,
                    self.passed, self.pr_id, self.num_samples, self.sha, self.time_elapsed, self.user, self.email,
                    self.status)
        return out

    def set_updated(self):
        self.status = 'Updated'
        self.passed = True
        self.date = (datetime.now() - timedelta(hours=7)).strftime("%b %d, %y. %H:%m MST")

    def get_report_markdown(self) -> str:
        out = "<h1><center>{}</center></h1>\n".format(self.branch)
        out += '<h2><center> Status: {} </center></h2>\n<center>{}</center>\n\n'.format(self.status, self.date)
        out += str(self.report)
        return out

    def get_report_html(self) -> str:
        md = self.get_report_markdown()
        html = markdown.markdown(md)
        return html

    def send_report(self, recipient: str='user'):
        if recipient == 'user':
            recipient = self.email
        s = smtplib.SMTP(host='mail.kimball-hill.com', port=587)
        s.starttls()
        s.login(WISHBUILDER_EMAIL, WISHBUILDER_PASS)

        if self.passed:
            subject = "Passed: {}".format(self.branch)
        else:
            subject = "Failed: {}".format(self.branch)

        message = EmailMessage()
        message['From'] = 'wishbuilder@kimball-hill.com'
        message['To'] = recipient
        message['Subject'] = subject
        message.set_content(self.get_report_html(), subtype='html')

        s.send_message(message)

    def check_if_passed(self) -> bool:
        passed = True
        if not self.report.valid_files:
            passed = False
        if not self.report.pass_directory_test:
            passed = False
        if not self.report.pass_configuration_test:
            passed = False
        if not self.report.pass_file_test:
            passed = False
        if not self.report.pass_script_test:
            passed = False
        if not self.report.pass_key_test:
            passed = False
        if not self.report.pass_data_tests:
            passed = False
        if not self.report.pass_meta_tests:
            passed = False
        if not self.report.pass_sample_comparison:
            passed = False
        if not self.report.pass_cleanup:
            passed = False
        self.passed = passed
        if passed:
            self.status = 'Complete'
            return True
        else:
            self.status = 'Failed'
            return False



if __name__=='__main__':
    pr = PullRequest(1, 'branch', '1/1/11', 1245.515, 1, 1, False, 1, 1, 'sha', '124', 'user', 'email', 'status')
    print(pr.getReportMarkdown())
    # print(pr.report.to_json())