CLI to execute dwm's X window stack management ideas as commands in a DE

### layouts

monocle M, tile T, centeredmaster C, centeredfloatingmaster c, spiral @, dwindle D, flow F

### commands

```
pocoy zoom
pocoy layout <code>
pocoy mfact <increment>
pocoy incnmaster <increment>
pocoy focusstack <number>
pocoy pushstack <number>
pocoy gap inner <number>
pocoy gap outer <number>
pocoy decoration toggle
```

manual: [pocoy.1.txt](pocoy.1.txt)

### install

```
sudo make install
```

### debian dependencies

```
python3-distutils python3-xdg python3-gi gir1.2-gtk-3.0 gir1.2-wnck-3.0 
```
