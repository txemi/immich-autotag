#!/usr/bin/env bash
# darnlang, pinned — used ONLY for the surfaces this repo's own gate cannot see.
#
# ⚠️ THIS DOES NOT REPLACE `check_no_spanish_chars`. That check is better than darnlang on files:
# it reads every tracked file rather than a chosen list of extensions, it judges file NAMES, and it
# carries a curated 100-word list plus an optional langdetect layer. It stays exactly as it is.
#
# What it cannot see is what is written straight into GitHub — commit messages, pull-request titles
# and descriptions, issues. Measured with this repo's OWN detector on 2026-08-13: 42 lines across
# the last 400 commit messages, 1 of 10 issues and 10 of 60 pull requests, with the file gate green
# the whole time. Those surfaces are also the least retractable: an indexed PR title cannot be
# withdrawn.
#
# darnlang is told to use THIS repo's wordlist (`--words-file`), so the policy stays here and only
# the plumbing is shared. One tool for the surface nobody was watching, not a second opinion about
# the files.
export DARNLANG_REF="git+https://github.com/txemi/darnlang@v0.7.0"
export DARNLANG_WORDS="$(git rev-parse --show-toplevel)/scripts/devtools/spanish_words.txt"
