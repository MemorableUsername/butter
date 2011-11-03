import math
import prob
import re

from collections import defaultdict
from hyphenate import hyphenate_word

class word(object):
    camelcase_ex = re.compile(r'(?<=[a-z])[A-Z]')

    def __init__(self, text):
        # get runs of repeated characters for collapsing later
        runs = [(i.start(), i.end()) for i in re.finditer(r'(.)\1{2,}', text)]

        # if the word is camelCase (or similar), break it into pieces
        chunks = []
        i = 0
        for m in self.camelcase_ex.finditer(text):
            chunks.append(text[i:m.start()])
            i = m.start()
        chunks.append(text[i:])

        self.syllables = reduce(lambda x,y: x+hyphenate_word(y), chunks, [])

        # collapse any long runs of identical characters
        for run in runs:
            begin = self._find_syllable(run[0])
            end   = self._find_syllable(run[1]-1)+1
            self.syllables[begin:end] = ["".join(self.syllables[begin:end])]
            
    def _find_syllable(self, char):
        """Find the index of the syllable containing the character at index
           |char|"""
        curr_len = 0
        for i, s in enumerate(self.syllables):
            curr_len += len(s)
            if char < curr_len:
                return i
        raise ValueError("out of bounds")

    def __getitem__(self, i):
        return self.syllables[i]

    def __setitem__(self, i, value):
        self.syllables[i] = value

    def __str__(self):
        return "".join(self.syllables)

    def __len__(self):
        return len(self.syllables)

class sentence(object):
    words_ex = re.compile(r'([\W_]+)')

    def __init__(self, text):
        self.words = self.words_ex.split(text)
        self.same_words = defaultdict(list)

        # ignore zero-character words at the ends of the list
        self.min, self.max = 0, len(self.words)
        if self.words[self.min]   == '': self.min += 2
        if self.words[self.max-1] == '': self.max -= 2

        for werd, token in enumerate(range(self.min, self.max, 2)):
            self.words[token] = word(self.words[token])
            self.same_words[str(self.words[token]).lower()].append(werd)

    def related(self, i):
        return self.same_words[ str(self[i]).lower() ]            

    def __getitem__(self, i):
        if self.min + i*2 >= self.max:
            raise IndexError("index out of bounds")
        return self.words[self.min + i*2] # skip spaces

    def __len__(self):
        return (self.max-self.min+1)/2

    def __str__(self):
        return "".join([str(i) for i in self.words])


class scorer(object):
    class score(tuple):
        def __new__(cls, total, each):
            return tuple.__new__(cls, each)

        def __init__(self, total, each):
            self.total = total

        def __repr__(self):
            return '<%s, %s>' % (self.total, list(self))

    block_words = set(['the', 'are', 'aren', 'was', 'wasn', 'were', 'weren',
                       'will', 'won', 'would', 'could', 'should', 'can', 'does',
                       'doesn', 'don', 'this', 'that', 'these', 'those',
                       'there', 'their', 'she', 'him', 'her', 'its', 'his',
                       'hers', 'they', 'you', 'and', 'from', 'for', 'once',
                       'been', 'have', 'had', 'who', 'what', 'where', 'when',
                       'why', 'how', 'has', 'had', 'have', 'yes', 'yeah', 'yah',
                       'yep', 'nah', 'nope'])
    block_sylls = set(['ing', 'tion'])

    good_prewords = set(['the', 'an', 'a', 'my', 'your', 'his', 'her',
                         'our', 'their', 'to'])

    def __init__(self, sent):
        self.values = self._score_sentence(sent)

    def _score_sentence(self, sent):
        words = [self._score_word(sent, i) for i in range(len(sent))]
        for i in range(len(sent)):
            factor = 1.25 ** (len(sent.related(i))-1)
            words[i].total = int(words[i].total * factor)
        score = reduce(lambda x, y: x+y.total, words, 0)
        return scorer.score(score, words)

    def _score_word(self, sent, i):
        if len(str(sent[i])) < 3 or str(sent[i]).lower() in self.block_words:
            return scorer.score(0, [])

        sylls = [self._score_syllable(sent, i, j) for j in range(len(sent[i]))]
        score = int(sum(sylls) / math.sqrt(len(sylls)))
        if score == 0:
            return scorer.score(0, [])

        # earlier syllables are funnier
        for j, val in enumerate(sylls):
            if val != 0:
                sylls[j] += min((len(sylls)-j-1)**2, 16)

        # one-syllable words are always easy to butt
        if len(sylls) == 1:
            score += 3

        if i>0:
            prev = str(sent[i-1]).lower()
            if prev in self.good_prewords:
                score += 5

        return scorer.score(score, sylls)

    def _score_syllable(self, sent, i, j):
        s = sent[i][j].lower()
        if s in self.block_sylls: return 0
        if 'butt' in s: return 0

        # check if "butt" got split across syllables
        if s == 'but' and len(sent[i]) > j+1 and sent[i][j+1][0].lower() == 't':
            return 0

        lengths = [0, 0, 1, 2, 3, 2, 2, 1]
        score = lengths[min(len(s), len(lengths)-1)]
        if score == 0:
            return 0

        if re.match(r'^[^aeiou][aeiouy]([^aeiouy])\1', s):
            score += 4
        elif re.match(r'^[^aeiou][aeiouy][^aeiouy]+$', s):
            score += 2
        elif re.match(r'^[^aeiou][aeiouy][^aeiouy]', s):
            score += 1

        if s[0] == 'b': score += 2
        if s[0] in 'pgd' and s[1] != 'h': score += 1 # bilabial/voiced plosives
        if s[-1] == 't': score += 1
        if s[-2] == 't': score += 1

        score = int(score ** 1.25)
        return score

    def sentence(self):
        return self.values.total

    def word(self, i=None):
        if i is None:
            return [w.total for w in self.values]
        else:
            return self.values[i].total

    def syllable(self, i, j=None):
        if j is None:
            return list(self.values[i])
        else:
            return self.values[i][j]


plurals = set(['men', 'women', 'feet', 'geese', 'teeth', 'lice', 'mice',
               'children'])
def is_plural(word):
    word = word.lower()
    if word[-1] == 's' and word[-2] not in 'ius': return True
    return word in plurals

def buttify(text, scorer=scorer, rate=40, allow_single=False):
    sent = sentence(text)
    if len(sent) == 0 or (not allow_single and len(sent) == 1):
        raise ValueError("unbuttable")

    score = scorer(sent)
    if score.sentence() == 0:
        raise ValueError("unbuttable")

    count = min(score.sentence()/rate+1, max(len(sent)/4, 1))
    words = prob.weighted_sample(score.word(), count)

    curr_count = 0
    for i in words:
        syllable = prob.weighted_choice(score.syllable(i))
        for j in sent.related(i):
            buttify_word(sent, j, syllable)
            curr_count += 1
        if curr_count >= count:
            break

    return str(sent)

def buttify_word(sentence, word, syllable):
    butt = 'butt'

    # if the syllable has repeated characters, emulate that
    m = re.search(r'(.)\1{2,}', sentence[word][syllable])
    if m:
        butt = 'b' + 'u'*(m.end() - m.start()) + 'tt'

    if syllable == len(sentence[word])-1:
        if is_plural(str(sentence[word])): butt += 's'

    if sentence[word][syllable].isupper():
        sentence[word][syllable] = butt.upper()
    elif sentence[word][syllable].istitle():
        sentence[word][syllable] = butt.title()
    else:
        sentence[word][syllable] = butt.lower()

    # if there would be 3 't's in a row, remove one
    if (len(sentence[word]) > syllable+1 and
        sentence[word][syllable+1][0].lower() == 't'):
        sentence[word][syllable] = sentence[word][syllable][:-1]

    # if this is the first syllable and the previous word is "an", fix it
    if syllable == 0 and word > 0 and str(sentence[word-1]).lower() == 'an':
        sentence[word-1][0] = sentence[word-1][0][0:1]


if __name__ == '__main__':
    from optparse import OptionParser

    usage = 'usage: %prog [options] string'
    parser = OptionParser(usage=usage)
    parser.add_option('-1', '--allow-single',
                  action='store_true', dest='allow_single', default=False,
                  help='allow butting single-word sentences')
    parser.add_option('-s', '--score',
                  action='store_true', dest='score', default=False,
                  help='show sentence score')
    
    (options, args) = parser.parse_args()
    if len(args) != 1:
        print parser.get_usage()
        exit(1)

    if options.score:
        sent = sentence(args[0])
        score = scorer(sent)

        print "%d:" % score.sentence(),
        for i, word in enumerate(sent):
            if score.word(i) == 0:
                print "-".join(word)+"(0)",
            else:
                print "-".join(word)+"(%d: %s)" % (score.word(i),
                                                   score.syllable(i)),
    else:
        print buttify(args[0], allow_single=options.allow_single)
