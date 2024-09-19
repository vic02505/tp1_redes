import datetime
import time

firstTimeoutMeasure = datetime.datetime.now()
print("Empezo ", firstTimeoutMeasure)

time.sleep(5)

secondTimeoutMeasure = datetime.datetime.now()
print("Termino ", secondTimeoutMeasure)

# Reset time
firstTimeoutMeasure = datetime.datetime.now()
print("Reset time to ", firstTimeoutMeasure)
