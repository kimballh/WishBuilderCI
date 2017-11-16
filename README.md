# WishBuilderCI
Continuous Integration Pipeline which tests and deploys pull requests to [*WishBuilder*](https://github.com/srp33/WishBuilder)

## Purpose

*WishBuilder* is an open source project that provides biology-related datasets to *Geney*, a service that makes the data easily to filter and query for research. *WishBuilder* allows users to submit code which gathers and reformats data pulled from public Web servers into a consistent format described on the project [wiki](https://srp33.github.io/WishBuilder/).

*WishBuilderCI* (Continuous Integration) manages the pull requests submitted to *WishBuilder* by detecting them automatically, testing that the ouput data is consistent with the *WishBuilder* requirements, and adding the datasets created by the code contained in each passed dataset to *Geney*.

## How it Works

### Environment
#### Docker
*WishBuilderCI* requires [Docker](https://docker.com) to test code in an environement container. The "wishbuilder" image used to create each container can be pulled from the docker hub with this command:
```bash
docker pull kimballer/wishbuilder
```
#### Directory
*WishBuilderCI* is executed through a bash script, all code must be in a directory which contains the following items to run correctly:

- Directories:
    - CompleteDataSets - the output data files (data.tsv.gz & metadata.tsv.gz) are put here if testing is successful
    - Descriptions - the output description file (<font>description.<font>md) is put here.
    - gh-pages - contains a cloned *WishBuilder* repository on the "gh-pages" branch.
    - WishBuilder - is a cloned *WishBuilder* repository on the "master" branch.
    - StatusReports - the status report (status.<font>md) created during testing is put here.
- Files:
    - checkWishBuilder.<font>sh
    - checkWishBuilder.<font>py
    - .prhistory - a list of pull requests which have already been tested by *WishBuilderCI*
### Execution (/bin/bash checkWishBuilder.<font>sh)
1. checkWishBuilder.<font>sh updates the git repositories and runs the wishbuilder container
1. wishbuilder Container executes "python checkWishBuilder.<font>py"
1. checkWishBuilder.<font>py requests a payload from the gitHub API containing information about pull requests.
1. checkWishBuilder.<font>py runs test on each new pull request "python test.<font>py '/path/to/user/code' 'Branch_Name'". All results are copied to gh-pages branch of *WishBuilder*
1. checkWishBuilder.<font>py stores the output from passing pull requests locally, then merges the code into to the *WishBuilder* project, and closes failing pull requests
1. wishbuilder container exits and is deleted
1. checkWishBuilder.<font>sh publishes results of all tests to [*WishBuilder* website](https://srp33.github.io/WishBuilder/) by committing and pushing changes to gh-pages branch of *WishBuilder* repository