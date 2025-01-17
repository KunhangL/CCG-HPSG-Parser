import sys
import os

CMD = sys.argv[1]
DIR = sys.argv[2]
FILENAMES = sys.argv[3:]

def convert(s):
  try:
    return int(s)
  except ValueError:
    return float(s)

def extract(input, output, ids):
  out = open(output, 'w')
  for i, line in enumerate(open(input, 'rU')):
    if i in ids:
      print >> out, line,

ids = set()

# stdin from evalb output
# ID Len Stat Recal Prec Bracket gold test Bracket Words Tags Accracy
nsents = 0
for line in sys.stdin:
  fields = line.split()
  if len(fields) == 12 and fields[0].isdigit():
    fields = map(convert, fields)
    id, length, _, R, P, matched, ngold, ntest, ncross, nwords, ntags, acc = fields
    F = P and R and 2*P*R/(P + R) or 0.0
    if eval(CMD):
      ids.add(id - 1)
    nsents += 1

nkeeps = len(ids)

if not os.path.exists(DIR):
  os.makedirs(DIR)

readme = os.path.join(DIR, "README")
readme = open(readme, "a")
print >> sys.stderr, "condition is", CMD
print >> sys.stderr, "kept %d of %d sentences (%.2f%%)" % (nkeeps, nsents, nkeeps*100.0/nsents)
print >> readme, "condition is", CMD
print >> readme, "kept %d of %d sentences (%.2f%%)" % (nkeeps, nsents, nkeeps*100.0/nsents)

for input in FILENAMES:
  filename = os.path.basename(input)
  output = os.path.join(DIR, filename)
  print >> readme, ' ', input, "->", output
  extract(input, output, ids)

