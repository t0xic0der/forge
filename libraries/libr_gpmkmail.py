import sqlite3, hashlib, time, rsa
from libraries.libr_fgconfig import dataunit, timedata

def convhash(textobjc):
    textobjc = textobjc.encode("utf-8")
    texthash = hashlib.sha512(textobjc).hexdigest()
    return texthash

def fetckeys(grupiden):
    database = sqlite3.connect(dataunit["clouduse"]["path"])
    acticurs = database.cursor()
    qurytext = "select pubkeynn, pubkeyee from grupinfo where grupiden = '" + str(grupiden) + "'"
    recvobjc = acticurs.execute(qurytext)
    recvobjc = recvobjc.fetchall()
    pubkeynn = int(recvobjc[0][0])
    pubkeyee = int(recvobjc[0][1])
    database.close()
    publckey = rsa.PublicKey(pubkeynn, pubkeyee)
    return publckey

def fencrypt(textobjc, publckey):
    textbyte = textobjc.encode("utf-8")
    textencr = rsa.encrypt(textbyte, publckey)
    encrstrg = ""
    for indx in textencr:
        encrstrg = encrstrg + str(indx) + "-"
    return encrstrg

def sendmail(subjtext, conttext, srceuser, grupiden):
    isitrmov = "false"
    timestmp = str(time.time())
    pubkeysd = fetckeys(grupiden)                   # Fetches the sender's public key for storing in SENT MAIL
    subjensd = fencrypt(subjtext, pubkeysd)         # Encrypts the SUBJECT with sender's public key for SENT MAIL
    contensd = fencrypt(conttext, pubkeysd)         # Encrypts the CONTENT with sender's public key for SENT MAIL
    textobjc = subjtext + "@" + timestmp
    mailiden = convhash(textobjc)
    database = sqlite3.connect(dataunit["clouduse"]["path"])
    acticurs = database.cursor()
    qurytext = "insert into grupmail values (" + \
               "'" + str(mailiden) + "', " + \
               "'" + str(grupiden) + "', " + \
               "'" + str(subjensd) + "', " + \
               "'" + str(contensd) + "', " + \
               "'" + str(srceuser) + "', " + \
               "'" + str(timestmp) + "', " + \
               "'" + str(isitrmov) + "') "
    acticurs.execute(qurytext)
    database.commit()

def timeconv(timestmp):
    timelist = list(time.gmtime(timestmp))
    timedict = {
        "form": "GMT",
        "year": str(timelist[0]),
        "mont": timedata["montlist"][str(timelist[1])],
        "date": str(timelist[2]),
        "hour": str(timelist[3]),
        "mins": str(timelist[4]),
        "secs": str(timelist[5]),
        "wday": timedata["weeklist"][str(timelist[6])]
    }
    return timedict

def readkeys(grupiden,username):
    database = sqlite3.connect(dataunit["clouduse"]["path"])
    acticurs = database.cursor()
    qurytext = "select useriden from grupteam where " + \
               "username = '" + str(username) + "' and " + \
               "grupiden = '" + str(grupiden) + "'"
    recvobjc = acticurs.execute(qurytext)
    recvobjc = recvobjc.fetchall()
    useriden = str(recvobjc[0][0])
    database.close()
    database = sqlite3.connect(dataunit["localuse"]["path"])
    acticurs = database.cursor()
    qurytext = "select prikeynn, prikeyee, prikeydd, prikeypp, prikeyqq from gruploca where " + \
               "useriden = '" + str(useriden) + "' and grupiden = '" + str(grupiden) + "'"
    recvobjc = acticurs.execute(qurytext)
    recvobjc = recvobjc.fetchall()
    prvkeynn = int(recvobjc[0][0])
    prvkeyee = int(recvobjc[0][1])
    prvkeydd = int(recvobjc[0][2])
    prvkeypp = int(recvobjc[0][3])
    prvkeyqq = int(recvobjc[0][4])
    database.close()
    privtkey = rsa.PrivateKey(prvkeynn, prvkeyee, prvkeydd, prvkeypp, prvkeyqq)
    return privtkey

def fdecrypt(encstrim, privtkey):
    encstrim = encstrim.split("-")
    bytestrg = b""
    for indx in encstrim:
        if indx != "":
            bytestrg = bytestrg + bytes([int(indx)])
    try:
        decrbyte = rsa.decrypt(bytestrg, privtkey)
        decrstrg = decrbyte.decode("utf-8")
    except rsa.DecryptionError:
        decrstrg = "Message integrity compromised - Decryption failed!"
    return decrstrg

def mailread(grupiden, mailiden, username):
    privtkey = readkeys(grupiden, username)
    database = sqlite3.connect(dataunit["clouduse"]["path"])
    acticurs = database.cursor()
    qurytext = "select subjtext, conttext, srceuser, timestmp from grupmail where " + \
               "mailiden = '" + str(mailiden) + "' and isitrmov = 'false'"
    recvobjc = acticurs.execute(qurytext)
    recvobjc = recvobjc.fetchall()
    subjdecr = fdecrypt(recvobjc[0][0], privtkey)
    contdecr = fdecrypt(recvobjc[0][1], privtkey)
    interact = recvobjc[0][2]
    timeinfo = timeconv(float(recvobjc[0][3]))
    database.close()
    maildict = {
        "mailiden": mailiden, "timedata": timeinfo, "interact": interact,
        "subjtext": subjdecr, "conttext": contdecr,
    }
    return maildict

def fetcmail(grupiden, username):
    privtkey = readkeys(grupiden, username)
    database = sqlite3.connect(dataunit["clouduse"]["path"])
    acticurs = database.cursor()
    qurytext = "select mailiden, subjtext, conttext, srceuser, timestmp from grupmail where " + \
               "grupiden = '" + str(grupiden) + "' and isitrmov = 'false'"
    recvobjc = acticurs.execute(qurytext)
    recvobjc = recvobjc.fetchall()
    mailcoll = []
    for indx in range(len(recvobjc)):
        mailiden = recvobjc[indx][0]
        subjdecr = fdecrypt(recvobjc[indx][1], privtkey)
        contdecr = fdecrypt(recvobjc[indx][2], privtkey)
        srceuser = recvobjc[indx][3]
        timeinfo = timeconv(float(recvobjc[indx][4]))
        singmail = {
            "subjtext": subjdecr, "conttext": contdecr,
            "srceuser": srceuser, "timedata": timeinfo,
            "mailiden": mailiden,
        }
        mailcoll.append(singmail)
    database.close()
    return mailcoll