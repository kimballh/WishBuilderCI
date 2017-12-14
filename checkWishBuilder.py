import requests
import os
import re
import subprocess
import time
import yaml
from sys import argv

WB_URL = "git@github.com:srp33/WishBuilder.git"


def update_branches():
    print("Updating WishBuilder Repository...", flush=True)
    os.chdir('/app/gh-pages/WishBuilder')
    os.system('git pull -q origin gh-pages')
    os.chdir('/app/WishBuilder')
    os.system('git pull -q origin master')
    os.system('git remote update origin --prune')
    os.chdir('/app')


def update_pages(rowToAdd, dataset):
    os.chdir('/app/gh-pages/WishBuilder')
    #os.system('git pull -q origin gh-pages')
    dataSets = open("/app/gh-pages/WishBuilder/docs/dataSets.md", 'a')
    dataSets.write(rowToAdd)
    dataSets.close()
    os.system('git add --all')
    os.system('git commit -q -m \"added dataset ' + dataset + '\"')
    os.chdir('/app')


def git_push(message, branch):
    os.system('git pull origin ' + branch)
    os.system('git add --all')
    os.system('git commit -q -m \"' + message + '\"')
    os.system('git push -q origin ' + branch)


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


def convertForGeney(src_directory, output_directory):
    print('Converting dataset to Geney format...', flush=True)
    os.system('python3 /app/GeneyTypeConverter/type_converter.py ' + src_directory + ' ' + output_directory)
    os.system('chmod 777 ' + output_directory)


def update_website():
    print('Pushing test resutls to gitHub', flush=True)
    os.chdir('/app/gh-pages/WishBuilder')
    # os.system('git add --all')
    # os.system('git commit -q -m \"added data sets\"')
    os.system('git push -q origin gh-pages')
    os.chdir('/app')


def test_pr(index):
    start = time.time()
    status = ""
    branchName = pr[index]['head']['ref']
    prHistory = open('/app/.prhistory', 'a')
    prHistory.write(str(pr[index]['id']) + '\t' +
                    branchName + '\t' + str(pr[index]['number']) + '\n')
    prHistory.close()
    os.mkdir(branchName)
    os.chdir(branchName)
    os.system('git clone ' + WB_URL)
    os.chdir('./WishBuilder')
    print('Pull Request #' +
          str(pr[index]['number']) + ' Branch: ' + branchName, flush=True)
    user = pr[index]['user']['login']
    print('Checking out branch . . .', flush=True)
    subprocess.run(["git", "checkout", "remotes/origin/" + branchName], stdout=subprocess.PIPE,
                   stderr=subprocess.PIPE)
    os.system('cp /app/test.py ./')
    os.system('cp -r ' + branchName + ' ./testDirectory')
    print('Testing ' + branchName +
          '(test.py \"./WishBuilder/' + branchName + '/\"):', flush=True)
    os.system(
        'python3 ./test.py \"/app/' + branchName + '/WishBuilder/testDirectory/\" ' + branchName)
    status = check_status("/app/StatusReports/" +
                          branchName + "-status.md")
    os.system('cp testDirectory/description.md /app/Descriptions/' +
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
        configFile.close()

    if status == "Complete":
        print('Moving data.tsv.gz, metadata.tsv.gz, and description.md to CompleteDataSets/' + branchName,
              flush=True)
        os.system('mkdir /app/CompleteDataSets/' + branchName)
        os.system('mv data.tsv.gz /app/CompleteDataSets/' +
                  branchName + '/')
        os.system(
            'mv metadata.tsv.gz /app/CompleteDataSets/' + branchName + '/')
        os.system(
            'mv ./testDirectory/description.md /app/CompleteDataSets/' + branchName + '/')
        os.system(
            'mv ./testDirectory/config.yaml /app/CompleteDataSets/' + branchName + '/')
        os.system('sudo chmod -R 777 /app/CompleteDataSets/' + branchName)
        convertForGeney('/app/CompleteDataSets/' + branchName, '/app/GeneyDataSets/' + branchName)
    else:
        print('Moving data.tsv.gz, metadata.tsv.gz, and description.md to IncompleteDataSets/' + branchName,
              flush=True)
        os.system('mkdir /app/IncompleteDataSets/' + branchName)
        if 'data.tsv.gz' in os.listdir():
            os.system('mv data.tsv.gz /app/IncompleteDataSets/' +
                      branchName + '/')
        if 'metadata.tsv.gz' in os.listdir():
            os.system('mv metadata.tsv.gz /app/IncompleteDataSets/' +
                      branchName + '/')
        if 'description.md' in os.listdir('./testDirectory'):
            os.system(
                'mv ./testDirectory/description.md /app/IncompleteDataSets/' + branchName + '/')
        if 'config.yaml' in os.listdir('./testDirectory'):
            os.system(
                'mv ./testDirectory/config.yaml /app/IncompleteDataSets/' + branchName + '/')
        os.system('sudo chmod -R 777 /app/IncompleteDataSets/' + branchName)
    os.system('rm -rf test*')
    subprocess.run(["git", "checkout", "-f", "master"],
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    timeElapsed = time.strftime(
        "%Hh:%Mm:%Ss", time.gmtime(time.time() - start))
    dateFinished = time.strftime("%D", time.gmtime(time.time()))
    print('Finished with branch \"%s\". Time elapsed: %s\n' %
          (branchName, timeElapsed), flush=True)
    os.chdir('/app')
    os.system('rm -rf ' + branchName)
    os.system('cp ./StatusReports/' + branchName +
              '-status.md ./gh-pages/WishBuilder/StatusReports/')
    os.system('cp ./Descriptions/' + branchName +
              '-description.md ./gh-pages/WishBuilder/Descriptions/')
    update_pages('|\t[{0}]({{{{site.url}}}}/Descriptions/{0}-description)\t|\t{1}\t|\t[{2}]({{{{site.url}}}}/StatusReports/{0}-status)\t|\t{3}\t|\t{4}\t|\t{5}\t|\t{6}\t|\t{7}\t|\n'.format(
        branchName, user, status, dateFinished, timeElapsed, numSamples, metaVariables, featureVariables), branchName)

print("Welcome To Wishbuilder!\n", flush=True)
# update_branches()
payload = requests.get('https://api.github.com/repos/srp33/WishBuilder/pulls')
pr = payload.json()
newPRs = True
updateNeeded = False

while newPRs:
    history = check_history('.prhistory')
    if history[0]:
        updateNeeded = True
        test_pr(history[1])
    else:
        newPRs = False

if updateNeeded:
    update_website()
else:
    print('No new pull requests', flush=True)
