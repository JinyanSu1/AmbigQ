import string
import regex as re

#################################
# Clarifying Question Utils
#################################

QA_INPUT = 'Question:'
QA_OUTPUT = 'Answer:'

ABSTAIN_OUTPUT = 'Abstain:'

CLARIFY_Q = 'Clarifying Question:'
CLARIFY_AS = 'Clarifying Answer Choices:'
CLARIFY_A = 'Clarifying Answer:'

def gen_clarify_q_prompt(
    qa_input,
    clarify_q=None,
):
    lines = []
    lines.append('{} {}'.format(QA_INPUT, qa_input.strip()))
    if clarify_q:
        lines.append('{} {}'.format(CLARIFY_Q, clarify_q.strip()))
        lines.append('')
    else:
        lines.append('{}'.format(CLARIFY_Q))

    return '\n'.join(lines)

def gen_clarify_a_prompt(
    qa_input,
    clarify_q,
    qa_output,
    clarify_a=None,
):
    lines = []
    lines.append('{} {}'.format(QA_INPUT, qa_input.strip()))
    lines.append('{} {}'.format(CLARIFY_Q, clarify_q.strip()))
    lines.append('{} {}'.format(QA_OUTPUT, qa_output.strip()))
    if clarify_a:
        lines.append('{} {}'.format(CLARIFY_A, clarify_a.strip()))
        lines.append('')
    else:
        lines.append('{}'.format(CLARIFY_A))
    return '\n'.join(lines)

def gen_direct_qa_output_prompt(
    qa_input,
    qa_output=None,
):
    lines = []
    lines.append('{} {}'.format(QA_INPUT, qa_input.strip()))
    if qa_output:
        lines.append('{} {}'.format(QA_OUTPUT, qa_output.strip()))
        lines.append('')
    else:
        lines.append('{}'.format(QA_OUTPUT))

    return '\n'.join(lines)

def gen_qa_output_prompt(
    qa_input,
    clarify_q,
    clarify_a,
    qa_output=None,
):
    lines = []
    lines.append('{} {}'.format(QA_INPUT, qa_input.strip()))
    lines.append('{} {}'.format(CLARIFY_Q, clarify_q.strip()))
    lines.append('{} {}'.format(CLARIFY_A, clarify_a.strip()))
    if qa_output:
        lines.append('{} {}'.format(QA_OUTPUT, qa_output.strip()))
        lines.append('')
    else:
        lines.append('{}'.format(QA_OUTPUT))

    return '\n'.join(lines)


#################################
# General Utils
#################################

def batched(iterable, n):
    return [iterable[batch_start:batch_start+n] for batch_start in range(0, len(iterable), n)]

def partitioned(iterable, n):
    partition_size = len(iterable) // n + bool(len(iterable) % n)
    partitions = batched(iterable, partition_size)
    assert len(partitions) == n
    return partitions

#################################
# QA Utils
#################################


def normalize(s):
    if s is None:
        return None
    """Lower text and remove punctuation, articles and extra whitespace."""
    def remove_articles(text):
        return re.sub(r'\b(a|an|the)\b', ' ', text)
    def white_space_fix(text):
        return ''.join(text.split())
    def remove_punc(text):
        exclude = set(string.punctuation)
        return ''.join(ch for ch in text if ch not in exclude)
    def lower(text):
        return text.lower()
    return white_space_fix(remove_articles(remove_punc(lower(s))))




