#
# script to kill running mongodb sessions based on various conditions
#

import pymongo
from pymongo import ASCENDING, DESCENDING
from pymongo import Connection
from optparse import OptionParser


def getinprog(c):
    inprog=c.admin["$cmd.sys.inprog"].find_one({'$all': True})
    print inprog
    return inprog["inprog"]

def killsess(c,opid):
    print "I am killing %s" % opid
    thesession={}
    thesession["op"]=opid
    print thesession
    result=c.admin["$cmd.sys.killop"].find_one(thesession)
    print result

def killlongrunners(connection,inprog,threshold):
    for i in inprog:
          if i["secs_running"] > threshold and i["ns"] != "local.oplog.rs" :
              killsess(connection,i["opid"])
              
def killorphan(connection,inprog):
    for i in inprog:
        if i["client"] == "(NONE)":
            killsess(connection,i["opid"])

def killidle(connection,inprog):
    for i in inprog:
        if i["active"] == "false":
            killsess(connection,i["opid"])
            
def killblockers(connection,inprog,threshold):
    for i in inprog:
        if i["active"] == "true" and i["waitingForLock"] == "false" and i["secs_running"] > threshold:
            killsess(connection,i["opid"])
            
def killwaiters(connection,inprog,threshold):
    for i in inprog:
        if i["active"] == "true" and i["waitingForLock"] == "true" and i["secs_running"] > threshold:
            killsess(connection,i["opid"])
    
def main():
    parser = OptionParser()
    parser.set_defaults(host="localhost",port="27017",threshold=30)
    parser.add_option("--port",dest="port",type=int,help="host port to connect to")
    parser.add_option("--host",dest="host",help="host to connect to")
    parser.add_option("--blockers",action="store_true",dest="blockers")
    parser.add_option("--waiters",action="store_true",dest="waiters")
    parser.add_option("--idle",action="store_true",dest="idle")
    parser.add_option("--orphan",action="store_true",dest="orphan")
    parser.add_option("--longrunners",action="store_true",dest="longrunners")
    parser.add_option("-t","--threshold",dest="threshold")
    (options, args) = parser.parse_args()
   
    connection = Connection( options.host , options.port )
    inprog=getinprog(connection)

    if options.orphan:
        killorphan(connection,inprog)
    if options.idle:
        killidle(connection,inprog)
    if options.waiters:
        killwaiters(connection,inprog,threshold)
    if options.blockers:
        killblockers(connection,inprog,threshold)
    if options.longrunners:
        killlongrunners(connection,inprog,threshold)

if __name__ == "__main__":
    main()