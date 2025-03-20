import tkinter as tk
from operator import iconcat
from tkinter import ttk, messagebox, filedialog, LabelFrame
import serial
import time
import csv
import os
import sys
import glob
import serial.tools.list_ports
from pathlib import Path


class SerialDevice:
    def __init__(self, port='/dev/serial', baudrate=9600, timeout=.1):
        """Initialize the serial device with the specified parameters."""
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None

    def open(self):
        """Open the serial connection."""
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout
            )

            if self.ser.is_open:
                return True
            else:
                tk.messagebox.showerror(title="Error", message="Failed to open the serial connection.", icon='error')
                return False

        except serial.SerialException as e:
            tk.messagebox.showerror(title="Serial Error", message=str(e), icon='error')
            return False

    def close(self):
        """Close the serial connection."""
        if self.ser and self.ser.is_open:
            self.ser.close()

    def send_line(self, data):
        """Send a line of ASCII text terminated with \r."""
        if not self.ser or not self.ser.is_open:
            tk.messagebox.showerror(title="Error", message="Serial port not open", icon='error')
            return False

        # Make sure the data ends with \r (not \n or \r\n)
        if data.endswith('\n'):
            data = data[:-1]
        if not data.endswith('\r'):
            data += '\r'

        try:
            # Encode the string to bytes and send
            self.ser.write(data.encode('ascii'))
            return True
        except Exception as e:
            tk.messagebox.showerror("Error", str(e), icon='error')
            return False

    @property
    def receive_line(self):
        """Receive a line of ASCII text."""
        if not self.ser or not self.ser.is_open:
            tk.messagebox.showerror("Error", "Serial port not open", icon='error')
            return None

        try:
            # Read until \r or timeout
            line = self.ser.readline().decode('ascii').strip()
            return line
        except Exception as e:
            tk.messagebox.showerror(title="Trouble receiving data", message=str(e), icon='error')
            return None


def bailout(sdevice: SerialDevice):
    if sdevice is not None:
        sdevice.send_line("EPG")
        sdevice.close()
    sys.exit()


def pull_from_scanner():
    # Get the selected option
    scanner = option_var.get()

    # Get the new filename
    channelfilename = file_path.get()

    device = SerialDevice(port=scanner, baudrate=9600)
    if device.open():

        # request device model
        device.send_line("MDL")

        # Wait for response
        time.sleep(0.5)

        # Read response
        response = device.receive_line

        if response=="ERR" or response=="":
            tk.messagebox.showerror(title="Communication Error", message="Trouble communicating with scanner.", icon='error')
            return()
        elif response!="MDL^BC95XLT":
            tk.messagebox.showerror(title="Device Error", message="Device returned invalid scanner model.", icon="error")
            bailout(device)

        # Put scanner into programming mode
        device.send_line("PRG")
        # Wait for response
        time.sleep(0.05)
        response = device.receive_line
        if response!="PRG^OK":
            tk.messagebox.showerror(title="Programming Error", message="Trouble putting scanner into programming mode.", icon="error")
            return()
        else:
            # Here we start reading the scanner and writing the CSV
            try:
                # Create parent directories if they don't exist
                Path(channelfilename).parent.mkdir(parents=True, exist_ok=True)

                with open(channelfilename, 'w', newline='', encoding='utf-8') as csvfile:
                    csv_writer = csv.writer(csvfile)

                    # write header
                    csv_writer.writerow(["Channel", "Frequency", "Lockout", "Priority", "Delay"])

                    # count how many lines read
                    linesread=0

                    # write channels
                    for chan in range(1,201):
                        result_label.configure(text=f"Reading channel {chan}")
                        root.update()
                        device.send_line("RCM^C" + str(chan).zfill(3))
                        time.sleep(0.05)
                        response = device.receive_line
                        linelist = response.split('^')
                        if linelist[0] != 'RCM':
                            tk.messagebox.showerror(title="Channel Error",
                                                    message=f"Couldn't read channel {chan}", icon="error")
                            root.update()
                        else:
                            linesread += 1
                        # teststring.split("^")
                        # ['RCM', 'C120', 'F425.0123', 'LS', 'PR', 'DS']
                        linelist[1] = linelist[1][1:]
                        linelist[2] = linelist[2][1:]
                        linelist[3] = "Y" if linelist[3][1] == "S" else "N"
                        linelist[4] = "Y" if linelist[4][1] == "S" else "N"
                        linelist[5] = "Y" if linelist[5][1] == "S" else "N"
                        csv_writer.writerow(linelist[1:])
            except FileNotFoundError:
                messagebox.showerror("File Error", f"Directory structure cannot be created for {channelfilename}.", icon='error')
                bailout(device)
            except PermissionError:
                messagebox.showerror("Permission Error", f"Permission denied when writing to {channelfilename}.", icon='error')
                bailout(device)
            except OSError as e:
                if e.errno == 28:  # No space left on device
                    messagebox.showerror("Disk Error", f"No space left on device when writing to {channelfilename}.", icon='error')
                else:
                    messagebox.showerror("OS Error", f"Error ({e.errno}): {e.strerror} when writing to {channelfilename}.", icon='error')
                bailout(device)
            except Exception as e:
                messagebox.showerror("Unexpected Error", f"{type(e).__name__}: {e} when writing to {channelfilename}.", icon='error')
                bailout(device)

        # Re-set the radio to regular mode and get out
        device.send_line("EPG")
        time.sleep(0.05)
        response = device.receive_line
        result_label.configure(text=f"Reading complete")
        root.update()
        tk.messagebox.showinfo(title="Programming complete", message=f"Read {linesread} channels.")
        root.update()
        device.close()
    else:
        tk.messagebox.showerror(title="Serial Error", message="Couldn't open serial device.", icon="error")
        root.update()
    sys.exit()


def push_to_scanner():
    # Get the selected option
    scanner = option_var.get()

    # Get the selected file
    channelfilename = file_path.get()

    result = tk.messagebox.askokcancel(title="Ready to Program",
                                         message=f"Programming file {channelfilename}.\nThis will potentially alter or erase data from scanner.")
    if result is not True:
        tk.messagebox.showinfo(title="Operation cancelled", message=f"Cancelling programming at your request.")
        bailout(None)
    else:
        root.update()

    device = SerialDevice(port=scanner, baudrate=9600)
    if device.open():

        # request device model
        device.send_line("MDL")

        # Wait for response
        time.sleep(0.5)

        # Read response
        response = device.receive_line

        if response=="ERR" or response=="":
            tk.messagebox.showerror(title="Communication Error", message="Trouble communicating with scanner.", icon='error')
            return()
        elif response!="MDL^BC95XLT":
            tk.messagebox.showerror(title="Device Error", message="Device returned invalid scanner model.", icon="error")
            bailout(device)

        # Put scanner into programming mode
        device.send_line("PRG")
        # Wait for response
        time.sleep(0.05)
        response = device.receive_line
        if response!="PRG^OK":
            tk.messagebox.showerror(title="Programming Error", message="Trouble putting scanner into programming mode.", icon="error")
            return()
        else:
            # Open the file in read mode
            with open(channelfilename, 'r') as file:
                # Read each line in the file

                #Count programmed lines
                linesprogrammed = 0

                try:
                    for line in file:
                        chanlist = [x.strip() for x in line.split(',')]
                        # will skip blank lines, textual header lines (if first column is non-numeric), ignore comments in
                        # columns > 5, but choke on malformed ones, sadly. 200 channels max in this scanner.
                        if len(chanlist) and chanlist[0].isnumeric() and linesprogrammed < 200:
                            thischanstr = "PCM^C" + chanlist[0].zfill(3)
                            thischanstr = thischanstr + ("^F%08.4f" % float(chanlist[1]))
                            thisitem = "S" if chanlist[2].upper()=="Y" else "R"
                            thischanstr = thischanstr + "^L" + thisitem
                            thisitem = "S" if chanlist[3].upper()=="Y" else "R"
                            thischanstr = thischanstr + "^P" + thisitem
                            thisitem = "S" if chanlist[4].upper()=="Y" else "R"
                            thischanstr = thischanstr + "^D" + thisitem
                            result_label.configure(text=f"Programming channel {chanlist[0]}")
                            root.update()
                            device.send_line(thischanstr)
                            time.sleep(0.05)
                            response = device.receive_line
                            if response!="PCM^OK":
                                tk.messagebox.showinfo(title="Channel Error", message=f"Couldn't program channel {chanlist[0]}", icon="error")
                                root.update()
                            linesprogrammed += 1
                except IndexError:
                    tk.messagebox.showerror(title="Channel File Error",
                                            message=f"Missing data while reading {channelfilename}.", icon="error")
                    bailout(device)
                except Exception as e:
                    messagebox.showerror("Unexpected Error",
                                         f"{type(e).__name__}: {e} while programming with {channelfilename}.", icon="error")
                bailout(device)
        # Re-set the radio to regular mode and get out
        device.send_line("EPG")
        time.sleep(0.05)
        response = device.receive_line
        result_label.configure(text=f"Programming complete")
        root.update()
        tk.messagebox.showinfo(title="Programming complete", message=f"Programmed {linesprogrammed} channels.")
        root.update()
        device.close()
    else:
        tk.messagebox.showerror(title="Serial Error", message="Couldn't open serial device.", icon="error")
    sys.exit()


def get_serial_ports():
    """Returns a list of available serial ports based on the operating system."""
    ports = []

    try:
        # Use pyserial's built-in port detection - works on all platforms
        available_ports = list(serial.tools.list_ports.comports())
        for port in available_ports:
            ports.append(port.device)

        # If no ports found via pyserial, try OS-specific methods
        if not ports:
            if sys.platform.startswith('win'):
                # Windows - just look for COM ports 1-16 (faster than checking all 256)
                for i in range(1, 17):
                    try:
                        port = f'COM{i}'
                        s = serial.Serial(port)
                        s.close()
                        ports.append(port)
                    except (OSError, serial.SerialException):
                        pass
            elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
                # Linux/Cygwin
                ports = glob.glob('/dev/tty[A-Za-z]*')
            elif sys.platform.startswith('darwin'):
                # macOS
                ports = glob.glob('/dev/cu.*')
                ports.extend(glob.glob('/dev/tty.*'))
    except Exception as e:
        tk.messagebox.showerror(title="Serial Error", message=f"Error detecting ports: {e}", icon="error")

    return sorted(ports)


def namesave_file():
    global gSerports, sbState, start_button
    filename = filedialog.asksaveasfilename(initialdir="~", defaultextension="*.csv",
                                            title="Choose a name for the CSV file", confirmoverwrite=True,
                                            filetypes=(("CSV files", "*.csv"), ("All files", "*.*"))
                                            )
    if filename:
        file_path.set(filename)
        # Display only the base filename, not the full path
        base_filename = os.path.basename(filename)
        file_label.config(text=f"Selected: {base_filename}")
        if gSerports != ["No ports available"]:
            sbState = "normal"
            start_button["state"] = sbState


def select_file():
    global gSerports, sbState, start_button
    filename = filedialog.askopenfilename(
        title="Select a CSV file to program the scanner.",
        filetypes=(("All files", "*.*"), ("Comma-separated value files", "*.csv"))
    )
    if filename:
        file_path.set(filename)
        # Display only the base filename, not the full path
        base_filename = os.path.basename(filename)
        file_label.config(text=f"Selected: {base_filename}")
        if gSerports != ["No ports available"]:
            sbState="normal"
            start_button["state"] = sbState


def set_push():
    if push_mode.get() is False:
        instruction_label.configure(text=pushinstrux)
        # push_frame.configure(padx=28)
        # pull_frame.configure(padx=30)
        pull_border.configure(bd=0)
        push_border.configure(bd=2)
        file_button.configure(text="Choose CSV Channel File", command=select_file)
        start_button.configure(text="Send to scanner", command=push_to_scanner)
        main_frame.update()
        push_mode.set(True)
        return


def set_pull():
    if push_mode.get() is True:
        instruction_label.configure(text=pullinstrux)
        # push_frame.configure(padx=30)
        # pull_frame.configure(padx=28)
        pull_border.configure(bd=2)
        push_border.configure(bd=0)
        file_button.configure(text="Create new CSV file", command=namesave_file)
        start_button.configure(text="Read from scanner", command=pull_from_scanner)
        main_frame.update()
        push_mode.set(False)
        return


gWinSize = (500,450)
gWinSizeStr = str(gWinSize[0]) + "x" + str(gWinSize[1])
pushinstrux = "Use this mode with a correctly-formatted CSV file to program a UNIDEN \nBearcat BC95XLT NASCAR scanner. (Radio Shack sold a bunch of ’em)\n\nYou need to choose your serial port, select your CSV file and push 'Send \nto scanner'."
pullinstrux = "Use this mode to create a CSV file of channels read from a UNIDEN \nBearcat BC95XLT NASCAR scanner. (Radio Shack sold a bunch of ’em)\n\nYou need to choose your serial port, name your new file and push 'Read \nfrom scanner'"
# Create the main window
root = tk.Tk()
root.title("BC95XLT Programmer")  # This sets the window's title bar text
root.geometry(gWinSizeStr)
root.resizable(False, False)
# track window mode - default Push
push_mode = tk.BooleanVar()
push_mode.set(True)

# Center the window on the screen
# Get the screen dimensions
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Calculate the position coordinates
x = (screen_width - gWinSize[0]) // 2  # the window width
y = (screen_height - gWinSize[1]) // 2  # the window height

# Set the position of the window
root.geometry(gWinSizeStr + "+" + str(x) + "+" + str(y))

# Create a frame for better layout
main_frame = tk.Frame(root, padx=20, pady=20)
main_frame.pack(fill=tk.BOTH, expand=True)

# Create a set of toggle buttons to switch between write scanner and read scanner
toggle_frame = tk.Frame(main_frame)
toggle_frame.pack(pady=(10, 20),)

push_frame = tk.Frame(toggle_frame, padx=18)
push_frame.pack(side=tk.LEFT,)

push_border = LabelFrame(push_frame, bd = 2, bg = "#444444")
push_border.pack()

sc_push_button = tk.Button(push_border, text="Write Scanner", command=set_push, padx=5, pady=5)
sc_push_button.pack(side=tk.LEFT,)

pull_frame = tk.Frame(toggle_frame, padx=20)
pull_frame.pack(side=tk.LEFT,)

pull_border = LabelFrame(pull_frame, bd = 0, bg = "#444444")
pull_border.pack()

sc_pull_button = tk.Button(pull_border, text="Read Scanner", command=set_pull, padx=5, pady=5)
sc_pull_button.pack(side=tk.RIGHT,)

# Instructional text
instruction_frame = tk.Frame(main_frame)
instruction_frame.pack(fill=tk.X, pady=(0, 10))

# set the instructions for the current mode (default is push-to-scanner)
instruction_label = tk.Label(instruction_frame, text=pushinstrux, justify=tk.LEFT, anchor="w")
instruction_label.pack(fill=tk.X)

# Option menu with 4 options
option_frame = tk.Frame(main_frame)
option_frame.pack(fill=tk.X, pady=(10, 10))

option_var = tk.StringVar(root)
gSerports = get_serial_ports()

# Message to show if no ports found
if not gSerports:
    option_label = tk.Label(option_frame, text="No serial ports detected!", foreground="red")
    gSerports = ["No ports available"]
else:
    option_label = tk.Label(option_frame, text="Select the serial connection to your scanner:")
option_label.pack(anchor=tk.W)

option_var.set(gSerports[0])  # Default value

option_menu = tk.OptionMenu(option_frame, option_var, *gSerports)
option_menu.pack(anchor=tk.W)

# File selection
file_frame = tk.Frame(main_frame)
file_frame.pack(fill=tk.X, pady=(10, 10))

file_path = tk.StringVar()
file_button = tk.Button(file_frame, text="Choose CSV Channel File", command=select_file)
file_button.pack(side=tk.LEFT)

file_label = tk.Label(file_frame, text="No file selected")
file_label.pack(side=tk.LEFT, padx=(10, 0))

# Start button
button_frame = tk.Frame(main_frame)
button_frame.pack(fill=tk.X, pady=(20, 10))

sbState="disabled"

start_button = tk.Button(button_frame, text="Send to scanner", command=push_to_scanner, padx=10, pady=10)
start_button.pack()
start_button["state"] = sbState

# Result label
result_label = tk.Label(main_frame, text="")
result_label.pack(pady=(10, 0))

# Run the application
root.mainloop()


