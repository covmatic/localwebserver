try:
    import system9
except ModuleNotFoundError:
    print("not installed")
else:
    print(system9.__version__)
