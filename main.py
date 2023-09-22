import jenkins
import yaml
from enum import Enum
from os import system
from time import sleep
import winsound
from datetime import datetime

global tag1 = ''
global tag2 = '' 

class bcolours:
    end = '\033[0m'
    red = "\u001b[31m"
    green = "\u001b[32m"
    yellow = "\u001b[33m"
    blue = "\u001b[34m"

class Status(Enum):
    ABORTED = "ABORTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    PROGRES = "PROGRES"

    @staticmethod
    def from_str(label: str):
        if label is None:
            return Status.PROGRES
        else:
            return Status[label]
    
    @staticmethod
    def with_colour(s) -> str:
        if s == Status.FAILURE:
            return bcolours.red + s.name + bcolours.end
        elif s == Status.SUCCESS:
            return bcolours.green + s.name + bcolours.end
        elif s == Status.PROGRES:
            return bcolours.blue + s.name + bcolours.end
        elif s == Status.ABORTED:
            return bcolours.yellow + s.name + bcolours.end
        else:
            raise NotImplementedError

class JBuild:
    def __init__(self, build_info, job: str):
        actions = build_info["actions"][0]["parameters"]
        self.owner = ""
        self.branch = ""
        for param in actions:
            if len(self.owner) > 0 and len(self.branch) > 0:
                break
            if param["name"] == tag1:
                self.owner = param["value"]
            if param["name"] == tag2:
                self.branch = param["value"]
        self.building = build_info["building"]
        self.buildno = build_info["number"]
        self.result = Status.from_str(build_info["result"])
        self.url = build_info["url"]
        self.timestamp = int(build_info["timestamp"])
        self.duration = int(build_info["duration"])
        if self.duration == 0:  #if the job is in progress, duration will be 0;
            self.duration = datetime.now().timestamp()*1000 - self.timestamp
        self.job = job
    
    def __eq__(self, other): 
        if not isinstance(other, JBuild):
            return NotImplemented
        return self.job == other.job and self.buildno ==  other.buildno and self.result == other.result
    
    def __hash__(self):
        return hash((self.job, self.buildno, self.result))
    
    @staticmethod
    def filler(s: str, n: int) -> str:
        r = n - len(s)
        if r >= 0:
            return s + ' '*r
        else:
            return s[:r]
    
    def toString(self):
        seconds=int((self.duration/1000)%60)
        minutes=int((self.duration/(1000*60)))
        ts = datetime.fromtimestamp(self.timestamp/1000).strftime('%m-%d %H:%M:%S')
        return "{0} | {1} | {2} | {3} | {4} | {5}".format(
            self.filler(str(self.buildno), 5), 
            Status.with_colour(self.result), 
            self.filler(self.branch, 11), 
            self.filler(self.job, 23),
            self.filler("{0}m{1}s".format(minutes, seconds), 8),
            ts)

def test(server):
    user = server.get_whoami()
    version = server.get_version()
    print("\nHello {0} from Jenkins {1}! ".format(user['fullName'], version))

def parse(server, job) -> list:
    output = list()
    build_list = server.get_job_info(job)["builds"]
    buildno_list = [item["number"] for item in build_list][:10]
    for buildno in buildno_list:
        build_info = server.get_build_info(job, buildno)
        try:
            b = JBuild(build_info, job)
            output.append(b)
        except KeyError:
            pass
    return output

def run(server, owner):
    prevbuilds = set()
    while(True):
        nestedbuilds = [[b for b in parse(server, job) if b.owner == owner] for job in config["jobs"]]
        mybuilds = [job for joblist in nestedbuilds for job in joblist]
        mybuilds.sort(key=lambda x: x.timestamp, reverse=True)
        if not all(build in prevbuilds for build in mybuilds):
            winsound.Beep(1000, 1000)
        prevbuilds = set(mybuilds)
        _ = system("clear")
        header =  "Jenkins Notifier\n"
        header += "Last refresh: {0}\n".format(datetime.now().strftime("%H:%M:%S"))
        header += "BUILD   STATUS    BRANCH        JOB                       DURATION   TIMESTAMP\n"
        header += "-----------------------------------------------------------------------------------"
        print(header)
        for b in mybuilds:
            print(b.toString())
        if len(mybuilds) == 0:
            print("No builds found!")
        sleep(120)

with open("config.yaml", "r", encoding="utf-8") as c:
    config = yaml.safe_load(c)
    server = jenkins.Jenkins(config["server"], username=config["username"], password=config["password"])
    test(server)
    print("Loading...")
    run(server, config["username"])



