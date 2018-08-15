import mosquitto
import os
import time
import re
import sys
import datetime
from datetime import timedelta
import json
import subprocess
import MySQLdb
import smtplib
import email.mime.base
from email.mime.multipart import MIMEMultipart
import email.message
from email.mime.text import MIMEText
import time
import datetime

topic = 'Sensor2' #topic same on Huzzah board
broker= '192.168.88.80'#IP Address change 
client_name = "Sensor2Client" #id
client = mosquitto.Mosquitto(client_name)
client.connect(broker)
client.subscribe(topic,0)

def getConfigurations():


	path = os.path.dirname(os.path.realpath(sys.argv[0]))

	#get configs
	configurationFile = path + '/config.json'
	configurations = json.loads(open(configurationFile).read())

	return configurations

# helper function for database actions. Handles select, insert and sqldumpings. Update te be added later
def databaseHelper(sqlCommand,sqloperation):

	configurations = getConfigurations()
	host = configurations["mysql"][0]["host"]
	user = configurations["mysql"][0]["user"]
	password = configurations["mysql"][0]["password"]
	database = configurations["mysql"][0]["database"]
	backuppath = configurations["sqlbackuppath"]
	
	data = ""
	
	db = MySQLdb.connect(host,user,password,database)
	cursor=db.cursor()

	if sqloperation == "Select":
		try:
			cursor.execute(sqlCommand)
			data = cursor.fetchone()
		except:
			db.rollback()
	elif sqloperation == "Insert":
		try:
			cursor.execute(sqlCommand)
			db.commit()
		except:
			db.rollback()
			emailWarning("Database insert failed", "")
			sys.exit(0)
    
	elif sqloperation == "Backup":	
		# Getting current datetime to create seprate backup folder like "12012013-071334".
		date = datetime.date.today().strftime("%Y-%m-%d")
		backupbathoftheday = backuppath + date

		# Checking if backup folder already exists or not. If not exists will create it.
		if not os.path.exists(backupbathoftheday):
			os.makedirs(backupbathoftheday)

		# Dump database
		db = database
		dumpcmd = "mysqldump -u " + user + " -p" + password + " " + db + " > " + backupbathoftheday + "/" + db + ".sql"
		os.system(dumpcmd)

	return data

	
# function for getting weekly average temperatures.
def getWeeklyAverageTemp(sensor):

	weekAverageTemp = ""	
	
	date = 	datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	delta = (datetime.date.today() - timedelta(days=7)).strftime("%Y-%m-%d 00:00:00")

	try:
		sqlCommand = "SELECT AVG(temperature) FROM temperaturedata WHERE dateandtime BETWEEN '%s' AND '%s' AND sensor='%s'" % (delta,date,sensor)
		data = databaseHelper(sqlCommand,"Select")
		weekAverageTemp = "%.2f" % data
	except:
		pass
	
	return weekAverageTemp

# function that sends emails, either warning or weekly averages in order to see that pi is alive
def emailWarning(msgbody, msgType):
	
	configurations = getConfigurations()
	fromaddr = configurations["mailinfo"][0]["senderaddress"]
	toaddr = configurations["mailinfo"][0]["receiveraddress"]
	password = configurations["mailinfo"][0]["password"]
	msg = MIMEMultipart()
	msg['From'] = fromaddr
	msg['To'] = toaddr
	msg['Subject'] = configurations["mailinfo"][0]["subjectwarning"]
	subj = configurations["mailinfo"][0]["subjectwarning"]	
	if msgType is 'Info':
		msg['Subject'] = configurations["mailinfo"][0]["subjectmessage"]
	
	# Message to be sended with subject field
	body = 'Subject: %s\n\n%s' % (subj,msgbody)
	msg.attach(MIMEText(body,msgType))
	# The actual mail sending
	server = smtplib.SMTP('vmail1.sentex.ca', 587) 
	server.starttls()
	server.login(str(fromaddr),str(password))
	text = msg.as_string()
	server.sendmail(str(fromaddr), str(toaddr), text )
	server.quit()
	return


# function for checking log that when last warning was sended, also inserts new entry to log if warning is sent
def checkWarningLog(sensor, sensortemp):

	currentTime = datetime.datetime.now()
	currentTimeAsString = datetime.datetime.strftime(currentTime,"%Y-%m-%d %H:%M:%S")
	lastLoggedTime = ""
	lastSensor = ""
	triggedLimit = ""
	lastTemperature = ""
	warning = ""
	okToUpdate = False
	# sql command for selecting last send time for sensor that trigged the warning

	sqlCommand = "select * from mailsendlog where triggedsensor='%s' and mailsendtime IN (SELECT max(mailsendtime)FROM mailsendlog where triggedsensor='%s')" % (sensor,sensor)
	data = databaseHelper(sqlCommand,"Select")

	# If there weren't any entries in database, then it is assumed that this is fresh database and first entry is needed
	if data == None:
		sqlCommand = "INSERT INTO mailsendlog SET mailsendtime='%s', triggedsensor='%s', triggedlimit='%s' ,lasttemperature='%s'" % (currentTimeAsString,sensor,"0.0",sensortemp)
		databaseHelper(sqlCommand,"Insert")
		lastLoggedTime = currentTimeAsString
		lastTemperature = sensortemp
		okToUpdate = True
	else:
		lastLoggedTime = data[0]
		lastSensor = data[1]
		triggedLimit = data[2]
		lastTemperature = data[3]

	# check that has couple of hours passed from the time that last warning was sended.
	# this check is done so you don't get warning everytime that sensor is trigged. E.g. sensor is checked every 5 minutes, temperature is lower than trigger -> you get warning every 5 minutes and mail is flooded.
	try:
		delta = currentTime - lastLoggedTime
		passedTime = (float(delta.seconds) // 3600)
	
		if passedTime > 0.5:#time between sending new email ! here
			okToUpdate = True
		else:
			pass
	except:
		pass

	# another check. If enough time were not passed, but if temperature has for some reason increased or dropped 5 degrees since last alarm, something might be wrong and warning mail is needed
	if okToUpdate == False:
		if "conchck" not in sensor:
			if sensortemp > float(lastTemperature) + 5.0:
				okToUpdate = True
				warning = "NOTE: Temperature increased 5 degrees"
			if sensortemp < float(lastTemperature) - 5.0:
				okToUpdate = True
				warning = "NOTE: Temperature decreased 5 degrees"

	return okToUpdate, warning

# Function for checking limits. If temperature is lower or greater than limit -> do something
def checkLimits(sensor,sensorTemperature,sensorHumidity,sensorhighlimit,sensorlowlimit):
	
	check = True
	warningmsg = ""
	
	if float(sensorTemperature) < float(sensorlowlimit):
		warningmsg = "Temperature low on sensor: {0}\nReading: {1}\nLimit: {2}\nHumidity: {3}".format(sensor,sensorTemperature,sensorlowlimit,sensorHumidity)
		check = False
	elif float(sensorTemperature) > float(sensorhighlimit):
		warningmsg = "Temperature too high on sensor: {0}\nReading: {1}\nLimit: {2}\nHumidity: {3}".format(sensor,sensorTemperature,sensorhighlimit,sensorHumidity)
		check = False
	return check,warningmsg

	
def checkEverything(intTemp, intHumidity):
	
	currentTime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

	configurations = getConfigurations()
	# how many sensors there is 1 or 2
	sensorsToRead = configurations["sensoramount"]
		
	# Sensor names to add to database, e.g. carage, outside
	sensor1 = configurations["sensors"][0]["sensor1"]

	# limits for triggering alarms
	sensor1lowlimit = configurations["triggerlimits"][0]["sensor1lowlimit"]
	sensor2lowlimit = configurations["triggerlimits"][0]["sensor2lowlimit"]
	sensor1highlimit = configurations["triggerlimits"][0]["sensor1highlimit"]
	sensor2highlimit = configurations["triggerlimits"][0]["sensor2highlimit"]


	# Backup enabled
	backupEnabled = configurations["sqlBackupDump"][0]["backupDumpEnabled"]
	backupHour = configurations["sqlBackupDump"][0]["backupHour"]                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           
	
	# Connection check enabled
	connectionCheckEnabled = configurations["connectionCheck"][0]["connectionCheckEnabled"]
	connectionCheckDay = configurations["connectionCheck"][0]["connectionCheckDay"]
	connectionCheckHour = configurations["connectionCheck"][0]["connectionCheckHour"]

	# type of the sensor used, e.g. DHT22 = 22
	# sensorType = configurations["sensortype"]

	# Default value for message type, not configurable
	msgType = "plain"

	d = datetime.date.weekday(datetime.datetime.now())
	h = datetime.datetime.now()

	# check if it is 5 o clock. If yes, take sql dump as backup
	if backupEnabled == "Y" or backupEnabled == "y":
		if h.hour == int(backupHour):
			databaseHelper("","Backup")

	# check if it is sunday, if yes send connection check on 23.00
	if connectionCheckEnabled == "Y" or connectionCheckEnabled == "y":
		okToUpdate = False
		if str(d) == str(connectionCheckDay) and str(h.hour) == str(connectionCheckHour):
			try:
				sensor1weeklyAverage = getWeeklyAverageTemp(sensor1)
				if sensor1weeklyAverage != None and sensor1weeklyAverage != '':
					checkSensor = sensor1+" conchck"
					okToUpdate, tempWarning = checkWarningLog(checkSensor,sensor1weeklyAverage)
					if okToUpdate == True:
						msgType = "plain"
						Message = "Connection check. Weekly average from {0} is {1}".format(sensor1,sensor1weeklyAverage)
						emailWarning(Message, msgType)
						sqlCommand = "INSERT INTO mailsendlog SET mailsendtime='%s', triggedsensor='%s', triggedlimit='%s' ,lasttemperature='%s'" % (currentTime,checkSensor,sensor1lowlimit,sensor1weeklyAverage)
						databaseHelper(sqlCommand,"Insert")
			except: 
				emailWarning("Couldn't get average temperature to sensor: {0} from current week".format(sensor1),msgType)
				pass				

			

	# default message type to send as email. DO NOT CHANGE
	msgType = "plain"       

	sensor1error = 0
	okToUpdate = False
	# Sensor 1 readings and limit check
	try:
		limitsOk,warningMessage = checkLimits(sensor1,intTemp,intHumidity,sensor1highlimit,sensor1lowlimit)
	except:
		emailWarning("Failed to read sensor",msgType)
		pass

	if sensor1error == 0:
		try:
			# if limits were trigged
			if limitsOk == False:
				#emailWarning(warningMessage, msgType)
				okToUpdate, tempWarning = checkWarningLog(sensor1,intTemp)
				print(okToUpdate)
		except: 
##                      # if limits were triggered but something caused error, send warning mail to indicate this
			emailWarning("Failed to check/insert log entry from mailsendlog. Sensor: {0}".format(sensor1),msgType)        
		if okToUpdate == True:
			# enough time has passed since last warning or temperature has increased/decreased by 5 degrees since last measurement
			warningMessage = warningMessage + "\n" + tempWarning
			# send warning
			emailWarning(warningMessage, msgType)
			try:
			# Insert line to database to indicate when warning was sent
				currentTime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				sqlCommand = sqlCommand = "INSERT INTO mailsendlog SET mailsendtime='%s', triggedsensor='%s', triggedlimit='%s' ,lasttemperature='%s'" % (currentTime,sensor1,sensor1lowlimit,intTemp)
				databaseHelper(sqlCommand,"Insert")
				#sys.exit(0)
			except:
				# if database insert failed, send warning to indicate that there is some issues with database
				emailWarning("Failed to insert from {0} to mailsendlog".format(sensor1),msgType)        
	# insert values to db
	try:
		sqlCommand = "INSERT INTO temperaturedata SET dateandtime='%s', sensor='%s', temperature='%s', humidity='%s'" % (currentTime,topic,intTemp,intHumidity )
		databaseHelper(sqlCommand,"Insert")
		sys.exit(0)
	except:
		sys.exit(0)


# function for reading HIH sensors
def on_message(mosq,obj,msg):
	print(msg.topic+" "+str(msg.payload))
	temString = str(msg.payload)
	temperature,humidity=temString.split("/")
	intTemp = float(temperature)
	intHumidity = float(humidity)
	intHumidity = intHumidity*100
	currentTime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	checkEverything(intTemp,intHumidity)
			
def main():
	client.on_message = on_message
	client.loop_forever()
if __name__ == "__main__":
	main()

