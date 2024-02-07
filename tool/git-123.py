import json
import os
import re
import subprocess
import webbrowser
from datetime import datetime


class RunCommandException(Exception):
    """Exception raised by RunCommand when exitcode is non-zero.

    Attributes:
        exitcode -- code returned by the process
        out -- stdout returned by the process
        err -- stderr returned by the process
    """

    def __init__(self, exitcode, out, err):
        self.exitcode = exitcode
        self.out = out
        self.err = err


def RunSqlCommand(sqlCommand, connectString):
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


def SqlCommand(filePaths, schema, db):
    file_paths_str = " ".join(filePaths)
    sqlCommandStr = f"set define off;\r\nset serveroutput on;\r\n@{file_paths_str};\r\nshow errors;\r\nexit;"
    sqlCommand = sqlCommandStr.encode()
    connectString = f"{schema}/{db}@{db}"
    print(f"Running {file_paths_str} as {connectString}")
    exitCode, queryResult, errorMessage = RunSqlCommand(sqlCommand, connectString)
    print(queryResult)


def RunCommand(arr, input=None):
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


def Print_(text=None):
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


def PrintIndented(text, level=1):
    indentation = ""
    for i in range(0, level):
        indentation += "    "

    lines = text.split("\n")

    for line in lines:
        if line:
            Print_(indentation + line)


def GetResponse(options, level=1, message="    >>> ", returnInt=True):
    m = len(max(options, key=len))
    s = "-" * 16 + "-" * m
    PrintIndented("\n" + s, level)
    for x in range(len(options)):
        l = len(options[x])
        p = "-" * (m - l + 3)
        if x > 9:
            p = "-" * (m - l + 1)
        PrintIndented(f"-> {str(x)} - {options[x]} {p} {str(x)} <-", level)
    PrintIndented(s + "\n", level)
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
        Print_(f" Selected: {option}")
    if returnInt:
        return optionInt
    else:
        return optionInt, option


def SelectMessage():
    global gMessages
    commitMessage = None
    numLines = len(gMessages)
    newMessage = False
    if numLines > 0:
        msgReversed = []
        msgReversed.append("-- [ New Message ]")
        for m in reversed(gMessages):
            msgReversed.append(m.strip("\n"))
        r, commitMessage = GetResponse(msgReversed, 0, ">>> ", False)
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


def GitCommands(
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
        Print_("Add all")
        command = gitAddAll[:]
        exitcode, out, err = RunCommand(command)
        Print_(out)

    def add(arg):
        Print_(f"Add {arg}")
        command = gitAdd[:]
        command.append(arg)
        exitcode, out, err = RunCommand(command)
        Print_(out)

    def checkout(branch):
        Print_(f"Checkout {branch}")
        branchType = type(branch)
        command = gitCheckout[:]
        if branchType is str:
            command.append(branch)
        elif branchType is list:
            command += branch
        exitcode, out, err = RunCommand(command)
        Print_(out)

    def commitAll(arg=None):
        commitMessage = arg or SelectMessage()
        if not commitMessage:
            return False
        command = gitCommitAll[:]
        command.append(commitMessage)
        exitcode, out, err = RunCommand(command)
        Print_(out)
        return True


    def commit(arg=None):
        commitMessage = arg or SelectMessage()
        if not commitMessage:
            return False
        command = gitCommit[:]
        command.append(commitMessage)
        exitcode, out, err = RunCommand(command)
        Print_(out)
        return True

    def fetch(arg=None):
        Print_("Fetch...")
        command = gitFetch[:] + arg if arg else gitFetch
        exitcode, out, err = RunCommand(command)
        Print_(out)

    def merge(arg):
        Print_(f"Merge {arg}")
        command = gitMerge[:]
        command.append(arg)
        exitcode, out, err = RunCommand(command)
        Print_(out)

    def pull(arg=None):
        Print_("Pull...")
        command = gitPull[:] + arg if arg else gitPull
        exitcode, out, err = RunCommand(command)
        Print_(out)

    def push(arg=None):
        m = "Push to New..." if arg else "Push..."
        command = gitPush[:] + arg if arg else gitPush
        Print_(m)
        exitcode, out, err = RunCommand(command)
        Print_(out)

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


def CheckoutFetchPull(taskBranch):
    if taskBranch != gMainBranch:
        gitCmd["checkout"](gMainBranch)
    gitCmd["fetch"](["--prune", "origin"])
    gitCmd["pull"]()


def CheckoutDevheadPull(taskBranch, option=0, mainBranch=False):
    if taskBranch != gSelectedDevHead:
        gitCmd["checkout"](gSelectedDevHead)
    gitCmd["pull"]()
    gitCmd["checkout"](gMainBranch)
    if mainBranch:
        gitCmd["pull"]()
    if option > 100:
        gitCmd["checkout"](taskBranch)


def GetKey(d, value):
    for k, v in d.items():
        for r in v:
            if r == value:
                return k
    return f"No DB set for {value}"


def Compile(repo, databaseItems):
    if not databaseItems:
        PrintIndented("**   No items to compile")
        return
    for schema, dbFiles in databaseItems.items():
        print(schema)
        for d in dbFiles:
            print(d)
    Print_()
    options = [
        "Compile All",          # 0
        "Compile Individually", # 1
        "Return",               # 2
    ]
    optionInt = GetResponse(options, 2)
    if optionInt == 0:
        for schema, dbFiles in databaseItems.items():
            SqlCommand(dbFiles, schema, gDatabase)
    elif optionInt == 1:
        for schema, dbFiles in databaseItems.items():
            for filePath in dbFiles:
                options = [
                    f"Compile {filePath}", # 0
                    "Skip",                # 1
                ]
                optionInt = GetResponse(options, 3)
                if optionInt == 0:
                    SqlCommand([filePath], schema, gDatabase)
                elif optionInt == 1:
                    pass
    elif optionInt == 2:
        pass


def MergeIntoDevhead(repo, taskBranch, databaseItems=None):
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
    optionInt = GetResponse(options)
    if optionInt < 2:
        try:
            gitCmd["checkout"](gSelectedDevHead)
        except:
            print(f"\n  ** Error checking out {gSelectedDevHead} **\n")
            return

    if optionInt == 0:
        gitCmd["merge"](taskBranch)
    elif optionInt == 1:
        gitCmd["pull"]()
        gitCmd["merge"](taskBranch)
    elif optionInt == 2:
        return

    options = [
        f"Push {gSelectedDevHead}", # 0
        f"Back to {taskBranch}",    # 1
        "Abort Merge",              # 2
        "Exit",                     # 3
    ]
    optionInt = GetResponse(options)

    if optionInt == 0:
        gitCmd["push"]()
        num_values = str(len(databaseItems.values()))

        options = [
            f"Back to {taskBranch}",   # 0
            f"Compile ({num_values})", # 1
            "Exit",                    # 2
        ]
        optionInt = GetResponse(options)

        if optionInt == 0:
            gitCmd["checkout"](taskBranch)
            options = [
                "Open in BitBucket", # 0
                "Exit",              # 1
            ]
            optionInt = GetResponse(options)

            if optionInt == 0:
                url = "https://bitbucket.org/{}/{}/branch/{}".format(
                    gBitBucketOrg, repo, taskBranch
                )
                Print_("Opening Branch...")
                webbrowser.open(url)
            elif optionInt == 1:
                return
        elif optionInt == 1:
            Compile(repo, databaseItems)
            options = [
                f"Back to {taskBranch}", # 0
                "Exit",                  # 1
            ]
            optionInt = GetResponse(options)

            if optionInt == 0:
                gitCmd["checkout"](taskBranch)
                options = [
                    "Open in BitBucket", # 0
                    "Exit",              # 1
                ]
                optionInt = GetResponse(options)

                if optionInt == 0:
                    url = "https://bitbucket.org/{}/{}/branch/{}".format(
                        gBitBucketOrg, repo, taskBranch
                    )
                    Print_("Opening Branch...")
                    webbrowser.open(url)
                elif optionInt == 1:
                    return
            elif optionInt == 1:
                return
        elif optionInt == 2:
            return
    elif optionInt == 1:
        gitCmd["checkout"](taskBranch)
    elif optionInt == 2:
        gitCmd["merge"]("--abort")
    elif optionInt == 3:
        pass


def AfterPush(repo, taskBranch, databaseItems=None):
    if taskBranch != gSelectedDevHead:
        options = [
            f"Merge into {gSelectedDevHead}", # 0
            "Open in BitBucket",              # 1
            "Main Menu",                      # 2
            "Exit",                           # 3
        ]
        optionInt = GetResponse(options)

        if optionInt == 0:
            MergeIntoDevhead(repo, taskBranch, databaseItems)
        elif optionInt == 1:
            url = "https://bitbucket.org/{}/{}/branch/{}".format(
                gBitBucketOrg, repo, taskBranch
            )
            Print_("Opening Branch...")
            webbrowser.open(url)
        elif optionInt == 2:
            Main(repo)
        elif optionInt == 3:
            pass

def TrackingRemote(taskBranch, indent=0):
    exitcode, out, err = RunCommand(["git", "branch", "-vv"])
    lines = out.splitlines()
    remoteBranch = f"[origin/{taskBranch}"
    remoteBranches = [
        line.split(None, 2)[2]
        for line in lines
        if f"{remoteBranch}]" in line or f"{remoteBranch}:" in line
    ]
    Print_()
    for branch in remoteBranches:
        msg = f"Remote: {branch}"
    if not remoteBranches:
        msg = "No remote."
    PrintIndented("-" * len(msg), indent)
    PrintIndented(msg, indent)
    return msg[:1]


def PushOption(repo, taskBranch):
    remote = TrackingRemote(taskBranch, 1)
    options = [
        "Push",      # 0
        "Main Menu", # 1
        "Exit",      # 2
    ]
    optionInt = GetResponse(options)
    if optionInt == 0:
        PushToRemote(remote, taskBranch)
        AfterPush(repo, taskBranch)
    elif optionInt == 1:
        Main(repo)
    elif optionInt == 2:
        pass


def PushToRemote(remote, taskBranch):
    if remote == "R":
        gitCmd["push"]()
    elif remote == "N":
        gitCmd["push"](["--set-upstream", "origin", taskBranch])    


def GetLocalBranches():
    exitcode, out, err = RunCommand(["git", "branch"])
    lines = out.splitlines()
    localLines = [l.strip() for l in lines]
    branchesList = []
    for p in gBranchPrefixes:
        for l in localLines:
            if l.find(p) == 0:
                branchesList.append(l)
    return branchesList


def CommitSteps(repo, taskBranch, stepsBranch, migration, issue, x="0"):
    # - "0":
    #   - Performs a pull on the main branch.
    #   - Displays push options.
    # - "10", "00":
    #   - "10": Performs a pull on the main branch.
    #   - Pushes to remote branch.
    #   - Opens the branch in Bitbucket.
    if taskBranch != stepsBranch:
        branchesList = GetLocalBranches()
        if stepsBranch in branchesList:
            gitCmd["checkout"](stepsBranch)
        elif taskBranch != gMainBranch:
            gitCmd["checkout"](gMainBranch)
            taskBranch = gMainBranch
        if taskBranch == gMainBranch:
            if x in ("0", "10"):
                gitCmd["pull"]()
            gitCmd["checkout"](["-b", stepsBranch])
    addFile = f"migration\\{migration}\\{issue}\\step_0.info"
    gitCmd["add"](addFile)
    gitCmd["commit"]("Add migration steps")
    if x == "0":
        PushOption(repo, stepsBranch)
    elif x in ("00", "10"):
        remote = TrackingRemote(stepsBranch)
        PushToRemote(remote, stepsBranch)
        url = "https://bitbucket.org/{}/{}/branch/{}".format(
            gBitBucketOrg, repo, stepsBranch
        )
        Print_("Opening Branch...")
        webbrowser.open(url)


def RemoteGone(taskBranch):
    if taskBranch != gMainBranch:
        options = [
            f"Checkout {gMainBranch}", # 0
            "Exit",                    # 1
        ]
        optionInt = GetResponse(options)
        if optionInt == 0:
            CheckoutFetchPull(taskBranch)
        elif optionInt == 1:
            return
    exitcode, out, err = RunCommand(["git", "branch", "-vv"])
    lines = out.splitlines()
    goneBranches = [line.split(None, 1)[0] for line in lines if ": gone]" in line]
    PrintIndented("**   Branches that no longer exist on Remote:")
    Print_()
    for branch in goneBranches:
        PrintIndented(branch)
    if not goneBranches:
        PrintIndented("**   No branches to delete")
        return
    Print_()
    options = [
        "Delete All",          # 0
        "Delete Individually", # 1
        "Exit",                # 2
    ]
    optionInt = GetResponse(options)
    if optionInt == 0:
        for b in goneBranches:
            exitcode, out, err = RunCommand(["git", "branch", "-D", b])
            Print_(out)
    elif optionInt == 1:
        for b in goneBranches:
            options = [
                f"Delete {b}", # 0
                "Skip",        # 1
            ]
            optionInt = GetResponse(options)
            if optionInt == 0:
                exitcode, out, err = RunCommand(["git", "branch", "-D", b])
                Print_(out)
            elif optionInt == 1:
                pass
    elif optionInt == 2:
        pass


def HeaderFooter(repo, taskBranch):
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
    Print_("\n" + s)
    Print_(p)
    Print_(b)
    Print_(m)
    Print_(d)
    Print_(s + "\n")


def Main(repo, optionOne=None, optionTwo=None):
    repoPath = os.path.join(gLocalReposDir, repo)
    exitcode, out, err = RunCommand(["git", "symbolic-ref", "--short", "HEAD"])
    taskBranch = out.strip()
    HeaderFooter(repo, taskBranch)
    exitcode, out, err = RunCommand(["git", "status"])
    Print_(out)

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
        optionInt = GetResponse(options)

    if optionInt == 0:
        remote = TrackingRemote(taskBranch, 2)
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
            optionInt = GetResponse(options, 2)
        if optionInt == 0:
            if gitCmd["commitAll"]():
                PushToRemote(remote, taskBranch)
                AfterPush(repo, taskBranch, databaseItems)
        elif optionInt == 2:
            gitCmd["addAll"]()
        if optionInt in (1, 2):
            if gitCmd["commit"]():
                PushToRemote(remote, taskBranch)
                AfterPush(repo, taskBranch, databaseItems)
        elif optionInt == 3:
            if gitCmd["commit"]():
                PushOption(repo, taskBranch)
        elif optionInt == 4:
            Main(repo)
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
        optionInt = GetResponse(options, 2)
        if optionInt in (0, 1):
            branchesList = GetLocalBranches()
        if optionInt == 0:
            if len(branchesList) > 0:
                optionInt = GetResponse(branchesList, 3)
                if optionInt == 1000:
                    return
                try:
                    gitCmd["checkout"](branchesList[optionInt])
                except:
                    raise Exception(" Invalid Selection.")
            else:
                Print_("\n")
                PrintIndented(
                    "** No prefixed branches available to checkout. **\n", level=3
                )
                Print_("\n")
            Main(repo)
        elif optionInt == 1:
            gitCmd["fetch"](["--prune", "origin"])
            exitcode, out, err = RunCommand(["git", "branch", "-r"])
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
                optionInt = GetResponse(RemoteBranchesList, 3)
                if optionInt == 1000:
                    return
                try:
                    exitcode, out, err = RunCommand(
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
                Print_("\n")
                PrintIndented(
                    "** No prefixed branches available to checkout. **\n", level=3
                )
                Print_("\n")
            Main(repo)
        elif optionInt == 2:
            gitCmd["checkout"](gSelectedDevHead)
            Main(repo)
        elif optionInt == 3:
            gitCmd["checkout"](gMainBranch)
            Main(repo)
        elif optionInt == 4:
            gitCmd["checkout"](gMainProdBranch)
            Main(repo)
        elif optionInt == 5:
            Main(repo)
    elif optionInt == 2:
        remote = TrackingRemote(taskBranch, 2)
        options = [
            f"Fetch, Prune & Pull (must be on {gMainBranch})", # 0
            "Fetch & Prune Origin",                            # 1
            "Pull",                                            # 2
            f"Pull {gSelectedDevHead}",                        # 3
            f"Pull {gSelectedDevHead} & {gMainBranch}",        # 4
            f"Pull {gMainBranch}",                             # 5
            "Push",                                            # 6
            "Main Menu",                                       # 7
            "Exit",                                            # 8
        ]
        optionInt = GetResponse(options, 2)
        if optionInt == 0:
            if taskBranch not in (gMainBranch, gMainProdBranch):
                Print_(
                    f"You must start from branch: {gMainBranch} or {gMainProdBranch}"
                )
                return
            gitCmd["fetch"](["--prune", "origin"])
            gitCmd["pull"]()
            Main(repo)
        elif optionInt == 1:
            gitCmd["fetch"](["--prune", "origin"])
            Main(repo)
        elif optionInt == 2:
            gitCmd["pull"]()
            Main(repo)
        elif optionInt in (3, 303):
            CheckoutDevheadPull(taskBranch, optionInt)
            Main(repo)
        elif optionInt in (4, 404):
            CheckoutDevheadPull(taskBranch, optionInt, True)
            Main(repo)
        elif optionInt in (5, 505):
            if taskBranch != gMainBranch:
                gitCmd["checkout"](gMainBranch)
            gitCmd["pull"]()
            if optionInt > 100:
                gitCmd["checkout"](taskBranch)
            Main(repo)
        elif optionInt == 6:
            PushToRemote(remote, taskBranch)
            Main(repo)
        elif optionInt == 7:
            Main(repo)
        elif optionInt == 8:
            pass

    elif optionInt == 3:
        migration = f"({gSelectedMigration})"
        PrintIndented("-" * len(migration), 2)
        PrintIndented(migration, 2)
        if optionTwo is not None:
            optionInt = optionTwo
        else:
            options = [
                "Steps File - Copy & Commit", # 0
                "Steps File - Commit Only",   # 1
                "Main Menu",                  # 2
                "Exit",                       # 3
            ]
            optionInt = GetResponse(options, 2)
        if optionInt == 20 and taskBranch != gMainBranch:
            Print_(f"You must start from branch: {gMainBranch}")
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
            x = input(" Modify file as needed. Press 0 [10,00] to continue...")
            if x in ("0", "00", "10"):
                CommitSteps(repo, taskBranch, stepsBranch, gSelectedMigration, issue, x)
        elif optionInt == 1:
            CommitSteps(repo, taskBranch, stepsBranch, gSelectedMigration, issue)
        elif optionInt == 2:
            Main(repo)
        elif optionInt == 3:
            pass
    elif optionInt == 4:
        options = [
            f"Merge in {gMainBranch}",           # 0
            f"Merge into {gSelectedDevHead}...", # 1
            "Main Menu",                         # 2
        ]
        optionInt = GetResponse(options, 2)
        if optionInt == 0:
            if taskBranch == gMainBranch:
                raise Exception(
                    f"You cannot run this from {gMainBranch}."
                    " Checkout your task branch first!"
                )
            gitCmd["checkout"](gMainBranch)
            gitCmd["pull"]()
            gitCmd["checkout"](taskBranch)
            gitCmd["merge"](gMainBranch)
            PushOption(repo, taskBranch)
        elif optionInt == 1:
            MergeIntoDevhead(repo, taskBranch, databaseItems)
        elif optionInt == 2:
            Main(repo)
    elif optionInt == 5:
        if taskBranch != gMainBranch:
            gitCmd["checkout"](gMainBranch)
        gitCmd["pull"]()
        newBranch = input(" New Branch: ")
        gitCmd["checkout"](["-b", newBranch])
        Main(repo)
    elif optionInt == 6:
        url = "https://bitbucket.org/{}/{}/branch/{}".format(
            gBitBucketOrg, repo, taskBranch
        )
        Print_("Opening Branch...")
        webbrowser.open(url)
    elif optionInt == 7:
        RemoteGone(taskBranch)
        Main(repo)
    elif optionInt == 8:
        SelectRepo(False)
    elif optionInt == 9:
        pass
    # hidden options
    elif optionInt == 100:
        CheckoutFetchPull(taskBranch)
        Main(repo)
    elif optionInt == 105:
        CheckoutFetchPull(taskBranch)
        newBranch = input(" New Branch: ")
        gitCmd["checkout"](["-b", newBranch])
        Main(repo)
    elif optionInt == 107:
        CheckoutFetchPull(taskBranch)
        RemoteGone(gMainBranch)
        Main(repo)


def SelectRepo(useDefault=True):
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
        optionInt = GetResponse(dirs, 1, " Choose Repository: ")
        if optionInt == 200:
            if gShortcutRepo and gShortcutRepo in dirs:
                repo = gShortcutRepo
                gRepo = repo
                optionOne = 0
                optionTwo = 0
            else:
                Print_(f"Repo {gShortcutRepo} not found.")
                return
        elif optionInt == 300:
            if gShortcutRepoMigration and gShortcutRepoMigration in dirs:
                repo = gShortcutRepoMigration
                gRepo = repo
                optionOne = 3
                optionTwo = 0
            else:
                Print_(f"Repo {gShortcutRepoMigration} not found.")
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

    gDatabase = GetKey(gDatabases, repo)
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

    Main(repo, optionOne, optionTwo)


# load global settings from config file
fileName = "git-123.json"
path = os.path.join(os.getcwd(), fileName)
if not os.path.exists(fileName):
    Print_("Could not find config file named git-123.json in same folder.")

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

gitCmd = GitCommands(
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

Print_("\n" * 3 + "_" * 24)
Print_(datetime.now().strftime("%a, %b %d: %I:%M:%S %p"))
Print_("\nBegin.\n" + "_" * 24 + "\n" * 3)
SelectRepo()

Print_(datetime.now().strftime("%a, %b %d: %I:%M:%S %p"))
Print_("\nDone.\n")

if gMessageHistory:
    gMsgLinesEnd = len(gMessages)
    if gMsgLinesEnd > gMsgLinesStart:
        gMessageFile = open(path, "w")
        for number, line in enumerate(gMessages):
            if gMsgLinesEnd < 9 or number > gMsgLinesEnd - 10:
                gMessageFile.write(line)
        gMessageFile.close()

try:
    exitcode, out, err = RunCommand(["git", "symbolic-ref", "--short", "HEAD"])
    taskBranch = out.strip()
    if gRepo:
        HeaderFooter(gRepo, taskBranch)
except:
    pass

if gOutputToFile:
    gOutputFile.close()
