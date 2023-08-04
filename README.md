## Requirements

- [pymcuprog](https://pypi.org/project/pymcuprog/)
- [minimalmodbus](https://pypi.org/project/minimalmodbus/)

```bash
python -m pip install pymcuprog minimalmodbus
```

## Usage

```bash
python main.py
```

```bash
# or on linux systems
./main.py
```

## Packaging

```bash
pyinstaller main.spec
```

## Test Snippets

```bash
pymcuprog ping -t uart -u /dev/ttyUSB0 -d attiny202
pymcuprog write -f app.hex -t uart -u /dev/ttyUSB0 -d attiny202 -v info --erase --verify

pyinstaller main.py -n coffe-probe-tester --windowed --onefile --hidden-import pymcuprog.deviceinfo.devices.attiny202
```

