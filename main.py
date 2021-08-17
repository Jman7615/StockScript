import csv
import requests
import time
from os import path
import pandas as pd
import sys
import os

filename = 'margin1.csv'
APIKEY = 'your_key_here'


file = os.path.abspath(filename)


# calls the API and downloads time series daily for given symbol as [symbol].csv
def getCSV(SYM):
    CSV_URL = 'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol=' + SYM + '&apikey= ' + APIKEY + '&outputsize=full&datatype=csv'
    print("Dowloading from: " + CSV_URL)
    with requests.Session() as s:
        download = s.get(CSV_URL)

        decoded_content = download.content.decode('utf-8')
        # content reader puts rows of csv in a list
        cr = csv.reader(decoded_content.splitlines(), delimiter=',')
        my_list = list(cr)

        with open(SYM + '.csv', 'w', newline='') as csvfile:
            # writes each row to a new csv file
            r = csv.writer(csvfile, delimiter=' ', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            for row in my_list:
                r.writerow(row)


# Given file name and list of column names, returns list of indices that correspond
def getCSVcolumnIDs(file, find):
    with open(file, newline='') as csvfile:
        # Pandas read csv as dataframe
        df = pd.read_csv(csvfile)

        i = []
        for col in find:
            # using pandas appends desired column location to the list
            i.append(df.columns.get_loc(col))

        return i


def getClosingPrice(file, date):
    with open(file) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')

        # format date to match the format in alphavantage
        date = date.replace('/', '-')

        # append leading zeros if applicable
        if date[1] == '-':
            date = '0' + date
        if date[4] == '-':
            date = date[0:3] + '0' + date[3:11]

        # display as year month day, with 4 digit year
        date = MDYtoYMD(date)

        next(reader)
        for row in reader:

            s = listToString(row)
            # gets the date from the csv file row
            temp = s[0:10]

            if temp == date:
                price = s.split()
                return price[5]

    return "error"


# removes characters in list remove from string s
def removeFormat(s, remove):
    output = s
    for char in remove:
        output = output.replace(char, '')

    return output


# given MM-DD-YY returns YYYY-MM-DD
def MDYtoYMD(d):
    return "20" + d[6:12] + "-" + d[0:5]


def listToString(s):
    # initialize an empty string
    str1 = ""

    # return string with list appended
    return str1.join(s)

# checks if csv file has an error message
def CSVisValid(file):
    with open(file, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            x = listToString(row)
            if x == '{' or row == '}':
                return False

    return "error"


colName = ['COST', 'GAIN_LOSS', 'DAYS_HELD', 'UNDERLYING_SYMBOL', 'SECURITY_DESCRIPTION', 'OPEN_DATE',
           'OPENING_TRANSACTION', "TERM"]
COST, GL, DH, SYM, DESC, DATE, TRANS, TERM = 0, 0, 0, 0, 0, 0, 0, 0

indices = getCSVcolumnIDs(file, colName)
LTOTAL, STOTAL = 0, 0
badchars = ['$', ',']
with open(file, newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')

    next(reader)
    for row in reader:

        # assigns indices from found columns

        COST = float(removeFormat(row[indices[0]], badchars))
        GL = float(removeFormat(row[indices[1]], badchars))
        DH = row[indices[2]]
        SYM = row[indices[3]]
        DESC = row[indices[4]]
        DATE = row[indices[5]]  # Date is OPEN_DATE
        TRANS = row[indices[6]]
        TERM = row[indices[7]]

        if TERM == "S":
            STOTAL += GL

        if TERM == "L":
            LTOTAL += GL

        if TERM == "60/40":
            STOTAL += (.4 * GL)
            LTOTAL += (.6 * GL)

        # skipping unimplemented types
        if TRANS == 'STO' or TRANS == 'EXC':
            print("skipping " + DESC + " " + TRANS + "\n")
            continue

        print(DESC)

        # check if file exists, else call API
        if path.exists(SYM + '.csv'):
            pass
        else:
            getCSV(SYM)
            time.sleep(20)

        if SYM == '':
            continue

        print("ROI: " + "{:.3f}".format(float(GL / COST)))
        print("ROI (year adj.): " + "{:.3f}".format(
            (float(GL) / float(COST)) * (float(DH) / 365)))

        if not CSVisValid(SYM + '.csv'):
            print("Invalid .csv\n")
            continue

        CPRICE = getClosingPrice(SYM + '.csv', DATE)

        print("Cost to Price Ratio: " + "{:.3f}".format(float(COST) / (float(CPRICE) * 100)))

        x = DESC.split()

        if x[0] != "CALL":
            print("\n")
            continue

        STRIKE = x[-1]

        print("% Premium: " + "{:.3f}".format((float(STRIKE) + (COST / 100)) / float(CPRICE)))
        print("Premium to Price Ratio: " + "{:.3f}".format(
            (float(STRIKE) + (COST / 100) - float(CPRICE)) / float(CPRICE)))

        print("\n")

print("Total Long Term Gain: " + str("{:.3f}".format(LTOTAL)))
print("Total Short Term Gain: " + str("{:.3f}".format(STOTAL)))

print("Done")
# sys.stdout.close()
