## Windows usage

Install Terminal from the Microsoft Store and set as standard terminal. CMD does not support all textual icons.

### create EXE/APP

#### Windows/macOS

```python
os.startfile(realpath(self.tree_path))  # Windows
os.system(f"open {realpath(self.tree_path)}")  # Mac
```

```bash
pyinstaller --noconfirm BulkMail.spec
```

### textual dev console
    
```bash
textual console
```

