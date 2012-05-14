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

    def __len__(self):
        return len(self.syllables)

    def __iter__(self):
        return iter(self.syllables)

    def __str__(self):
        return "".join(self.syllables)

class unword(word):
    def __init__(self, text):
        self.syllables = [text]

class sentence(object):
    words_ex = re.compile(r'([\W_]+)')
    space_ex = re.compile(r'\s')

    def __init__(self, text):
        self.words = self.words_ex.split(text)
        self.same_words = defaultdict(list)

        # rejoin any URLs together so they count as one (un)word
        i = 0
        urls = []
        while i < len(self.words):
            if self.words[i] == "www":
                start = i
            elif self.words[i] == "://" and i > 0:
                start = i-1
            else:
                i += 1
                continue

            end = len(self.words)
            for j in range(i, len(self.words)):
                if self.space_ex.search(self.words[j]):
                    end = j
                    break
            self.words[start:end] = ["".join(self.words[start:end])]
            urls.append(start)
            i = start+1

        # ignore zero-character words at the ends of the list
        self.min, self.max = 0, len(self.words)
        if self.words[self.min]   == '': self.min += 2
        if self.words[self.max-1] == '': self.max -= 2

        for werd, token in enumerate(range(self.min, self.max, 2)):
            if token in urls:
                self.words[token] = unword(self.words[token])
            else:
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

    def __iter__(self):
        for i in range(len(self)):
            yield self[i]

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
                       'hers', 'they', 'you', 'and', 'but', 'not', 'also', 
                       'from', 'for', 'once', 'been', 'have', 'had', 'who',
                       'what', 'where', 'when', 'why', 'how', 'has', 'had',
                       'have', 'yes', 'yeah', 'yah', 'yep', 'nah', 'nope',
                       'with', 'without'])
    block_sylls = set(['ing', 'sion', 'tion'])

    good_prewords = set(['the', 'an', 'a', 'my', 'your', 'his', 'her',
                         'our', 'their', 'to'])

    def __init__(self, sent):
        self.values = self._score_sentence(sent)

    def _score_sentence(self, sent):
        words = [self._score_word(werd) for werd in sent]

        for i in range(len(sent)):
            if words[i].total == 0: continue

            # words after good pre-words
            if i > 0:
                prev = str(sent[i-1]).lower()
                if prev in self.good_prewords:
                    words[i].total += 5

            # repeated words
            factor = 1.25 ** (len(sent.related(i))-1)
            words[i].total = int(words[i].total * factor)

        score = int(reduce(lambda x, y: x+y.total, words, 0) /
                    (len(words) ** 0.75))
        return scorer.score(score, words)

    def _score_word(self, werd):
        if (len(str(werd)) < 3 or str(werd).lower() in self.block_words or
            isinstance(werd, unword)):
            return scorer.score(0, [])

        sylls = [self._score_syllable(syll) for syll in werd]
        for i in range(len(werd)):
            if len(werd) == i+1: break
            # check if "butt" got split across syllables
            if werd[i] == 'but' and werd[i+1][0].lower() == 't':
                sylls[i] = 0

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

        return scorer.score(score, sylls)

    def _score_syllable(self, syll):
        syll = syll.lower()
        if syll in self.block_sylls: return 0
        if 'butt' in syll: return 0

        lengths = [0, 0, 1, 2, 3, 2, 2, 1]
        score = lengths[min(len(syll), len(lengths)-1)]
        if score == 0:
            return 0

        if re.match(r'^[^aeiou][aeiouy]([^aeiouy])\1', syll):
            score += 4
        elif re.match(r'^[^aeiou][aeiouy][^aeiouy]+$', syll):
            score += 2
        elif re.match(r'^[^aeiou][aeiouy][^aeiouy]', syll):
            score += 1

        if syll[0] == 'b': score += 2
        # bilabial/voiced plosives
        if syll[0] in 'pgd' and syll[1] != 'h': score += 1
        if syll[-1] == 't': score += 1
        if syll[-2] == 't': score += 1

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

past_tense = set([
    'ate', 'became', 'began', 'bent', 'blew', 'broke', 'bought', 'brought',
    'built', 'burnt', 'came', 'caught', 'chose', 'did', 'drew', 'drank',
    'dreamt', 'drove', 'dug', 'fell', 'flew', 'forgot', 'fought', 'found',
    'gave', 'grew', 'heard', 'held', 'hid', 'kept', 'knew', 'leapt', 'learnt',
    'made', 'meant', 'met', 'paid', 'ran', 'rang', 'said', 'sang', 'sank',
    'sent', 'shook', 'shot', 'slept', 'slid', 'sold', 'spent', 'spoke', 'stank',
    'stole', 'stood', 'stuck', 'swam', 'taught', 'threw', 'told', 'took',
    'tore', 'went', 'woke', 'won', 'wore', 'wrote'])
def is_past_tense(word):
    word = word.lower()
    if word[-2:] == 'ed': return True
    return word in past_tense

def score_sentence(text, scorer=scorer, allow_single=False):
    sent = sentence(text)
    if len(sent) == 0 or (not allow_single and len(sent) == 1):
        raise ValueError("sentence too short")

    score = scorer(sent)
    if score.sentence() == 0:
        raise ValueError("sentence has no buttable words")

    return sent, score

def buttify_sentence(sent, score, rate=40):
    count = min(sum(score.word())/rate+1, max(len(sent)/4, 1))
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
        if is_plural(str(sentence[word])):
            butt += 's'
        elif is_past_tense(str(sentence[word])):
            butt += 'ed'

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

def buttify(text, scorer=scorer, rate=50, allow_single=False):
    sent, score = score_sentence(text, scorer, allow_single)
    return buttify_sentence(sent, score)

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

        print "%f:" % score.sentence(),
        for i, word in enumerate(sent):
            if score.word(i) == 0:
                print "-".join(word)+"(0)",
            else:
                print "-".join(word)+"(%d: %s)" % (score.word(i),
                                                   score.syllable(i)),
    else:
        print buttify(args[0], allow_single=options.allow_single)
