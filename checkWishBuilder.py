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
    if fullUpdate:
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
                elif prHistory[index]['timeElapsed'] == 'N/A':
                    stat = "Updated"
                elif prHistory[index]['timeElapsed'] == 'In Progress':
                    stat = "In Progress"
                else:
                    stat = "Failed"
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
        cwd = os.getcwd()
        os.chdir('/app/WishBuilder')
        os.system('git checkout -q master')
        os.system('git pull -q origin master')
        os.system('git remote update origin --prune')
        os.system('git push -q origin --delete ' + branch_name)
        os.chdir(cwd)
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
        # if pr[i]['head']['ref'] == 'ICGC_BRCA-US_exp_seq':
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


def update_history(i, passed=False, time_elapsed='In Progress', num_samples=0, meta_variables=0, feature_variables=0, update=False):
    with open('/app/prHistory.json') as fp:
        prHistory = json.load(fp)
    if update:
        prHistory[str(pr[i]['number'])].time_elapsed = 'N/A'
        prHistory[str(pr[i]['number'])].branch = pr[i]['head']['ref'] + ' Update'
        prHistory[str(pr[i]['number'])].passed = True
    else: 
        prHistory[str(pr[i]['number'])] = {
            'branch': pr[i]['head']['ref'],
            'prID': pr[i]['id'],
            'prNum': pr[i]['number'],
            'user': pr[i]['user']['login'],
            'sha': pr[i]['head']['sha'],
            'passed': passed,
            'date': time.strftime("%D", time.gmtime(time.time())),
            'eDate': time.time(),
            'timeElapsed': time_elapsed,
            'samples': num_samples,
            'metaVariables': meta_variables,
            'featureVariables': feature_variables
        }
    
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


def test_pr(index):
    fullTest = True
    Pass = False
    update_history(index)
    branchName = pr[index]['head']['ref']
    start = time.time()
    status = ""
    os.mkdir(branchName)
    os.chdir(branchName)
    os.system('git clone ' + WB_URL)
    os.chdir('./WishBuilder')
    print('Pull Request #' + str(pr[index]['number']) + ' Branch: ' + branchName, flush=True)
    user = pr[index]['user']['login']
    print('Checking out branch . . .', flush=True)
    wbDirectory = os.listdir('/app/' + branchName + '/WishBuilder')
    if branchName not in wbDirectory:
        existingDataset = False
    else:
        existingDataset = True
        os.system('cp -r ' + branchName + ' ../original')
    subprocess.run(["git", "checkout", "remotes/origin/" + branchName], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Check if only description or yaml was edited
    if existingDataset:
        if only_description(branchName):
            fullTest = False
    if not fullTest:
        update_history(index, update=True)
        Pass = True
        print('Only description.md and/or config was edited, no test needed', flush=True)
        os.system('mv ./' + branchName + '/config.yaml /app/CompleteDataSets/' + branchName + '/')
        os.system('mv ./' + branchName + '/description.md /app/CompleteDataSets/' + branchName + '/')
        os.system('cp /app/CompleteDataSets/' + branchName + '/description.md /app/gh-pages/WishBuilder/Descriptions/' + branchName + '-description.md')
        convertForGeney('/app/CompleteDataSets/' + branchName, '/app/GeneyDataSets/' + branchName, simple=True)
        update_pages(branchName, fullUpdate=False)
        os.chdir('/app')
    else:
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
        update_history(index, Pass, timeElapsed, numSamples, metaVariables, featureVariables)
        print('Finished with branch \"%s\". Time elapsed: %s\n' % (branchName, timeElapsed), flush=True)
        os.chdir('/app')
        os.system('cp ./StatusReports/' + branchName + '-status.md ./gh-pages/WishBuilder/StatusReports/')
        os.system('cp ./Descriptions/' + branchName + '-description.md ./gh-pages/WishBuilder/Descriptions/')
        update_pages(branchName)
    os.system('rm -rf ' + branchName)
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
    else:
        newPRs = False

if updateNeeded:
    update_website()
# else:
#     print('No new pull requests')
