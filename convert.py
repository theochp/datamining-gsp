import csv
import time
import datetime
import time

days=24*60*60

# in seconds
minSequenceSize = 2
windowSize = 2*days
minGap = 4*60*60
maxGap = 12*60*60

dataset = None

sequences = []

itemIds = {}
itemNames = {}
itemIdCount = 1
def parseDate(date):
    return time.mktime(datetime.datetime.strptime(date, "%d/%m/%Y %H:%M").timetuple())

def parseRow(row):
    global itemIdCount
    if row[1] not in itemIds:
        itemIds[row[1]] = itemIdCount
        itemNames[itemIdCount] = row[2]
        itemIdCount = itemIdCount + 1
    if row[6] == None or len(row[6]) == 0:
        return None
    return {
        'transactionId': row[0],
        'timestamp': parseDate(row[4]),
        'stockId': row[1],
        'customerId': row[6]
    }

def getDataset(dataset):
    with open(dataset, newline = '') as cvsFile:
        content = csv.reader(cvsFile, delimiter=';')
        next(content, None) # skip header
        transactions = []
        for row in content:
            el = parseRow(row)
            if el is not None:
                transactions.append(el)
        return transactions

def sequenceSize(sequence):
    count = 0
    for item in sequence:
        count = count + len(item)
    return count

def generateItem(trStart, dataset, currentClient):
    i = 0
    item = [trStart]
    while i < len(dataset):
        if dataset[i]['customerId'] != currentClient:
            i=i+1
            continue
        # check WS between nextTr and First element of current item
        if dataset[i]['timestamp'] - trStart['timestamp'] <= windowSize:
            item.append(dataset[i])
        else:
            break
        i=i+1
    return [item, i+1]

def generateSequence(tr, dataset):
    sequence = []
    currentClient = tr['customerId']
    [item, i] = generateItem(tr, dataset[1:], currentClient)
    sequence.append(item)
    while i < len(dataset):
        [item, iout] = generateItem(dataset[i], dataset[i+1:], currentClient)
        if (item[-1]['timestamp'] - sequence[-1][0]['timestamp']) > maxGap:
            return [sequence, i]
        if item[0]['timestamp'] - sequence[-1][-1]['timestamp'] > minGap:
                sequence.append(item)
        i = i+iout
    return [sequence, None]

def convert(datasetName, mingap, maxgap, ws):
    global dataset
    global minGap
    global maxGap
    global windowSize
    minGap = mingap
    maxGap = maxgap
    windowSize = ws
    dataset = getDataset(datasetName)

    doneCustomers = []
    for idx, tr in enumerate(dataset):
        if tr['customerId'] not in doneCustomers:
            doneCustomers.append(tr['customerId'])
            [sequence, iout] = generateSequence(tr, dataset[idx:])
            if sequenceSize(sequence) >= minSequenceSize:
                sequences.append(sequence)
            while iout is not None:
                [sequence, iout] = generateSequence(dataset[iout], dataset[iout+1:])
                if sequenceSize(sequence) >= minSequenceSize:
                    sequences.append(sequence)

    finalResult = []
    items = []
    for seq in sequences:
        finalSequence = []
        for item in seq:
            finalItem = []
            for el in item:
                id = itemIds[el['stockId']]
                if id not in items:
                    items.append(id)
                finalItem.append(id)
            finalItem.sort()
            finalSequence.append(finalItem)
        finalResult.append(finalSequence)
    items.sort()
    print(len(finalResult), "transactions")
    return [finalResult, items, itemNames]