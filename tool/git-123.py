import json
import os
import subprocess
import webbrowser
from datetime import datetime


class RunCommandException(Exception):
    """Exception raised by run_command when exitcode is non-zero.

    Attributes:
        exitcode -- code returned by the process
        out -- stdout returned by the process
        err -- stderr returned by the process
    """

    def __init__(self, exitcode, out, err):
        self.exitcode = exitcode
        self.out = out
        self.err = err


def run_command(arr, input=None):
    # Stack Overflow: https://stackoverflow.com/questions/1996518/retrieving-the-output-of-subprocess-call
    # Note, Out and Err are buffered in memory, so do not use this method if
    # the data size is large or unlimited.
    out = None
    err = None
    exitcode = None
    if input is None:
        proc = subprocess.Popen(arr, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        exitcode = proc.returncode
    else:
        proc = subprocess.Popen(
            arr, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE
        )
        out, err = proc.communicate(input.encode("ascii"))
        exitcode = proc.returncode

    outStr = out.decode("ascii")
    errStr = err.decode("ascii")

    if exitcode != 0:
        raise RunCommandException(exitcode, outStr, errStr)
    else:
        return exitcode, outStr, errStr


def print_(text=None):
    global gOutputToFile
    global gOutputFile
    if text:
        print(text)
    else:
        print()
    if gOutputToFile:
        if text:
            print(text, file=gOutputFile)
        else:
            print(file=gOutputFile)


def print_indented(text, level=1):
    indentation = ""
    for i in range(0, level):
        indentation += "    "

    lines = text.split("\n")

    for line in lines:
        if line:
            print_(indentation + line)


def getResponse(options, level=1, message="    >>> "):
    m = len(max(options, key=len))
    s = "-" * 16 + "-" * m
    print_indented("\n" + s, level)
    for x in range(len(options)):
        l = len(options[x])
        p = "-" * (m - l + 3)
        if x > 9:
            p = "-" * (m - l + 1)
        print_indented(
            "-> {} - {} {} {} <-".format(str(x), options[x], p, str(x)), level
        )
    print_indented(s + "\n", level)
    optionStr = input(message)
    try:
        optionInt = int(optionStr)
    except:
        return 1000
    if optionInt < 100:
        try:
            option = options[optionInt]
        except:
            raise Exception(" Invalid Selection.")
        print_(" Selected: {}".format(option))
    return optionInt


def commitAll(arg=None):
    if arg:
        commitMessage = arg
    else:
        commitMessage = input(" Commit Message: ")
    c = gCommitAll[:]
    c.append(commitMessage)
    exitcode, out, err = run_command(c)
    print_(out)


def commit(arg=None):
    if arg:
        commitMessage = arg
    else:
        commitMessage = input(" Commit Message: ")
    c = gCommit[:]
    c.append(commitMessage)
    exitcode, out, err = run_command(c)
    print_(out)


def fetch(arg=None):
    print_("Fetch...")
    c = gFetch[:]
    if arg:
        c = gFetch + arg
    exitcode, out, err = run_command(c)
    print_(out)


def pull(arg=None):
    print_("Pull...")
    c = gPull[:]
    if arg:
        c = gPull + arg
    exitcode, out, err = run_command(c)
    print_(out)


def push(arg=None):
    m = "Push..."
    c = gPush[:]
    if arg:
        c = gPush + arg
        m = "Push to New..."
    print_(m)
    exitcode, out, err = run_command(c)
    print_(out)


def checkout(branch):
    print_("Checkout {}".format(branch))
    c = gCheckout[:]
    c.append(branch)
    exitcode, out, err = run_command(c)
    print_(out)


def merge(arg):
    print_("Merge {}".format(arg))
    c = gMerge[:]
    c.append(arg)
    exitcode, out, err = run_command(c)
    print_(out)


def merge_into_devhead(repo, taskBranch):
    if taskBranch == gSelectedDevHead:
        raise Exception(
            "You cannot run this from {0}. Checkout your"
            " task branch first!".format(gSelectedDevHead)
        )
    options = [
        "Merge",        # 0
        "Pull & Merge", # 1
        "Exit",         # 2
    ]
    optionInt = getResponse(options)
    if optionInt < 2:
        checkout(gSelectedDevHead)

    if optionInt == 0:
        merge(taskBranch)
    elif optionInt == 1:
        pull()
        merge(taskBranch)
    elif optionInt == 2:
        return

    options = [
        "Push {}".format(gSelectedDevHead), # 0
        "Back to {}".format(taskBranch),    # 1
        "Abort Merge",                      # 2
        "Exit",                             # 3
    ]
    optionInt = getResponse(options)

    if optionInt == 0:
        push()
        print_('"Compile DB objects here."')
        options = [
            "Back to {}".format(taskBranch), # 0
            "Exit",                          # 1
        ]
        optionInt = getResponse(options)

        if optionInt == 0:
            checkout(taskBranch)
            options = [
                "Open in BitBucket", # 0
                "Exit",              # 1
            ]
            optionInt = getResponse(options)

            if optionInt == 0:
                url = "https://bitbucket.org/{}/{}/branch/{}".format(
                    gBitBucketOrg, repo, taskBranch
                )
                print_("Opening Branch...")
                webbrowser.open(url)
            elif optionInt == 1:
                return
        elif optionInt == 1:
            return
    elif optionInt == 1:
        checkout(taskBranch)
    elif optionInt == 2:
        merge("--abort")
    elif optionInt == 3:
        pass


def afterPush(repo, taskBranch):
    if taskBranch != gSelectedDevHead:
        options = [
            "Open in BitBucket",                      # 0
            "Merge into {}".format(gSelectedDevHead), # 1
            "Main Menu",                              # 2
            "Exit",                                   # 3
        ]
        optionInt = getResponse(options)

        if optionInt == 0:
            url = "https://bitbucket.org/{}/{}/branch/{}".format(
                gBitBucketOrg, repo, taskBranch
            )
            print_("Opening Branch...")
            webbrowser.open(url)
        elif optionInt == 1:
            merge_into_devhead(repo, taskBranch)
        elif optionInt == 2:
            main(repo)
        elif optionInt == 3:
            pass


def pushOption(repo, taskBranch):
    options = [
        "Push to Existing", # 0
        "Push to New",      # 1
        "Main Menu",        # 2
        "Exit",             # 3
    ]
    optionInt = getResponse(options)

    if optionInt == 0:
        push()
        afterPush(repo, taskBranch)
    elif optionInt == 1:
        push(["--set-upstream", "origin", taskBranch])
        afterPush(repo, taskBranch)
    elif optionInt == 2:
        main(repo)
    elif optionInt == 3:
        pass


def addAll():
    print_("Add all")
    c = gAddAll[:]
    exitcode, out, err = run_command(c)
    print_(out)


def add(arg):
    print_("Add {}".format(arg))
    c = gAdd[:]
    c.append(arg)
    exitcode, out, err = run_command(c)
    print_(out)


def commitSteps(repo, taskBranch, stepsBranch, migration, issue):
    if taskBranch != stepsBranch:
        if taskBranch != gMainBranch:
            checkout(gMainBranch)
        pull()
        checkout(["-b", stepsBranch])
    addFile = "migration\\{}\\{}\\step_0.info".format(migration, issue)
    add(addFile)
    commit("Add migration steps")
    pushOption(repo, stepsBranch)


def remoteGone(taskBranch):
    if taskBranch != gMainBranch:
        print_("You must start from branch: {0}".format(gMainBranch))
        return
    exitcode, out, err = run_command(["git", "branch", "-vv"])
    lines = out.splitlines()
    branchesList = []
    print_indented("**   Branches that no longer exist on Remote:")
    print_()
    for line in lines:
        if ": gone]" in line:
            branches = line.split(None, 1)
            branchesList.append(branches[0])
            print_indented(branches[0])
    if not branchesList:
        print_indented("**   No branches to delete")
        return
    print_()
    options = [
        "Delete All",          # 0
        "Delete Individually", # 1
        "Exit",                # 2
    ]
    optionInt = getResponse(options)
    if optionInt == 0:
        for b in branchesList:
            exitcode, out, err = run_command(["git", "branch", "-D", b])
            print_(out)
    elif optionInt == 1:
        for b in branchesList:
            options = [
                "Delete {}".format(b), # 0
                "Continue",            # 1
            ]
            optionInt = getResponse(options)
            if optionInt == 0:
                exitcode, out, err = run_command(["git", "branch", "-D", b])
                print_(out)
            elif optionInt == 1:
                pass
    elif optionInt == 2:
        pass


def checkout_fetch_pull(taskBranch):
    if taskBranch != gMainBranch:
        checkout(gMainBranch)
    fetch(["--prune", "origin"])
    pull()


def checkout_devhead_pull(taskBranch):
    if taskBranch != gSelectedDevHead:
        checkout(gSelectedDevHead)
    pull()
    checkout(gMainBranch)


def header_footer(repo, taskBranch):
    lenRepo = len(repo)
    lenBranch = len(taskBranch)
    lenMain = len(gMainBranch)
    l = max(lenRepo + 12, lenBranch + 8, lenMain + 6)
    p = (
        "    **   Repository: {}".format(repo)
        + "   "
        + " " * (l - lenRepo - 12)
        + "**"
    )
    b = (
        "    **   Branch: {}".format(taskBranch)
        + "   "
        + " " * (l - lenBranch - 8)
        + "**"
    )
    m = (
        "    **   Main: {}".format(gMainBranch)
        + "   "
        + " " * (l - lenMain - 6)
        + "**"
    )

    s = "    " + "*" * (len(b) - 4)
    print_("\n" + s)
    print_(p)
    print_(b)
    print_(m)
    print_(s + "\n")


def main(repo):
    repoPath = os.path.join(gLocalReposDir, repo)
    exitcode, out, err = run_command(["git", "symbolic-ref", "--short", "HEAD"])
    taskBranch = out.strip()
    header_footer(repo, taskBranch)
    exitcode, out, err = run_command(["git", "status"])
    print_(out)

    options = [
        "Commit...",                               # 0
        "Checkout...",                             # 1
        "Pull / Push / Fetch...",                  # 2
        "Migration Steps...",                      # 3
        "Merge...",                                # 4
        "New Branch",                              # 5
        "Open in BitBucket",                       # 6
        "Remote Gone",                             # 7
        "Repository List",                         # 8
        "Exit (Press Enter)",                      # 9
    ]
    optionInt = getResponse(options)

    if optionInt == 0:
        options = [
            "Commit All, Push To Existing Remote",      # 0
            "Commit All, Push to New Remote",           # 1
            "Add All, Commit, Push To Existing Remote", # 2
            "Add All, Commit, Push to New Remote",      # 3
            "Commit Staged, Push To Existing Remote",   # 4
            "Commit Staged, Push to New Remote",        # 5
            "Commit Only",                              # 6
            "Main Menu",                                # 7
            "Exit",                                     # 8
        ]
        optionInt = getResponse(options, 2)
        if optionInt == 0:
            commitAll()
            push()
            afterPush(repo, taskBranch)
        elif optionInt == 1:
            commitAll()
            push(["--set-upstream", "origin", taskBranch])
            afterPush(repo, taskBranch)
        if optionInt == 2:
            addAll()
            commit()
            push()
            afterPush(repo, taskBranch)
        elif optionInt == 3:
            addAll()
            commit()
            push(["--set-upstream", "origin", taskBranch])
            afterPush(repo, taskBranch)
        if optionInt == 4:
            commit()
            push()
            afterPush(repo, taskBranch)
        elif optionInt == 5:
            commit()
            push(["--set-upstream", "origin", taskBranch])
            afterPush(repo, taskBranch)
        elif optionInt == 6:
            commit()
            pushOption(repo, taskBranch)
        elif optionInt == 7:
            main(repo)
        elif optionInt == 8:
            pass
    elif optionInt == 1:
        options = [
            "Checkout local...",                     # 0
            "Checkout remote...",                    # 1
            "Checkout {}".format(gSelectedDevHead),  # 2
            "Checkout {}".format(gMainBranch),       # 3
            "Checkout {}".format(gMainProdBranch),   # 4
            "Main Menu",                             # 5
        ]
        optionInt = getResponse(options, 2)
        if optionInt in (0, 1):
            exitcode, out, err = run_command(["git", "branch"])
            lines = out.splitlines()
            localLines = [l.strip() for l in lines]
            branchesList = []
            for p in gBranchPrefixes:
                for l in localLines:
                    if l.find(p) == 0:
                        branchesList.append(l)
        if optionInt == 0:
            if len(branchesList) > 0:
                optionInt = getResponse(branchesList, 3)
                if optionInt == 1000:
                    return
                try:
                    checkout(branchesList[optionInt])
                except:
                    raise Exception(" Invalid Selection.")
            else:
                print_("\n")
                print_indented(
                    "** No prefixed branches available to checkout. **\n", level=3
                )
                print_("\n")
            main(repo)
        elif optionInt == 1:
            fetch(["--prune", "origin"])
            exitcode, out, err = run_command(["git", "branch", "-r"])
            lines = out.splitlines()
            remoteLines = [l.strip() for l in lines]
            RemoteBranchesList = []
            for p in gBranchPrefixes:
                if taskBranch.find(p) == 0:
                    branchesList.append(taskBranch)
                    break
            for p in gBranchPrefixes:
                for l in remoteLines:
                    if l.find("origin/{}".format(p)) == 0 and l[7:] not in branchesList:
                        RemoteBranchesList.append(l)
            if len(RemoteBranchesList) > 0:
                optionInt = getResponse(RemoteBranchesList, 3)
                if optionInt == 1000:
                    return
                try:
                    exitcode, out, err = run_command(
                        [
                            "git",
                            "checkout",
                            "-b",
                            RemoteBranchesList[optionInt][7:],
                            "--track",
                            RemoteBranchesList[optionInt],
                        ]
                    )
                except:
                    raise Exception(" Invalid Selection.")
            else:
                print_("\n")
                print_indented(
                    "** No prefixed branches available to checkout. **\n", level=3
                )
                print_("\n")
            main(repo)
        elif optionInt == 2:
            checkout(gSelectedDevHead)
            main(repo)
        elif optionInt == 3:
            checkout(gMainBranch)
            main(repo)
        elif optionInt == 4:
            checkout(gMainProdBranch)
            main(repo)
        elif optionInt == 5:
            main(repo)
    elif optionInt == 2:
        options = [
            "Fetch, Prune & Pull (must be on {})".format(gMainBranch), # 0
            "Fetch & Prune Origin",              # 1
            "Pull",                              # 2
            "Pull {0}".format(gSelectedDevHead), # 3
            "Push to Existing",                  # 4
            "Push to New",                       # 5
            "Main Menu",                         # 6
            "Exit",                              # 7
        ]
        optionInt = getResponse(options, 2)
        if optionInt == 0:
            if taskBranch not in (gMainBranch, gMainProdBranch):
                print_(
                    "You must start from branch: {0} or {1}".format(
                        gMainBranch, gMainProdBranch
                    )
                )
                return
            fetch(["--prune", "origin"])
            pull()
            main(repo)
        elif optionInt == 1:
            fetch(["--prune", "origin"])
            main(repo)
        elif optionInt == 2:
            pull()
            main(repo)
        elif optionInt == 3:
            checkout_devhead_pull(taskBranch)
            main(repo)
        elif optionInt == 4:
            push()
            main(repo)
        elif optionInt == 5:
            push(["--set-upstream", "origin", taskBranch])
            main(repo)
        elif optionInt == 6:
            main(repo)
        elif optionInt == 7:
            pass

    elif optionInt == 3:
        print_indented("({})".format(gSelectedMigration), 2)
        options = [
            "Steps File - Copy & Commit", # 0
            "Steps File - Commit Only",   # 1
            "Main Menu",                  # 2
            "Exit",                       # 3
        ]
        optionInt = getResponse(options, 2)
        if optionInt == 20 and taskBranch != gMainBranch:
            print_("You must start from branch: {0}".format(gMainBranch))
            return
        if optionInt in (0, 1, 20):
            issue = input(" Issue/Task: ")
            if not issue:
                return
            stepsBranch = "{}/{}".format(gStepsPrefix, issue)
        if optionInt == 0:
            stepsPath = os.path.join(repoPath, gStepsTemplate)
            c = "xcopy {} {}\\migration\\{}\\{} /i /k".format(
                stepsPath, repoPath, gSelectedMigration, issue
            )
            os.system(c)
            x = input(" Modify file as needed. Press 0 to continue.")
            if x == "0":
                commitSteps(repo, taskBranch, stepsBranch, gSelectedMigration, issue)
        elif optionInt == 1:
            commitSteps(repo, taskBranch, stepsBranch, gSelectedMigration, issue)
        elif optionInt == 2:
            main(repo)
        elif optionInt == 3:
            pass
    elif optionInt == 4:
        options = [
            "Merge in {}".format(gMainBranch),           # 0
            "Merge into {}...".format(gSelectedDevHead), # 1
            "Main Menu",                                 # 2
        ]
        optionInt = getResponse(options, 2)
        if optionInt == 0:
            if taskBranch == gMainBranch:
                raise Exception(
                    "You cannot run this from {0}. Checkout your"
                    " task branch first!".format(gMainBranch)
                )
            checkout(gMainBranch)
            pull()
            checkout(taskBranch)
            merge(gMainBranch)
            pushOption(repo, taskBranch)
        elif optionInt == 1:
            merge_into_devhead(repo, taskBranch)
        elif optionInt == 2:
            main(repo)
    elif optionInt == 5:
        newBranch = input(" New Branch: ")
        checkout(["-b", newBranch])
        main(repo)
    elif optionInt == 6:
        url = "https://bitbucket.org/{}/{}/branch/{}".format(
            gBitBucketOrg, repo, taskBranch
        )
        print_("Opening Branch...")
        webbrowser.open(url)
    elif optionInt == 7:
        remoteGone(taskBranch)
        main(repo)
    elif optionInt == 8:
        selectRepo(False)
    elif optionInt == 9:
        pass
    elif optionInt == 100:
        checkout_fetch_pull(taskBranch)
        main(repo)
    elif optionInt == 105:
        checkout_fetch_pull(taskBranch)
        newBranch = input(" New Branch: ")
        checkout(["-b", newBranch])
        main(repo)
    elif optionInt == 107:
        checkout_fetch_pull(taskBranch)
        remoteGone(gMainBranch)
        main(repo)


def selectRepo(useDefault=True):
    global gRepo
    global gMainBranch
    global gSelectedDevHead
    global gSelectedMigration
    with os.scandir(gLocalReposDir) as mydir:
        dirs = sorted(
            list(set([i.name for i in mydir if i.is_dir()]) - set(gExcludeReposList))
        )
    if gDefaultRepo and useDefault and gDefaultRepo in dirs:
        repo = gRepo = gDefaultRepo
    else:
        optionInt = getResponse(dirs, 1, " Choose Repository: ")
        if optionInt == 1000:
            return
        try:
            repo = dirs[optionInt]
        except:
            raise Exception(" Invalid Selection.")
        gRepo = "{} ({})".format(repo, optionInt)
    repoPath = os.path.join(gLocalReposDir, repo)
    os.chdir(repoPath)

    if repo in gSpecificMainDev:
        gMainBranch = gSpecificMainDev[repo]
    else:
        gMainBranch = gMainDevBranch

    if repo in gSpecificDevHead:
        gSelectedDevHead = gSpecificDevHead[repo]
    else:
        gSelectedDevHead = gDevHeadBranch

    if repo in gSpecificMigration:
        gSelectedMigration = gSpecificMigration[repo]
    else:
        gSelectedMigration = gMigrationFolder

    main(repo)


# load global settings from config file
fileName = "git-123.json"
path = os.path.join(os.getcwd(), fileName)
if not os.path.exists(fileName):
    print_("Could not find config file named git-123.json in same folder.")

with open(path, "r") as json_config_file:
    configData = json.load(json_config_file)

gBitBucketOrg = configData["bitBucketOrg"]
gLocalReposDir = configData["localReposDir"]
gDefaultRepo = configData["defaultRepo"]
gExcludeReposList = configData["excludeRepos"]
gReleasesList = configData["releases"]
gDevHeadBranch = configData["devHeadBranch"]
gSelectedDevHead = gDevHeadBranch
gMainDevBranch = configData["mainDevBranch"]
gMainBranch = gMainDevBranch
gMigrationFolder = configData["migrationFolder"]
gSelectedMigration = gMigrationFolder
gSpecificMainDev = configData["specificMainDev"]
gSpecificDevHead = configData["specificDevHead"]
gSpecificMigration = configData["specificMigration"]
gMainProdBranch = configData["mainProdBranch"]
gOutputToFile = configData["outputToFile"]
gBranchPrefixes = configData["branchPrefixes"]
gStepsPrefix = configData["stepsPrefix"]
gStepsTemplate = configData["stepsTemplate"]
gCheckout = ["git", "checkout"]
gCommit = ["git", "commit", "-m"]
gCommitAll = ["git", "commit", "-a", "-m"]
gFetch = ["git", "fetch"]
gMerge = ["git", "merge"]
gPull = ["git", "pull"]
gPush = ["git", "push"]
gAdd = ["git", "add"]
gAddAll = ["git", "add", "--all"]
gStashPatch = ["git", "stash", "--patch"]
gOutputFile = None
gRepo = ""


if gOutputToFile:
    gOutputFile = open("git-123.log", "a")

print_("\n" * 3 + "_" * 24)
print_(datetime.now().strftime("%a, %b %d: %I:%M:%S %p"))
print_("\nBegin.\n" + "_" * 24 + "\n" * 3)
selectRepo()

print_(datetime.now().strftime("%a, %b %d: %I:%M:%S %p"))
print_("\nDone.\n")
try:
    exitcode, out, err = run_command(["git", "symbolic-ref", "--short", "HEAD"])
    taskBranch = out.strip()
    if gRepo:
        header_footer(gRepo, taskBranch)
except:
    pass

if gOutputToFile:
    gOutputFile.close()
