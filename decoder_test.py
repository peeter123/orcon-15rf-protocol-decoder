from decoder import RF15Decoder as rf15dec

lines = []
with open("data/data_bin.txt") as file:
    for line in file:
        if line[0] == '#' or line[0] == ' ' or line[0] == '\n':
            continue
        line.strip("\n")
        lines.append(line)

# Print Info
print('| Type    | | Addr0 | | Addr1 | | Addr2 | |P| |P| |CMD | |N| | Data')
decoder = rf15dec()
for line in lines:
    try:
        decoder.decode(line)
    except Exception as e:
        print('Invalid Packet %s' % type(e))
        continue

    pass
