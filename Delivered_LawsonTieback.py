import requests, json, time, os, sys, glob, csv, shutil
from multiprocessing import Queue
from datetime import datetime
from pytz import timezone


vouchernums=[]
vendornums=[]
invoicenums=[]
status=[]
process_level=[]

headers = {'content-type': 'application/json'}
dir_path = os.path.dirname(os.path.realpath(__file__))
est = timezone('US/Eastern')

print("Current directory path is " + dir_path)

currenttime = time.strftime("%Y%m%d_%H%M")

datetime.now(est).strftime("%m/%d/%Y %H:%M:%S")

def login():
    login_url = 'https://applications.filebound.com/v3/login?fbsite=https://burriswebdocs.filebound.com'
    data = {
        'username': 'lawsontieback',
        'password': 'YourSecretPasswordGoesHere'
    }
    r = requests.post(login_url, data)
    guid = r.json()
    return(guid)

global guid
guid = login()
#print(guid)


def findCSVs():
    """
    Returns a list of the CSVs
    """
    global processed
    processed = dir_path + '/completed/' + currenttime + '/'
    global incoming
    incoming = dir_path + '/incoming/'
    #Check and see if we have an incoming and a completed folder
    if not os.path.exists(incoming):
        os.makedirs(incoming)
        print('No incoming folder found. Creating it for future use and exiting for now')
    incomingfilecount = glob.glob(incoming + '/*.csv')
    #print(len(incomingfilecount))
    if len(incomingfilecount) == 0:
        print('\n' + datetime.now(est).strftime("%m/%d/%Y %H:%M:%S") + ' - No CSV file in {}\n'.format(incoming))
    if len(incomingfilecount) >= 1:
        print(datetime.now(est).strftime("%m/%d/%Y %H:%M:%S") + ' - CSV file found!\n')
    #If there is an incoming folder, go through all of its CSVs
        return(incomingfilecount)


def getfields(vendorno, invoiceno, r):
    fileId = data[0]['fileId']
    poststring = 'https://applications.filebound.com/v3/files/{}/?fbsite=burriswebdocs.filebound.com&guid={}'.format(fileId, guid)
    r = requests.get(poststring)
    data = r.json()
    return(data)





def assemblequery1(path_to_csv_file):
    """
    Creates a datastream from the CSVs
    found in the above function
    """
    with open(path_to_csv_file) as currentfile:
        readcontents = csv.DictReader(currentfile, delimiter='|')
        for row in readcontents:
            vouchernums.append(row['voucher_number'])
            vendornums.append(row['vendor_number'])
            invoicenums.append(row['invoice'])
            status.append(row['status'])
            process_level.append(row['process_level'])
            wfstatus = 'Complete'

new_CSVs = findCSVs()

if bool(new_CSVs) == True:
    for i in new_CSVs:
        busy_i = i + '.processed'
        os.rename(i, busy_i)
        assemblequery1(busy_i)





succ = []
err = []
notthere = []



amnt = len(vouchernums)

for i in range(len(vouchernums)):
    #We query on these values
    vendorno = vendornums[i]
    invoiceno = invoicenums[i]
    
    
    
    #We will work with these later
    voucherno = vouchernums[i]
    processno = process_level[i]
    statusno = status[i]
    wfstatus = 'Complete'
    
    querystring = 'https://applications.filebound.com/v3/files/?filter=ProjectID_55,F2_{},F5_{}&fbsite=burriswebdocs.filebound.com&guid={}'.format(vendorno, invoiceno, guid)
    r = requests.get(querystring)
    if r.status_code == 200:
        print(datetime.now(est).strftime("%m/%d/%Y %H:%M:%S") + ' - Querying {} of {}: VendorNo is {}, InvoiceNo is {}'.format(i+1, amnt, vendorno, invoiceno))
        if len(r.text) > 20:
            print(datetime.now(est).strftime("%m/%d/%Y %H:%M:%S") + ' - Found!')
            data = json.loads(r.text)
            fileId = data[0]['fileId']
            URI = 'https://applications.filebound.com/v3/files/{}/?fbsite=burriswebdocs.filebound.com&guid={}'.format(fileId, guid)
            r = requests.get(URI)
            data = json.loads(r.text)
            data['field'][1] = voucherno
            data['field'][7] = processno
            data['field'][8] = statusno
            data['field'][20] = wfstatus
            post_string = json.dumps(data)
            #print('Im not POSTing, but this is what I would have posted.')
            print(datetime.now(est).strftime("%m/%d/%Y %H:%M:%S") + ' - ATTEMPTING POST NOW!!!')
            URI = 'https://applications.filebound.com/v3/files/{}/?fbsite=burriswebdocs.filebound.com&guid={}'.format(fileId, guid)
            boom = requests.post(URI, post_string, headers = headers)
            if boom.status_code == 200:
                print(datetime.now(est).strftime("%m/%d/%Y %H:%M:%S") + ' - SUCCESSFUL POST to FileID {} with Voucher Number {}, Vendor Number {}, and Invoice Number {}=n'.format(fileId, voucherno, vendorno, invoiceno))
                #print(datetime.now(est).strftime("%m/%d/%Y %H:%M:%S") + ' - Added to success log\n')
                succ.append(voucherno)
            else:
                print(datetime.now(est).strftime("%m/%d/%Y %H:%M:%S") + ' - PROBLEMATIC POST FileID {} with Voucher Number {}, Vendor Number {}, and Invoice Number {}\n'.format(fileId, voucherno, vendorno, invoiceno))
                #print(datetime.now(est).strftime("%m/%d/%Y %H:%M:%S") + ' - Added to error log\n')
                err.append(voucherno)
        else:
            print(datetime.now(est).strftime("%m/%d/%Y %H:%M:%S") + ' - Nothing to update\n')            
            notthere.append(voucherno)
            #print(datetime.now(est).strftime("%m/%d/%Y %H:%M:%S") + ' - Added to not-present log\n')
    else:
        print(datetime.now(est).strftime("%m/%d/%Y %H:%M:%S") + ' - Network error!\n')
        #print(datetime.now(est).strftime("%m/%d/%Y %H:%M:%S") + ' - Added to error log\n')
        err.append(voucherno)




#Write out reports!



#House cleaning!
print(datetime.now(est).strftime("%m/%d/%Y %H:%M:%S") + ' - Moving data files from {} to {}'.format(incoming, processed))
if not os.path.exists(processed):
    os.makedirs(processed)

renamelist = glob.glob(incoming + '/*csv.processed')
for item in renamelist:
    shutil.move(item, processed)



if len(err) > 0:
    print(datetime.now(est).strftime("%m/%d/%Y %H:%M:%S") + ' - Writing problematic vouchers and successful vouchers to text files.')
    review_vouchers = open(processed + '/review_vouchers.txt', 'w')
    for item in err:
        review_vouchers.write(item+'\n')
    review_vouchers.close()

if len(succ) > 0:
    updated_vouchers = open(processed + '/updated_vouchers.txt', 'w')
    for item in succ:
        updated_vouchers.write(item+'\n')
    updated_vouchers.close()

print('\n' + datetime.now(est).strftime("%m/%d/%Y %H:%M:%S") + ' - Successfully completed run!')
