import json
tl=json.load(open("final/timeline.json")); S={s["name"]:s for s in tl["segments"]}
T=[]
def add(i,txt,seg,a,b,ri,ro):
    s=S[seg]["start"]; T.append({"id":i,"text":txt,"rec_in":round(s+a,2),"rec_out":round(min(s+b,tl["duration"]),2),"read_in":ri,"read_out":ro})
add("card1","NOVEMBER 14. 4:12 AM.","card1",0.8,4.5,.3,.3)
add("phone","Can't connect to server","b2c",0.1,3.7,.25,.25)
add("wrong","Something went wrong","b2c",3.7,7.2,.25,.25)
add("card3","THE CLOUD IS GONE.","card3",0.2,3.7,.3,.3)
add("ask","> are you there?","scr_ask",0.3+16/12,4.6,0,0.1)
add("reply","I'm here. I run on this machine.","scr_reply",0.2+32/20,5.8,0,0.1)
add("card6","ONE MACHINE. NO SIGNAL.","card6",0.2,4.1,.3,.3)
add("limit","Usage limit reached","u1",0.05,3.4,.25,.25)
add("narr","NarrateClaude","nar",0.2,3.7,.3,.3)
add("sf","SONG FORGE","sf",0.0,3.2,.3,.1)
add("l1","Flashlight.","rt",0.3,5.4,.2,.3); add("l2","Radio.","rt",1.4,5.4,.2,.3); add("l3","Door... open.","rt",2.4,5.4,.2,.3)
add("title","BLACKOUT","title",0.12,8.4,0,0.5)
add("tag","Your AI doesn't need the cloud.","title",2.4,8.4,.4,.5)
add("end","Claude Code Local. Free and open source.","title",3.2,8.4,.4,.4)
add("still","Still here.","still",0.3+11/12,4.2,0,0.4)
tl["texts"]=T; json.dump(tl,open("final/timeline.json","w"),indent=1)
