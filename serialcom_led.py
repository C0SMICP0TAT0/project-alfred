import serial
import time

if __name__ == '__main__':
    ser = serial.Serial('/dev/ttyACM1',9600, timeout=1)
    ser.flush()
    
    while True:
        ser.write(b"red\n")
        time.sleep(1)
        ser.write(b"white\n")
        time.sleep(1)
        ser.write(b"blue\n")
        time.sleep(1)
        ser.write(b"green\n")
        time.sleep(1)
        ser.write(b"all\n")
        time.sleep(1)
        ser.write(b"off\n")
        time.sleep(1)