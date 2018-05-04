import requests
import os
import re
import subprocess
import time
import yaml
import json
from sys import argv
from private import GH_TOKEN

WB_URL = "git@github.com:srp33/WishBuilder.git"


def update_branches():
    print("Updating WishBuilder Repository...", flush=True)
    os.chdir('/app/gh-pages/WishBuilder')
    os.system('git pull -q origin gh-pages')
    os.chdir('/app/WishBuilder')
    os.system('git pull -q origin master')
    os.system('git remote update origin --prune')
    os.chdir('/app')


def update_pages(branch_name, fullUpdate=True):
    cwd = os.getcwd()
    os.chdir('/app/gh-pages/WishBuilder')
    with open("/app/gh-pages/WishBuilder/docs/dataSets.md", 'w') as dataSets:
        dataSets.write("## WishBuilder Data Sets\n\n<div class=\"table-scroll\" markdown = \"block\">\n\n|\t" +
                    "Data Set\t|\tUser\t|\tStatus\t|\tDate\t|\tTime Elapsed\t|\tSamples\t|\tMeta Data Variables" +
                    "\t|\tFeature Variables\t|\n|\t----\t|\t----\t|\t----\t|\t----\t|\t----\t|\t----\t|\t----\t|" +
                    "\t----\t|\n")
        with open('/app/prHistory.json') as fp:
            prHistory = json.load(fp)
        pulls = []
        for pull in prHistory:
            pulls.append((prHistory[pull]['eDate'], pull))
        pulls.sort(reverse=True)
        for i in range(len(pulls)):
            index = pulls[i][1]
            if prHistory[index]['passed']:
                stat = "Complete"
            elif prHistory[index]['timeElapsed'] == 'In Progress':
                stat = "In Progress"
            else:
                stat = "Failed"
            if prHistory[index]['timeElapsed'] != 'updated' and prHistory[index]['timeElapsed'] != 'update':
                dataSets.write('|\t[{0}]({{{{site.url}}}}/Descriptions/{0}-description)\t|\t{1}\t|\t[{2}]({{{{site.url}}}}/StatusReports/{0}-status)\t|\t{3}\t|\t{4}\t|\t{5}\t|\t{6}\t|\t{7}\t|\n'.format(
                    prHistory[index]['branch'], prHistory[index]['user'], stat, prHistory[index]['date'], prHistory[index]['timeElapsed'], str(prHistory[index]['samples']), str(prHistory[index]['metaVariables']), str(prHistory[index]['featureVariables'])))
    with open('/app/prHistory.json', 'w') as fp:
        json.dump(prHistory, fp, sort_keys=True, indent=4)
    os.system('git add --all')
    if fullUpdate:
        os.system('git commit -q -m \"added dataset ' + branch_name + '\"')
    else:
        os.system('git commit -q -m \"modified description of dataset ' + branch_name + '\"')
    os.chdir(cwd)


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


def merge_branch(index):
    pr_number = str(pr[index]['number'])
    branch_name = pr[index]['head']['ref']
    payload = {'sha': pr[index]['head']['sha']}
    response = requests.put('https://api.github.com/repos/srp33/WishBuilder/pulls/' + pr_number + '/merge?access_token=' + GH_TOKEN, json=payload)
    if 'Pull Request successfully merged' in response.json()['message']:
        print('Pull Request #' + pr_number + ', Branch \"' + branch_name + '\", has been merged to WishBuilder Master branch', flush=True)
        # cwd = os.getcwd()
        # os.chdir('/app/WishBuilder')
        # os.system('git checkout -q master')
        # os.system('git pull -q origin master')
        # os.system('git remote update origin --prune')
        # os.system('git push -q origin --delete ' + branch_name)
        # os.chdir(cwd)
    else:
        print('Pull Request #' + pr_number + ', Branch \"' + branch_name + '\", could not be merged to WishBuilder Master branch', flush=True)


def check_history(file_name):
    currentJobs = os.listdir('/app')
    pulls = []
    with open(file_name) as fp:
        prHistory = json.load(fp)
        history = prHistory
    with open(file_name, 'w') as fp:
        json.dump(prHistory, fp, sort_keys=True, indent=4)
    for pull in history.keys():
        pulls.append(pull)
    for i in range(len(pr)):
        # if pr[i]['head']['ref'] == 'test_branch':
        #     return [True, i]
        if str(pr[i]['number']) not in pulls:
            return [True, i]
        elif (str(pr[i]['number']) in pulls) and (pr[i]['head']['sha'] != history[str(pr[i]['number'])]['sha']) and (pr[i]['head']['ref'] not in currentJobs):
            return [True, i]
    return[False, -1]


def convertForGeney(src_directory, output_directory, simple=False):
    print('Converting dataset to Geney format...', flush=True)
    if simple:
        os.system('python3 /app/GeneyTypeConverter/type_converter.py -s ' + src_directory + ' ' + output_directory)
    else:
        os.system('python3 /app/GeneyTypeConverter/type_converter.py ' + src_directory + ' ' + output_directory)
    os.system('chmod 777 ' + output_directory)
    os.system('tar -czf ' + output_directory + '.tar.gz ' + output_directory)
    os.system('chmod 777 ' + output_directory + '.tar.gz')


def update_website():
    print('Pushing test results to gitHub', flush=True)
    os.chdir('/app/gh-pages/WishBuilder')
    # os.system('git add --all')
    # os.system('git commit -q -m \"added data sets\"')
    os.system('git push -q origin gh-pages')
    os.chdir('/app')


def update_history(index, pr_number, passed=False, time_elapsed='In Progress', num_samples=0, meta_variables=0, feature_variables=0, update=False):
    with open('/app/prHistory.json') as fp:
        prHistory = json.load(fp)
    prHistory[pr_number] = {
        'branch': pr[index]['head']['ref'],
        'prID': pr[index]['id'],
        'prNum': pr[index]['number'],
        'user': pr[index]['user']['login'],
        'sha': pr[index]['head']['sha'],
        'passed': passed,
        'date': time.strftime("%D", time.gmtime(time.time())),
        'eDate': time.time(),
        'timeElapsed': time_elapsed,
        'samples': num_samples,
        'metaVariables': meta_variables,
        'featureVariables': feature_variables
    }
    if update:
        originalPR = "none"
        for pull in prHistory.keys():
            if prHistory[pull]['branch'] == prHistory[pr_number]['branch']:
                originalPR = pull
        if originalPR != "none":
            prHistory[pr_number] = {
                'branch': pr[index]['head']['ref'],
                'prID': pr[index]['id'],
                'prNum': pr[index]['number'],
                'user': pr[index]['user']['login'],
                'sha': pr[index]['head']['sha'],
                'passed': True,
                'date': time.strftime("%D", time.gmtime(time.time())),
                'eDate': time.time(),
                'timeElapsed': prHistory[originalPR]['timeElapsed'],
                'samples': prHistory[originalPR]['samples'],
                'metaVariables': prHistory[originalPR]['metaVariables'],
                'featureVariables': prHistory[originalPR]['featureVariables']
            }
            prHistory[originalPR]['timeElapsed'] = 'updated'
    with open('/app/prHistory.json', 'w') as fp:
        json.dump(prHistory, fp, sort_keys=True, indent=4)


def only_description(branch_name):
    descriptionFiles = ['description.md', 'config.yaml']
    originalDirPath = '/app/' + branch_name + '/original/'
    newDirPath = '/app/' + branch_name + '/WishBuilder/' + branch_name + '/'
    originalDir = os.listdir(originalDirPath)
    newDir = os.listdir(newDirPath)
    filesChanged = []
    if len(originalDir) != len(newDir):
        return False
    else:
        for file in newDir:
            if file not in originalDir:
                return False
    for file in newDir:
        contentsNew = open(newDirPath + file).read()
        contentsOld = open(originalDirPath + file).read()
        if contentsNew != contentsOld:
            filesChanged.append(file)
    for file in filesChanged:
        if file not in descriptionFiles:
            return False
    return True


def valid_files(pr_number, branch_name):
    commit = requests.get('https://api.github.com/repos/srp33/WishBuilder/pulls/' + pr_number + '/files').json()
    files = []
    badFiles = []
    for i in range(len(commit)):
        files.append(commit[i]['filename'])
    for fileName in files:
        if fileName.split("/")[0] != branch_name:
            badFiles.append(fileName)
    if len(badFiles) > 0:
        with open("/app/gh-pages/WishBuilder/StatusReports/" + branch_name + "-status.md", "w") as status_file:
            status_file.write("<h1><center>" + branch_name + "</center></h1>\n")
            status_file.write("<h2><center> Status: Failed </center></h2>\n\n")
            status_file.write("Only files in the \"" + branch_name + "\" directory should be changed. The following files were also changed in this branch:\n")
            for file in badFiles:
                status_file.write("- " + file + "\n")
        status_file.close()
        return 0
    else:
        for fileName in files:
            if fileName != branch_name + "/description.md" and fileName != branch_name + "/config.yaml":
                return 1
    return 2


def test_pr(index):
    fullTest = True
    Pass = False
    branchName = pr[index]['head']['ref']
    ssh_url = pr[index]['head']['repo']['ssh_url']
    url = pr[index]['head']['repo']['url']
    sha = pr[index]['head']['sha']
    pullNumber = str(pr[index]['number'])
    user = pr[index]['user']['login']
    testType = valid_files(pullNumber, branchName)
    start = time.time()
    status = ""
    if branchName in os.listdir():
        os.system('rm -rf ' + branchName)
    os.mkdir(branchName)
    os.chdir(branchName)
    os.system('git clone ' + ssh_url)
    os.chdir('./WishBuilder')
    print('Pull Request #' + str(pr[index]['number']) + ' Branch: ' + branchName, flush=True)
    print('Checking out branch . . .', flush=True)
    subprocess.run(["git", "checkout", "remotes/origin/" + branchName], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Check if only description or yaml was edited
    if testType == 2:
        update_history(index, pullNumber, update=True)
        Pass = True
        print('Only description.md and/or config was edited, no test needed', flush=True)
        os.system('mv ./' + branchName + '/config.yaml /app/CompleteDataSets/' + branchName + '/')
        os.system('mv ./' + branchName + '/description.md /app/CompleteDataSets/' + branchName + '/')
        os.system('cp /app/CompleteDataSets/' + branchName + '/description.md /app/gh-pages/WishBuilder/Descriptions/' + branchName + '-description.md')
        convertForGeney('/app/CompleteDataSets/' + branchName, '/app/GeneyDataSets/' + branchName, simple=True)
        os.chdir('/app')
    elif testType == 1:
        update_history(index, pullNumber)
        os.system('cp /app/test.py ./')
        os.system('cp -r ' + branchName + ' ./testDirectory')
        print('Testing ' + branchName + '(test.py \"./WishBuilder/' + branchName + '/\"):', flush=True)
        os.system('python3 ./test.py \"/app/' + branchName + '/WishBuilder/testDirectory/\" ' + branchName)
        status = check_status("/app/StatusReports/" + branchName + "-status.md")
        os.system('cp testDirectory/description.md /app/Descriptions/' + branchName + '-description.md')

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
        else:
            numSamples = 0
            metaVariables = 0
            featureVariables = 0
        if status == "Complete":
            Pass = True
            print('Moving data.tsv.gz, metadata.tsv.gz, and description.md to CompleteDataSets/' + branchName, flush=True)
            os.system('mkdir /app/CompleteDataSets/' + branchName)
            os.system('mv data.tsv.gz /app/CompleteDataSets/' + branchName + '/')
            os.system(
                'mv metadata.tsv.gz /app/CompleteDataSets/' + branchName + '/')
            os.system(
                'mv ./testDirectory/description.md /app/CompleteDataSets/' + branchName + '/')
            os.system(
                'mv ./testDirectory/config.yaml /app/CompleteDataSets/' + branchName + '/')
            os.system('sudo chmod -R 777 /app/CompleteDataSets/' + branchName)
            convertForGeney('/app/CompleteDataSets/' + branchName, '/app/GeneyDataSets/' + branchName)
        else:
            Pass = False
            # print('Moving data.tsv.gz, metadata.tsv.gz, and description.md to IncompleteDataSets/' + branchName,
            #       flush=True)
            # os.system('mkdir /app/IncompleteDataSets/' + branchName)
            # if 'data.tsv.gz' in os.listdir():
            #     os.system('mv data.tsv.gz /app/IncompleteDataSets/' +
            #               branchName + '/')
            # if 'metadata.tsv.gz' in os.listdir():
            #     os.system('mv metadata.tsv.gz /app/IncompleteDataSets/' +
            #               branchName + '/')
            # if 'description.md' in os.listdir('./testDirectory'):
            #     os.system(
            #         'mv ./testDirectory/description.md /app/IncompleteDataSets/' + branchName + '/')
            # if 'config.yaml' in os.listdir('./testDirectory'):
            #     os.system(
            #         'mv ./testDirectory/config.yaml /app/IncompleteDataSets/' + branchName + '/')
            # os.system('sudo chmod -R 777 /app/IncompleteDataSets/' + branchName)
        os.system('rm -rf test*')
        subprocess.run(["git", "checkout", "-f", "master"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        timeElapsed = time.strftime("%Hh:%Mm:%Ss", time.gmtime(time.time() - start))
        dateFinished = time.strftime("%D", time.gmtime(time.time()))
        update_history(index, pullNumber, Pass, timeElapsed, numSamples, metaVariables, featureVariables)
        print('Finished with branch \"%s\". Time elapsed: %s\n' % (branchName, timeElapsed), flush=True)
        os.chdir('/app')
        os.system('cp ./StatusReports/' + branchName + '-status.md ./gh-pages/WishBuilder/StatusReports/')
        os.system('cp ./Descriptions/' + branchName + '-description.md ./gh-pages/WishBuilder/Descriptions/')
    elif testType == 0:
        update_history(index, pullNumber, time_elapsed="N\A")
        Pass = False
        print('Invalid File Changes', flush=True)
    update_pages(branchName)
    os.system('rm -rf /app/' + branchName)
    if Pass:
        merge_branch(index)


payload = requests.get('https://api.github.com/repos/srp33/WishBuilder/pulls')
pr = payload.json()
newPRs = True
updateNeeded = False

while newPRs:
    history = check_history('/app/prHistory.json')
    if history[0]:
        updateNeeded = True
        test_pr(history[1])
        # newPRs = False
    else:
        newPRs = False

if updateNeeded:
    update_website()
# else:
#     print('No new pull requests')
