from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from pourover.models import BrewProfile
import json, serial, time
from datetime import datetime, timedelta
# (pour type, water weight, flow rate, agitation level (low, medium, high))
class MyConsumer(WebsocketConsumer):
    group_name = 'pourover_group'
    channel_name = 'pourover_channel'
    
    profile = None
    printer = None
    arduino = None
    
    x, y, z = 0, 0, 0
    steps = []
    stepsTimes = []
    startTime = None
    
    def getTime(self):
        return (datetime.now() - self.startTime).total_seconds()

    def connect(self):
        async_to_sync(self.channel_layer.group_add)(
            self.group_name, self.channel_name
        )

        self.accept()

        # Connect to printer
        try:
            self.printer = printer()
        except serial.SerialException:
            printError('WARNING: PRINTER NOT CONNECTED')
            self.broadcast_message('Printer not connected. Please connect printer and reload page.')
            return
    
        try:
            self.arduino = serial.Serial(port='/dev/ttyACM0', baudrate=9600, timeout=.1) 
        except serial.SerialException:
            printError('WARNING: ARDUINO NOT CONNECTED')
            self.broadcast_message('Arduino not connected. Please connect Arduino and reload page.')
            return
        
        self.startTime = datetime.now()
        self.broadcast_message('Successfully connected to Printer and Arduino.')
        self.broadcast_data()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name, self.channel_name
        )
        if self.printer is not None:
            self.printer.close()
        else:
            printError('WARNING: PRINTER NOT CONNECTED')
            return

    def receive(self, **kwargs):
        if 'text_data' not in kwargs:
            printError('You must send text_data')
            return

        try:
            data = json.loads(kwargs['text_data'])
        except json.JSONDecoder:
            printError('invalid JSON sent to server')
            return
        print(data)
        if 'command' not in data:
            printError('command property not sent in JSON')
            return

        action = data['command']
        
        if action == 'profileSelect':
            if 'profile' not in data:
                printError('profile property not sent in JSON')
                return
            
            self.profile = BrewProfile.objects.get(id=data['profile'])
            print(f'Profile selected: {self.profile}')
            steps = parseSteps(self.profile.steps)
            self.broadcast_data()
            return

        if action == 'startBrew':
            x, y, z = self.printer.currPos()
            print(bcolors.OKBLUE + f'Current position: {x}, {y}, {z}' + bcolors.ENDC)
            self.received_start(data)
            return

        if action == "stopBrew":
            self.received_stop(data)
            return
        
        if action == "restartBrew":
            self.received_restart(data)
            return

        
        printError(f'Invalid action property: "{action}"')

################## To be filled in #######################
    def received_start(self, data):
        
        self.broadcast_data()
    
    def received_pause(self, data):
        self.broadcast_data()
    
    def received_resume(self, data):
        self.broadcast_data()
        
    def received_stop(self, data):
        self.broadcast_data()
        
    def received_restart(self, data):
        self.broadcast_data()
################################################

    def broadcast_data(self):
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                'type': 'broadcast_event',
                'message': ""
            }
        )
    
    def broadcast_message(self, error_message):
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                'type': 'broadcast_event',
                'message': json.dumps(error_message)
            }
        )
    def broadcast_event(self, event):
        self.send(text_data=event['message'])


class printer:
    def __init__(self):
        self.center = [127, 115, 0]
        self.ser = serial.Serial("/dev/ttyUSB0", 115200)
        # home printer
        self.ser.write(str.encode("G28 X Y\r\n"))
        # time.sleep(2)
        self.ser.write(str.encode("G0 X127 Y90 Z0 F3600\r\n")) # move to center
    
    def write(self, command):
        self.ser.write(str.encode(command + "\r\n"))

    def currPos(self) -> list[int, int, int]:
        self.ser.reset_input_buffer()
        self.ser.write(str.encode("M114\r\n"))
        x, y, z = 0, 0, 0
        for val in self.ser.readline().decode('utf-8').split(' '):
            print(val)
            if 'X' in val:
                x = int(val.strip('X:').split('.')[0])
            elif 'Y' in val:
                y = int(val.strip('Y:').split('.')[0])
            elif 'Z' in val:
                z = int(val.strip('Z:').split('.')[0])
            elif 'E' in val:
                break
        return [x, y, z]
        
    def close(self):
        self.ser.close()
        print(bcolors.OKGREEN + "Exiting..." + bcolors.ENDC)

# (pour type, water weight, flow rate, agitation level (low, medium, high))
def parseSteps(steps):
    parsed = []
    for step in steps.strip('][').split(','):
        temp = step.strip('"').split('/')
        temp[1] = int(temp[1])
        temp[2] = int(temp[2])
        parsed.append(temp)
    print(parsed)
    return parsed
    

def printError(error_message):
    print(bcolors.FAIL + '#'*len(error_message))
    print(bcolors.FAIL + error_message)
    print('#'*len(error_message) + bcolors.ENDC)

        
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'