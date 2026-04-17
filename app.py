"""
PFT Navigator — app.py v5
All room coordinates re-measured pixel-by-pixel from floor plan images.
Image content area: roughly x 0.13–0.98, y 0.07–0.96 of image dimensions.

FLOOR 1 key observations (image ~1190×940px):
  Top lab block:   y ≈ 0.07–0.26  (Enhanced Oil, Rock Mech, Thermal, Instrumentation, Civil labs)
  Corridor H1:     y ≈ 0.27       (white space between top labs and commons)
  Commons area:    y ≈ 0.28–0.43  (Capstone, Human Factors, Campus Computer)
  Corridor H2:     y ≈ 0.44       (The Commons spine, elevators)
  Classroom area:  y ≈ 0.46–0.56  (upper classroom row)
  Corridor H3:     y ≈ 0.57       (between classroom rows)
  Classroom area:  y ≈ 0.58–0.70  (lower classroom row)
  Corridor H4:     y ≈ 0.72       (Atrium N edge)
  Atrium area:     y ≈ 0.73–0.96  (Chem Eng labs, Auditorium)

  Vertical spines (white gaps):
    V_W:  x ≈ 0.30  (west of Mech labs)
    V_CW: x ≈ 0.54  (between Mech/PETE and Civil blocks)
    V_CE: x ≈ 0.69  (between Civil block and east ECE/Robotics)
    V_E:  x ≈ 0.87  (east side, near Main Entrance)
"""

from flask import Flask, render_template, request, jsonify, session
import heapq, math

app = Flask(__name__)
app.secret_key = 'pft_nav_2024'

SCALE      = 100
ELEV_COST  = 18
STAIR_COST = 10

# ═══════════════════════════════════════════════════════════════
#  ROOMS  — pixel-accurate centres from floor plan images
# ═══════════════════════════════════════════════════════════════
ROOMS = {
    "1100":{"name":"Auditorium","floor":1,"dept":"College","type":"auditorium","x":0.8382,"y":0.729,"door":(0.7858,0.7162),"keywords":["1100","auditorium","lecture hall"]},
    "1114":{"name":"Unit Operations Lab","floor":1,"dept":"Chemical Engineering","type":"lab","x":0.5835,"y":0.682,"door":(0.5745,0.69),"keywords":["1114","unit operations lab","unit operations","cheme lab"]},
    "1124":{"name":"Computer Lab 1124","floor":1,"dept":"Chemical Engineering","type":"lab","x":0.5835,"y":0.773,"door":(0.6079,0.7686),"keywords":["1124","computer lab 1124"]},
    "1154":{"name":"Sustainable Living Lab","floor":1,"dept":"Chemical Engineering","type":"lab","x":0.17,"y":0.678,"door":(0.315,0.69),"keywords":["1154","sustainable living lab","green"]},
    "1200":{"name":"Classroom 1200","floor":1,"dept":"University","type":"classroom","x":0.6494,"y":0.519,"door":(0.7821,0.5066),"keywords":["1200","classroom 1200"]},
    "1202":{"name":"Pete Classroom","floor":1,"dept":"Petroleum Engineering","type":"classroom","x":0.7206,"y":0.519,"door":(0.7153,0.5066),"keywords":["1202","pete classroom"]},
    "1206":{"name":"Modular 1206","floor":1,"dept":"University","type":"lab","x":0.5581,"y":0.519,"door":(0.5745,0.5371),"keywords":["1206","modular 1206"]},
    "1212":{"name":"Classroom 1212","floor":1,"dept":"University","type":"classroom","x":0.2127,"y":0.581,"door":(0.2669,0.4716),"keywords":["1212","classroom 1212"]},
    "1216":{"name":"Classroom 1216","floor":1,"dept":"University","type":"classroom","x":0.1873,"y":0.519,"door":(0.3113,0.5371),"keywords":["1216","classroom 1216"]},
    "1218B":{"name":"Classroom 1218B","floor":1,"dept":"University","type":"classroom","x":0.2669,"y":0.5371,"door":(0.2669,0.5371),"keywords":["1218b","classroom 1218b"]},
    "1221":{"name":"Classroom 1221","floor":1,"dept":"University","type":"classroom","x":0.0457,"y":0.577,"door":(0.1631,0.5328),"keywords":["1221","classroom 1221"]},
    "1225":{"name":"Classroom 1225","floor":1,"dept":"University","type":"classroom","x":0.0457,"y":0.505,"door":(0.1631,0.4672),"keywords":["1225","classroom 1225"]},
    "1238":{"name":"Classroom 1238","floor":1,"dept":"University","type":"classroom","x":0.1348,"y":0.519,"door":(0.3188,0.4716),"keywords":["1238","classroom 1238"]},
    "1240":{"name":"Classroom 1240","floor":1,"dept":"University","type":"classroom","x":0.2367,"y":0.519,"door":(0.3781,0.4716),"keywords":["1240","classroom 1240"]},
    "1245":{"name":"Classroom 1245","floor":1,"dept":"College","type":"classroom","x":0.1843,"y":0.436,"door":(0.4151,0.3974),"keywords":["1245","classroom 1245"]},
    "1246":{"name":"Computer Room 1246","floor":1,"dept":"University","type":"lab","x":0.3393,"y":0.519,"door":(0.4633,0.4716),"keywords":["1246","computer room 1246"]},
    "1253":{"name":"Classroom 1253","floor":1,"dept":"University","type":"classroom","x":0.2891,"y":0.581,"door":(0.4299,0.5371),"keywords":["1253","classroom 1253"]},
    "1254":{"name":"Human Factors Lab","floor":1,"dept":"University","type":"lab","x":0.3124,"y":0.261,"door":(0.3632,0.2795),"keywords":["1254","human factors lab","human factors","lab"]},
    "1256":{"name":"Computer Room 1256","floor":1,"dept":"University","type":"lab","x":0.3895,"y":0.519,"door":(0.5152,0.4716),"keywords":["1256","computer room 1256"]},
    "1258":{"name":"Modular 1258","floor":1,"dept":"University","type":"lab","x":0.4419,"y":0.519,"door":(0.5745,0.4716),"keywords":["1258","modular 1258"]},
    "1262":{"name":"Modular 1262","floor":1,"dept":"University","type":"lab","x":0.4996,"y":0.519,"door":(0.6264,0.4716),"keywords":["1262","modular 1262"]},
    "1263":{"name":"Classroom 1263","floor":1,"dept":"University","type":"classroom","x":0.6045,"y":0.519,"door":(0.6338,0.5371),"keywords":["1263","classroom 1263"]},
    "1264":{"name":"Seminar 1264","floor":1,"dept":"University","type":"classroom","x":0.2891,"y":0.519,"door":(0.4188,0.4716),"keywords":["1264","seminar 1264"]},
    "1269":{"name":"Center for Engineering Ed","floor":1,"dept":"University","type":"lab","x":0.9341,"y":0.261,"door":(0.8154,0.3974),"keywords":["1269","center for engineering ed","center for engineering education","cee"]},
    "1272":{"name":"Classroom 1272","floor":1,"dept":"University","type":"classroom","x":0.391,"y":0.436,"door":(0.3781,0.5371),"keywords":["1272","classroom 1272"]},
    "1280":{"name":"Student Leadership Incubator","floor":1,"dept":"College","type":"office","x":0.0457,"y":0.408,"door":(0.1297,0.4148),"keywords":["1280","student leadership incubator","student leadership","incubator","sli"]},
    "1300":{"name":"Robotics Lab","floor":1,"dept":"Electrical/Computer Engineering","type":"lab","x":0.8142,"y":0.227,"door":(0.7339,0.2751),"keywords":["1300","robotics lab","robotics","mee 4900"]},
    "1311":{"name":"Geotech Lab","floor":1,"dept":"Civil/Environmental Engineering","type":"lab","x":0.8876,"y":0.102,"door":(0.7858,0.1135),"keywords":["1311","geotech lab"]},
    "1321":{"name":"Strength & Materials Lab","floor":1,"dept":"Mechanical/Industrial Engineering","type":"lab","x":0.7416,"y":0.052,"door":(0.6301,0.1135),"keywords":["1321","strength & materials lab"]},
    "1321A":{"name":"Asphalt Lab","floor":1,"dept":"Civil/Environmental Engineering","type":"lab","x":0.7116,"y":0.1135,"door":(0.7116,0.1135),"keywords":["1321a","asphalt lab"]},
    "1322":{"name":"Strength & Materials Lab 2","floor":1,"dept":"Mechanical/Industrial Engineering","type":"lab","x":0.6704,"y":0.138,"door":(0.6301,0.1921),"keywords":["1322","strength & materials lab 2"]},
    "1323":{"name":"Germano Computer Lab","floor":1,"dept":"Civil/Environmental Engineering","type":"lab","x":0.6704,"y":0.052,"door":(0.5337,0.1921),"keywords":["1323","germano computer lab"]},
    "1325":{"name":"Concrete Lab","floor":1,"dept":"Civil/Environmental Engineering","type":"lab","x":0.588,"y":0.052,"door":(0.5337,0.1293),"keywords":["1325","concrete lab"]},
    "1329":{"name":"Rock Mechanics","floor":1,"dept":"Mechanical/Industrial Engineering","type":"lab","x":0.4157,"y":0.131,"door":(0.4374,0.1572),"keywords":["1329","rock mechanics"]},
    "1330":{"name":"EE Micro Grid","floor":1,"dept":"Electrical/Computer Engineering","type":"lab","x":0.5169,"y":0.057,"door":(0.7858,0.2751),"keywords":["1330","ee micro grid"]},
    "1331":{"name":"Enchanced Oil Recovery","floor":1,"dept":"University","type":"lab","x":0.4157,"y":0.044,"door":(0.4374,0.0978),"keywords":["1331","enchanced oil recovery"]},
    "1340":{"name":"Capstone Design Space","floor":1,"dept":"College","type":"lab","x":0.6794,"y":0.261,"door":(0.6523,0.2751),"keywords":["1340","capstone design space","capstone","senior design","cen 4027"]},
    "1340A":{"name":"Capstone Design Space Annex","floor":1,"dept":"College","type":"lab","x":0.5634,"y":0.2795,"door":(0.5634,0.2795),"keywords":["1340a","capstone design space annex"]},
    "1342":{"name":"Room 1342","floor":1,"dept":"College","type":"lab","x":0.5056,"y":0.291,"door":(0.5115,0.3581),"keywords":["1342","room 1342"]},
    "1344":{"name":"Room 1344","floor":1,"dept":"College","type":"lab","x":0.5468,"y":0.227,"door":(0.5115,0.2795),"keywords":["1344","room 1344"]},
    "1350":{"name":"Campus Computer Lab","floor":1,"dept":"College","type":"lab","x":0.4157,"y":0.261,"door":(0.4225,0.2795),"keywords":["1350","campus computer lab","computer lab"]},
    "1355":{"name":"Thermal Science Lab","floor":1,"dept":"Mechanical/Industrial Engineering","type":"lab","x":0.1843,"y":0.132,"door":(0.2965,0.2166),"keywords":["1355","thermal science lab"]},
    "1356":{"name":"Materials Lab","floor":1,"dept":"Mechanical/Industrial Engineering","type":"lab","x":0.3423,"y":0.132,"door":(0.3632,0.2166),"keywords":["1356","materials lab"]},
    "1357":{"name":"Thermal System Lab","floor":1,"dept":"Mechanical/Industrial Engineering","type":"lab","x":0.1843,"y":0.046,"door":(0.2965,0.1354),"keywords":["1357","thermal system lab"]},
    "1358":{"name":"Instrumentation Lab","floor":1,"dept":"Mechanical/Industrial Engineering","type":"lab","x":0.3124,"y":0.046,"door":(0.3632,0.1467),"keywords":["1358","instrumentation lab"]},
    "1360":{"name":"System Integration Classroom","floor":1,"dept":"University","type":"classroom","x":0.1843,"y":0.261,"door":(0.2928,0.2795),"keywords":["1360","system integration classroom","system integration","classroom"]},
    "1367":{"name":"Cheme Machine Shop","floor":1,"dept":"Chemical Engineering","type":"lab","x":0.0457,"y":0.088,"door":(0.1297,0.1528),"keywords":["1367","cheme machine shop"]},
    "1375":{"name":"Restaurant","floor":1,"dept":"College","type":"amenity","x":0.0457,"y":0.317,"door":(0.1038,0.2969),"keywords":["1375","restaurant","food","cafe"]},
    "2128":{"name":"Student Lounge","floor":2,"dept":"College","type":"office","x":0.3124,"y":0.832,"door":(0.6153,0.821),"keywords":["2128","student lounge","lounge"]},
    "2130":{"name":"Cheme Biotech Lab","floor":2,"dept":"Chemical Engineering","type":"lab","x":0.2067,"y":0.832,"door":(0.5486,0.821),"keywords":["2130","cheme biotech lab","cheme biotech","biotech lab"]},
    "2132":{"name":"Cheme Research Lab","floor":2,"dept":"Chemical Engineering","type":"lab","x":0.0764,"y":0.832,"door":(0.4818,0.821),"keywords":["2132","cheme research lab"]},
    "2141":{"name":"Rock/Fluids Properties Lab","floor":2,"dept":"Petroleum Engineering","type":"lab","x":0.5169,"y":0.702,"door":(0.5189,0.7598),"keywords":["2141","rock/fluids properties lab","rock fluids","properties lab"]},
    "2145":{"name":"Reservoir Dynamics Teaching Lab","floor":2,"dept":"Petroleum Engineering","type":"lab","x":0.4157,"y":0.702,"door":(0.4448,0.7598),"keywords":["2145","reservoir dynamics teaching lab","reservoir dynamics","pete"]},
    "2147":{"name":"Petro Lab 2147","floor":2,"dept":"Petroleum Engineering","type":"lab","x":0.1139,"y":0.702,"door":(0.2891,0.821),"keywords":["2147","petro lab 2147"]},
    "2154":{"name":"Petro Lab","floor":2,"dept":"Petroleum Engineering","type":"lab","x":0.039,"y":0.702,"door":(0.2891,0.7598),"keywords":["2154","petro lab"]},
    "2200":{"name":"COES Admin Suite","floor":2,"dept":"College","type":"office","x":0.7715,"y":0.261,"door":(0.8154,0.4891),"keywords":["2200","coes admin suite","coes admin","dean office","administration"]},
    "2214":{"name":"Dean's Suite","floor":2,"dept":"College","type":"office","x":0.8154,"y":0.5939,"door":(0.8154,0.5939),"keywords":["2214","dean's suite","dean"]},
    "2215":{"name":"Characterization Lab","floor":2,"dept":"Chemical Engineering","type":"lab","x":0.3124,"y":0.702,"door":(0.3632,0.6987),"keywords":["2215","characterization lab"]},
    "2215B":{"name":"CBE Classroom","floor":2,"dept":"Civil/Environmental Engineering","type":"classroom","x":0.8154,"y":0.7598,"door":(0.8154,0.7598),"keywords":["2215b","cbe classroom"]},
    "2217":{"name":"Drilling Fluids Teaching Lab","floor":2,"dept":"Chemical Engineering","type":"lab","x":0.2067,"y":0.702,"door":(0.3632,0.7598),"keywords":["2217","drilling fluids teaching lab","drilling fluids","pete lab"]},
    "2224":{"name":"Petro Computational","floor":2,"dept":"Petroleum Engineering","type":"lab","x":0.2217,"y":0.408,"door":(0.3632,0.4279),"keywords":["2224","petro computational"]},
    "2229":{"name":"Student Services Suite","floor":2,"dept":"College","type":"office","x":0.4944,"y":0.261,"door":(0.8154,0.3406),"keywords":["2229","student services suite","student services","advising"]},
    "2241":{"name":"EE Circuits 2","floor":2,"dept":"Electrical/Computer Engineering","type":"lab","x":0.1438,"y":0.408,"door":(0.2965,0.4279),"keywords":["2241","ee circuits 2"]},
    "2241B":{"name":"CS Computer Lab","floor":2,"dept":"Computer Science","type":"lab","x":0.4374,"y":0.4279,"door":(0.4374,0.4279),"keywords":["2241b","cs computer lab"]},
    "2248":{"name":"CMR BIM Lab","floor":2,"dept":"Construction Management","type":"lab","x":0.3039,"y":0.2795,"door":(0.3039,0.2795),"keywords":["2248","cmr bim lab"]},
    "2248B":{"name":"Petro Teaching","floor":2,"dept":"Petroleum Engineering","type":"classroom","x":0.5189,"y":0.5677,"door":(0.5189,0.5677),"keywords":["2248b","petro teaching"]},
    "2249":{"name":"EE Circuits 1","floor":2,"dept":"Electrical/Computer Engineering","type":"lab","x":0.0539,"y":0.408,"door":(0.2313,0.4279),"keywords":["2249","ee circuits 1"]},
    "2249B":{"name":"CBE Simulations Lab","floor":2,"dept":"University","type":"lab","x":0.5189,"y":0.4279,"door":(0.5189,0.4279),"keywords":["2249b","cbe simulations lab"]},
    "2250":{"name":"CMR Computer Classroom","floor":2,"dept":"Construction Management","type":"classroom","x":0.0539,"y":0.088,"door":(0.2313,0.2795),"keywords":["2250","cmr computer classroom"]},
    "2271":{"name":"CE Fluids Mechanics","floor":2,"dept":"Mechanical/Industrial Engineering","type":"lab","x":0.4157,"y":0.408,"door":(0.593,0.4279),"keywords":["2271","ce fluids mechanics"]},
    "2274":{"name":"Petro Teaching Electric Drive","floor":2,"dept":"Petroleum Engineering","type":"classroom","x":0.2921,"y":0.553,"door":(0.4374,0.5677),"keywords":["2274","petro teaching electric drive"]},
    "2275":{"name":"EE Petro Absorbance","floor":2,"dept":"Petroleum Engineering","type":"lab","x":0.2217,"y":0.553,"door":(0.3632,0.5677),"keywords":["2275","ee petro absorbance"]},
    "2277":{"name":"EE Optics","floor":2,"dept":"Electrical/Computer Engineering","type":"lab","x":0.1438,"y":0.553,"door":(0.2965,0.5677),"keywords":["2277","ee optics"]},
    "2279":{"name":"EE Power","floor":2,"dept":"Electrical/Computer Engineering","type":"lab","x":0.0539,"y":0.553,"door":(0.2313,0.5677),"keywords":["2279","ee power"]},
    "2301":{"name":"Comp Sci Research Lab 2301","floor":2,"dept":"Computer Science","type":"lab","x":0.3632,"y":0.0786,"door":(0.3632,0.0786),"keywords":["2301","comp sci research lab 2301"]},
    "2302":{"name":"Comp Sci Research Lab 2302","floor":2,"dept":"Computer Science","type":"lab","x":0.6523,"y":0.0786,"door":(0.6523,0.0786),"keywords":["2302","comp sci research lab 2302"]},
    "2303":{"name":"Comp Sci Research Lab 2303","floor":2,"dept":"Computer Science","type":"lab","x":0.4596,"y":0.0786,"door":(0.4596,0.0786),"keywords":["2303","comp sci research lab 2303"]},
    "2304":{"name":"Comp Sci Teaching","floor":2,"dept":"Computer Science","type":"classroom","x":0.5189,"y":0.2533,"door":(0.5189,0.2533),"keywords":["2304","comp sci teaching"]},
    "2305":{"name":"Comp Sci Research Lab 2305","floor":2,"dept":"Computer Science","type":"lab","x":0.556,"y":0.0786,"door":(0.556,0.0786),"keywords":["2305","comp sci research lab 2305"]},
    "2307":{"name":"Comp Sci Research Lab 2307","floor":2,"dept":"Computer Science","type":"lab","x":0.5041,"y":0.0786,"door":(0.5041,0.0786),"keywords":["2307","comp sci research lab 2307"]},
    "2308":{"name":"Comp Sci Research Lab 2308","floor":2,"dept":"Computer Science","type":"lab","x":0.7487,"y":0.0786,"door":(0.7487,0.0786),"keywords":["2308","comp sci research lab 2308"]},
    "2309":{"name":"Comp Sci Research Lab 2309","floor":2,"dept":"Computer Science","type":"lab","x":0.6004,"y":0.0786,"door":(0.6004,0.0786),"keywords":["2309","comp sci research lab 2309"]},
    "2310":{"name":"Comp Sci Research Lab 2310","floor":2,"dept":"Computer Science","type":"lab","x":0.8451,"y":0.0786,"door":(0.8451,0.0786),"keywords":["2310","comp sci research lab 2310"]},
    "2355":{"name":"Materials & Manufacturing Lab","floor":2,"dept":"Mechanical/Industrial Engineering","type":"lab","x":0.1843,"y":0.088,"door":(0.3632,0.2341),"keywords":["2355","materials & manufacturing lab","materials","manufacturing","mme"]},
    "2399":{"name":"Mech CAD Classroom","floor":2,"dept":"Mechanical/Industrial Engineering","type":"classroom","x":0.6153,"y":0.2533,"door":(0.6153,0.2533),"keywords":["2399","mech cad classroom"]},
    "3020":{"name":"Pollution Control Lab","floor":3,"dept":"University","type":"lab","x":0.603,"y":0.69,"door":(0.6672,0.6987),"keywords":["3020","pollution control lab"]},
    "3025":{"name":"Pollution Control Lab II","floor":3,"dept":"University","type":"lab","x":0.4757,"y":0.69,"door":(0.5634,0.6987),"keywords":["3025","pollution control lab ii","pollution control","environmental lab"]},
    "3212":{"name":"Office 3212","floor":3,"dept":"University","type":"office","x":0.7858,"y":0.5371,"door":(0.7858,0.5371),"keywords":["3212","office 3212"]},
    "3228":{"name":"Office 3228","floor":3,"dept":"University","type":"office","x":0.8154,"y":0.4891,"door":(0.8154,0.4891),"keywords":["3228","office 3228"]},
    "3229":{"name":"Office 3229","floor":3,"dept":"University","type":"office","x":0.8154,"y":0.4279,"door":(0.8154,0.4279),"keywords":["3229","office 3229"]},
    "3230":{"name":"Office 3230","floor":3,"dept":"University","type":"office","x":0.6746,"y":0.5371,"door":(0.6746,0.5371),"keywords":["3230","office 3230"]},
    "3240":{"name":"Office 3240","floor":3,"dept":"University","type":"office","x":0.5634,"y":0.5371,"door":(0.5634,0.5371),"keywords":["3240","office 3240"]},
    "3252":{"name":"Office 3252","floor":3,"dept":"University","type":"office","x":0.6301,"y":0.4279,"door":(0.6301,0.4279),"keywords":["3252","office 3252"]},
    "3255":{"name":"ChE & EEvEG Suite","floor":3,"dept":"Civil/Environmental Engineering","type":"office","x":0.4195,"y":0.397,"door":(0.4374,0.3755),"keywords":["3255","che & eeveg suite","che","eveg","chemical engineering suite"]},
    "3258":{"name":"Office 3258","floor":3,"dept":"University","type":"office","x":0.5189,"y":0.4279,"door":(0.5189,0.4279),"keywords":["3258","office 3258"]},
    "3261":{"name":"ME & ISE Suite","floor":3,"dept":"Mechanical/Industrial Engineering","type":"office","x":0.1843,"y":0.397,"door":(0.3188,0.393),"keywords":["3261","me & ise suite","me","ise","mechanical industrial suite"]},
    "3265":{"name":"Office 3265","floor":3,"dept":"University","type":"office","x":0.4522,"y":0.4279,"door":(0.4522,0.4279),"keywords":["3265","office 3265"]},
    "3267":{"name":"Cheme Suite","floor":3,"dept":"Chemical Engineering","type":"office","x":0.5506,"y":0.25,"door":(0.5708,0.2795),"keywords":["3267","cheme suite","chemical engineering"]},
    "3275":{"name":"Office 3275","floor":3,"dept":"University","type":"office","x":0.3632,"y":0.4279,"door":(0.3632,0.4279),"keywords":["3275","office 3275"]},
    "3277":{"name":"Office 3277","floor":3,"dept":"University","type":"office","x":0.2965,"y":0.4279,"door":(0.2965,0.4279),"keywords":["3277","office 3277"]},
    "3280":{"name":"Office 3280","floor":3,"dept":"University","type":"office","x":0.2313,"y":0.4279,"door":(0.2313,0.4279),"keywords":["3280","office 3280"]},
    "3287":{"name":"PETE Suite","floor":3,"dept":"Petroleum Engineering","type":"office","x":0.5506,"y":0.397,"door":(0.6449,0.3755),"keywords":["3287","pete suite","petroleum engineering"]},
    "3297":{"name":"Dean's Seminar Suite","floor":3,"dept":"College","type":"classroom","x":0.8382,"y":0.69,"door":(0.8302,0.7162),"keywords":["3297","dean's seminar suite","dean seminar","seminar suite"]},
    "3305":{"name":"Office 3305","floor":3,"dept":"University","type":"office","x":0.7487,"y":0.0786,"door":(0.7487,0.0786),"keywords":["3305","office 3305"]},
    "3308":{"name":"Office 3308","floor":3,"dept":"University","type":"office","x":0.8006,"y":0.0786,"door":(0.8006,0.0786),"keywords":["3308","office 3308"]},
    "3311":{"name":"Shared Learning Lab","floor":3,"dept":"University","type":"lab","x":0.3723,"y":0.69,"door":(0.4744,0.7686),"keywords":["3311","shared learning lab"]},
    "3312":{"name":"Office 3312","floor":3,"dept":"University","type":"office","x":0.8525,"y":0.0786,"door":(0.8525,0.0786),"keywords":["3312","office 3312"]},
    "3314":{"name":"Office 3314","floor":3,"dept":"University","type":"office","x":0.8127,"y":0.088,"door":(0.6968,0.0786),"keywords":["3314","office 3314"]},
    "3315":{"name":"Office 3315","floor":3,"dept":"University","type":"office","x":0.4944,"y":0.088,"door":(0.5634,0.0786),"keywords":["3315","office 3315"]},
    "3319":{"name":"CME Suite","floor":3,"dept":"Construction Management","type":"office","x":0.4195,"y":0.25,"door":(0.4151,0.2795),"keywords":["3319","cme suite","construction management"]},
    "3319B":{"name":"Verandah","floor":3,"dept":"University","type":"lab","x":0.2817,"y":0.7686,"door":(0.2817,0.7686),"keywords":["3319b","verandah"]},
    "3321":{"name":"Mfg Industrial Systems","floor":3,"dept":"Construction Management","type":"lab","x":0.2217,"y":0.69,"door":(0.3484,0.6987),"keywords":["3321","mfg industrial systems"]},
    "3322":{"name":"CM Senior Project Lab","floor":3,"dept":"Construction Management","type":"lab","x":0.1843,"y":0.832,"door":(0.3558,0.7686),"keywords":["3322","cm senior project lab","cm senior project","construction management lab"]},
    "3323":{"name":"CM Detailing/Controls Lab","floor":3,"dept":"Construction Management","type":"lab","x":0.1438,"y":0.69,"door":(0.2817,0.6987),"keywords":["3323","cm detailing/controls lab"]},
    "3324":{"name":"COES HR / Finance","floor":3,"dept":"College","type":"office","x":0.2891,"y":0.2314,"door":(0.2891,0.2314),"keywords":["3324","coes hr / finance"]},
    "3325":{"name":"ECEE & CSE Suite","floor":3,"dept":"Electrical/Computer Engineering","type":"office","x":0.1843,"y":0.202,"door":(0.2965,0.2795),"keywords":["3325","ecee & cse suite","ecee","cse","electrical","computer science suite"]},
    "3325C":{"name":"CM Exterior Teaching","floor":3,"dept":"Construction Management","type":"classroom","x":0.4151,"y":0.6987,"door":(0.4151,0.6987),"keywords":["3325c","cm exterior teaching"]},
    "3325b":{"name":"Office 3325b","floor":3,"dept":"University","type":"office","x":0.252,"y":0.0873,"door":(0.252,0.0873),"keywords":["3325b","office 3325b"]},
    "3327":{"name":"Office 3327","floor":3,"dept":"University","type":"office","x":0.3188,"y":0.0873,"door":(0.3188,0.0873),"keywords":["3327","office 3327"]},
    "3329":{"name":"Office 3329","floor":3,"dept":"University","type":"office","x":0.1927,"y":0.1266,"door":(0.1927,0.1266),"keywords":["3329","office 3329"]},
    "3336":{"name":"Office 3336","floor":3,"dept":"University","type":"office","x":0.126,"y":0.1266,"door":(0.126,0.1266),"keywords":["3336","office 3336"]},
    "RR_F1_COMMONS":{"name":"Restroom (near The Commons)","floor":1,"x":0.2313,"y":0.3406,"keywords":["restroom","bathroom","toilet","wc","washroom"]},
    "RR_F1_ATRIUM":{"name":"Restroom (Cambre Atrium)","floor":1,"x":0.5967,"y":0.6507,"keywords":["restroom","bathroom","toilet","wc","washroom"]},
    "RR_F2_WEST":{"name":"Restroom (West, F2)","floor":2,"x":0.2313,"y":0.3406,"keywords":["restroom","bathroom","toilet","wc","washroom"]},
    "RR_F2_CENTER":{"name":"Restroom (Central, F2)","floor":2,"x":0.5967,"y":0.4891,"keywords":["restroom","bathroom","toilet","wc","washroom"]},
    "RR_F2_SOUTH":{"name":"Restroom (South, F2)","floor":2,"x":0.5967,"y":0.6507,"keywords":["restroom","bathroom","toilet","wc","washroom"]},
    "RR_F3_WEST":{"name":"Restroom (West, F3)","floor":3,"x":0.2313,"y":0.3406,"keywords":["restroom","bathroom","toilet","wc","washroom"]},
    "RR_F3_EAST":{"name":"Restroom (East, F3)","floor":3,"x":0.5967,"y":0.4891,"keywords":["restroom","bathroom","toilet","wc","washroom"]},
}

# ═══════════════════════════════════════════════════════════════
#  RESTROOMS
# ═══════════════════════════════════════════════════════════════
RESTROOMS = {
    "RR_F1_COMMONS": {"name":"Restroom (near The Commons)","floor":1,
                      "x":0.305,"y":0.464,
                      "keywords":["restroom","bathroom","toilet","wc","washroom"]},
    "RR_F1_ATRIUM":  {"name":"Restroom (Cambre Atrium)","floor":1,
                      "x":0.628,"y":0.760,
                      "keywords":["restroom","bathroom","toilet","wc","washroom"]},
    "RR_F2_WEST":    {"name":"Restroom (West Wing, F2)","floor":2,
                      "x":0.305,"y":0.440,
                      "keywords":["restroom","bathroom","toilet","wc","washroom"]},
    "RR_F2_CENTER":  {"name":"Restroom (Central, F2)","floor":2,
                      "x":0.628,"y":0.500,
                      "keywords":["restroom","bathroom","toilet","wc","washroom"]},
    "RR_F2_SOUTH":   {"name":"Restroom (South Corridor, F2)","floor":2,
                      "x":0.628,"y":0.680,
                      "keywords":["restroom","bathroom","toilet","wc","washroom"]},
    "RR_F3_WEST":    {"name":"Restroom (West Wing, F3)","floor":3,
                      "x":0.305,"y":0.460,
                      "keywords":["restroom","bathroom","toilet","wc","washroom"]},
    "RR_F3_EAST":    {"name":"Restroom (East Wing, F3)","floor":3,
                      "x":0.628,"y":0.460,
                      "keywords":["restroom","bathroom","toilet","wc","washroom"]},
}

# ═══════════════════════════════════════════════════════════════
#  CORRIDOR GRAPH NODES  — in white-space hallways only
#  Grid: 4 horizontal corridors × 4 vertical spines per floor
# ═══════════════════════════════════════════════════════════════
GRAPH_NODES = {
    "w_anchor_main":{"x":0.9229,"y":0.3799,"floor":1,"label":"PFT Main Entrance","type":"junction"},
    "w_anchor_south":{"x":0.4448,"y":0.9432,"floor":1,"label":"South Entrance","type":"junction"},
    "w_elev_a_1":{"x":0.4596,"y":0.31,"floor":1,"label":"Elevator A","type":"elevator"},
    "w_stair_b_1":{"x":0.2313,"y":0.31,"floor":1,"label":"Stair B","type":"stair"},
    "w_stair_c_1":{"x":0.5967,"y":0.6507,"floor":1,"label":"Stair C","type":"stair"},
    "w_cor_n1":{"x":0.2313,"y":0.1921,"floor":1,"label":"","type":"corridor"},
    "w_cor_n2":{"x":0.341,"y":0.1921,"floor":1,"label":"","type":"corridor"},
    "w_cor_n3":{"x":0.4225,"y":0.1921,"floor":1,"label":"","type":"corridor"},
    "w_cor_n4":{"x":0.493,"y":0.1921,"floor":1,"label":"","type":"corridor"},
    "w_cor_m1":{"x":0.1149,"y":0.3406,"floor":1,"label":"","type":"corridor"},
    "w_cor_m2":{"x":0.2313,"y":0.3406,"floor":1,"label":"","type":"corridor"},
    "w_cor_m3":{"x":0.341,"y":0.3406,"floor":1,"label":"","type":"corridor"},
    "w_cor_m4":{"x":0.4225,"y":0.3406,"floor":1,"label":"","type":"corridor"},
    "w_cor_m5":{"x":0.493,"y":0.3406,"floor":1,"label":"","type":"corridor"},
    "w_cor_m6":{"x":0.5634,"y":0.3406,"floor":1,"label":"","type":"corridor"},
    "w_cor_m7":{"x":0.6486,"y":0.3406,"floor":1,"label":"","type":"corridor"},
    "w_cor_m8":{"x":0.7265,"y":0.3406,"floor":1,"label":"","type":"corridor"},
    "w_cor_m9":{"x":0.8525,"y":0.3406,"floor":1,"label":"","type":"corridor"},
    "w_cor_s1":{"x":0.2313,"y":0.5066,"floor":1,"label":"","type":"corridor"},
    "w_cor_s2":{"x":0.3188,"y":0.5066,"floor":1,"label":"","type":"corridor"},
    "w_cor_s3":{"x":0.404,"y":0.5066,"floor":1,"label":"","type":"corridor"},
    "w_cor_s4":{"x":0.4855,"y":0.5066,"floor":1,"label":"","type":"corridor"},
    "w_cor_s5":{"x":0.5634,"y":0.5066,"floor":1,"label":"","type":"corridor"},
    "w_cor_s6":{"x":0.6486,"y":0.5066,"floor":1,"label":"","type":"corridor"},
    "w_cor_s7":{"x":0.7265,"y":0.5066,"floor":1,"label":"","type":"corridor"},
    "w_cor_c1":{"x":0.2313,"y":0.6507,"floor":1,"label":"","type":"corridor"},
    "w_cor_c2":{"x":0.3262,"y":0.6507,"floor":1,"label":"","type":"corridor"},
    "w_cor_c3":{"x":0.4225,"y":0.6507,"floor":1,"label":"","type":"corridor"},
    "w_cor_c4":{"x":0.5041,"y":0.6507,"floor":1,"label":"","type":"corridor"},
    "w_cor_c5":{"x":0.5967,"y":0.6507,"floor":1,"label":"","type":"corridor"},
    "w_cor_c6":{"x":0.6746,"y":0.6507,"floor":1,"label":"","type":"corridor"},
    "w_elev_a_2":{"x":0.4596,"y":0.31,"floor":2,"label":"Elevator A","type":"elevator"},
    "w_stair_b_2":{"x":0.2313,"y":0.31,"floor":2,"label":"Stair B","type":"stair"},
    "w_stair_c_2":{"x":0.5967,"y":0.6507,"floor":2,"label":"Stair C","type":"stair"},
    "w_cor2_n1":{"x":0.3632,"y":0.1266,"floor":2,"label":"","type":"corridor"},
    "w_cor2_n2":{"x":0.4596,"y":0.1266,"floor":2,"label":"","type":"corridor"},
    "w_cor2_n3":{"x":0.556,"y":0.1266,"floor":2,"label":"","type":"corridor"},
    "w_cor2_n4":{"x":0.6523,"y":0.1266,"floor":2,"label":"","type":"corridor"},
    "w_cor2_n5":{"x":0.7487,"y":0.1266,"floor":2,"label":"","type":"corridor"},
    "w_cor2_n6":{"x":0.8451,"y":0.1266,"floor":2,"label":"","type":"corridor"},
    "w_cor2_m1":{"x":0.2313,"y":0.3406,"floor":2,"label":"","type":"corridor"},
    "w_cor2_m2":{"x":0.3188,"y":0.3406,"floor":2,"label":"","type":"corridor"},
    "w_cor2_m3":{"x":0.4225,"y":0.3406,"floor":2,"label":"","type":"corridor"},
    "w_cor2_m4":{"x":0.5041,"y":0.3406,"floor":2,"label":"","type":"corridor"},
    "w_cor2_m5":{"x":0.5856,"y":0.3406,"floor":2,"label":"","type":"corridor"},
    "w_cor2_m6":{"x":0.682,"y":0.3406,"floor":2,"label":"","type":"corridor"},
    "w_cor2_m7":{"x":0.7858,"y":0.3406,"floor":2,"label":"","type":"corridor"},
    "w_cor2_m8":{"x":0.8821,"y":0.3406,"floor":2,"label":"","type":"corridor"},
    "w_cor2_s1":{"x":0.2313,"y":0.4891,"floor":2,"label":"","type":"corridor"},
    "w_cor2_s2":{"x":0.3188,"y":0.4891,"floor":2,"label":"","type":"corridor"},
    "w_cor2_s3":{"x":0.4151,"y":0.4891,"floor":2,"label":"","type":"corridor"},
    "w_cor2_s4":{"x":0.5041,"y":0.4891,"floor":2,"label":"","type":"corridor"},
    "w_cor2_s5":{"x":0.593,"y":0.4891,"floor":2,"label":"","type":"corridor"},
    "w_cor2_c1":{"x":0.2313,"y":0.6507,"floor":2,"label":"","type":"corridor"},
    "w_cor2_c2":{"x":0.3262,"y":0.6507,"floor":2,"label":"","type":"corridor"},
    "w_cor2_c3":{"x":0.4225,"y":0.6507,"floor":2,"label":"","type":"corridor"},
    "w_cor2_c4":{"x":0.5189,"y":0.6507,"floor":2,"label":"","type":"corridor"},
    "w_cor2_c5":{"x":0.6153,"y":0.6507,"floor":2,"label":"","type":"corridor"},
    "w_elev_a_3":{"x":0.4596,"y":0.31,"floor":3,"label":"Elevator A","type":"elevator"},
    "w_stair_b_3":{"x":0.2313,"y":0.31,"floor":3,"label":"Stair B","type":"stair"},
    "w_stair_c_3":{"x":0.5967,"y":0.6507,"floor":3,"label":"Stair C","type":"stair"},
    "w_cor3_n1":{"x":0.2965,"y":0.1266,"floor":3,"label":"","type":"corridor"},
    "w_cor3_n2":{"x":0.4299,"y":0.1266,"floor":3,"label":"","type":"corridor"},
    "w_cor3_n3":{"x":0.5634,"y":0.1266,"floor":3,"label":"","type":"corridor"},
    "w_cor3_n4":{"x":0.6968,"y":0.1266,"floor":3,"label":"","type":"corridor"},
    "w_cor3_n5":{"x":0.8302,"y":0.1266,"floor":3,"label":"","type":"corridor"},
    "w_cor3_m1":{"x":0.2313,"y":0.3406,"floor":3,"label":"","type":"corridor"},
    "w_cor3_m2":{"x":0.3262,"y":0.3406,"floor":3,"label":"","type":"corridor"},
    "w_cor3_m3":{"x":0.4374,"y":0.3406,"floor":3,"label":"","type":"corridor"},
    "w_cor3_m4":{"x":0.5411,"y":0.3406,"floor":3,"label":"","type":"corridor"},
    "w_cor3_m5":{"x":0.6449,"y":0.3406,"floor":3,"label":"","type":"corridor"},
    "w_cor3_m6":{"x":0.7487,"y":0.3406,"floor":3,"label":"","type":"corridor"},
    "w_cor3_m7":{"x":0.8525,"y":0.3406,"floor":3,"label":"","type":"corridor"},
    "w_cor3_s1":{"x":0.2313,"y":0.4891,"floor":3,"label":"","type":"corridor"},
    "w_cor3_s2":{"x":0.341,"y":0.4891,"floor":3,"label":"","type":"corridor"},
    "w_cor3_s3":{"x":0.4522,"y":0.4891,"floor":3,"label":"","type":"corridor"},
    "w_cor3_s4":{"x":0.5634,"y":0.4891,"floor":3,"label":"","type":"corridor"},
    "w_cor3_s5":{"x":0.6746,"y":0.4891,"floor":3,"label":"","type":"corridor"},
    "w_cor3_s6":{"x":0.7858,"y":0.4891,"floor":3,"label":"","type":"corridor"},
    "w_cor3_c1":{"x":0.2313,"y":0.6507,"floor":3,"label":"","type":"corridor"},
    "w_cor3_c2":{"x":0.3336,"y":0.6507,"floor":3,"label":"","type":"corridor"},
    "w_cor3_c3":{"x":0.4374,"y":0.6507,"floor":3,"label":"","type":"corridor"},
    "w_cor3_c4":{"x":0.5411,"y":0.6507,"floor":3,"label":"","type":"corridor"},
    "w_cor3_c5":{"x":0.6449,"y":0.6507,"floor":3,"label":"","type":"corridor"},
}

RAW_EDGES = [
    ("w_anchor_main","w_cor_m9","walk"),
    ("w_anchor_south","w_cor_c3","walk"),
    ("w_elev_a_1","w_cor_m4","walk"),
    ("w_elev_a_1","w_cor_n3","walk"),
    ("w_stair_b_1","w_cor_m2","walk"),
    ("w_stair_b_1","w_cor_n1","walk"),
    ("w_stair_c_1","w_cor_c5","walk"),
    ("w_cor_n1","w_cor_n2","walk"),
    ("w_cor_n1","w_cor_m2","walk"),
    ("w_cor_n2","w_cor_n3","walk"),
    ("w_cor_n3","w_cor_n4","walk"),
    ("w_cor_n3","w_cor_m4","walk"),
    ("w_cor_m1","w_cor_m2","walk"),
    ("w_cor_m2","w_cor_m3","walk"),
    ("w_cor_m2","w_cor_s1","walk"),
    ("w_cor_m3","w_cor_m4","walk"),
    ("w_cor_m4","w_cor_m5","walk"),
    ("w_cor_m4","w_cor_s3","walk"),
    ("w_cor_m5","w_cor_m6","walk"),
    ("w_cor_m6","w_cor_m7","walk"),
    ("w_cor_m7","w_cor_m8","walk"),
    ("w_cor_m8","w_cor_m9","walk"),
    ("w_cor_m8","w_cor_s7","walk"),
    ("w_cor_s1","w_cor_s2","walk"),
    ("w_cor_s1","w_cor_c1","walk"),
    ("w_cor_s2","w_cor_s3","walk"),
    ("w_cor_s3","w_cor_s4","walk"),
    ("w_cor_s3","w_cor_c3","walk"),
    ("w_cor_s4","w_cor_s5","walk"),
    ("w_cor_s5","w_cor_s6","walk"),
    ("w_cor_s5","w_cor_c5","walk"),
    ("w_cor_s6","w_cor_s7","walk"),
    ("w_cor_c1","w_cor_c2","walk"),
    ("w_cor_c2","w_cor_c3","walk"),
    ("w_cor_c3","w_cor_c4","walk"),
    ("w_cor_c4","w_cor_c5","walk"),
    ("w_cor_c5","w_cor_c6","walk"),
    ("w_elev_a_2","w_cor2_m3","walk"),
    ("w_stair_b_2","w_cor2_m1","walk"),
    ("w_stair_c_2","w_cor2_c5","walk"),
    ("w_cor2_n1","w_cor2_n2","walk"),
    ("w_cor2_n2","w_cor2_n3","walk"),
    ("w_cor2_n2","w_cor2_m3","walk"),
    ("w_cor2_n3","w_cor2_n4","walk"),
    ("w_cor2_n4","w_cor2_n5","walk"),
    ("w_cor2_n5","w_cor2_n6","walk"),
    ("w_cor2_m1","w_cor2_m2","walk"),
    ("w_cor2_m1","w_cor2_s1","walk"),
    ("w_cor2_m2","w_cor2_m3","walk"),
    ("w_cor2_m3","w_cor2_m4","walk"),
    ("w_cor2_m3","w_cor2_s3","walk"),
    ("w_cor2_m4","w_cor2_m5","walk"),
    ("w_cor2_m5","w_cor2_m6","walk"),
    ("w_cor2_m5","w_cor2_s4","walk"),
    ("w_cor2_m6","w_cor2_m7","walk"),
    ("w_cor2_m7","w_cor2_m8","walk"),
    ("w_cor2_m8","w_cor2_s5","walk"),
    ("w_cor2_s1","w_cor2_s2","walk"),
    ("w_cor2_s1","w_cor2_c1","walk"),
    ("w_cor2_s2","w_cor2_s3","walk"),
    ("w_cor2_s3","w_cor2_s4","walk"),
    ("w_cor2_s3","w_cor2_c3","walk"),
    ("w_cor2_s4","w_cor2_s5","walk"),
    ("w_cor2_s4","w_cor2_c4","walk"),
    ("w_cor2_c1","w_cor2_c2","walk"),
    ("w_cor2_c2","w_cor2_c3","walk"),
    ("w_cor2_c3","w_cor2_c4","walk"),
    ("w_cor2_c4","w_cor2_c5","walk"),
    ("w_elev_a_3","w_cor3_m3","walk"),
    ("w_stair_b_3","w_cor3_m1","walk"),
    ("w_stair_c_3","w_cor3_c5","walk"),
    ("w_cor3_n1","w_cor3_n2","walk"),
    ("w_cor3_n2","w_cor3_n3","walk"),
    ("w_cor3_n2","w_cor3_m3","walk"),
    ("w_cor3_n3","w_cor3_n4","walk"),
    ("w_cor3_n4","w_cor3_n5","walk"),
    ("w_cor3_m1","w_cor3_m2","walk"),
    ("w_cor3_m1","w_cor3_s1","walk"),
    ("w_cor3_m2","w_cor3_m3","walk"),
    ("w_cor3_m3","w_cor3_m4","walk"),
    ("w_cor3_m3","w_cor3_s3","walk"),
    ("w_cor3_m4","w_cor3_m5","walk"),
    ("w_cor3_m5","w_cor3_m6","walk"),
    ("w_cor3_m5","w_cor3_s5","walk"),
    ("w_cor3_m6","w_cor3_m7","walk"),
    ("w_cor3_m7","w_cor3_s6","walk"),
    ("w_cor3_s1","w_cor3_s2","walk"),
    ("w_cor3_s1","w_cor3_c1","walk"),
    ("w_cor3_s2","w_cor3_s3","walk"),
    ("w_cor3_s3","w_cor3_s4","walk"),
    ("w_cor3_s3","w_cor3_c3","walk"),
    ("w_cor3_s4","w_cor3_s5","walk"),
    ("w_cor3_s4","w_cor3_c4","walk"),
    ("w_cor3_s5","w_cor3_s6","walk"),
    ("w_cor3_c1","w_cor3_c2","walk"),
    ("w_cor3_c2","w_cor3_c3","walk"),
    ("w_cor3_c3","w_cor3_c4","walk"),
    ("w_cor3_c4","w_cor3_c5","walk"),
    ("w_elev_a_1","w_elev_a_2","elevator"),
    ("w_elev_a_2","w_elev_a_3","elevator"),
    ("w_stair_b_1","w_stair_b_2","stair"),
    ("w_stair_b_2","w_stair_b_3","stair"),
    ("w_stair_c_1","w_stair_c_2","stair"),
    ("w_stair_c_2","w_stair_c_3","stair"),
]


def _build_adj():
    adj = {n: [] for n in GRAPH_NODES}
    seen = set()
    for a, b, et in RAW_EDGES:
        k = (min(a,b), max(a,b))
        if k in seen: continue
        seen.add(k)
        if et == "walk":
            na, nb = GRAPH_NODES[a], GRAPH_NODES[b]
            w = math.hypot(na['x']-nb['x'], na['y']-nb['y']) * SCALE
        else:
            w = ELEV_COST if et == "elevator" else STAIR_COST
        adj[a].append((b, w, et)); adj[b].append((a, w, et))
    return adj

ADJ = _build_adj()


def _nearest_node(x, y, floor):
    """Find the corridor node nearest to a door point."""
    best, bd = None, 1e9
    for nid, n in GRAPH_NODES.items():
        if n['floor'] != floor: continue
        d = math.hypot(n['x']-x, n['y']-y) * SCALE
        if d < bd: bd, best = d, nid
    return best, bd


def dijkstra(sx, sy, sf, sdx, sdy, ex, ey, ef, edx, edy):
    """
    Route from start room (sx,sy) through its door (sdx,sdy),
    along corridors, through destination door (edx,edy) to end room (ex,ey).
    sdx,sdy and edx,edy must lie on the corridor grid.
    """
    sn, sd = _nearest_node(sdx, sdy, sf)
    dn, dd = _nearest_node(edx, edy, ef)
    VS, VD = "__src__", "__dst__"
    # Door-to-corridor cost
    sd_cost = math.hypot(sdx-GRAPH_NODES[sn]['x'], sdy-GRAPH_NODES[sn]['y']) * SCALE
    dd_cost = math.hypot(edx-GRAPH_NODES[dn]['x'], edy-GRAPH_NODES[dn]['y']) * SCALE

    ext = {k: list(v) for k, v in ADJ.items()}
    ext[VS] = [(sn, sd_cost, "walk")]
    ext[VD] = []
    ext.setdefault(sn, []).append((VS, sd_cost, "walk"))
    ext.setdefault(dn, []).append((VD, dd_cost, "walk"))
    heap = [(0.0, VS, [VS])]; dist = {}
    while heap:
        cost, node, path = heapq.heappop(heap)
        if node in dist: continue
        dist[node] = cost
        if node == VD: return cost, path, ext
        for nbr, w, et in ext.get(node, []):
            if nbr not in dist:
                heapq.heappush(heap, (cost+w, nbr, path+[nbr]))
    return None, [], {}


def _nxy(nid, sx, sy, sf, ex, ey, ef):
    if nid == "__src__": return sx, sy, sf, "your start"
    if nid == "__dst__": return ex, ey, ef, "your destination"
    n = GRAPH_NODES[nid]
    return n['x'], n['y'], n['floor'], n['label']


def _rel_dir(pdx, pdy, cdx, cdy):
    if pdx == 0 and pdy == 0: return "straight"
    cross = pdx*cdy - pdy*cdx
    mag = math.hypot(pdx,pdy)*math.hypot(cdx,cdy) + 1e-9
    if abs(cross)/mag < 0.28: return "straight"
    return "left" if cross > 0 else "right"


def _init_dir(dx, dy):
    if abs(dx) >= abs(dy):
        return "right" if dx > 0 else "left"
    return "forward" if dy < 0 else "backward"


def build_payload(path, ext, sx,sy,sf, sdx,sdy, ex,ey,ef, edx,edy, sname,ename, sid,eid):
    VS, VD = "__src__","__dst__"
    et_map = {}
    for i in range(len(path)-1):
        a,b = path[i],path[i+1]
        for nbr,w,et in ext.get(a,[]):
            if nbr==b: et_map[(a,b)]=et; break

    # Build waypoints: src_center → src_door → corridor nodes → dst_door → dst_center
    raw_waypoints = []
    for nid in path:
        if nid == VS:
            # Start: room center
            raw_waypoints.append({"node_id":"__src__","x":sx,"y":sy,"floor":sf,"label":"start","node_type":"room"})
            # Then door (only if door != center)
            if abs(sdx-sx)>0.005 or abs(sdy-sy)>0.005:
                raw_waypoints.append({"node_id":"__src_door__","x":sdx,"y":sdy,"floor":sf,"label":"room exit","node_type":"door"})
        elif nid == VD:
            # Destination door first
            if abs(edx-ex)>0.005 or abs(edy-ey)>0.005:
                raw_waypoints.append({"node_id":"__dst_door__","x":edx,"y":edy,"floor":ef,"label":"room entrance","node_type":"door"})
            # Then destination center
            raw_waypoints.append({"node_id":"__dst__","x":ex,"y":ey,"floor":ef,"label":"destination","node_type":"room"})
        else:
            n = GRAPH_NODES[nid]
            raw_waypoints.append({"node_id":nid,"x":n['x'],"y":n['y'],"floor":n['floor'],
                                   "label":n['label'],"node_type":n['type']})

    steps = [f"Start at {sname} (Room {sid}, Floor {sf})"]
    pdx,pdy = 0.0,0.0
    i = 0
    while i < len(path)-1:
        a,b = path[i],path[i+1]
        et = et_map.get((a,b),"walk")
        ax,ay,af,_ = _nxy(a,sx,sy,sf,ex,ey,ef)
        bx,by,bf,blbl = _nxy(b,sx,sy,sf,ex,ey,ef)
        if et in ("elevator","stair"):
            verb = "elevator" if et=="elevator" else "stairs"
            ud = "up" if bf>af else "down"
            steps.append(f"Take the {verb} {ud} to Floor {bf}  ({blbl})")
            pdx,pdy = 0.0,0.0; i+=1; continue
        j = i+1; total_d = 0.0
        while j < len(path):
            pax,pay,paf,_ = _nxy(path[j-1],sx,sy,sf,ex,ey,ef)
            pbx,pby,pbf,_ = _nxy(path[j],sx,sy,sf,ex,ey,ef)
            if et_map.get((path[j-1],path[j]),"walk")!="walk" or paf!=pbf: break
            total_d += math.hypot(pax-pbx,pay-pby)*SCALE; j+=1
        ex2,ey2,_,end_lbl = _nxy(path[j-1],sx,sy,sf,ex,ey,ef)
        cdx,cdy = ex2-ax, ey2-ay
        dm = max(5,int(total_d))
        if i==0:
            steps.append(f"Exit room and head {_init_dir(cdx,cdy)} ~{dm} m along the corridor")
        else:
            turn = _rel_dir(pdx,pdy,cdx,cdy)
            if turn=="straight": steps.append(f"Continue straight ~{dm} m toward {end_lbl}")
            else:                steps.append(f"Turn {turn} and walk ~{dm} m toward {end_lbl}")
        pdx,pdy = cdx,cdy
        i = j-2 if j>i+1 else i; i+=1

    steps.append(f"You have arrived at {ename} (Room {eid})")
    return raw_waypoints, steps


def nearest_restrooms(x, y, floor, n=2):
    s = []
    for rid,r in RESTROOMS.items():
        if r['floor']!=floor: continue
        d = math.hypot(r['x']-x,r['y']-y)*SCALE
        s.append({"id":rid,"name":r['name'],"floor":r['floor'],
                  "x":r['x'],"y":r['y'],"dist_m":round(d,1)})
    s.sort(key=lambda r:r['dist_m']); return s[:n]


# ═══════════════════════════════════════════════════════════════
#  FLASK ROUTES
# ═══════════════════════════════════════════════════════════════
@app.route('/')
def index(): return render_template('index.html')

@app.route('/api/search')
def search():
    q = request.args.get('q','').lower().strip()
    if not q: return jsonify([])
    results = []
    for rid,info in ROOMS.items():
        sc = 0
        if q==rid.lower():              sc=100
        elif q in rid.lower():          sc=80
        elif q in info['name'].lower(): sc=70
        elif q in info.get('dept','').lower(): sc=50
        else:
            for kw in info.get('keywords',[]):
                if q in kw.lower(): sc=40; break
        if sc>0:
            results.append({'id':rid,'score':sc,'is_restroom':False,
                            **{k:info.get(k,'') for k in ('name','floor','dept','type','x','y')}})
    for rid,r in RESTROOMS.items():
        for kw in r['keywords']:
            if q in kw.lower():
                results.append({'id':rid,'score':65,'is_restroom':True,
                                'name':r['name'],'floor':r['floor'],
                                'dept':'Facility','type':'restroom',
                                'x':r['x'],'y':r['y']}); break
    results.sort(key=lambda r:-r['score']); return jsonify(results[:12])

@app.route('/api/room/<room_id>')
def get_room(room_id):
    if room_id in ROOMS: return jsonify({'id':room_id,**ROOMS[room_id]})
    if room_id in RESTROOMS:
        r=RESTROOMS[room_id]
        return jsonify({'id':room_id,'name':r['name'],'floor':r['floor'],
                        'dept':'Facility','type':'restroom','x':r['x'],'y':r['y']})
    return jsonify({'error':'Not found'}),404

@app.route('/api/navigate',methods=['POST'])
def navigate():
    data=request.get_json(); sid,eid=data.get('start'),data.get('end')
    if not sid or not eid: return jsonify({'error':'Missing'}),400
    if sid==eid: return jsonify({'error':'Same room'}),400

    def lk(rid):
        if rid in ROOMS:
            r=ROOMS[rid]
            door=r.get('door',(r['x'],r['y']))
            return r['x'],r['y'],r['floor'],r['name'],door[0],door[1]
        if rid in RESTROOMS:
            r=RESTROOMS[rid]
            return r['x'],r['y'],r['floor'],r['name'],r['x'],r['y']
        return None

    sc,ec=lk(sid),lk(eid)
    if not sc or not ec: return jsonify({'error':'Invalid room'}),404

    sx,sy,sf,sname,sdx,sdy = sc
    ex,ey,ef,ename,edx,edy = ec

    cost,path,ext=dijkstra(sx,sy,sf,sdx,sdy, ex,ey,ef,edx,edy)
    if not path: return jsonify({'error':'No path'}),500
    wps,steps=build_payload(path,ext, sx,sy,sf,sdx,sdy, ex,ey,ef,edx,edy, sname,ename,sid,eid)

    transitions=[]
    for i in range(len(path)-1):
        a,b=path[i],path[i+1]
        if a.startswith("__") or b.startswith("__"): continue
        na,nb=GRAPH_NODES.get(a),GRAPH_NODES.get(b)
        if na and nb and na['floor']!=nb['floor']:
            transitions.append({"from_floor":na['floor'],"to_floor":nb['floor'],
                                 "type":na['type'],"label":na['label']})
    nearby_rr=nearest_restrooms(ex,ey,ef)
    session.setdefault('history',[])
    entry={'start':sid,'end':eid,'start_name':sname,'end_name':ename}
    session['history']=[h for h in session['history'] if not(h['start']==sid and h['end']==eid)]
    session['history'].insert(0,entry); session['history']=session['history'][:10]
    session.modified=True
    return jsonify({'start':{'id':sid,'x':sx,'y':sy,'floor':sf,'name':sname},
                   'end':{'id':eid,'x':ex,'y':ey,'floor':ef,'name':ename},
                   'steps':steps,'waypoints':wps,'cost_metres':round(cost,1),
                   'same_floor':sf==ef,'floors_involved':sorted({sf,ef}),
                   'transitions':transitions,'nearby_restrooms':nearby_rr})

@app.route('/api/nearby_restrooms')
def api_nearby_restrooms():
    floor=int(request.args.get('floor',1))
    x=float(request.args.get('x',0.5)); y=float(request.args.get('y',0.5))
    return jsonify(nearest_restrooms(x,y,floor))

@app.route('/api/history')
def get_history(): return jsonify(session.get('history',[]))
@app.route('/api/history/clear',methods=['POST'])
def clear_history():
    session['history']=[]; session.modified=True; return jsonify({'status':'cleared'})
@app.route('/api/saved',methods=['GET'])
def get_saved(): return jsonify(session.get('saved',[]))
@app.route('/api/saved',methods=['POST'])
def save_location():
    data=request.get_json(); rid=data.get('room_id')
    info=ROOMS.get(rid) or RESTROOMS.get(rid)
    if not info: return jsonify({'error':'Not found'}),404
    session.setdefault('saved',[])
    if any(s['room_id']==rid for s in session['saved']): return jsonify({'status':'already_saved'})
    session['saved'].append({'room_id':rid,'name':info['name'],'floor':info['floor'],
                              'dept':info.get('dept','Facility'),'label':data.get('label',info['name'])})
    session.modified=True; return jsonify({'status':'saved'})
@app.route('/api/saved/<room_id>',methods=['DELETE'])
def unsave_location(room_id):
    if 'saved' in session:
        session['saved']=[s for s in session['saved'] if s['room_id']!=room_id]
        session.modified=True
    return jsonify({'status':'removed'})
@app.route('/api/rooms/floor/<int:floor_num>')
def rooms_by_floor(floor_num):
    return jsonify([{'id':rid,**info} for rid,info in ROOMS.items() if info['floor']==floor_num])

if __name__=='__main__': app.run(debug=True,port=5000)
