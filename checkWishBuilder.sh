#! /bin/bash
echo Updating WishBuilder Repository
cd ./gh-pages/WishBuilder/
git pull -q origin gh-pages
cd ..
cd ../WishBuilder/
git pull -q origin master
git remote update origin --prune
cd ..
LINES_BEFORE="$(wc -l .prhistory)"
docker run -v $(pwd):/app --rm kimballer/wishbuilder
LINES_AFTER="$(wc -l .prhistory)"
if [ "${LINES_BEFORE}" = "${LINES_AFTER}" ]; then
    echo No new Pull Requests
else
    echo Pushing test results to gitHub
    cd ./gh-pages/WishBuilder
    git add --all
    git commit -q -m "added data sets"
    git push -q origin gh-pages
fi
