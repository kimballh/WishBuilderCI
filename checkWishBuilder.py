import requests
import os
import re
import subprocess
import time
import yaml
from sys import argv


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


def check_history(file_name):
    prIDs = []
    prHistory = open(file_name, 'r')
    for line in prHistory:
        prHistoryData = line.rstrip('\n').split('\t')
        prIDs.append(prHistoryData[0])
    prHistory.close()
    for i in range(len(pr)):
        if str(pr[i]['id']) not in prIDs:
            return [True, i]
    return[False, -1]


def test_pr(index):
    start = time.time()
    status = ""
    branchName = pr[index]['head']['ref']
    prHistory = open('.prhistory', 'a')
    prHistory.write(str(pr[index]['id']) + '\t' +
                    branchName + '\t' + str(pr[index]['number']) + '\n')
    prHistory.close()
    os.chdir('./WishBuilder')
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
    
    if 'config.yaml' in os.listdir('./testDirectory'):
        configFile = open('./testDirectory/config.yaml', 'r')
        configs = yaml.load(configFile)
        if 'numSamples' in configs.keys():
            numSamples = configs['numSamples']
        else:
            numSamples = 0
        if 'metaVariables' in configs.keys():
            metaVariables = configs['metaVariables']
        else:
            metaVariables = 0
        if 'featureVariables' in configs.keys():
            featureVariables = configs['featureVariables']
        else:
            featureVariables = 0

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
        os.system(
            'mv ./testDirectory/config.yaml ../CompleteDataSets/' + branchName + '/')
        os.system('sudo chmod -R 777 ../CompleteDataSets/' + branchName)
    else:
        print('Moving data.tsv.gz, metadata.tsv.gz, and description.md to IncompleteDataSets/' + branchName,
              flush=True)
        os.system('mkdir ../IncompleteDataSets/' + branchName)
        if 'data.tsv.gz' in os.listdir():
            os.system('mv data.tsv.gz ../IncompleteDataSets/' +
                      branchName + '/')
        if 'metadata.tsv.gz' in os.listdir():
            os.system('mv metadata.tsv.gz ../IncompleteDataSets/' +
                      branchName + '/')
        if 'description.md' in os.listdir('./testDirectory'):
            os.system(
                'mv ./testDirectory/description.md ../IncompleteDataSets/' + branchName + '/')
        if 'config.yaml' in os.listdir('./testDirectory'):
            os.system(
                'mv ./testDirectory/config.yaml ../IncompleteDataSets/' + branchName + '/')
        os.system('sudo chmod -R 777 ../IncompleteDataSets/' + branchName)
    os.system('rm -rf test*')
    subprocess.run(["git", "checkout", "-f", "master"],
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    timeElapsed = time.strftime(
        "%Hh:%Mm:%Ss", time.gmtime(time.time() - start))
    dateFinished = time.strftime("%D", time.gmtime(time.time()))
    print('Finished with branch \"%s\". Time elapsed: %s\n' %
          (branchName, timeElapsed), flush=True)
    os.chdir('..')
    os.system('cp ./StatusReports/' + branchName +
              '-status.md ./gh-pages/WishBuilder/StatusReports/')
    os.system('cp ./Descriptions/' + branchName +
              '-description.md ./gh-pages/WishBuilder/Descriptions/')
    dataSets = open("./gh-pages/WishBuilder/docs/dataSets.md", 'a')
    dataSets.write('|\t[{0}]({{{{site.url}}}}/Descriptions/{0}-description)\t|\t{1}\t|\t[{2}]({{{{site.url}}}}/StatusReports/{0}-status)\t|\t{3}\t|\t{4}\t|\t{5}\t|\t{6}\t|\t{7}\t|\n'.format(
        branchName, user, status, dateFinished, timeElapsed, numSamples, metaVariables, featureVariables))
    dataSets.close()


payload = requests.get('https://api.github.com/repos/srp33/WishBuilder/pulls?page=2')
pr = payload.json()
newPRs = True
while newPRs:
    history = check_history('.prhistory')
    if history[0]:
        test_pr(history[1])
    else:
        newPRs = False
