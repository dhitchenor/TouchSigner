# TouchSigner
*Forked from Souramoo/TouchSigner (https://github.com/souramoo/TouchSigner/)*

Have you ever had that moment when you need to sign a document you receive online, only to find that you're too lazy to go and print it out, sign it and scan it back in?

Why not copy and paste in your signature with a computer? But what if you're too lazy to even sign something and scan it in? Who even has a scanner these days?

TouchSigner lets you use your laptop's capacitive touchpad to quickly draw up a signature. Just use your finger and save it to a file!

## Screenshots
![Main window](/screens/screen1.png?raw=true "Main window")
![After drawing a bit](/screens/screen2.png?raw=true "After drawing a bit")

## Dependencies
- python3 (https://www.python.org/about/gettingstarted/)
- pygame (https://www.geeksforgeeks.org/installation-guide/how-to-install-pygame-in-windows/)
- Tkinter (https://stackoverflow.com/questions/24499602/how-to-install-tkinter)

## Usage
Run `./signer.py` to launch the program

Now just use your finger/capacitive stylus to draw your signature on your touchpad without lifting it.

Press:
- 'enter': saves file (svg + png), dialog chooses location and filename, not file type.
- 'escape': resets signature (so you can try again)
- 'q': exits without saving
