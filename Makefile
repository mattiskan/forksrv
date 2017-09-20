PHONY: test virtualenv_run

test:
	virtualenv_run/bin/python -m pytest --capture=no tests/

virtualenv_run:
	virtualenv -p `which python3.6` virtualenv_run
	virtualenv_run/bin/pip install -r requirements.txt
