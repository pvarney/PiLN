#!/usr/bin/python

import cgi
import MySQLdb
from MySQLdb.cursors import DictCursor
import jinja2

db = MySQLdb.connect( user="piln", passwd="p!lnp@ss", db="PiLN", host="localhost", cursorclass=DictCursor, use_unicode=True) 
cursor = db.cursor()
env = jinja2.Environment(loader=jinja2.FileSystemLoader(["/home/PiLN/template"])) 

maxsegs = 20
def_rate = 9999
def_holdmin = 0
def_intsec = 10

form = cgi.FieldStorage()
page = form.getfirst( "page", "" )
run_id = form.getfirst( "run_id", "0" )
notes = form.getfirst( "notes", "" )
state = form.getfirst( "state", "" )



if page == "view":

  cursor.execute( "select * from Profiles where run_id=%d;" % int(run_id) )
  profile = cursor.fetchone()
  
  cursor.execute( "select segment, set_temp, rate, hold_min, int_sec, date_format(start_time, '%%m/%%d/%%Y %%H:%%i') as start_time, date_format(end_time, '%%m/%%d/%%Y %%H:%%i') as end_time from Segments where run_id=%d order by segment;" % int(run_id) )
  segments = cursor.fetchall()
  
  template = env.get_template( "header.html" ) 
  hdr = template.render( 
    title="Profile Details"
  )
  
  viewtmpl="view_staged.html"

  if state == "Completed":
    viewtmpl="view_comp.html"
  elif state == "Running":
    viewtmpl="view_run.html"

  template = env.get_template( viewtmpl ) 
  bdy = template.render(
    segments=segments,
    profile=profile,
    run_id=run_id,
    state=state,
    notes=notes
  )

  if state == "Completed" or state == "Running" or state == "Stopped":
    template = env.get_template( "chart.html" ) 
    bdy += template.render(
      run_id=run_id,
      notes=notes
    )
  
  template = env.get_template( "footer.html" ) 
  ftr = template.render()
  
  print hdr.encode('utf-8') + bdy.encode('utf-8') + ftr.encode('utf-8')



elif page == "new":

  template = env.get_template( "header.html" ) 
  hdr = template.render( 
    title="New Profile"
  )
 
  segments = range(1,maxsegs + 1)
  
  template = env.get_template( "new.html" ) 
  bdy = template.render(
    segments=segments
  )

  template = env.get_template( "footer.html" ) 
  ftr = template.render()
  
  print hdr.encode('utf-8') + bdy.encode('utf-8') + ftr.encode('utf-8')



elif page == "editcopy":

  cursor.execute( "select segment, set_temp, rate, hold_min, int_sec from Segments where run_id=%d order by segment;" % int(run_id) )
  segments = cursor.fetchall()
  curcount = cursor.rowcount
  addsegs = range(curcount + 1, maxsegs + 1)
  lastseg = curcount + 1

  sql = "select notes, p_param, i_param, d_param from Profiles where run_id=%d;" % int(run_id)
  cursor.execute( sql )
  profile = cursor.fetchone()

  #if profile is not None:
  #  Kp = float(profile['p_param'])
  #  Ki = float(profile['i_param'])
  #  Kd = float(profile['d_param'])

  template = env.get_template( "header.html" ) 
  hdr = template.render( 
    title="Edit/Copy Profile"
  )
  
  template = env.get_template( "editcopy.html" ) 
  bdy = template.render(
    segments=segments,
    addsegs=addsegs,
    lastseg=lastseg,
    run_id=run_id,
    profile=profile,
    state=state,
    notes=notes
  )

  template = env.get_template( "footer.html" ) 
  ftr = template.render()
  
  print hdr.encode('utf-8') + bdy.encode('utf-8') + ftr.encode('utf-8')



elif page == "run":

  template = env.get_template( "header.html" ) 
  hdr = template.render( 
    title="Run Profile"
  )

  sql = "select run_id from Profiles where state='Running'"
  cursor.execute( sql )
  runningid = cursor.fetchone()

  if runningid:

    message = "Unable start profile - Profile %d already running" % int(runningid['run_id'])
    template = env.get_template( "reload.html" ) 
    bdy = template.render(
      target_page = "view",
      timeout = 5000,
      message = message,
      params = { "run_id": run_id, "state":"Staged", "notes": notes }
    )

  else:

    sql = "update Profiles set state='Running' where run_id=%d" % int(run_id)
    cursor.execute( sql )
    db.commit()
 
    template = env.get_template( "reload.html" ) 
    bdy = template.render(
      target_page = "view",
      timeout = 1000,
      message = "Updating profile to running state...",
      params = { "run_id": run_id, "state":"Running", "notes": notes }
    )

  template = env.get_template( "footer.html" ) 
  ftr = template.render()

  print hdr.encode('utf-8') + bdy.encode('utf-8') + ftr.encode('utf-8')



elif page == "savenew":

  template = env.get_template( "header.html" ) 
  hdr = template.render( 
    title="Save Profile"
  )

  p_param = form.getfirst( "Kp", 0.000 )
  i_param = form.getfirst( "Ki", 0.000 )
  d_param = form.getfirst( "Kd", 0.000 )

  sql = "insert into Profiles (state, notes, p_param, i_param, d_param) values ('%s', '%s', %0.3f, %0.3f, %0.3f)" % \
    ( "Staged", notes, float(p_param), float(i_param), float(d_param) )

  cursor.execute( sql )
  newrunid = cursor.lastrowid
  db.commit()
 
  template = env.get_template( "reload.html" ) 
  bdy = template.render(
    target_page = "view",
    timeout = 1000,
    message = "Saving profile...",
    params = { "state": "Staged", "run_id": newrunid, "notes": notes }
  )

  template = env.get_template( "footer.html" ) 
  ftr = template.render()

  for num in range(1,maxsegs + 1):
  
    seg = str(num)
    set_temp = form.getfirst( "set_temp" + seg, "" )
    rate = form.getfirst( "rate" + seg, "" )
    hold_min = form.getfirst( "hold_min" + seg, "" )
    int_sec = form.getfirst( "int_sec" + seg, "" )
 
    if set_temp != "":

      if rate == "":
        rate = def_rate
      if hold_min == "":
        hold_min = def_holdmin 
      if int_sec == "":
        int_sec = def_intsec

      sql = "insert into Segments (run_id, segment, set_temp, rate, hold_min, int_sec) values ('%d', '%d', '%d', '%d', '%d', '%d')" % \
        ( int(newrunid), num, int(set_temp), int(rate), int(hold_min), int(int_sec) )
      cursor.execute( sql )
      db.commit()

  print hdr.encode('utf-8') + bdy.encode('utf-8') + ftr.encode('utf-8')



elif page == "saveupd":

  template = env.get_template( "header.html" ) 
  hdr = template.render( 
    title="Save Profile"
  )

  template = env.get_template( "reload.html" ) 
  bdy = template.render(
    target_page = "view",
    timeout = 1000,
    message = "Saving profile...",
    params = { "state": "Staged", "run_id": run_id, "notes": notes }
  )

  template = env.get_template( "footer.html" ) 
  ftr = template.render()

  print hdr.encode('utf-8') + bdy.encode('utf-8') + ftr.encode('utf-8')

  p_param = form.getfirst( "Kp", 0.000 )
  i_param = form.getfirst( "Ki", 0.000 )
  d_param = form.getfirst( "Kd", 0.000 )

  lastseg = form.getfirst( "lastseg", 0 )

  sql = "update Profiles set notes='%s', p_param=%0.3f, i_param=%0.3f, d_param=%0.3f where run_id=%d" % \
    ( notes, float(p_param), float(i_param), float(d_param), int(run_id) )
  cursor.execute( sql )
 
  for num in range(1,maxsegs + 1):
    seg = str(num)
    set_temp = form.getfirst( "set_temp" + seg, "" )
    rate = form.getfirst( "rate" + seg, "" )
    hold_min = form.getfirst( "hold_min" + seg, "" )
    int_sec = form.getfirst( "int_sec" + seg, "" )

    if set_temp != "":
      if rate == "":
        rate = def_rate
      if hold_min == "":
        hold_min = def_holdmin 
      if int_sec == "":
        int_sec = def_intsec

      if num >= int(lastseg):
        sql = "insert into Segments (run_id, segment, set_temp, rate, hold_min, int_sec) values ('%d', '%d', '%d', '%d', '%d', '%d')" % \
          ( int(run_id), num, int(set_temp), int(rate), int(hold_min), int(int_sec) )
        cursor.execute( sql )

      else:
        sql = "update Segments set set_temp=%d, rate=%d, hold_min=%d, int_sec=%d where run_id=%d and segment=%d" % \
          ( int(set_temp), int(rate), int(hold_min), int(int_sec), int(run_id), num )
        cursor.execute( sql )

    else:
      sql = "delete from Segments where run_id=%d and segment=%d" % \
        ( int(run_id), num )
      cursor.execute( sql )

  db.commit()



elif page == "del_conf":

  cursor.execute( "select segment, set_temp, rate, hold_min, int_sec, date_format(start_time, '%%m/%%d/%%Y %%H:%%i') as start_time, date_format(end_time, '%%m/%%d/%%Y %%H:%%i') as end_time from Segments where run_id='%s' order by segment;" % run_id )
  segments = cursor.fetchall()
  
  template = env.get_template( "header.html" ) 
  hdr = template.render( title="Confirm Profile Delete" )
  
  template = env.get_template( "del_conf.html" ) 
  bdy = template.render(
    segments=segments,
    run_id=run_id,
    notes=notes,
    state=state
  )
  
  template = env.get_template( "footer.html" ) 
  ftr = template.render()

  print hdr.encode('utf-8') + bdy.encode('utf-8') + ftr.encode('utf-8')



elif page == "delete":

  template = env.get_template( "header.html" ) 
  hdr = template.render( 
    title="Delete Profile"
  )
 
  template = env.get_template( "reload.html" ) 
  bdy = template.render(
    target_page = "home",
    timeout = 1000,
    message = "Deleting profile...",
    params = { "run_id": run_id }
  )

  template = env.get_template( "footer.html" ) 
  ftr = template.render()

  sql1 = "delete from Firing where run_id=%d" % int(run_id)
  sql2 = "delete from Segments where run_id=%d" % int(run_id)
  sql3 = "delete from Profiles where run_id=%d" % int(run_id)
  cursor.execute( sql1 )
  cursor.execute( sql2 )
  cursor.execute( sql3 )
  db.commit()

  print hdr.encode('utf-8') + bdy.encode('utf-8') + ftr.encode('utf-8')



elif page == "stop":

  template = env.get_template( "header.html" ) 
  hdr = template.render( 
    title="Stop Profile Run"
  )
 
  template = env.get_template( "reload.html" ) 
  bdy = template.render(
    target_page = "home",
    timeout = 1000,
    message = "Updating profile...",
    params = { "run_id": run_id }
  )

  template = env.get_template( "footer.html" ) 
  ftr = template.render()

  cursor.execute( "update Profiles set state='Stopped' where run_id=%d" % int(run_id) )
  db.commit()

  print hdr.encode('utf-8') + bdy.encode('utf-8') + ftr.encode('utf-8')



elif page == "notes_save":

  template = env.get_template( "header.html" ) 
  hdr = template.render( 
    title="Save Notes"
  )

  sql = "update Profiles set notes='%s' where run_id=%d" % ( notes, int(run_id))
  cursor.execute( sql )
  db.commit()
 
  template = env.get_template( "reload.html" ) 
  bdy = template.render(
    target_page = "view",
    timeout = 0,
    message = "Saving notes...",
    params = { "state": state, "run_id": run_id, "notes": notes }
  )

  template = env.get_template( "footer.html" ) 
  ftr = template.render()

  print hdr.encode('utf-8') + bdy.encode('utf-8') + ftr.encode('utf-8')



else:

  cursor.execute( "select state, run_id, notes, date_format(start_time, '%m/%d/%Y') as lastdate from Profiles order by FIELD(state,'Running','Staged','Stopped','Completed'), run_id desc;")
  profiles = cursor.fetchall()
  
  template = env.get_template( "header.html" ) 
  hdr = template.render( title="Profile List" )
  
  template = env.get_template( "home.html" ) 
  bdy = template.render(profiles=profiles )
  
  template = env.get_template( "footer.html" ) 
  ftr = template.render()
  
  print hdr.encode('utf-8') + bdy.encode('utf-8') + ftr.encode('utf-8')


cursor.close()
db.close()
