import argparse
import urllib.request
import re
import json
import csv

def extract_route(url):
    fp = urllib.request.urlopen(url)
    mybytes = fp.read()

    html = mybytes.decode("utf8")
    fp.close()

    regex_string = re.findall("payload\s=\s(\{.+?});", html)[0]
    payload = json.loads(regex_string)

    travels = sort_travels(payload["travels"])

    for i in range(len(travels)):
        travels[i]["infoJson"] = json.loads(travels[i]["infoJson"])
        travels[i]["optionsJson"] = json.loads(travels[i]["optionsJson"])

        for j in range(len(travels[i]["legs"])):
            travels[i]["legs"][j]["infoJson"] = json.loads(travels[i]["legs"][j]["infoJson"])

    return {
        "name": payload["name"],
        "travels": travels,
        "simplified": simplify_route(travels)
    }

def simplify_route(travels):
    nodatamarker = '---------'
    simplified = []
    for travel in travels:

        interchanges = ""
        for l in range(len(travel["legs"]) - 1):
            interchanges += (travel["legs"][l]["infoJson"]["trainStopStations"][-1]["name"]) + ", "

        date = add_leading_zeros(f'{travel["infoJson"]["date"]["year"]}/{travel["infoJson"]["date"]["month"]}/{travel["infoJson"]["date"]["day"]}')

        timestamp = travel["date"]

        for l in range(len(travel["legs"])):
            leg = travel["legs"][l]["infoJson"]

            if l > 0:
                timestamp = nodatamarker
                date = nodatamarker

            simplified.append({
                "timestamp": timestamp,
                "from": f'{leg["trainStopStations"][0]["name"]}, {leg["trainStopStations"][0]["country"]}',
                "to": f'{leg["trainStopStations"][-1]["name"]}, {leg["trainStopStations"][-1]["country"]}',
                "date": date,
                "trainNames": (travel["legs"][l]["infoJson"]["trainName"]),
                "departureTime": add_leading_zeros(f'{leg["startTime"]["hours"]}:{leg["startTime"]["minutes"]}'),
                "arrivalTime": add_leading_zeros(f'{leg["endTime"]["hours"]}:{leg["endTime"]["minutes"]}'),
                "duration": add_leading_zeros(f'{leg["duration"]["hours"]}:{leg["duration"]["minutes"]}'),
            })

    return simplified

def sort_travels(travels):
    travels.sort(key=lambda x : x["date"])
    return travels

def correct_negative_minutes(time:str):
    hours, minutes = time.split(":")
    if int(minutes) < 0:
        return f'{int(hours) - 1}:{60 + int(minutes)}'
    return time

def add_leading_zeros(x):
    if ":" in x:
        fragments = x.split(":")
    else:
        fragments = x.split("/")

    for i in range(len(fragments)):
        if int(fragments[i]) < 10:
            fragments[i] = "0" + fragments[i]

    if ":" in x:
        return f'{fragments[0]}:{fragments[1]}'
    else:
        return f'{fragments[0]}/{fragments[1]}/{fragments[2]}'
    

def save_route(data):

    # json
    json_obj = json.dumps(data["travels"], indent=4)
    with open(f'{data["name"]}.json', 'w') as file:
        file.write(json_obj)

    # csv
    csv_file = open(f'{data["name"]}.csv', 'w')
 
    csv_writer = csv.writer(csv_file)
    count = 0
 
    for travel in data["simplified"]:
        if count == 0:
            header = travel.keys()
            csv_writer.writerow(header)
            count += 1
 
        csv_writer.writerow(travel.values())
 
    csv_file.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="This application creates a well formated json file of the full data and a csv file of a selection of attributes")

    parser.add_argument("--url", required=True, help='url has to be the shared link from the eurail application: python3 get_route.py --url "https://share.eurailapp.com/xxxx" ')

    args = parser.parse_args()

    data = extract_route(args.url)

    save_route(data)