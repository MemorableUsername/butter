import math
import prob
import re

from hyphenate import hyphenate_word

class word(object):
    def __init__(self, text):
        # if the word is camelCase (or similar), break it into pieces
        chunks = re.findall(r'(\w*?[a-z])(?=(?:[A-Z]|$))', text) or [text]
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
        self.words = sentence.words_ex.split(text)
        for i in range(0, len(self.words), 2):
            self.words[i] = word(self.words[i])

    def __getitem__(self, i):
        return self.words[i*2] # skip spaces

    def __len__(self):
        return (len(self.words)+1)/2

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
                       'should', 'can', 'does', 'doesn', 'this', 'that',
                       'these', 'those', 'there', 'their', 'she', 'him', 'her',
                       'its', 'his', 'hers', 'they', 'you', 'and', 'from',
                       'for', 'once', 'been', 'have', 'had', 'who', 'what',
                       'where', 'when', 'why', 'how'])
    block_sylls = set(['ing', 'butt', 'tion'])

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

        if i>0:
            prev = str(sent[i-1]).lower()
            if prev == 'the' or prev == 'a' or prev == 'an':
                score += 3

        return scorer.score(score, sylls)

    def _score_syllable(self, sent, i, j):
        s = sent[i][j].lower()
        if s in self.block_sylls: return 0

        lengths = [0, 0, 1, 2, 4, 2, 2, 1]
        score = lengths[min(len(s), len(lengths)-1)]
        if score == 0:
            return 0

        if re.match(r'^[^aeiou][aeiouy]([^aeiouy])\1', s):
            score += 6
        elif re.match(r'^[^aeiou][aeiouy][^aeiouy]+$', s):
            score += 2
        elif re.match(r'^[^aeiou][aeiouy][^aeiouy]', s):
            score += 1

        if s[0]  == 'b': score += 2
        if s[-1] == 't': score += 1
        if s[-2] == 't': score += 1

        score = int(score ** 1.5)
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
    if word[-1] == 's' and word[-2] not in 'ui': return True
    return word in plurals

def buttify(text, scorer=scorer, rate=50, allow_single=False):
    sent = sentence(text)
    if len(sent) == 0 or (not allow_single and len(sent) == 1):
        raise ValueError("unbuttable")

    score = scorer(sent)
    if score.sentence() == 0:
        raise ValueError("unbuttable")

    count = score.sentence()/rate+1
    words = prob.weighted_sample(score.word(), count)

    for i in words:
        buttify_word(sent, i, score.syllable(i))

    return str(sent)

def buttify_word(sent, i, scores):
    butt = 'butt'
    if len(sent[i]) == 1:
        if is_plural(str(sent[i])): butt = 'butts'
        j = 0
    else:
        j = prob.weighted_choice(scores)

    if sent[i][j].isupper():
        sent[i][j] = butt.upper()
    elif sent[i][j].istitle():
        sent[i][j] = butt.title()
    else:
        sent[i][j] = butt.lower()

    # if there would be 3 't's in a row, remove one
    if len(sent[i]) > j+1 and sent[i][j+1][0].lower() == 't':
        sent[i][j] = sent[i][j][:-1]
        
    if i>0 and str(sent[i-1]).lower() == 'an':
        sent[i-1][0] = sent[i-1][0][0:1]


if __name__ == "__main__":
    import sys
    print buttify(sys.argv[1], allow_single=True)
