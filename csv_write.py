import csv
import pandas as pd

def writer(header, data, filename, option):
    with open(filename, 'w') as csvfile:
        if option == 'write':
            movies = csv.writer(csvfile)
            movies.writerow(header)
            for x in data:
                movies.writerow(x)
        elif option == 'update':
            writer = csv.DictWriter(csvfile, fieldnames = header)
            writer.writeheader()
            writer.writerows(data)
        else:
            print('option is unknown')

def update(filename):
    with open(filename, 'r+') as file:
        readData = [row for row in csv.DictReader(file)]
        print(readData)
        readData[0]['Rating'] = '9.4'
        print(readData)

        readHeader = readData[0].keys()
        writer(readHeader, readData, filename, "update")

def csv_operate():
    filename = "test.csv"
    header = ("Rank", "Rating", "Title")
    data = [
            (1, 9.2, "The Shawshank Redemption(1994)"),
            (2, 9.2, "The Godfather(1972)"),
            (3, 9, "The Godfather: Part II(1974)"),
            (4, 8.9, "Pulp Fiction(1994)")
         ]

    writer(header, data, filename, "write")
    update(filename)

if __name__ == '__main__':
    csv_operate()
    #data = pd.read_excel('test.csv', sheet_name="test")
    #print data