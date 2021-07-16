import datetime


def timestamp_filename(filename:str):
	time = datetime.datetime.now().isoformat()
	date,time = time.split("T")
	return date.replace("-"," ") +" "+"".join(time.split(":")[:2])+" "+filename
