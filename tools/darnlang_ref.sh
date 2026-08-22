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
# This repo's wordlist DOES reach darnlang, but not the way the two lines above used to claim.
# Nothing passes `--words-file`; grep the workflows and it is simply absent. What actually happens
# is AUTO-DETECTION: `scripts/devtools/spanish_words.txt` is one of the filenames darnlang looks for
# on its own, and it says so out loud on every run ("adding 100 word(s) from …").
#
# The difference is not academic and it runs the other way from the old comment:
#   `--words-file`   REPLACES the built-in list  -> this repo's 100 words, and nothing else
#   auto-detection   ADDS to the built-in list   -> this repo's 100 words PLUS the shared ones
# Auto-detection is the behaviour we want here. But it is bound to the FILENAME, so renaming or
# moving that file drops the 100 words in silence, and the variable below will not save it — it is
# read by nobody. Kept, and labelled, because deleting it would hide where the list lives.
#
# ⚠️ DO NOT QUOTE A SAMPLE WORD ANYWHERE IN THIS FILE. It is tracked, so `check_no_spanish_chars`
# scans it like any other, and it has no general "this is only an example" marker — the single
# per-line opt-out is the literal `SPANISH_PATTERN=`, reserved for the shell gate's own regex.
# Quoting two samples in the twin comment of `.github/workflows/lang-surfaces.yml` is what turned
# four Jenkins rows red on 2026-08-13. Name the list file instead; that is what it is for.
export DARNLANG_REF="git+https://github.com/txemi/darnlang@v0.9.1"
# Documentation only: darnlang finds this path by name, it is not passed as a flag anywhere.
export DARNLANG_WORDS="$(git rev-parse --show-toplevel)/scripts/devtools/spanish_words.txt"
