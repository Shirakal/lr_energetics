import pandas as pd
from datetime import datetime
import plotly.express as px

# load 'date' and 'movement_type' columns from the LR log file
csvLogFile = pd.read_csv('lift_LR002998.csv')
csvLogFile = csvLogFile[['date', 'movement_type', 'is_vertical', 'CHG_current']].copy()


def get_the_time(time_date_string):
    # sets the time of every 'movement_type'
    time_mark = time_date_string.replace('T', ' ', 1)
    time_mark = datetime.strptime(time_mark, '%Y-%m-%d %H:%M:%S.%f')
    return time_mark


# clean the csv into active(1) or resting(0) states only
csvLogFile['date'] = csvLogFile['date'].apply(get_the_time)
csvLogFile = csvLogFile.loc[csvLogFile['movement_type'] != 16]
csvLogFile = csvLogFile.loc[csvLogFile['movement_type'] != 32]
csvLogFile = csvLogFile.dropna()
csvLogFile.loc[csvLogFile['movement_type'] != 0, 'movement_type'] = 1
csvLogFile = csvLogFile.reset_index()
csvLogFile = csvLogFile.drop('index', axis=1)

# clean the csv into charging(1) or not-charging(0) states only
csvLogFile.loc[csvLogFile['CHG_current'] > 0, 'CHG_current'] = 1
csvLogFile.loc[csvLogFile['CHG_current'] < 0, 'CHG_current'] = 0

# getting the charge vs. work periods of the LR
chargeChangeCounter = 0
chargingTimeOfChange = []
for i in range(0, len(csvLogFile.index) - 1, 1):
    if i == 0:
        if csvLogFile.iloc[0, 3] == 0:
            continue
        else:
            chargeChangeCounter = chargeChangeCounter + 1
            chargingTimeOfChange.append(csvLogFile.iloc[i, 0])
    else:
        if csvLogFile.iloc[i, 3] != csvLogFile.iloc[i + 1, 3]:
            chargeChangeCounter = chargeChangeCounter + 1
            chargingTimeOfChange.append(csvLogFile.iloc[i + 1, 0])
        else:
            continue
    if chargeChangeCounter == 3:
        chargeChangeCounter = 1

# printing the working and charging periods of the LR
chargingLR = pd.DataFrame(chargingTimeOfChange, columns=['charger timestamp'])
for i in range(0, len(chargingLR) - 1, 1):
    if i % 2 == 0:
        print('charge time:', (chargingLR.iloc[i + 1, 0] - chargingLR.iloc[i, 0]).total_seconds() / 60)
    else:
        print('work time:', (chargingLR.iloc[i + 1, 0] - chargingLR.iloc[i, 0]).total_seconds() / 60)

# recording time-points of the LR`s state changes
stateChange = []
for i in range(0, len(csvLogFile.index) - 1, 1):
    if i == 0:
        if csvLogFile.iloc[0, 1] == 0:
            stateChange.append(csvLogFile.iloc[0, 0])
            if csvLogFile.iloc[i, 1] != csvLogFile.iloc[(i + 1), 1]:
                stateChange.append(csvLogFile.iloc[i + 1, 0])
        else:
            continue
    elif csvLogFile.iloc[i, 1] != csvLogFile.iloc[(i + 1), 1]:
        stateChange.append(csvLogFile.iloc[i + 1, 0])

# recording time periods of inactivity
restPeriods = []
for record in range(0, len(stateChange) - 1, 1):
    period = stateChange[record + 1] - stateChange[record]
    period = period.total_seconds() / 60
    restPeriods.append(period)
restingLR = pd.DataFrame(restPeriods, columns=['rest_period'])

# clearing irrelevant inactivity periods
minTime = 1
restingLR = restingLR.drop(restingLR[restingLR.rest_period < minTime].index)
restingLR = restingLR.reset_index(drop=True)


def my_round(value, base):
    # rounds the max value to the max. bucket value
    return base * round(value / base) + base


# bucket settings
maxTime = restingLR.max()
bucketSize = 5
maxTime = my_round(maxTime[0], bucketSize)
numberOfBuckets = int(maxTime / bucketSize)
bucketList = []

for bucket in range(numberOfBuckets):
    minValue = bucket * bucketSize
    maxValue = minValue + bucketSize
    bucketName = "{} to {} min".format(minValue, maxValue)
    bucketList.append(bucketName)

bucketDataFrame = pd.DataFrame(bucketList, columns=['bucket'])
bucketDataFrame['count'] = 0
# bucketDataFrame['vertical'] = 0
# bucketDataFrame['horizontal'] = 0
# print(bucketDataFrame)
# print(restingLR)

# bucket sorting to a new data frame
for bucket in range(0, numberOfBuckets, 1):
    periodsInBucket = 0
    # verticalCount = 0
    # horizontalCount = 0
    for value in range(0, len(restingLR.index), 1):
        period = restingLR.iloc[value, 0]
        # isVertical = restingLR.iloc[value, 3]
        minValue = bucket * bucketSize
        maxValue = minValue + bucketSize
        if (period >= minValue) and (period < maxValue):
            periodsInBucket = periodsInBucket + 1
            # if isVertical == 0:
            #     horizontalCount = horizontalCount + 1
            # else:
            #     verticalCount = verticalCount + 1
    bucketDataFrame.iloc[bucket, 1] = periodsInBucket
    # bucketDataFrame.iloc[bucket, 2] = verticalCount
    # bucketDataFrame.iloc[bucket, 3] = horizontalCount

print(bucketDataFrame)
# bar-graph set+print
# restPeriodsFig = px.bar(restingLR, x=restingLR.index, y=restingLR['rest_period'])
# restPeriodsFig.show()
bucketFig = px.bar(bucketDataFrame, x=bucketDataFrame['bucket'], y=bucketDataFrame['count'])
bucketFig.show()
