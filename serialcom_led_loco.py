import serial
import time

if __name__ == '__main__':
    ser = serial.Serial('/dev/ttyACM0',9600, timeout=1)
    ser.flush()
    
    while True:
        ser.write(b"frontleft\n")
        time.sleep(1)
        ser.write(b"midleft\n")
        time.sleep(1)
        ser.write(b"backleft\n")
        time.sleep(1)
        ser.write(b"frontright\n")
        time.sleep(1)
        ser.write(b"midright\n")
        time.sleep(1)
        ser.write(b"backright\n")
        time.sleep(1)
        ser.write(b"all\n")
        time.sleep(1)
        ser.write(b"off\n")
        time.sleep(1)