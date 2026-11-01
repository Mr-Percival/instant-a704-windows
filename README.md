# Instant A704 mouse fixer for Windows

Many cheap no-name "USB GAMING MOUSE" devices use the **Instant Microelectronics A704** chip (USB `30fa:1701`). They ship with weird onboard bindings (a thumb button that sends **Win+D** and minimizes everything, "fire" bursts) and no Windows software. This is a small Python daemon that reconfigures the chip on Windows and turns the extra buttons into useful actions.

Based on the reverse-engineered protocol from [AmberIsFrozen/Instant-A704F-Mouse-Utilities](https://github.com/AmberIsFrozen/Instant-A704F-Mouse-Utilities) (Linux/macOS), extended with two undocumented button codes (`07`, `09`) found on a 10-button model.

## What it does
- Resets the 5 basic buttons to their normal function and removes the factory Win+D macro.
- Thumb button → held left click (handy when the chip ignores left click while right is held, e.g. bows in *Horizon Zero Dawn*).
- Small side button → `Win+Shift+S` (screen snip). Button on top of the wheel → `Ctrl+V`.
- The chip does **not** store settings, so the daemon re-applies them on every reconnect.

Edit `BOTONES` and `manejar()` in `mouse_a704.py` to change bindings.

## Button codes (10-button model)
| Physical button | Rebind code | Event on `0xFF00` |
|---|---|---|
| Left / Wheel / Right | 01 / 02 / 03 | f1 / f2 / f3 |
| Side buttons | 04, 05 | f4, f5 |
| Large thumb button | 07 | f7 |
| Top-of-wheel button | 08 | f8 |
| Small button under the side buttons | 09 | f9 |

Rebind command: feature report ID 7, 8 bytes, on the vendor collection `0xFF01` of interface 1: `07 10 <button> <action> 00 00 00 00`. Actions: `00` key input (reported on `0xFF00` as `06 <f-code> 03|83`), `01` left, `02` middle, `03` right, `04` back, `05` forward, `06` DPI cycle, `07` show desktop, `08` double click, `09` fire.

**Known chip limitation:** while the right button is held, the chip does not register the left button at all. No configuration fixes that; use another button to fire.

## Install
Requires Python 3.10+ from python.org (check "Add python.exe to PATH").
```
git clone https://github.com/Mr-Percival/instant-a704-windows
cd instant-a704-windows
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\pythonw -I mouse_a704.py
```
It runs silently in the background; logs go to `mouse_a704.log`. To stop it, end `pythonw.exe` in Task Manager.

**Start at logon:** press `Win+R`, type `shell:startup`, and create a shortcut there with the full paths, e.g.
`"C:\path\to\instant-a704-windows\.venv\Scripts\pythonw.exe" -I "C:\path\to\instant-a704-windows\mouse_a704.py"`
(a bare `pythonw.exe` would use the system Python, which does not have `hidapi`).

## Notes
- Unplugging the mouse (or its receiver) always restores factory behavior.
- If the daemon is killed while you hold the thumb button, left click may stay pressed: one physical left click releases it.
- Windows does not allow injected input into apps running as administrator.

## License
MIT
