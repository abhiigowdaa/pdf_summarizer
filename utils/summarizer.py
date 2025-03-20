from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.text_rank import TextRankSummarizer
import nltk

for resource in ['punkt', 'punkt_tab', 'stopwords']:
    nltk.download(resource, quiet=True)


def generate_summary(text):
    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    summarizer = TextRankSummarizer()
    summary_sentences = summarizer(parser.document, sentences_count=5)
    summary = " ".join(str(sentence) for sentence in summary_sentences)
    return summary
