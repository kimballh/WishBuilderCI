import requests
import os
import re
import subprocess
from sys import argv

prIDs = []
newPRs = []
payload = requests.get(
    'https://api.github.com/repos/srp33/WishBuilder/pulls?page=2')
pr = payload.json()
prFilter = r""

if len(argv) > 1:
    prFilter = argv[1]


def git_push(message, branch):
    os.system('git pull origin ' + branch)
    os.system('git add --all')
    os.system('git commit -m \"' + message + '\"')
    os.system('git push origin ' + branch)


def check_status(file_path):
    status_file = open(file_path, 'r')
    status_file.readline()
    if "Complete" in status_file.readline().rstrip('\n').split():
        return "Complete"
    else:
        return "In Progress"


def merge_branch(branch_name):
    os.system('git checkout -q master')
    os.system('git merge -q -m \"Passed Tests\" origin/' + branch_name)
    os.system('git push -q origin master')
    os.system('git push -q origin --delete ' + branch_name)


prHistory = open('.prhistory', 'r')
for line in prHistory:
    prHistoryData = line.rstrip('\n').split('\t')
    prIDs.append(prHistoryData[0])
prHistory.close()

for i in range(len(pr)):
    if str(pr[i]['id']) not in prIDs:
        newPRs.append(i)

if len(newPRs) > 0:
    os.chdir('./WishBuilder')
    for index in newPRs:
        status = ""
        branchName = pr[index]['head']['ref']
        if re.search(prFilter, branchName):
            print('Pull Request #' +
                  str(pr[index]['number']) + ' Branch: ' + branchName, flush=True)
            user = pr[index]['user']['login']
            print('Checking out branch . . .', flush=True)
            subprocess.run(["git", "checkout", "remotes/origin/" + branchName], stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
            os.system('cp ../test.* ./')
            os.system('cp -r ' + branchName + ' ./testDirectory')
            print('Testing ' + branchName +
                  '(test.py \"./WishBuilder/' + branchName + '/\"):', flush=True)
            os.system(
                'python3 ./test.py \"/app/WishBuilder/testDirectory/\" ' + branchName)
            status = check_status("/app/StatusReports/" +
                                  branchName + "-status.md")
            os.system('cp testDirectory/description.md ../Descriptions/' +
                      branchName + '-description.md')
            if status == "Complete":
                print('Moving data.tsv.gz, metadata.tsv.gz, and description.md to CompleteDataSets/' + branchName,
                      flush=True)
                os.system('mkdir ../CompleteDataSets/' + branchName)
                os.system('mv data.tsv.gz ../CompleteDataSets/' +
                          branchName + '/')
                os.system(
                    'mv metadata.tsv.gz ../CompleteDataSets/' + branchName + '/')
                os.system(
                    'mv ./testDirectory/description.md ../CompleteDataSets/' + branchName + '/')
                os.system('sudo chmod -R 777 ../CompleteDataSets/' + branchName)
            os.system('rm -rf test*')
            subprocess.run(["git", "checkout", "-f", "master"],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print('Finished with branch \"' + branchName +
                  '\", moving results to gh-pages\n', flush=True)
            os.chdir('..')
            os.system('cp ./StatusReports/' + branchName +
                      '-status.md ./gh-pages/WishBuilder/StatusReports/')
            os.system('cp ./Descriptions/' + branchName +
                      '-description.md ./gh-pages/WishBuilder/Descriptions/')
            dataSets = open("./gh-pages/WishBuilder/docs/dataSets.md", 'a')
            dataSets.write('|\t[' + branchName + ']({{site.url}}/Descriptions/' + branchName + '-description)\t|\t' +
                           user + '\t|\t[' + status + ']({{site.url}}/StatusReports/' + branchName +
                           '-status)\t|\tno\t|\n')
            dataSets.close()
            prHistory = open('.prhistory', 'a')
            prHistory.write(str(pr[index]['id']) + '\t' +
                            branchName + '\t' + str(pr[index]['number']) + '\n')
            prHistory.close()
            os.chdir('./WishBuilder')
