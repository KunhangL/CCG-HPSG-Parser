from sys import stdin, stderr, argv, exit
from string import join

if len(argv) not in [2,3]:
  print >> stderr, "usage: %s [-g] <project>" % argv[0]
  exit(1)

if len(argv) == 3:
  if argv[1] != '-g':
    print >> stderr, "usage: %s [-g] <project>" % argv[0]
    exit(1)

  gold = 1
  model = argv[2]
else:
  gold = 0
  model = argv[1]

model = model.rstrip('/')

def ignore_preface(lines):
  in_preface = True
  for line in lines:
    if in_preface:
      in_preface = line != '\n'
      continue
    yield line

def load(filename, lookup):
  for line in ignore_preface(open(filename)):
    line = line[:-1]
    fields = line.split()
    freq = int(fields[-1])
    # ignore the - placeholder in attributes rather than join all fields
    lookup.append(fields[-2])

klasses = ['__NONE__', '__SENTINEL__']
load(model + "/classes", klasses)

attributes = []
load(model + "/attributes", attributes)

weights = {}
for line in ignore_preface(open(model + "/weights")):
  line = line[:-1]
  (klass, attrib, weight) = line.split()
  weights[klasses[int(klass)], attributes[int(attrib)]] = float(weight)

confusion = {}
ntotal = 0
nfine_correct = 0
ncoarse_correct = 0
correct = ''
for line in stdin:
  line = line[:-1]
  attributes = line.split()
  if gold:
    correct = attributes[0]
    attributes = attributes[1:]
    line = ' '.join(attributes)
  results = []
  for klass in klasses[1:]:
    score = 0.0
    for attrib in attributes:
      score += weights.get((klass, attrib), 0.0)
    results.append((score, klass))
  (score, klass) = max(results)
  ntotal += 1
  if gold:
    print "%s %s %.2f %s" % (correct, klass, score, line)
    if correct == klass:
      nfine_correct += 1
    else:
      error = (correct, klass)
      confusion[error] = confusion.get(error, 0) + 1
    klass = klass.split(':')[0]
    if correct.startswith(klass):
      ncoarse_correct += 1
  else:
    print "%s %.2f %s" % (klass, score, line)

pct = 100.0/ntotal;
if gold:
  print >> stderr, "fine accuracy: %.1f %% (%d/%d)" % (nfine_correct*pct, nfine_correct, ntotal)
  print >> stderr, "coarse accuracy: %.1f %% (%d/%d)" % (ncoarse_correct*pct, ncoarse_correct, ntotal)

  confusion = confusion.items()
  confusion.sort(lambda x, y: cmp(y[1], x[1]))
  for ((correct, error), count) in confusion[:10]:
    print >> stderr, "  %2d  %15s -> %15s" % (count, correct, error)
