import os

from twisted.application import service
from buildbot.master import BuildMaster

basedir = '.'

rotateLength = 10000000
maxRotatedFiles = 10
configfile = 'master.cfg'

# Default umask for server
umask = None

# if this is a relocatable tac file, get the directory containing the TAC
if basedir == '.':
    import os.path
    basedir = os.path.abspath(os.path.dirname(__file__))

# note: this line is matched against to check that this is a buildmaster
# directory; do not edit it.
application = service.Application('buildmaster')
from twisted.python.logfile import LogFile
from twisted.python.log import ILogObserver, FileLogObserver
logfile = LogFile.fromFullPath(os.path.join(basedir, "twistd.log"), rotateLength=rotateLength,
                                maxRotatedFiles=maxRotatedFiles)
application.setComponent(ILogObserver, FileLogObserver(logfile).emit)

m = BuildMaster(basedir, configfile, umask)
m.setServiceParent(application)
m.log_rotation.rotateLength = rotateLength
m.log_rotation.maxRotatedFiles = maxRotatedFiles

from twisted.application import internet
from twisted.web import server
from github_buildbot_service import GitHubBuildBot
import secrets
gh = GitHubBuildBot()
gh.github = 'github.com'
gh.master = 'localhost:9989'
gh.secret = secrets.gh_secret
gh.auth = secrets.pbcs_user + ':' + secrets.pbcs_pass

ghservice = internet.TCPServer(55081, server.Site(gh))
ghservice.setServiceParent(application)
