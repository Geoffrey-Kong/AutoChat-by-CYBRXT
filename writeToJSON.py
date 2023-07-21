from datetime import datetime
import pytz
import json

#Used to write data to the json file
def appendToDatabase(user, type: str, pingedUser = None, numPings = 0, numDeleted = 0, server = None, channel = None):
  with open("database.json", "a") as f:
    dt_string = datetime.now(pytz.timezone('US/Eastern')).strftime("%m/%d/%Y at %I:%M:%S %p")
    dict = {
      "time": dt_string,
      "user": user.id,
      "action": ""
    }
    match type:
      case "awayMessage":
        dict["action"] = f"Intercepted help request in: {server} -> {channel}."
        f.write(json.dumps(dict) + "\n")
      case "whyMessage":
        dict["action"] = "Gave explanation on why CYBRXT is avoiding help."
        f.write(json.dumps(dict) + "\n")
      case "deleteMessage":
        dict["action"] = f"Deleted {numDeleted} message(s) in: {server} -> {channel}."
        f.write(json.dumps(dict) + "\n")
      case "pingMessage":
        dict["action"] = f"Pinged {pingedUser} {numPings} time(s) in: {server} -> {channel}."
        f.write(json.dumps(dict) + "\n")
      case "timeoutMessage":
        dict["action"] = f"Timed out {user} for"
        f.write(json.dumps(dict) + "\n")