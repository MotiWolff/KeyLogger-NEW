# KeyLogger Project

## Overview
- The project is made of 3 parts:
    - A KeyLogger code that is made of 5 segments (classes):
        - KeyLoggerService: 2 versions of the code that is incharge of getting the keystrokes using pynput (A MUST). Made for macOS and Windows.
        - KeyLoggerManager: first gets the user choice of OS Type to run of, and with the answer then runs in a loop, every X seconds read the keystrokes, binds it to a buffer and transfers the data to the FileWriter segment. 
        - FileWriter: gets the data as strings and writes to the file (or virtual database like mongoDB) with timestamp, having through an encryption via Encryptor segment.
        - NetworkWriter: Gets data and transfer to the server via IWriter class.
        - Encryptor: responsible for doing a XOR encryption and likewise.

    - Backend side via Flask with 2 main uses:
        1. Getting KeyLogger data from the tool and keeping it for later use.
        2. Enabling access to the data from the user interface.

    - Frontend Side (with HTML, css and JavaScript):
        Structure:
        - A header element with the website logo, the text KeyLogger Manager and a paragraph with the text Every Key Tells A Story, and a navbar for the website sections.

        - A div element with the text:
        Select an OS type; Currently only macOS is available.
        Then 3 buttons inside the div, with the logos of macOS, windows and Linux.
        Pressing the macOS and windows buttons will open the connected devices list. The Linux button is disabled.

        - A section element with the connected devices list that will appear dynamically upon clicking an OS button.
        The list will be shown the connected devices as device-Items with the following buttons:
        start, stop, view encrypted logs (a toggle button that will show decrypted logs upon clicking twice) and remove device button.
        The start button will run the KeyLogger, the stop button will stop it. After a stop, the view logs button will show the logs upon clicking. The remove device will be disconnect the device and remove it from the list. 
        Each device will have a unique id that will appear dynamically.
        The logs will be shown dynamically in the section under the buttons in a nice way.

        - A section with option to view logs history after deactivating devices.
        Will be ordered based on id and timestamp.

        - A section with the about of the page and project.

        - A section for contact.

        - A footer

        - The css files are attached.

### Implementation

- KeyLogger:
    - ## Step 1: Implementing KeyLoggerService:
        First of all:
        There will be 3 files for the keylogger, one for each os type. 
        the app.py in the backend side will ask the user on the frontend side (using buttons) which OS to use.


        At this point, we will align and implement the KeyLoggerService in a uniform interface. The goal is to create a class that listens to keyboard keystrokes and temporarily stores them in memory (Buffer) for later use.

        - Implementation Requirements:
            1. We will set a IKeyLogger class with the following functions:
                - start_logging(): Starting the Listener
                - stop_logging(): Stopping the Listener
                - get_logged_keys() -> list[str]: Returning a string of all keystrokes gathered.
            2. We will implement a KeyLoggerService class that will implement the IKeyLogger class.
            3. We will use pynput library for listening to keyboard keystrokes.

        At this point, the goal is to "clean up the noise" and provide a consistent starting point so that later on, capabilities such as encryption, writing to a file, and sending to a server can be added. Using a defined interface allows for clean, maintainable, and modular code, so that the KeyLoggerService implementation can be easily replaced or upgraded.

        ### Required Result: 
        - A working KeyLoggerService that listens to keystrokes and stores them in memory. 
        - The implementation will be carried out according to a uniform interface (IKeyLogger), so that in the future the code can be easily expanded.
    
    ## Step 2: FileWriter Implementaion
        Task: Implementing a class named FileWriter that is responsible for writing to the file.

        FileWriter is handling only the writing to file process, and the KeyLoggerManager class will work on the data before sending it.

        ### Required Result:
        - FileWriter that gets a string of text and writes it to the file.

    ## Step 3: Writing XOR Encryption
        Task: 
        1. Write an Encryptor class that executes a basic XOR encryption on the data stored.
        2. Save a simple key for the XOR operation.

        Encryption is a vital part in the project - the sensitive data should'nt be saved openly in a file. XOR is a simple method that uses basics consepts of encryption.

        ### Required Result:
        The file will be saved encrypted - so that when a user try to read the file directly, the text will look gibberish. Only those who have the decryption function and key can read the data.

    ## Step 4: KeyLoggerManager Implementation
        Task:
        Implement a KeyLoggerManager class that will receive the KeyLoggerService and the FileWriter, and manage the central Buffer.

        Will do, on a periodic time:
        - Gathering keystrokes from KeyLoggerService
        - Binding data to the Buffer
        - When the program is stopped:
            - Adds a timestamp to the data
            - Encrypting data with Encryptor
            - Transfering encrypted string to FileWriter

        Centralizes the logic of data collection, processing, and transmission.
        Allows flexibility in changes – for example, changing the update frequency, changing the encryption method, adding Buffer management

        ### Required Result:
        KeyLoggerManager which initiates the collection, bundles the data, adds a timestamp, and performs encryption before sending the data to the writer class (and, if configured, to the sender class to the network).

        ### A secret agent decrypts the file
        Task:
        1. Write a script that gets the path for the encrypted file and the xor key from the user in the CLI.
        2. The script will load the file, will process decryption, and will print the decrypted data to the screen.

        ### Required Result:
        A Python file that allows you to recover the visible information from the file that the keylogger created.

    ## Step 5: Retina writing
        Task:
        Implement a NetworkWriter according to the IWriter, that will use the requests library to send data to the server.

        ### Required Result:
        A class that implements this method:
        send_data(data: str, machine_name: str) -> None


        Advice:
        Think on handling Execptions and Logs in every segment.

        ## Requirements:
        Code will be compatible for all major OS, like Windows, MacOS and Linux.

- Backend:
    Task:

    1. Make sure Flask is installed (or install it using pip install flask).
    2. Create a new backend folder and navigate to it.
    3. Inside the folder, create the following files:
    3.1. app.py (server main file)
    3.2. data/ (in which keylogger files will be stored)

    ### Required Result:
    Project structure that includes data folder and an empty app.py file

    ## Step 2: Creating basic Flask server
        Task:
        1. Open app.py and insert the following code:

        from flask import Flask, jsonify
        app = Flask(__name__)
        @app.route('/')
        def home():
        return "KeyLogger Server is Running"
        if __name__ == '__main__':
        app.run(debug=True) 

        2. Run the server (python app.py) and make sure it works.
        3. Go to address http://127.0.0.1:5000 and check if page loads successfully.

        ### Required Result:
        An active Flask server that shows a message in the browser.

    ## Step 3: Creating API to get KeyLogger data
        Task:
        Create a listener via Flask that will listen to data from the tool.

        ### Required Result:
        Data from the tool will be recieved by the server, will be decrypted and saved to the disk under data/ folder.

        - POST to api/upload/ that gets data and save it in structure:
        - data/<machine>/log_<timestamp>.txt

        Here is a starter code (rest of app.py):

        from flask import request
        import time

        def generate_log_filename():
        return "log_" + time.strftime("%Y-%m-%d_%H-%M-%S") + ".txt"
        @app.route('/api/upload', methods=['POST'])
        def upload():
        data = request.get_json()
        if not data or "machine" not in data or "data" not in data:
            return jsonify({"error": "Invalid payload"}), 400
        machine = data["machine"]
        log_data = data["data"]

        machine_folder = os.path.join(DATA_FOLDER, machine)
        if not os.path.exists(machine_folder):
            os.makedirs(machine_folder)

        filename = generate_log_filename()
        file_path = os.path.join(machine_folder, filename)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(log_data)

        return jsonify({"status": "success", "file": file_path}), 200

    ## Step 4: Creating API to get computer list
        Task:
        Create an API on your server named get_target_machines_list(), allowing to get the computer list on which the tool ran so far.
        The computer list will be extracted from folders names, no need for a database.

        ### Required Result:
        A GET call to api/get_target_machines_list/ will return a JSON array with computers names.

    ## Step 5: Extracting specific machine keystrokes data
        Task:
        Create an API in the server named get_target_machine_key_strokes(target_machine) that allows to get keystrokes from a specific machine.

        ### Required Result:
        A call to pi/get_keystrokes?machine=computer1/ will return a JSON with the computer data.

- Frontend:
    - Already implemented, needs connection to js files and more.
    