
import sys
data = {}
fd = open(sys.argv[1])
for line in fd.readlines():
    if '#' in line:
        continue
    if 'n' in line:
        continue
    if len(line) < 4 :
        continue
    _, lamb, prob, err = line.split(' ',4)
    data[float(lamb)] = float(prob)
import matplotlib.pyplot as plot
plot.plot(data.keys(), data.values(), '.')
plot.savefig(sys.argv[2])
