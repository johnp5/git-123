import json
import os
import re
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


def runSqlCommand(sqlCommand, connectString):
    global subprocess
    out = None
    err = None
    exitcode = None

    proc = subprocess.Popen(
        ["sqlplus", "-S", "-L", connectString],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    proc.stdin.write(sqlCommand)
    out, err = proc.communicate()
    exitcode = proc.returncode

    outStr = out.decode("ascii")
    errStr = err.decode("ascii")

    if exitcode != 0:
        raise RunCommandException(exitcode, outStr, errStr)
    else:
        return exitcode, outStr, errStr


def sqlCommand(filePaths, schema, db):
    file_paths_str = " ".join(filePaths)
    sqlCommandStr = f"set define off;\r\nset serveroutput on;\r\n@{file_paths_str};\r\nshow errors;\r\nexit;"
    sqlCommand = sqlCommandStr.encode()
    connectString = f"{schema}/{db}@{db}"
    print(f"Running {file_paths_str} as {connectString}")
    exitCode, queryResult, errorMessage = runSqlCommand(sqlCommand, connectString)
    print(queryResult)


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


def getResponse(options, level=1, message="    >>> ", returnInt=True):
    m = len(max(options, key=len))
    s = "-" * 16 + "-" * m
    print_indented("\n" + s, level)
    for x in range(len(options)):
        l = len(options[x])
        p = "-" * (m - l + 3)
        if x > 9:
            p = "-" * (m - l + 1)
        print_indented(f"-> {str(x)} - {options[x]} {p} {str(x)} <-", level)
    print_indented(s + "\n", level)
    optionStr = input(message)
    if optionStr == "00":
        return 200
    elif optionStr == "130":
        return 300
    try:
        optionInt = int(optionStr)
    except:
        if returnInt:
            return 1000
        else:
            return 1000, ""
    if optionInt < 100:
        try:
            option = options[optionInt]
        except:
            raise Exception(" Invalid Selection.")
        print_(f" Selected: {option}")
    if returnInt:
        return optionInt
    else:
        return optionInt, option


def selectMessage():
    global gMessages
    commitMessage = None
    numLines = len(gMessages)
    newMessage = False
    if numLines > 0:
        msgReversed = []
        msgReversed.append("-- [ New Message ]")
        for m in reversed(gMessages):
            msgReversed.append(m.strip("\n"))
        r, commitMessage = getResponse(msgReversed, 0, ">>> ", False)
        if r == 0:
            newMessage = True
    else:
        newMessage = True
    if newMessage:
        newMessage = False
        commitMessage = input("\n   Commit Message: ")
        if commitMessage:
            gMessages.append(commitMessage + "\n")
            newMessage = True
    return commitMessage


def git_commands(
    gitAddAll,
    gitAdd,
    gitCommitAll,
    gitCommit,
    gitCheckout,
    gitFetch,
    gitMerge,
    gitPull,
    gitPush,
):
    def addAll():
        print_("Add all")
        command = gitAddAll[:]
        exitcode, out, err = run_command(command)
        print_(out)

    def add(arg):
        print_(f"Add {arg}")
        command = gitAdd[:]
        command.append(arg)
        exitcode, out, err = run_command(command)
        print_(out)

    def checkout(branch):
        print_(f"Checkout {branch}")
        command = gitCheckout[:]
        command.append(branch)
        exitcode, out, err = run_command(command)
        print_(out)

    def commitAll(arg=None):
        commitMessage = arg or selectMessage()
        if not commitMessage:
            return False
        command = gitCommitAll[:]
        command.append(commitMessage)
        exitcode, out, err = run_command(command)
        print_(out)
        return True

    def commit(arg=None):
        commitMessage = arg or selectMessage()
        if not commitMessage:
            return False
        command = gitCommit[:]
        command.append(commitMessage)
        exitcode, out, err = run_command(command)
        print_(out)
        return True

    def fetch(arg=None):
        print_("Fetch...")
        command = gitFetch[:] + arg if arg else gitFetch
        exitcode, out, err = run_command(command)
        print_(out)

    def merge(arg):
        print_(f"Merge {arg}")
        command = gitMerge[:]
        command.append(arg)
        exitcode, out, err = run_command(command)
        print_(out)

    def pull(arg=None):
        print_("Pull...")
        command = gitPull[:] + arg if arg else gitPull
        exitcode, out, err = run_command(command)
        print_(out)

    def push(arg=None):
        m = "Push to New..." if arg else "Push..."
        command = gitPush[:] + arg if arg else gitPush
        print_(m)
        exitcode, out, err = run_command(command)
        print_(out)

    return {
        "addAll": addAll,
        "add": add,
        "commitAll": commitAll,
        "commit": commit,
        "checkout": checkout,
        "fetch": fetch,
        "merge": merge,
        "pull": pull,
        "push": push,
    }


def checkout_fetch_pull(taskBranch):
    if taskBranch != gMainBranch:
        git_cmd["checkout"](gMainBranch)
    git_cmd["fetch"](["--prune", "origin"])
    git_cmd["pull"]()


def checkout_devhead_pull(taskBranch, option=0, mainBranch=False):
    if taskBranch != gSelectedDevHead:
        git_cmd["checkout"](gSelectedDevHead)
    git_cmd["pull"]()
    git_cmd["checkout"](gMainBranch)
    if mainBranch:
        git_cmd["pull"]()
    if option > 100:
        git_cmd["checkout"](taskBranch)


def get_key(d, value):
    for k, v in d.items():
        for r in v:
            if r == value:
                return k
    return f"No DB set for {value}"


def compile(repo, databaseItems):
    if not databaseItems:
        print_indented("**   No items to compile")
        return
    for schema, dbFiles in databaseItems.items():
        print(schema)
        for d in dbFiles:
            print(d)
    print_()
    options = [
        "Compile All",          # 0
        "Compile Individually", # 1
        "Return",               # 2
    ]
    optionInt = getResponse(options, 2)
    if optionInt == 0:
        for schema, dbFiles in databaseItems.items():
            sqlCommand(dbFiles, schema, gDatabase)
    elif optionInt == 1:
        for schema, dbFiles in databaseItems.items():
            for filePath in dbFiles:
                options = [
                    f"Compile {filePath}", # 0
                    "Skip",                # 1
                ]
                optionInt = getResponse(options, 3)
                if optionInt == 0:
                    sqlCommand([filePath], schema, gDatabase)
                elif optionInt == 1:
                    pass
    elif optionInt == 2:
        pass


def merge_into_devhead(repo, taskBranch, databaseItems=None):
    if taskBranch == gSelectedDevHead:
        raise Exception(
            f"You cannot run this from {gSelectedDevHead}."
            " Checkout your task branch first!"
        )
    options = [
        "Merge",        # 0
        "Pull & Merge", # 1
        "Exit",         # 2
    ]
    optionInt = getResponse(options)
    if optionInt < 2:
        try:
            git_cmd["checkout"](gSelectedDevHead)
        except:
            print(f"\n  ** Error checking out {gSelectedDevHead} **\n")
            return

    if optionInt == 0:
        git_cmd["merge"](taskBranch)
    elif optionInt == 1:
        git_cmd["pull"]()
        git_cmd["merge"](taskBranch)
    elif optionInt == 2:
        return

    options = [
        f"Push {gSelectedDevHead}", # 0
        f"Back to {taskBranch}",    # 1
        "Abort Merge",              # 2
        "Exit",                     # 3
    ]
    optionInt = getResponse(options)

    if optionInt == 0:
        git_cmd["push"]()
        num_values = str(len(databaseItems.values()))

        options = [
            f"Back to {taskBranch}",   # 0
            f"Compile ({num_values})", # 1
            "Exit",                    # 2
        ]
        optionInt = getResponse(options)

        if optionInt == 0:
            git_cmd["checkout"](taskBranch)
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
            compile(repo, databaseItems)
            options = [
                f"Back to {taskBranch}", # 0
                "Exit",                  # 1
            ]
            optionInt = getResponse(options)

            if optionInt == 0:
                git_cmd["checkout"](taskBranch)
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
        elif optionInt == 2:
            return
    elif optionInt == 1:
        git_cmd["checkout"](taskBranch)
    elif optionInt == 2:
        git_cmd["merge"]("--abort")
    elif optionInt == 3:
        pass


def afterPush(repo, taskBranch, databaseItems=None):
    if taskBranch != gSelectedDevHead:
        options = [
            f"Merge into {gSelectedDevHead}", # 0
            "Open in BitBucket",              # 1
            "Main Menu",                      # 2
            "Exit",                           # 3
        ]
        optionInt = getResponse(options)

        if optionInt == 0:
            merge_into_devhead(repo, taskBranch, databaseItems)
        elif optionInt == 1:
            url = "https://bitbucket.org/{}/{}/branch/{}".format(
                gBitBucketOrg, repo, taskBranch
            )
            print_("Opening Branch...")
            webbrowser.open(url)
        elif optionInt == 2:
            main(repo)
        elif optionInt == 3:
            pass

def trackingRemote(taskBranch, indent=0):
    exitcode, out, err = run_command(["git", "branch", "-vv"])
    lines = out.splitlines()
    remoteBranch = f"[origin/{taskBranch}"
    remoteBranches = [
        line.split(None, 2)[2]
        for line in lines
        if f"{remoteBranch}]" in line or f"{remoteBranch}:" in line
    ]
    print_()
    for branch in remoteBranches:
        msg = f"Remote: {branch}"
    if not remoteBranches:
        msg = "No remote."
    print_indented("-" * len(msg), indent)
    print_indented(msg, indent)
    return msg[:1]


def pushOption(repo, taskBranch):
    remote = trackingRemote(taskBranch, 1)
    options = [
        "Push",      # 0
        "Main Menu", # 1
        "Exit",      # 2
    ]
    optionInt = getResponse(options)
    if optionInt == 0:
        if remote == "R":
            git_cmd["push"]()
        elif remote == "N":
            git_cmd["push"](["--set-upstream", "origin", taskBranch])
        afterPush(repo, taskBranch)
    elif optionInt == 1:
        main(repo)
    elif optionInt == 2:
        pass


def commitSteps(repo, taskBranch, stepsBranch, migration, issue, x="0"):
    if taskBranch != stepsBranch:
        if taskBranch != gMainBranch:
            git_cmd["checkout"](gMainBranch)
        if x in ("0", "10"):
            git_cmd["pull"]()
        git_cmd["checkout"](["-b", stepsBranch])
    addFile = f"migration\\{migration}\\{issue}\\step_0.info"
    git_cmd["add"](addFile)
    git_cmd["commit"]("Add migration steps")
    if x == "0":
        pushOption(repo, stepsBranch)
    elif x in ("00", "10"):
        git_cmd["push"](["--set-upstream", "origin", stepsBranch])
        url = "https://bitbucket.org/{}/{}/branch/{}".format(
            gBitBucketOrg, repo, stepsBranch
        )
        print_("Opening Branch...")
        webbrowser.open(url)


def remoteGone(taskBranch):
    if taskBranch != gMainBranch:
        print_(f"You must start from branch: {gMainBranch}")
        return
    exitcode, out, err = run_command(["git", "branch", "-vv"])
    lines = out.splitlines()
    goneBranches = [line.split(None, 1)[0] for line in lines if ": gone]" in line]
    print_indented("**   Branches that no longer exist on Remote:")
    print_()
    for branch in goneBranches:
        print_indented(branch)
    if not goneBranches:
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
        for b in goneBranches:
            exitcode, out, err = run_command(["git", "branch", "-D", b])
            print_(out)
    elif optionInt == 1:
        for b in goneBranches:
            options = [
                f"Delete {branch}", # 0
                "Skip",             # 1
            ]
            optionInt = getResponse(options)
            if optionInt == 0:
                exitcode, out, err = run_command(["git", "branch", "-D", b])
                print_(out)
            elif optionInt == 1:
                pass
    elif optionInt == 2:
        pass


def header_footer(repo, taskBranch):
    lenRepo = len(repo)
    lenBranch = len(taskBranch)
    lenMain = len(gMainBranch)
    lenDb = len(gDatabase)
    l = max(lenRepo + 12, lenBranch + 8, lenMain + 6, lenDb + 10)
    p = f"    **   Repository: {repo}" + "   " + " " * (l - lenRepo - 12) + "**"
    b = f"    **   Branch: {taskBranch}" + "   " + " " * (l - lenBranch - 8) + "**"
    m = f"    **   Main: {gMainBranch}" + "   " + " " * (l - lenMain - 6) + "**"
    d = f"    **   Database: {gDatabase}" + "   " + " " * (l - lenDb - 10) + "**"
    s = "    " + "*" * (len(b) - 4)
    print_("\n" + s)
    print_(p)
    print_(b)
    print_(m)
    print_(d)
    print_(s + "\n")


def main(repo, optionOne=None, optionTwo=None):
    repoPath = os.path.join(gLocalReposDir, repo)
    exitcode, out, err = run_command(["git", "symbolic-ref", "--short", "HEAD"])
    taskBranch = out.strip()
    header_footer(repo, taskBranch)
    exitcode, out, err = run_command(["git", "status"])
    print_(out)

    lines = out.splitlines()
    pattern = re.compile(r"database\/(\w+)\/\S+\.sql$")
    databaseItems = {}
    for line in lines:
        match = pattern.search(line)
        if match:
            schema = match.group(1)
            if schema not in databaseItems:
                databaseItems[schema] = []
            databaseItems[schema].append(match.group(0))

    if optionOne is not None:
        optionInt = optionOne
    else:
        options = [
            "Commit...",              # 0
            "Checkout...",            # 1
            "Pull / Push / Fetch...", # 2
            "Migration Steps...",     # 3
            "Merge...",               # 4
            "New Branch",             # 5
            "Open in BitBucket",      # 6
            "Remote Gone",            # 7
            "Repository List",        # 8
            "Exit (Press Enter)",     # 9
        ]
        optionInt = getResponse(options)

    if optionInt == 0:
        remote = trackingRemote(taskBranch, 2)
        if optionTwo is not None:
            optionInt = optionTwo
        else:
            options = [
                f"Commit Tracked, Push",  # 0
                f"Commit Staged, Push",   # 1
                f"Add All, Commit, Push", # 2
                "Commit Staged",          # 3
                "Main Menu",              # 4
                "Exit",                   # 5
            ]
            optionInt = getResponse(options, 2)
        if optionInt == 0:
            if git_cmd["commitAll"]():
                if remote == "R":
                    git_cmd["push"]()
                elif remote == "N":
                    git_cmd["push"](["--set-upstream", "origin", taskBranch])    
                afterPush(repo, taskBranch, databaseItems)
        elif optionInt == 2:
            git_cmd["addAll"]()
        if optionInt in (1, 2):
            if git_cmd["commit"]():
                if remote == "R":
                    git_cmd["push"]()
                elif remote == "N":
                    git_cmd["push"](["--set-upstream", "origin", taskBranch])    
                afterPush(repo, taskBranch, databaseItems)
        elif optionInt == 3:
            if git_cmd["commit"]():
                pushOption(repo, taskBranch)
        elif optionInt == 4:
            main(repo)
        elif optionInt == 5:
            pass
    elif optionInt == 1:
        options = [
            "Checkout local...",            # 0
            "Checkout remote...",           # 1
            f"Checkout {gSelectedDevHead}", # 2
            f"Checkout {gMainBranch}",      # 3
            f"Checkout {gMainProdBranch}",  # 4
            "Main Menu",                    # 5
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
                    git_cmd["checkout"](branchesList[optionInt])
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
            git_cmd["fetch"](["--prune", "origin"])
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
                    if l.find(f"origin/{p}") == 0 and l[7:] not in branchesList:
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
            git_cmd["checkout"](gSelectedDevHead)
            main(repo)
        elif optionInt == 3:
            git_cmd["checkout"](gMainBranch)
            main(repo)
        elif optionInt == 4:
            git_cmd["checkout"](gMainProdBranch)
            main(repo)
        elif optionInt == 5:
            main(repo)
    elif optionInt == 2:
        remote = trackingRemote(taskBranch, 2)
        options = [
            f"Fetch, Prune & Pull (must be on {gMainBranch})", # 0
            "Fetch & Prune Origin",                            # 1
            "Pull",                                            # 2
            f"Pull {gSelectedDevHead}",                        # 3
            f"Pull {gSelectedDevHead} & {gMainBranch}",        # 4
            "Push",                                            # 5
            "Main Menu",                                       # 6
            "Exit",                                            # 7
        ]
        optionInt = getResponse(options, 2)
        if optionInt == 0:
            if taskBranch not in (gMainBranch, gMainProdBranch):
                print_(
                    f"You must start from branch: {gMainBranch} or {gMainProdBranch}"
                )
                return
            git_cmd["fetch"](["--prune", "origin"])
            git_cmd["pull"]()
            main(repo)
        elif optionInt == 1:
            git_cmd["fetch"](["--prune", "origin"])
            main(repo)
        elif optionInt == 2:
            git_cmd["pull"]()
            main(repo)
        elif optionInt in (3, 303):
            checkout_devhead_pull(taskBranch, optionInt)
            main(repo)
        elif optionInt in (4, 404):
            checkout_devhead_pull(taskBranch, optionInt, True)
            main(repo)
        elif optionInt == 5:
            if remote == "R":
                git_cmd["push"]()
            elif remote == "N":
                git_cmd["push"](["--set-upstream", "origin", taskBranch])    
            main(repo)
        elif optionInt == 6:
            main(repo)
        elif optionInt == 7:
            pass

    elif optionInt == 3:
        migration = f"({gSelectedMigration})"
        print_indented("-" * len(migration), 2)
        print_indented(migration, 2)
        if optionTwo is not None:
            optionInt = optionTwo
        else:
            options = [
                "Steps File - Copy & Commit", # 0
                "Steps File - Commit Only",   # 1
                "Main Menu",                  # 2
                "Exit",                       # 3
            ]
            optionInt = getResponse(options, 2)
        if optionInt == 20 and taskBranch != gMainBranch:
            print_(f"You must start from branch: {gMainBranch}")
            return
        if optionInt in (0, 1, 20):
            if taskBranch.find(gStepsPrefix) == 0:
                currentIssue = taskBranch[taskBranch.rfind("/") + 1 :]
                issue = input(f"\n   Issue/Task (0 for {currentIssue}): {gStepsPrefix}/")
                if not issue:
                    return
                if issue == "0":
                    stepsBranch = taskBranch
                    issue = currentIssue
                else:
                    stepsBranch = f"{gStepsPrefix}/{issue}"
            else:
                issue = input(f" Issue/Task: {gStepsPrefix}/")
                if not issue:
                    return
                stepsBranch = f"{gStepsPrefix}/{issue}"
        if optionInt == 0:
            if not os.path.exists(gStepsPath):
                raise Exception(" Steps not found.")
            c = f'xcopy "{gStepsPath}" "{repoPath}\\migration\\{gSelectedMigration}\\{issue}" /f /i /k'
            os.system(c)
            x = input(" Modify file as needed. Press 0 to continue...")
            if x in ("0", "00", "10"):
                commitSteps(repo, taskBranch, stepsBranch, gSelectedMigration, issue, x)
        elif optionInt == 1:
            commitSteps(repo, taskBranch, stepsBranch, gSelectedMigration, issue)
        elif optionInt == 2:
            main(repo)
        elif optionInt == 3:
            pass
    elif optionInt == 4:
        options = [
            f"Merge in {gMainBranch}",           # 0
            f"Merge into {gSelectedDevHead}...", # 1
            "Main Menu",                         # 2
        ]
        optionInt = getResponse(options, 2)
        if optionInt == 0:
            if taskBranch == gMainBranch:
                raise Exception(
                    f"You cannot run this from {gMainBranch}."
                    " Checkout your task branch first!"
                )
            git_cmd["checkout"](gMainBranch)
            git_cmd["pull"]()
            git_cmd["checkout"](taskBranch)
            git_cmd["merge"](gMainBranch)
            pushOption(repo, taskBranch)
        elif optionInt == 1:
            merge_into_devhead(repo, taskBranch, databaseItems)
        elif optionInt == 2:
            main(repo)
    elif optionInt == 5:
        if taskBranch != gMainBranch:
            git_cmd["checkout"](gMainBranch)
        git_cmd["pull"]()
        newBranch = input(" New Branch: ")
        git_cmd["checkout"](["-b", newBranch])
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
    # hidden options
    elif optionInt == 100:
        checkout_fetch_pull(taskBranch)
        main(repo)
    elif optionInt == 105:
        checkout_fetch_pull(taskBranch)
        newBranch = input(" New Branch: ")
        git_cmd["checkout"](["-b", newBranch])
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
    global gDatabase
    optionOne = None
    optionTwo = None
    with os.scandir(gLocalReposDir) as mydir:
        dirs = sorted(
            list(set([i.name for i in mydir if i.is_dir()]) - set(gExcludeReposList))
        )
    if gDefaultRepo and useDefault and gDefaultRepo in dirs:
        repo = gRepo = gDefaultRepo
    else:
        optionInt = getResponse(dirs, 1, " Choose Repository: ")
        if optionInt == 200:
            if gShortcutRepo and gShortcutRepo in dirs:
                repo = gShortcutRepo
                gRepo = repo
                optionOne = 0
                optionTwo = 0
            else:
                print_(f"Repo {gShortcutRepo} not found.")
                return
        elif optionInt == 300:
            if gShortcutRepoMigration and gShortcutRepoMigration in dirs:
                repo = gShortcutRepoMigration
                gRepo = repo
                optionOne = 3
                optionTwo = 0
            else:
                print_(f"Repo {gShortcutRepoMigration} not found.")
                return
        elif optionInt == 1000:
            return
        else:
            try:
                repo = dirs[optionInt]
            except:
                raise Exception(" Invalid Selection.")
            gRepo = f"{repo} ({optionInt})"
    repoPath = os.path.join(gLocalReposDir, repo)
    os.chdir(repoPath)

    gDatabase = get_key(gDatabases, repo)
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

    main(repo, optionOne, optionTwo)


# load global settings from config file
fileName = "git-123.json"
path = os.path.join(os.getcwd(), fileName)
if not os.path.exists(fileName):
    print_("Could not find config file named git-123.json in same folder.")

with open(path, "r") as json_config_file:
    configData = json.load(json_config_file)

gBitBucketOrg = configData["bitBucketOrg"]
gDatabases = configData["databases"]
gDatabase = ""
gLocalReposDir = configData["localReposDir"]
gDefaultRepo = configData["defaultRepo"]
gShortcutRepo = configData["shortcutRepo"]
gShortcutRepoMigration = configData["shortcutRepoMigration"]
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
gMessageHistory = configData["messageHistory"]
gOutputToFile = configData["outputToFile"]
gBranchPrefixes = configData["branchPrefixes"]
gStepsPath = os.path.join(os.getcwd(), "Steps")
gStepsPrefix = configData["stepsPrefix"]
gMessageFile = None
gOutputFile = None
gMessages = []
gMsgLinesStart = 0
gMsgLinesEnd = 0
gRepo = ""

git_cmd = git_commands(
    ["git", "add", "--all"],
    ["git", "add"],
    ["git", "commit", "-a", "-m"],
    ["git", "commit", "-m"],
    ["git", "checkout"],
    ["git", "fetch"],
    ["git", "merge"],
    ["git", "pull"],
    ["git", "push"],
)

if gOutputToFile:
    gOutputFile = open("git-123.log", "a")

fileName = "git-123.txt"
path = os.path.join(os.getcwd(), fileName)

if gMessageHistory and os.path.exists(fileName):
    with open(path, "r") as m:
        gMessages = m.readlines()
        gMsgLinesStart = len(gMessages)

print_("\n" * 3 + "_" * 24)
print_(datetime.now().strftime("%a, %b %d: %I:%M:%S %p"))
print_("\nBegin.\n" + "_" * 24 + "\n" * 3)
selectRepo()

print_(datetime.now().strftime("%a, %b %d: %I:%M:%S %p"))
print_("\nDone.\n")

if gMessageHistory:
    gMsgLinesEnd = len(gMessages)
    if gMsgLinesEnd > gMsgLinesStart:
        gMessageFile = open(path, "w")
        for number, line in enumerate(gMessages):
            if gMsgLinesEnd < 9 or number > gMsgLinesEnd - 10:
                gMessageFile.write(line)
        gMessageFile.close()

try:
    exitcode, out, err = run_command(["git", "symbolic-ref", "--short", "HEAD"])
    taskBranch = out.strip()
    if gRepo:
        header_footer(gRepo, taskBranch)
except:
    pass

if gOutputToFile:
    gOutputFile.close()
