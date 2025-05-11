.PHONY: clean clone count

all:
	$(MAKE) clean clone count

clean:
	cd data && rm -rf repos counts.csv

clone:
	cd data && parallel -j16 --halt never "git clone git@github.com:{1}.git repos/{1} 2>/dev/null || true" < repos.txt

count:
	python scripts/pycount.py data/repos/ data/counts.csv
