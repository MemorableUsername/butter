import math
import prob
import re

from hyphenate import hyphenate_word

class word(object):
    camelcase_ex = re.compile(r'((?:\w*?[a-z])(?=(?:[A-Z]|$))|[A-Z]+)')

    def __init__(self, text):
        # if the word is camelCase (or similar), break it into pieces
        chunks = self.camelcase_ex.findall(text) or [text]
        self.syllables = reduce(lambda x,y: x+hyphenate_word(y), chunks, [])

    def __getitem__(self, i):
        return self.syllables[i]

    def __setitem__(self, i, value):
        self.syllables[i] = value

    def __str__(self):
        return "".join(self.syllables)

    def __len__(self):
        return len(self.syllables)

class sentence(object):
    words_ex = re.compile(r'(\W+)')

    def __init__(self, text):
        self.words = self.words_ex.split(text)

        # ignore zero-character words at the ends of the list
        self.min, self.max = 0, len(self.words)
        if self.words[self.min]   == '': self.min += 2
        if self.words[self.max-1] == '': self.max -= 2

        for i in range(self.min, self.max, 2):
            self.words[i] = word(self.words[i])

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

    block_words = set(['the', 'are', 'was', 'were', 'will', 'would', 'could', 
                       'should', 'can', 'does', 'doesn', 'don', 'this', 'that',
                       'these', 'those', 'there', 'their', 'she', 'him', 'her',
                       'its', 'his', 'hers', 'they', 'you', 'and', 'from',
                       'for', 'once', 'been', 'have', 'had', 'who', 'what',
                       'where', 'when', 'why', 'how', 'has', 'had', 'have'])
    block_sylls = set(['ing', 'tion'])

    good_prewords = set(['the', 'an', 'a', 'my', 'your', 'his', 'her',
                         'our', 'their'])

    def __init__(self, sent):
        self.values = self._score_sentence(sent)

    def _score_sentence(self, sent):
        words = [self._score_word(sent, i) for i in range(len(sent))]
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
                score += 3

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


plurals = set(['men', 'women', 'goose', 'mice', 'children', 'feet', 'teeth'])
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

    for i in words:
        buttify_word(sent, i, score.syllable(i))

    return str(sent)

def buttify_word(sent, i, scores):
    butt = 'butt'
    j = prob.weighted_choice(scores)

    if j == len(sent[i])-1:
        if is_plural(str(sent[i])): butt = 'butts'

    if sent[i][j].isupper():
        sent[i][j] = butt.upper()
    elif sent[i][j].istitle():
        sent[i][j] = butt.title()
    else:
        sent[i][j] = butt.lower()

    # if there would be 3 't's in a row, remove one
    if len(sent[i]) > j+1 and sent[i][j+1][0].lower() == 't':
        sent[i][j] = sent[i][j][:-1]

    if j==0 and i>0 and str(sent[i-1]).lower() == 'an':
        sent[i-1][0] = sent[i-1][0][0:1]


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
