#! /bin/bash
cd /Analysis/GeneyWishBuilder/Testing
date
docker run -v $(pwd):/app --rm kimballer/wishbuilder