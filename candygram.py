#
# script to kill running mongodb sessions based on various conditions
#

import pymongo
from pymongo import ASCENDING, DESCENDING
from pymongo import Connection
from optparse import OptionParser

def getinprog(c):
    inprog=c.admin["$cmd.sys.inprog"].find_one({'$all': True},  _is_command=True)
    return inprog["inprog"]

def killsess(c,opid):
    thesession={}
    if options.testmode:
        print "I am in testmode (--testmode), so I am not actually killing, but I would have killed opid %s" % opid
    else:
        if opid != 0:
            print "killing %s" % opid
            thesession["op"]=opid
            result=c.admin["$cmd.sys.killop"].find_one(thesession, _is_command=True)
            print result
        else:
            print "not killing opid %s" % opid
    
def killlongrunners(connection,inprog,t):
    for i in inprog:
        if "secs_running" in i:
            if i["secs_running"] > t and i["ns"] != "local.oplog.rs" :
                killsess(connection,i["opid"])
              
def killorphan(connection,inprog):
    for i in inprog:
        if i["client"] == "(NONE)":
            killsess(connection,i["opid"])

def killidle(connection,inprog):
    for i in inprog:
        if i["active"] == "false":
            killsess(connection,i["opid"])
            
def killblockers(connection,inprog,t):
    for i in inprog:
        if i["active"] == "true" and i["waitingForLock"] == "false" and i["secs_running"] > t:
            killsess(connection,i["opid"])
            
def killwaiters(connection,inprog,t):
    for i in inprog:
        if i["active"] == "true" and i["waitingForLock"] == "true" and i["secs_running"] > t:
            killsess(connection,i["opid"])
    
def main():
   
    connection = Connection( options.host , options.port )
    inprog=getinprog(connection)
        
    if options.orphan:
        killorphan(connection,inprog)
    if options.idle:
        killidle(connection,inprog)
    if options.waiters:
        killwaiters(connection,inprog,options.threshold)
    if options.blockers:
        killblockers(connection,inprog,options.threshold)
    if options.longrunners:
        killlongrunners(connection,inprog,options.threshold)

if __name__ == "__main__":

    parser = OptionParser()
    parser.set_defaults(host="localhost",port="27017",threshold=30)
    parser.add_option("--port",dest="port",type=int,help="host port to connect to")
    parser.add_option("--host",dest="host",help="host to connect to")
    parser.add_option("--blockers",action="store_true",dest="blockers")
    parser.add_option("--waiters",action="store_true",dest="waiters")
    parser.add_option("--idle",action="store_true",dest="idle")
    parser.add_option("--orphan",action="store_true",dest="orphan")
    parser.add_option("--longrunners",action="store_true",dest="longrunners")
    parser.add_option("--threshold",dest="threshold",type="int")
    parser.add_option("--testmode",dest="testmode",action="store_true")
    (options, args) = parser.parse_args()

    main()