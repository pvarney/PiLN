#!/usr/bin/python
 
import sys
import re
import datetime
import pymysql
import json
 
DBSvr = "localhost"
DBName = "PiLN"
DBID = "piln"
DBPwd = "p!lnp@ss"
 
# Get json data from standard in
jsonin = ""
 
for line in sys.stdin:
  jsonin += line
 
query = json.loads(jsonin)
 
conn = pymysql.connect(host=DBSvr, port=3306, user=DBID, passwd=DBPwd, db=DBName)
cur = conn.cursor()

cur.execute(query['select'])

#jsoncol = json.dumps(query['columns'])
retdata = '\n{"cols":' + json.dumps(query['columns']) + ',"rows":['

for row in cur:

  retdata += '{"c":['

  colindx = 0
  for coldata in query['columns']:

    cval = ""
    colname = coldata['id']

    if coldata['type'] == "datetime":
      dtvals = re.split('[- :]', str(row[colindx]) )
      dtvals[1] = str( int( dtvals[1] ) - 1 )
      cval = '"Date(' + ",".join(dtvals) + ')"'

    elif coldata['type'] == "number":
      cval = float(row[colindx])

    else:
      cval = '"' + str(row[colindx]) + '"'

    colindx += 1

    if cval:
      retdata += '{"v":' + str(cval) + '},'

    else:
      retdata += '{"v":null},'

  retdata = retdata.rstrip(',')
  retdata += "]},"

cur.close()
conn.close()

retdata = retdata.rstrip(',')
retdata += "]}\n"
 
print retdata
 
