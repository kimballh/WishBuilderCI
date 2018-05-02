import requests
from PullRequest import PullRequest
import os
from Constants import REPO_URL


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

    def get_files_changed(self, pr: PullRequest):
        url = self.repo_url + 'pulls/{}/files'.format(pr.pr)
        payload = requests.get(url).json()
        files = []
        download_urls = []
        for i in range(len(payload)):
            files.append(payload[i]['filename'])
            download_urls.append(payload[i]['raw_url'])
        return files, download_urls

    def check_files(self, pr: PullRequest):
        url = self.repo_url + 'pulls/{}/files'.format(pr.pr)
        payload = requests.get(url).json()
        files = []
        bad_files = []
        download_urls = []
        for i in range(len(payload)):
            files.append(payload[i]['filename'])
            download_urls.append(payload[i]['raw_url'])
        for fileName in files:
            if fileName.split("/")[0] != pr.branch:
                bad_files.append(fileName)
        if len(bad_files) > 0:
            pr.status = 'Failed'
            report = "Only files in the \"{branch}\" directory should be changed. The following files were " \
                     "also changed in this branch:\n".format(branch=pr.branch)
            for file in bad_files:
                report += "- {file}\n".format(file=file)
            pr.report.valid_files = False
            pr.report.valid_files_report = report
            valid = False
        else:
            valid = True
        for fileName in files:
            if fileName != "{}/description.md".format(pr.branch) and fileName != "{}/config.yaml".format(pr.branch):
                return valid, False, download_urls
        return valid, True, download_urls

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

    def get_email(self, sha: str) -> str:
        url = '{}git/commits/{}'.format(self.repo_url, sha)
        response = requests.get(url).json()
        email = response['author']['email']
        return email

    def make_request(self, url: str, request_type: str='get', authorization: str=None, full_url: bool = False):
        if not full_url:
            url = self.repo_url + url
        if request_type == 'get':
            response = requests.get(url).json()
        else:
            response = requests.put(url).json()
        return response

    @staticmethod
    def download_file(url: str, destination: str= './'):
        split_url = url.split('/')
        i = split_url.index('raw')
        local_path = destination + "/".join(split_url[i+2:-1])
        local_filename = destination + "/".join(split_url[i+2:])
        if not os.path.exists(local_path):
            os.makedirs(local_path)
        # local_filename = destination + url.split('/')[-1]
        response = requests.get(url, stream=True)
        with open(local_filename, 'wb') as fs:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    fs.write(chunk)
        return local_filename


if __name__ == '__main__':
    dao = GithubDao(REPO_URL, '')
    # print(dao.make_request('pulls/351/files'))
    # print(dao.download_file('https://github.com/srp33/WishBuilder/raw/18172c2dcfaa81fa5ef116ed86fbfd04a067f863/TCGA_BreastCancer_DNAMethylation/cleanup.sh'))
    url = REPO_URL + 'pulls'.format(351)
    payload = requests.get(url).json()
    print(payload[0]['head']['sha'])
    # files = []
    # bad_files = []
    # download_urls = []
    # for i in range(len(payload)):
    #     files.append(payload[i]['filename'])
    #     download_urls.append(payload[i]['raw_url'])
    # print(download_urls)