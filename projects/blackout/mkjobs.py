import json
S=", cinematic thriller film still, cold blue teal night grade, anamorphic lens, heavy atmosphere, fine film grain, shallow depth of field, no text, no letters, no watermark"
shots={
"b2a":"long data center aisle between tall server racks, rows of status lights turning off one row at a time toward the camera, cold blue light, deep perspective",
"b2b":"wide night city skyline, whole blocks of windows gone black district by district, a few last lit towers, moody blue haze",
"b2c":"open-plan office at night, a dozen people frozen in their chairs staring at monitors, faces lit pale blue by the screens, wide shot, dark room",
"b4a":"cliffside wooden cabin in dense coastal fog at night, tall redwoods, one single window glowing warm orange, cold blue fog all around",
"b4b":"close up of a man's hands opening a laptop on a rough wooden table in a dark cabin, warm screen light blooming across the hands, rest in darkness",
"b7a":"dark office, a single computer monitor glowing red, a person slumped back in their chair in defeat, silhouette, otherwise black",
"b7b":"a laptop alone on a wooden cabin table glowing in total darkness, faint dust floating in the light beam, warm screen glow",
"b7c":"handheld phone camera point of view in a dark cabin room, flashlight beam on a wooden shelf, an old radio on the shelf, front door slightly ajar in the background",
"b8a":"open cabin doorway at night, a tall silhouette backlit by a warm lantern, fog rolling in, face not visible, dark wood walls",
"b9":"wide night shot of a foggy coastal road, a long line of small lanterns approaching a single glowing cabin window on a hill, redwoods, cold blue fog",
"b10":"a laptop on a wooden cabin table in darkness, the screen the only light, warm glow on the wood, black background",
}
jobs=[{"out":f"stills/{k}.png","prompt":v+S,"w":1248,"h":720,"seed":11} for k,v in shots.items()]
json.dump(jobs,open("stills_jobs.json","w"),indent=1)
