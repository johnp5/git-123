# git-123

A git command-line tool. Run from anywhere on your machine. i.e. C:\Apps\git-123

It was designed for a numeric keypad (hence the name).

Repository Owner: John P

## Contributor Guidelines

Contributions to this repository can be made by creating a branch off the
development branch. When ready, create a pull request to merge the changes back
into the development branch. Approval and inclusion of changes will be handled
by the repository owner. Approval will largely be based on whether the change
is something I would find useful - otherwise, forking will be recommended!

Git branches should use the following prefix:

- `issue/`

## Setup
In git-123.json

Set the prefixes to include for checkout:
  "branchPrefixes": [
    "issue",
    "release"
  ],

Set to your local path:
  "localReposDir": "C:\\git",

Set to bypass the Repository select:
  "defaultRepo": "",

Change if needed:
  "mainDevBranch": "development",
  "devHeadBranch": "devhead",
  "mainProdBranch": "master",

Set to also save all screen output to a git-123.log file:
  "outputToFile": true,

