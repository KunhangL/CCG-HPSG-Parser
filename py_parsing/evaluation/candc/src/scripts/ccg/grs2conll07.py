import sys

CONVERT = {'-LRB-': '(', '-RRB-': ')',
           '-LCB-': '{', '-RCB-': '}',
           '-LSB-': '[', '-RSB-': ']'}

def punct_convert(s):
    for (old, new) in CONVERT.iteritems():
        s = s.replace(old, new)
    return s

PUNCT = set("( ) { } [ ] -- : ; , . ? !".split())

# the following sentence (wsj2343.19/Depbank #374) is missing from CCGbank
# the POS tags are from the Penn Treebank
SENT374 = '<c> Maybe|RB|X Lily|NNP|X became|VBD|X so|RB|X obsessed|JJ|X with|IN|X where|WRB|X people|NNS|X slept|VBD|X and|CC|X how|WRB|X because|IN|X her|PRP$|X own|JJ|X arrangements|NNS|X kept|VBD|X shifting|VBG|X .|.|X'
PLACE374 = '<c> __PLACEHOLDER_wsj2343.19__|NN|N'

class Word:
    def __init__(self, token, index):
        self.index = index
        fields = token.split('|')
        self.token = fields[0]
        self.pos = fields[1]
        self.cat = fields[2]
        self.grs = []
        self.sub = None

    def __cmp__(self, other):
        return cmp(self.index, other.index)

    def is_num(self):
        return self.pos == 'CD'

    def __repr__(self):
        if self.sub:
            return repr(self.sub)
        else:
            return '%s_%d' % (self.token, self.index)

def convert_arg(arg, gr, words):
    if '_' in arg and arg != '_':
        word = words[arg]
        word.grs.append(gr)
        return word
    else:
        return arg

def nopos(word):
    if type(word) == type(''):
        return word
    else:
        return word.token

class GR:
    def __init__(self, line, words):
        self.line = line
        fields = line[1:-1].split()
        self.label = fields[0]
        self.args = [convert_arg(arg, self, words) for arg in fields[1:]]
        self.ignore = False
    def __repr__(self):
        return '(%s %s)' % (self.label, ' '.join(map(str, self.args)))

    def nopos(self):
        return '(%s %s)' % (self.label, ' '.join(map(nopos, self.args)))

    def replace(self, old, new):
        for i in xrange(len(self.args)):
            if self.args[i] == old:
                self.args[i] = new

class Sentence:
    def __init__(self, grs, line):
        self.words = {}
        self.sentence = []
        for (i, token) in enumerate(line.split()):
            word = Word(token, i)
            self.sentence.append(word)
            self.words[str(word)] = word

        self.grs = [GR(gr, self.words) for gr in grs]
        self.tokens = {}
        self.pos = {}
        self.cats = {}
        for w in self.sentence:
            self.tokens.setdefault(w.token, []).append(w)
            self.pos.setdefault(w.pos, []).append(w)
            self.cats.setdefault(w.cat, []).append(w)

    def postprocess(self):
        self.add_funny_conj()
        self.merge_conj_args()
        self.remove_comma_conj()
        self.add_passives()
        self.ncmod_to_iobj()
        self.fix_ncmod_num()
        self.sfs_to_conj()
        self.filter_punct()
        self.fix_ampersands()
        self.remove_relpro_cmod()
        self.cmod_to_ta()
        self.ncmod_to_prt()
        self.xmod_add_to()
        self.fix_that_relpro()

#        self.xmod_to_ta()
#        self.pct_ncmod_to_dobj()

    def add_passives(self):
        for w in self.sentence:
            if w.cat.lstrip('(').startswith('S[pss]\NP') or \
                   (w.pos == 'VBN' and w.cat == 'N/N'):
                self.grs.append(GR('(passive %s)' % w, self.words))

    def add_funny_conj(self):
        for w in self.sentence:
            if w.cat == 'conj' and w.grs == []:
                prev = self.sentence[w.index - 1]
                gr = GR('(conj %s %s)' % (w, prev), self.words)
                self.grs.append(gr)
                w.grs.append(gr)
                
                next = self.sentence[w.index + 1]
                gr = GR('(conj %s %s)' % (w, next), self.words)
                self.grs.append(gr)
                w.grs.append(gr)
                
    def merge_conj_args(self):
        for w in self.sentence:
            if w.cat == 'conj':
                # get all the words coordinated by w
                conj = [gr.args[1] for gr in w.grs if gr.label == 'conj']
                # now count the number of times they occur with other relations
                # substituting the conjunction w for the word x
                common = {}
                for x in conj:
                    x.sub = w
                    for gr in x.grs:
                        if gr.label == 'conj':
                            continue
                        common.setdefault(str(gr), []).append(gr)

                for (gr, instances) in common.iteritems():
                    if len(instances) == len(conj):
                        # ignore the GRs with the same number of elements as conj
                        for x in instances:
                            x.ignore = True
                        # and replace them with a new GR using w
                        self.grs.append(GR(gr, self.words))

                # undo the substitution with w
                for x in conj:
                    x.sub = None

    def remove_comma_conj(self):
        for w in self.sentence:
            if w.token == ',' and w.grs:
                conj = [gr for gr in w.grs if gr.label == 'conj']
                for gr in conj:
                    gr.ignore = True
                    
                if len(conj) == 2:
                    head, mod = sorted([conj[0].args[1], conj[1].args[1]])

                    mod.sub = head
                    head_grs = set([str(gr) for gr in head.grs])
                    for gr in mod.grs:
                        if str(gr) in head_grs:
                            gr.ignore = True
                    mod.sub = None

#                    self.grs.append(GR('(ncmod _ %s %s)' % (head, mod), self.words))

    def fix_ncmod_num(self):
        for w in self.cats.get('N[num]', []):
            for gr in w.grs:
                if gr.label != 'ncmod':
                    continue
                if gr.args[1] == w:
                    gr.args[0] = 'num'
                    gr.args[1], gr.args[2] = gr.args[2], gr.args[1]
                elif gr.args[2] == w:
                    gr.args[0] = 'num'
                    gr.args[2] = self.sentence[gr.args[1].index + 1]
        for gr in self.grs:
            if gr.label == 'ncmod' and \
                   (gr.args[1].is_num() or gr.args[2].is_num()):
                gr.args[0] = 'num'

    PART = set("several some most all any more less many".split())
    def ncmod_to_iobj(self):
        for gr in self.grs:
            if gr.label == 'ncmod' and gr.args[2].token == 'of':
                if gr.args[1].token.lower() not in self.PART:
                    gr.args.pop(0)
                    gr.label = 'iobj'

    def sfs_to_conj(self):
        for gr in self.grs:
            if gr.label == 'ncmod' and gr.args[2].pos == 'CC' and gr.args[2].cat == 'S/S':
                self.grs.append(GR('(conj %s %s)' % (gr.args[2], gr.args[1]), self.words))
                gr.ignore = True

    def pct_ncmod_to_dobj(self):
        for gr in self.grs:
            if gr.label == 'ncmod' and gr.args[0] == '_' and gr.args[2].token == '%':
                gr.args.pop(0)
                gr.label = 'dobj'

    def xmod_to_ta(self):
        for gr in self.grs:
            if gr.label == 'xmod':
                start, end = sorted([gr.args[1].index, gr.args[2].index])
                for i in xrange(start + 1, end):
                    if self.sentence[i].token == ',':
                        gr.label = 'ta'
                        for i in xrange(end + 1, len(self.sentence)):
                            if self.sentence[i].token == ',':
                                gr.args[0] = 'bal'
                                break
                        else:
                            gr.args[0] = 'end'
                        break

    def xmod_add_to(self):
        for gr in self.grs:
            if gr.label == 'xmod':
                start, end = sorted([gr.args[1].index, gr.args[2].index])
                for i in xrange(start + 1, end):
                    if self.sentence[i].token == 'to':
                        gr.args[0] = 'to'
                        break

    SAY = set("say said says".split())
    def cmod_to_ta(self):
        for gr in self.grs:
            if gr.label == 'cmod':
                if gr.args[2].token.lower() in self.SAY:
                    gr.label = 'ta'
                    gr.args[0] = 'quote'
                    gr.args[1], gr.args[2] = gr.args[2], gr.args[1]
                elif gr.args[1].token.lower() in self.SAY:
                    gr.label = 'ta'
                    gr.args[0] = 'quote'

    def ncmod_to_prt(self):
        for gr in self.grs:
            if gr.label == 'ncmod':
                if gr.args[1].pos.startswith('V') and gr.args[2].pos == 'RP':
                    gr.args[0] = 'prt'

    def filter_punct(self):
        for gr in self.grs:
            for arg in gr.args:
                if isinstance(arg, Word) and arg.token in PUNCT:
                    gr.ignore = True
                    break

    def fix_ampersands(self):
        for w in self.sentence:
            if w.token == '&' and w.cat == 'N/N':
                prev = self.sentence[w.index - 1]
                next = self.sentence[w.index + 1]
                for gr in w.grs:
                    gr.ignore = True
                for gr in next.grs:
                    if prev in gr.args:
                        gr.ignore = True
                    else:
                        gr.replace(next, w)
                self.grs.append(GR('(conj %s %s)' % (w, prev), self.words))
                self.grs.append(GR('(conj %s %s)' % (w, next), self.words))

    def remove_relpro_cmod(self):
        for gr in self.grs:
            if gr.label == 'cmod' and gr.args[0] != '_' and gr.args[0].token != 'that':
                gr.args[0] = '_'

    def fix_that_relpro(self):
        for gr in self.grs:
            if gr.label == "cmod" and gr.args[0] != '_' and gr.args[0].token == 'that':
                that = gr.args[0]
                for gr2 in that.grs:
                    if gr2.label == "ncsubj" and gr2.args[1] == that:
                        gr2.args[1] = gr.args[1]                    

def read(filename, OUTPUT, ADD374):
    grs = []
    for line in open(filename):
        line = line.strip()
        if ADD374 and line == PLACE374:
            line = SENT374
        elif not line or line.startswith('#'):
            if OUTPUT == '--ccgbank':
                print line
            continue
        line = punct_convert(line)
        if line.startswith('('):
            grs.append(line)
        elif line.startswith('<c> '):
            yield Sentence(grs, line[4:])
            grs = []

OUTPUT = sys.argv[1]
if sys.argv[2].startswith('--'):
    if sys.argv[2] != '--no-postprocess':
        print >> sys.stderr, "unrecognised command line argument %s" % sys.argv[2]
        sys.exit(1)

    POSTPROCESS = False
    FILENAME = sys.argv[3]
else:
    POSTPROCESS = True
    FILENAME = sys.argv[2]

if OUTPUT == "--ccgbank":
    print "# generated by grs2depbank"
elif OUTPUT == '--rasp-parse':
    print "%LB ("
    print "%RB )"

ADD374 = OUTPUT in ['--text', '--pos']

for i, s in enumerate(read(FILENAME, OUTPUT, ADD374)):
    if POSTPROCESS:
        s.postprocess()
    
    if OUTPUT == '--ccgbank':
        for gr in s.grs:
            if not gr.ignore:
                print gr
                
        print '<c>',
        for w in s.sentence:
            print '%s|%s|%s' % (w.token, w.pos, w.cat),
        print
    elif OUTPUT == '--rasp-text':
        print
        print i + 1
        for w in s.sentence:
            print w.token,
        print
    elif OUTPUT == '--rasp-parse':
        print
        print i + 1
        print
        for gr in s.grs:
            if not gr.ignore:
                print gr.nopos()
    elif OUTPUT == '--text':
        for w in s.sentence:
            print w.token,
        print
    elif OUTPUT == '--pos':
        for w in s.sentence:
            print '%s|%s' % (w.token, w.pos),
        print
