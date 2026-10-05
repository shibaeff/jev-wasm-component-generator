.PHONY: test audit compile-library clean

test: compile-library
	python3 -m unittest discover -s synth/tests -v
	npm test

compile-library:
	@for file in library/*.wat; do node scripts/compile-wat.js "$$file" >/dev/null || exit 1; done
	@echo "all library modules compile independently"

audit:
	python3 -m synth.audit

clean:
	rm -rf generated __pycache__ synth/__pycache__ synth/jev/__pycache__ synth/tests/__pycache__
