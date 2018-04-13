import requests
from PullRequest import PullRequest


class GithubDao:
    def __init__(self, repo_url: str, token: str):
        if repo_url[-1] != '/':
            repo_url += '/'
        self.repo_url = repo_url
        self.__token = token

    def get_prs(self):
        url = self.repo_url + 'pulls'
        payload = requests.get(url).json()
        prs = []
        for i in range(len(payload)):
            branch = payload[i]['head']['ref']
            pr_id = payload[i]['id']
            pr_num = payload[i]['number']
            user = payload[i]['user']['login']
            sha = payload[i]['head']['sha']
            pr = PullRequest(int(pr_num), branch, 'N/A', 0, 0, 0, False, int(pr_id), 0, sha, 'N/A', user, 'N/A', 'N/A')
            prs.append(pr)
        return prs

    def check_files(self, pr: PullRequest):
        url = self.repo_url + 'pulls/' + pr.pr + '/files'
        payload = requests.get(url).json()
        files = []
        bad_files = []
        for i in range(len(payload)):
            files.append(payload[i]['filename'])
        for fileName in files:
            if fileName.split("/")[0] != pr.branch:
                bad_files.append(fileName)
        if len(bad_files) > 0:
            report = "<h1><center>{branch}</center></h1>\n<h2><center> Status: Failed </center></h2>\n\n" \
                     "Only files in the \"{branch}\" directory should be changed. The following files were " \
                     "also changed in this branch:\n".format(branch=pr.branch)
            for file in bad_files:
                report += "- {file}\n".format(file=file)
            valid = False
        else:
            valid = True
        for fileName in files:
            if fileName != "{}/description.md".format(pr.branch) and fileName != "{}/config.yaml".format(pr.branch):
                return valid, False
        return valid, True

    def merge(self, pr: PullRequest) -> bool:
        request = {'sha': pr.sha}
        url = '{repo}pulls/{num}/merge?access_token={token}'.format(repo=self.repo_url, num=pr.pr, token=self.__token)
        response = requests.put(url, json=request)
        if 'Pull Request successfully merged' in response.json()['message']:
            print('Pull Request #{num}, Branch \"{branch}\", has been merged to WishBuilder Master branch'.format(
                num=pr.pr, branch=pr.branch), flush=True)
            return True
        else:
            print('Pull Request #{num}, Branch \"{branch}\", could not be merged to WishBuilder Master branch'.format(
                num=pr.pr, branch=pr.branch), flush=True)
            return False


