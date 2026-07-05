import json

# This tells the cloud computer to open our settings file
with open('config.json', 'r') as file:
    brain = json.load(file)

# Camera AI reads its own brain and speaks to us!
print("STATUS: " + brain["project_name"] + " is ALIVE!")
print("ARCHITECTURE: " + brain["architecture"])
print("MISSION: " + brain["mission"])