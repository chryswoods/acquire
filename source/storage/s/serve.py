
if __name__ == "__main__":
    with open("index.html", "r") as FILE:
        lines = FILE.readlines()
        for line in lines:
            print(line, end="")
