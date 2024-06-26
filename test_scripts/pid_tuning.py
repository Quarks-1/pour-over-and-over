import serial
import time
from simple_pid import PID

# Serial port configuration
arduino = serial.Serial(port='/dev/ttyACM0', baudrate=9600, timeout=.1) 
time.sleep(2)  # Wait for the serial connection to initialize
print('Connected')
# PID controller setup
pid = PID(70, 30, 500, setpoint=200)  # P=1.0, I=0.1, D=0.05, desired temperature=25°C
pid.sample_time = 0.5  # Update every 1 second
pid.output_limits = (0, 1)  # Output value will be between 0 and 1 (off/on)

def control_heating(element_state):
    # Send control command to Arduino
    arduino.write(b'1\n' if element_state else b'0\n')
    

while True:
    try:
        # Read temperature from serial
        # arduino.reset_input_buffer()
        line = arduino.readline().decode('utf-8').strip()
        # control_heating('heating_on')
        if line:  # If line is not empty
            # print(f'Line: {line}')
            current_temp = float(line.split('/')[1])
            print(f"Current Temperature: {current_temp}°F")
            
            # Compute PID output
            control = pid(current_temp)
            # Decide on the heating element state based on PID output
            heating_on = control >= 0.5  # Example logic to turn heating on/off
            # Send command to Arduino to control the heating element
            control_heating(heating_on)
            # Optional: Print the control decision
            print("Heating On" if heating_on else "Heating Off")
            
    except KeyboardInterrupt:
        print("Exiting...")
        break
    except ValueError:
        # In case of faulty serial data that cannot be converted to float
        print("Invalid data received.")
        continue

arduino.close()  # Close the serial connection when done
