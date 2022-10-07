import RPi.GPIO as GPIO
import dht11
import time,datetime,picamera,threading,signal,socket
import matplotlib.pyplot as plt
import numpy as np
from picamera import Color
from PIL import Image, ImageFont, ImageDraw
import firebase_admin
from firebase_admin import credentials, firestore, storage, messaging
from pyfcm import FCMNotification

camera = picamera.PiCamera()
host, port = "192.168.0.127", 1234
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cred = credentials.Certificate("weatherstation-key.json")
fs = firebase_admin.initialize_app(cred, {
'storageBucket': 'weatherstation-d0365.appspot.com'
})
threads = []
clients = []
tokens = ["eFzbf-KxRJq3tcnqBWbhOm:APA91bHJI6wQUBG6-56QEUBin4ssldeUzHHYOaVFfoG1VN1r5NkCsd67bsSRg_Qbtjd87Kpm9RAyz4wM1p45Lq4SpMLTc5bZfGQhkWe8lft3Ct7EOw2SAgRZ0PsV-NGc5J7ZoRbY93S-"]

# initialize GPIO
GPIO.setwarnings(True)
GPIO.setmode(GPIO.BCM)
GPIO.setup(21,GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
instance = dht11.DHT11(pin=21)

class ClientW():
    def __init__(self,ids,ip,tok):
        self.temp_list = []
        self.hum_list = []
        self.temp_reg = 0
        self.id = ids
        self.addr = ip
        self.token = tok
    def get_token(self):
        return self.token
    def get_ID(self):
        return self.id
    def get_addr(self):
        return self.addr
    def empty_lists(self):
        self.temp_list.clear()
        self.hum_list.clear()
    def add_temp(self,temp):
        self.temp_list.append(temp)
    def add_hum(self,hum):
        self.hum_list.append(hum)
    def get_temp(self):
        return self.temp_list
    def get_hum(self):
        return self.hum_list
    def register_temps(self):
        global threads,clients
        if (self.temp_reg == 0):
            self.temp_reg = 1
            self.empty_lists()
            t = ThreadWorker(self.id)
            t.start()
            threads.append(t)
        else:
            self.temp_reg = 0
            for th in threads:
                if (th.get_clientID() == self.id) and (isinstance(th,ThreadWorker)):
                    th.shutdown_flag.set()
                threads.remove(th)
                break
            #to move into a separate thread - blocking
            x = np.arange(0, (len(self.get_temp()))*10,10)
            y = np.array(self.get_temp())
            plt.plot(x,y)
            plt.xlabel('time (s)')
            plt.ylabel('temperature (C)')
            plt.title('Temperature in specified interval.')
            filename = getFileName()
            filename = filename.replace('jpg','_resultfigure.png')
            plt.savefig(filename)
            print('stat figure saved --')
            url = upload_to_firebase(filename,"statistics/")
            sendPush("statistics",url,self.get_token())
            sendNotification("WeatherApp retrieved statistics", url, self.get_token())
         
            
def sendPush(title, msg, registration_token, dataObject=None):
#     message = messaging.MulticastMessage(
#         notification=messaging.Notification(
#             title=title,
#             body=msg
#         ),
#         data=dataObject,
#         tokens=registration_token,
#     )
#     response = messaging.send_multicast(message)
    message = messaging.Message(
    data={
        'title': title,
        'msg': msg,
    },
    token=registration_token,
    )
    response = messaging.send(message)
    print('Successfully sent message:', response)
    
def sendNotification(title,msg, registration_id, dataObject=None):
    push_service = FCMNotification(api_key="AAAAeoYdJWQ:APA91bFz3wdhUVZfGz-9xW6Qse5teMVE8MRfaMlFnwxLuhzbgZCCroNXTsH3BEAq9t1liOXazVjGC6Mhi3XdRz0mlS4aOXhQpXRmNaExD7wEV5V2GCf3WPal8usYRK---MgKOGX_VtVR")
    message_title = title
    message_body = msg
    result=push_service.notify_single_device(registration_id=registration_id, message_title=message_title, message_body=message_body)
    print (result)         
         
def upload_to_firebase(filename, location):
    db = firestore.client()
    bucket = storage.bucket()
    blob = bucket.blob(location+filename)
    blob.upload_from_filename(filename)
    url = blob.generate_signed_url(datetime.timedelta(seconds=3600), method='GET')
    print ("uploaded photo to firebase in:" +url)
    return url
              
        
class ThreadWorker(threading.Thread):
    def __init__(self,ids):
        threading.Thread.__init__(self)
        self.shutdown_flag = threading.Event()
        self.clientID = ids
    def get_clientID(self):
        return self.clientID
    def run(self):
        global clients
        try:
            print('Thread #%s started.' % self.ident)
            while not self.shutdown_flag.is_set():
                result = instance.read()
                if result.is_valid():
                    for cli in clients:
                        if (cli.get_ID()==self.clientID):
                            cli.add_temp(result.temperature)
                            cli.add_hum(result.humidity)
                            print("----------DEBUG----------")
                            print(cli.get_temp())
                            print(cli.get_hum())
                time.sleep(10)
            print('Thread #%s stopped.' % self.ident)
        except KeyboardInterrupt:
            print("Cleanup")
            GPIO.cleanup()
            return

class MainThread(threading.Thread):
    def __init__(self,ids):
        threading.Thread.__init__(self)
        self.shutdown_flag = threading.Event()
        self.clientID = ids
    def get_clientID(self):
        return self.clientID
    def run(self):
        global threads
        try:
            print('Thread #%s started.' % self.ident)
            result = instance.read()
            if result.is_valid():
                print("Last valid input: " + str(datetime.datetime.now()))
                print("Temperature: %-3.1f C" % result.temperature)
                print("Humidity: %-3.1f %%" % result.humidity)
                fln = take_photo_with_stamp(result.temperature,result.humidity)
                url = upload_to_firebase(fln,"images/")
                token = ""
                for ci in clients:
                    if (ci.get_ID() == self.get_clientID()):
                        token = ci.get_token()
                        break
                sendPush("image", url, token)
                sendNotification("WeatherApp retrieved photo", url, token)
            threads.remove(self)
            print('Thread #%s stopped.' % self.ident)
        except KeyboardInterrupt:
            print("Cleanup")
            GPIO.cleanup()

class ServiceExit(Exception):
    """
    Custom exception which is used to trigger the clean exit
    of all running threads and the main program.
    """
    pass
def service_shutdown(signum, frame):
    print('Caught signal %d' % signum)
    raise ServiceExit


def getFileName():
    return datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S.jpg")

def take_photo_with_stamp(temp,hum):
    global camera
    camera.shutter_speed = 0
    camera.exposure_mode = 'auto'
    camera.ISO = 200
    camera.exposure_compensation = 25
    camera.awb_mode = 'auto'
    ann_str="Temperature: %-3.1f C" % temp + "\nHumidity: %-3.1f %%" % hum
    #camera.annotate_text = ann_str
    #camera.annotate_foreground = Color('black')
    #camera.annotate_background = Color('white')
    time.sleep(3)
    filename = getFileName()
    camera.resolution=(1920,1080)
    camera.capture("/home/pi/Documents/AndroidThings/teamproject/DHT11_Python-master/"+filename)
    print ("Picture saved at ISO: ", camera.ISO)
    my_image = Image.open(filename)
    title_font = ImageFont.truetype('times.ttf', 50)
    image_editable = ImageDraw.Draw(my_image)
    image_editable.text((10,950), ann_str, (237, 230, 211), font=title_font)
    filename = filename.replace('jpg','_result.jpg')
    my_image.save(filename)
    #implement firebase upload
    return filename

def main():
    global clients,threads
    result = instance.read()
    signal.signal(signal.SIGTERM, service_shutdown)
    signal.signal(signal.SIGINT, service_shutdown)
    try:
        try:
            sock.bind((host, port))
        finally:
            pass
        sock.listen(10) # how many connections can it receive at one time
        print ("Start Listening...")
        client_count = 0
        while True:
            print("Waiting for next client..")
            conn, addr = sock.accept()
            print ("client with address: "+str(addr[0]))
            #check if client already exists or create a new one based on ip address
            #for ci in clients:
            #    print(str(ci.get_addr()) +" " + str(addr[0]))
            #    if (ci.get_addr() == addr[0]):
            #        print("hello again")
            #        cl = ci
            #        break
            #    else:
            #        cl = ClientW(client_count,addr[0])
            #        clients.append(cl)
            #        client_count+=1
            #if there are no clients add the first one
            #if (len(clients)==0):
            #   cl = ClientW(client_count,addr[0])
            #    clients.append(cl)
            #   client_count+=1
            data = conn.recv(1024)
            partialdata = data.decode("utf-8")
            res = partialdata.split(" ")
            print ("Received this token: ")
            for ci in clients:
                #print(str(ci.get_addr()) +" " + str(addr[0]))
                if (ci.get_token() == res[0]):
                    print("hello again")
                    cl = ci
                    break
                else:
                    cl = ClientW(client_count,addr[0],res[0])
                    clients.append(cl)
                    client_count+=1
            #if there are no clients add the first one
            if (len(clients)==0):
                cl = ClientW(client_count,addr[0],res[0])
                clients.append(cl)
                client_count+=1
            print(res[0]+"\n")
            print ("Received this data: ")
            print(res[1])
            if res[1] == "sendphoto":
                t = MainThread(cl.get_ID())
                t.start()
                threads.append(t)
                reply = "Success"
                conn.send(reply.encode("utf-8"))
                conn.close()
                print ("-----------------------------")
            elif res[1] == "statistics":
                cl.register_temps()
                reply = "Success"
                conn.send(reply.encode("utf-8"))
                conn.close()
            else:
                reply = "Failed"
                conn.send(reply.encode("utf-8"))
                conn.close()
                print ("-----------------------------")
        sock.close()
    except (ServiceExit,KeyboardInterrupt):
        for t in threads:
            t.join()
            t.shutdown_flag.set()
        print('Exiting main program')
        sock.close()
    
if __name__ == '__main__':
    main()